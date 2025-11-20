import streamlit as st
from utils.keyword_loader import load_keywords_from_csv
from utils.state_manager import save_state

def render_write(selected_project, writer, coder, file_manager):
    """
    Renders the Write page for content generation.
    
    Args:
        selected_project: Name of the currently selected project
        writer: Writer agent instance
        coder: Coder agent instance
        file_manager: FileManager instance
    """
    st.title("✍️ Генератор Контенту")
    
    if not st.session_state.research_data:
        st.warning("⚠️ Спочатку проведіть дослідження у вкладці '🔍 Дослідження'!")
    else:
        st.markdown(f"### Тема: {st.session_state.research_data['topic']}")
        
        # Step 1: Outline
        if st.button("📝 Згенерувати План (Outline)"):
            with st.spinner("Створюю структуру статті..."):
                # Load ToV
                tov = file_manager.get_tov(selected_project)
                outline = writer.generate_outline(st.session_state.research_data, tov)
                st.session_state.current_outline = outline
                st.rerun()
        
        if st.session_state.current_outline:
            st.subheader("Редагування Плану")
            # Editable JSON is okay for MVP, maybe a better UI later
            edited_outline = st.data_editor(
                st.session_state.current_outline,
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("✅ Затвердити План і Написати Статтю", use_container_width=True):
                with st.spinner("Пишу статтю (це може зайняти хвилину)..."):
                    tov = file_manager.get_tov(selected_project)
                    keywords = load_keywords_from_csv(selected_project, file_manager, top_n=5)
                    
                    # Load internal links
                    pages_content = file_manager.read_file(selected_project, "pages.csv")
                    internal_links = pages_content if pages_content else None
                    
                    article = writer.write_article(edited_outline, tov, keywords, internal_links=internal_links)
                    st.session_state.generated_article = article
                    
                    # Save article to project folder (archive)
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_slug = st.session_state.research_data.get('topic', 'article').replace(' ', '_')[:50]
                    
                    # Create articles folder if not exists
                    articles_dir = file_manager.get_project_path(selected_project) / "articles"
                    articles_dir.mkdir(exist_ok=True)
                    
                    # Save Markdown
                    article_filename = f"{timestamp}_{topic_slug}.md"
                    (articles_dir / article_filename).write_text(article, encoding='utf-8')
                    
                    # Save state
                    save_state(selected_project, {
                        'generated_article': article,
                        'current_outline': edited_outline,
                        'last_article_file': str(articles_dir / article_filename),
                        'selected_project': selected_project
                    })
                    
                    st.success(f"✅ Стаття збережена: {article_filename}")
                    st.rerun()

        # Step 2: Article Review
        if st.session_state.generated_article:
            st.divider()
            st.subheader("📄 Готова Стаття")
            tab1, tab2, tab3 = st.tabs(["👁️ Попередній перегляд", "💻 HTML Код", "📊 SEO Аудит"])
            
            with tab1:
                st.markdown(st.session_state.generated_article)
                
                # Explicit Save Button
                if st.button("💾 Зберегти статтю в проект", key="save_article_btn"):
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_slug = st.session_state.research_data.get('topic', 'article').replace(' ', '_')[:50]
                    
                    articles_dir = file_manager.get_project_path(selected_project) / "articles"
                    articles_dir.mkdir(exist_ok=True)
                    
                    article_filename = f"{timestamp}_{topic_slug}.md"
                    (articles_dir / article_filename).write_text(st.session_state.generated_article, encoding='utf-8')
                    
                    st.success(f"✅ Стаття успішно збережена: {article_filename}")
            
            with tab2:
                html_content = coder.convert_to_html(st.session_state.generated_article)
                st.code(html_content, language='html')
                
                st.download_button(
                    label="💾 Завантажити HTML",
                    data=html_content,
                    file_name=f"{st.session_state.research_data['topic']}.html",
                    mime="text/html"
                )

            with tab3:
                from utils.seo_scorer import calculate_seo_score
                
                st.subheader("SEO Аудит Статті")
                
                col_audit, col_rewrite = st.columns([1, 1])
                
                with col_audit:
                    audit_btn = st.button("🔍 Провести Аудит", use_container_width=True)
                
                if audit_btn:
                    html_content = coder.convert_to_html(st.session_state.generated_article)
                    keywords = load_keywords_from_csv(selected_project, file_manager, top_n=5)
                    
                    if not keywords:
                        st.warning("⚠️ Ключові слова не знайдено! Завантажте їх у налаштуваннях або згенеруйте у вкладці 'Дослідження'.")
                    else:
                        st.info(f"Використовую ключі: {', '.join(keywords)}")
                    
                    tov_rules = {} 
                    
                    audit_result = calculate_seo_score(html_content, keywords, tov_rules)
                    st.session_state.audit_result = audit_result # Save audit result
                
                if st.session_state.get('audit_result'):
                    audit_result = st.session_state.audit_result
                    
                    # Display Score
                    score = audit_result['score']
                    if score >= 80:
                        st.success(f"SEO Score: {score}/100 🚀")
                    elif score >= 50:
                        st.warning(f"SEO Score: {score}/100 ⚠️")
                    else:
                        st.error(f"SEO Score: {score}/100 ❌")
                    
                    # Display Feedback
                    if audit_result['feedback']:
                        st.write("**Рекомендації:**")
                        for item in audit_result['feedback']:
                            st.info(f"• {item}")
                    
                    # Display Missing Keywords
                    if audit_result['missing_keywords']:
                        st.write("**Відсутні ключові слова:**")
                        st.write(", ".join(audit_result['missing_keywords']))
                        
                    # Rewrite Button
                    st.divider()
                    st.write("### 🔄 Покращення")
                    if st.button("✨ Переписати статтю з урахуванням аудиту", type="primary"):
                        with st.spinner("Переписую статтю..."):
                            tov = file_manager.get_tov(selected_project)
                            feedback_str = "\n".join(audit_result['feedback'])
                            missing_kw_str = ", ".join(audit_result['missing_keywords'])
                            full_feedback = f"Fix these issues:\n{feedback_str}\n\nInclude missing keywords:\n{missing_kw_str}"
                            
                            new_article = writer.rewrite_article(st.session_state.generated_article, full_feedback, tov)
                            st.session_state.generated_article = new_article
                            st.session_state.audit_result = None # Reset audit
                            st.success("✅ Статтю оновлено! Перевірте вкладку 'Попередній перегляд'.")
                            st.rerun()
