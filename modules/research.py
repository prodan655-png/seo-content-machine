import streamlit as st
from utils.state_manager import save_state

def render_research(selected_project, strategist, API_KEY, file_manager):
    """
    Renders the Research page with Topic Ideas and SERP Analysis tabs.
    
    Args:
        selected_project: Name of the currently selected project
        strategist: Strategist agent instance
        API_KEY: Gemini API key
        file_manager: FileManager instance
    """
    st.title("🔍 Дослідження та Аналіз")
    
    # Tabs for different research features
    research_tab1, research_tab2, research_tab3 = st.tabs(["💡 Ідеї Тем", "🔎 SERP Аналіз", "🔑 Генератор Ключів"])
    
    with research_tab1:
        _render_topic_ideas(selected_project, strategist, API_KEY, file_manager)
    
    with research_tab2:
        _render_serp_analysis(selected_project, strategist, API_KEY)

    with research_tab3:
        _render_keyword_generator(selected_project, strategist, API_KEY, file_manager)
    
    # Display research results if available
    if st.session_state.get('research_data'):
        _display_research_results(selected_project, strategist, file_manager)


def _render_topic_ideas(selected_project, strategist, API_KEY, file_manager):
    """Renders the Topic Ideas generator tab."""
    st.subheader("💡 Генератор Ідей Тем")
    st.markdown("Введіть вашу нішу, і я згенерую 10 ідей для статей.")
    
    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        niche_input = st.text_input("Ніша/Індустрія", placeholder="напр. Випічка, Фітнес, Електроніка")
    
    # Context Options
    with st.expander("🧠 Додатковий контекст (для кращих ідей)"):
        # Check for sitemap
        pages_content = file_manager.read_file(selected_project, "pages.csv")
        has_sitemap = pages_content is not None and len(pages_content) > 10
        
        # Check for competitor data
        has_competitors = False # Placeholder, as we don't have a global competitor DB yet
        
        c1, c2 = st.columns(2)
        with c1:
            use_competitors = st.checkbox("Використати аналіз конкурентів", value=True, disabled=not has_competitors)
            if not has_competitors:
                st.caption("❌ Дані конкурентів відсутні")
            else:
                st.caption("✅ Дані доступні")
                
        with c2:
            use_sitemap = st.checkbox("Використати карту сайту", value=has_sitemap, disabled=not has_sitemap)
            if has_sitemap:
                page_count = len(pages_content.split('\n')) - 1
                st.caption(f"✅ Sitemap завантажено ({page_count} сторінок)")
            else:
                st.caption("❌ Sitemap відсутній (завантажте в Налаштуваннях)")
    
    with col2:
        generate_topics_btn = st.button("🚀 Генерувати", use_container_width=True)
    
    if generate_topics_btn and niche_input:
        if not API_KEY:
            st.error("⚠️ API Key не знайдено!")
        else:
            with st.spinner(f"Генерую ідеї для: {niche_input}..."):
                try:
                    # Gather context
                    context_data = ""
                    if use_competitors:
                        # Try to load competitor data from previous research
                        pass # For now, we don't have a global competitor DB, but we could load from files
                    
                    if use_sitemap:
                        # Load sitemap pages
                        pages_csv = file_manager.read_file(selected_project, "pages.csv")
                        if pages_csv:
                            context_data += f"Existing pages on site (DO NOT DUPLICATE):\n{pages_csv[:2000]}\n"
                            
                    topics = strategist.generate_topic_ideas(niche_input, num_topics=10, context_data=context_data)
                    st.session_state.topic_ideas = topics
                    st.success(f"Згенеровано {len(topics)} ідей!")
                except Exception as e:
                    st.error(f"Помилка: {e}")
    
    if st.session_state.get('topic_ideas'):
        st.divider()
        st.markdown("### 📋 Згенеровані Теми")
        for i, topic in enumerate(st.session_state.topic_ideas, 1):
            with st.expander(f"**{i}. {topic.get('title', 'Без назви')}**"):
                st.markdown(topic.get('description', 'Опис відсутній'))
                if st.button(f"Використати цю тему", key=f"use_topic_{i}"):
                    st.session_state.selected_topic_for_analysis = topic.get('title')
                    st.success(f"Тема обрана! Перейдіть до вкладки 'SERP Аналіз'")


def _render_keyword_generator(selected_project, strategist, API_KEY, file_manager):
    """Renders the Keyword Generator tab."""
    st.subheader("🔑 Генератор Ключових Слів")
    st.markdown("Згенеруйте семантичне ядро для вашої теми.")
    
    topic_input = st.text_input("Тема для підбору ключів", value=st.session_state.get('selected_topic_for_analysis', ''))
    
    if st.button("🎲 Згенерувати Ключі"):
        if not topic_input:
            st.error("Введіть тему!")
        else:
            with st.spinner("Підбираю ключові слова..."):
                try:
                    keywords = strategist.generate_keywords(topic_input)
                    st.session_state.generated_keywords = keywords
                except Exception as e:
                    st.error(f"Помилка: {e}")

    if st.session_state.get('generated_keywords'):
        import pandas as pd
        df = pd.DataFrame(st.session_state.generated_keywords)
        st.dataframe(df, use_container_width=True)
        
        # Save option
        if st.button("💾 Зберегти в Semantic Core"):
            # Convert to CSV string
            csv_data = df.to_csv(index=False)
            file_manager.save_file(selected_project, "semantic_core.csv", csv_data)
            st.success("✅ Ключі збережено в проект!")


def _render_serp_analysis(selected_project, strategist, API_KEY):
    """Renders the SERP Analysis tab."""
    st.subheader("🔎 SERP Аналіз")
    
    # Pre-fill if topic was selected from Topic Ideas
    default_topic = st.session_state.get('selected_topic_for_analysis', '')

    with st.form(key='search_form'):
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            topic = st.text_input("Введіть тему", placeholder="напр. Пресовані дріжджі", value=default_topic)
        with col2:
            analyze_btn = st.form_submit_button("🚀 Аналізувати", use_container_width=True)
    
    if analyze_btn:
        if not API_KEY:
            st.error("⚠️ API Key не знайдено! Перевірте .env файл.")
        else:
            with st.spinner(f"Аналізую видачу для: {topic}..."):
                try:
                    serp_data = strategist.analyze_serp(topic)
                    st.session_state.research_data = serp_data
                    
                    # Save state
                    save_state(selected_project, {
                        'research_data': serp_data,
                        'selected_project': selected_project
                    })
                    
                    st.success(f"Аналіз завершено: {topic}")
                except Exception as e:
                    st.error(f"Помилка аналізу: {e}")


def _display_research_results(selected_project, strategist, file_manager):
    """Displays SERP analysis results."""
    data = st.session_state.research_data
    
    # Intent & Features
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**Інтент (Намір):** {data.get('intent', 'Не визначено')}")
    with c2:
        feats = ", ".join(data.get('serp_features', []))
        st.warning(f"**SERP Фічі:** {feats if feats else 'Немає особливих фіч'}")
    
    st.subheader("🔍 Інсайти з Конкурентів")
    
    # Competitors Accordion
    if data.get('competitor_outlines'):
        for comp in data['competitor_outlines']:
            with st.expander(f"📄 {comp.get('h1', 'No Title')} ({comp['url']})"):
                st.write("**Структура:**")
                for h in comp.get('structure', []):
                    st.text(h)
    else:
        st.info("Детальні аутлайни конкурентів ще не завантажені. Натисніть кнопку нижче.")
        
        if st.button("📥 Завантажити структури конкурентів"):
            with st.spinner("Сканую сайти конкурентів..."):
                try:
                    urls = [r['url'] for r in data['competitors']]
                    outlines = strategist.analyze_competitors(urls)
                    st.session_state.research_data['competitor_outlines'] = outlines
                    
                    # Save state
                    save_state(selected_project, {'research_data': st.session_state.research_data})
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Не вдалося завантажити структури: {e}")
