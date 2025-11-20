import streamlit as st
import json
from utils.report_generator import generate_brand_book_html
from utils.sitemap_parser import ingest_sitemap

def render_settings(selected_project, strategist, vector_db, file_manager, API_KEY):
    """
    Renders the Settings page.
    
    Args:
        selected_project: Name of the currently selected project
        strategist: Strategist agent instance
        vector_db: VectorDB instance
        file_manager: FileManager instance
        API_KEY: Gemini API key
    """
    st.title("⚙️ Налаштування Проекту")
    
    # Load Project Data
    tov = file_manager.read_file(selected_project, "tov.md")
    assets = file_manager.get_asset_names(selected_project)
    
    # Tabs for different settings
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📢 Tone of Voice", "👥 Персони", "🖼️ Асети", "🗺️ CJM", "📤 Експорт", "📚 База Знань", "🔑 Ключові слова"])
    
    with tab1:
        st.subheader("📢 Tone of Voice (Голос Бренду)")
        
        if tov:
            st.markdown(tov)
        else:
            st.info("Tone of Voice ще не налаштовано.")
            
        with st.expander("✏️ Редагувати Tone of Voice"):
            tov_content = st.text_area("Markdown редактор", value=tov, height=400, key="tov_settings")
            if st.button("💾 Зберегти ToV"):
                file_manager.save_file(selected_project, "tov.md", tov_content)
                st.success("ToV збережено!")
                st.rerun()
    
    with tab2:
        st.subheader("Персони вашої аудиторії")
        
        # Load config to get personas
        try:
            config_path = file_manager.get_project_path(selected_project) / "config.json"
            if config_path.exists():
                config = json.loads(config_path.read_text(encoding="utf-8"))
                audience_text = config.get("audience", "")
                
                if audience_text:
                    # Display personas in markdown
                    st.markdown(audience_text)
                    
                    # Edit option
                    with st.expander("✏️ Редагувати персони"):
                        edited_audience = st.text_area(
                            "Опис аудиторії",
                            value=audience_text,
                            height=400,
                            key="audience_settings"
                        )
                        if st.button("💾 Зберегти зміни"):
                            config["audience"] = edited_audience
                            config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")
                            st.success("Персони оновлено!")
                            st.rerun()
                else:
                    st.info("Персони ще не створені. Створіть новий проект з персонами або додайте їх вручну.")
                    
                    # Option to generate personas for existing project
                    if st.button("✨ Згенерувати персони для цього проекту"):
                        with st.spinner("Створюю персони..."):
                            try:
                                brand_name = config.get("brand_name", selected_project)
                                industry = config.get("industry", "")
                                url = config.get("website_url", "")
                                
                                personas_text = strategist.generate_audience(
                                    brand_name,
                                    industry,
                                    url,
                                    business_model="B2C",
                                    num_personas=2
                                )
                                config["audience"] = personas_text
                                config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")
                                config["audience"] = personas_text
                                st.success("Персони згенеровано!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Помилка: {e}")
            else:
                st.warning("Файл config.json не знайдено. Це старий проект без персон.")
        except Exception as e:
            st.error(f"Помилка завантаження персон: {e}")
    
    with tab3:
        st.subheader("Завантаження Асетів")
        uploaded_file = st.file_uploader("Завантажити зображення", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_file:
            file_manager.save_asset(selected_project, uploaded_file.name, uploaded_file.read())
            st.success(f"Файл {uploaded_file.name} завантажено!")
            st.rerun()
        
        if assets:
            st.write("**Завантажені асети:**")
            for asset in assets:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(asset)
                with col2:
                    if st.button("🗑️", key=f"del_{asset}"):
                        file_manager.delete_asset(selected_project, asset)
                        st.rerun()

    with tab4:
        st.subheader("🗺️ Customer Journey Map (CJM)")
        st.info("Карта шляху клієнта допомагає зрозуміти досвід користувача на кожному етапі.")
        
        # Load config for CJM
        try:
            config_path = file_manager.get_project_path(selected_project) / "config.json"
            if config_path.exists():
                config = json.loads(config_path.read_text(encoding="utf-8"))
                current_cjm = config.get("cjm", "")
                
                if current_cjm:
                    st.markdown("### 🗺️ Поточна Карта")
                    
                    # Try to parse and display as dataframe
                    try:
                        df = _parse_cjm_markdown(current_cjm)
                        if df is not None and not df.empty:
                            # Option to transpose for better readability
                            show_transposed = st.checkbox("🔄 Транспонувати таблицю (зручно для мобільних)", value=False)
                            
                            if show_transposed:
                                st.dataframe(df.T, use_container_width=True)
                            else:
                                st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("Не вдалося розпізнати таблицю. Показую як текст.")
                            st.markdown(current_cjm, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f"Помилка відображення таблиці: {e}")
                        st.markdown(current_cjm, unsafe_allow_html=True)
                    
                    with st.expander("✏️ Редагувати CJM"):
                        new_cjm = st.text_area("Markdown CJM", value=current_cjm, height=400)
                        if st.button("💾 Зберегти CJM"):
                            config["cjm"] = new_cjm
                            config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")
                            st.success("CJM оновлено!")
                            st.rerun()


                else:
                    st.write("CJM ще не створено.")
                    if st.button("✨ Згенерувати CJM (ШІ)"):
                        if not config.get("audience"):
                            st.error("Спочатку створіть Персони (вкладка 'Персони')!")
                        else:
                            with st.spinner("Аналізую шлях клієнта..."):
                                try:
                                    cjm = strategist.generate_cjm(
                                        config.get("brand_name"),
                                        config.get("industry"),
                                        config.get("audience")
                                    )
                                    config["cjm"] = cjm
                                    config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")
                                    st.success("CJM створено!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Помилка: {e}")
            else:
                st.warning("Конфігурація проекту не знайдена.")
        except Exception as e:
            st.error(f"Помилка завантаження CJM: {e}")

    with tab5:
        st.subheader("📤 Експорт Бренд-буку")
        st.info("Згенеруйте та завантажте повний бренд-бук у форматі HTML.")
        
        if st.button("📄 Згенерувати Бренд-бук", type="primary"):
            with st.spinner("Генерую документ..."):
                try:
                    # Gather data
                    brand_name = selected_project
                    
                    # Get ToV
                    tov_text = file_manager.read_file(selected_project, "tov.md")
                    
                    # Get Personas & CJM from config
                    config_path = file_manager.get_project_path(selected_project) / "config.json"
                    personas_text = ""
                    cjm_text = ""
                    
                    if config_path.exists():
                        config = json.loads(config_path.read_text(encoding="utf-8"))
                        personas_text = config.get("audience", "")
                        cjm_text = config.get("cjm", "")
                    
                    # Generate HTML
                    html_content = generate_brand_book_html(brand_name, tov_text, personas_text, cjm_text)
                    
                    # Offer download
                    st.success("✅ Бренд-бук успішно згенеровано!")
                    st.download_button(
                        label="💾 Завантажити Brand Book (HTML)",
                        data=html_content,
                        file_name=f"BrandBook_{brand_name}.html",
                        mime="text/html"
                    )
                    
                except Exception as e:
                    st.error(f"Помилка генерації: {e}")

    with tab6:
        st.subheader("📚 База Знань (Sitemap)")
        st.info("Завантажте карту сайту, щоб ШІ знав про ваші існуючі сторінки і міг робити внутрішню перелінковку.")
        
        sitemap_url = st.text_input("URL Sitemap.xml", placeholder="https://example.com/sitemap.xml")
        
        max_pages = 10000  # Full crawl
        
        if st.button("📥 Завантажити Sitemap (Full)", type="primary"):
            if not sitemap_url:
                st.error("Введіть URL!")
            else:
                with st.spinner("Сканую карту сайту у багатопотоковому режимі (це займе 1-2 хвилини)..."):
                    try:
                        # 1. Parse Sitemap
                        st.info("Збираю всі посилання та сканую сторінки...")
                        
                        # Create a placeholder for progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Run ingestion
                        df = ingest_sitemap(sitemap_url, max_pages=max_pages)
                        
                        progress_bar.progress(100)
                        status_text.text("Готово!")
                        
                        if df.empty:
                            st.error("Не знайдено жодної сторінки!")
                        else:
                            st.success(f"✅ Завантажено {len(df)} сторінок!")
                            
                            # 2. Save to CSV
                            csv_path = file_manager.get_project_path(selected_project) / "pages.csv"
                            df.to_csv(csv_path, index=False, encoding='utf-8')
                            st.info(f"Збережено в: {csv_path}")
                            
                            # 3. Ingest into Vector DB
                            with st.spinner("Індексую в векторну базу даних..."):
                                vector_db.add_pages(selected_project, df)
                            
                            st.success("🎉 База знань оновлена! Тепер ШІ може робити внутрішню перелінковку.")
                            
                            # Show preview
                            with st.expander("Переглянути завантажені сторінки"):
                                st.dataframe(df[['url', 'title']].head(20))
                    
                    except Exception as e:
                        st.error(f"Помилка: {e}")
                        import traceback
                        st.code(traceback.format_exc())

    with tab7:
        st.subheader("🔑 Семантичне Ядро")
        st.markdown("Завантажте CSV або Excel файл з ключовими словами (має бути колонка 'keyword').")
        
        uploaded_file = st.file_uploader("Завантажити файл", type=["csv", "xlsx"])
        
        if uploaded_file:
            try:
                import pandas as pd
                
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                    
                if 'keyword' in df.columns:
                    # Save as CSV internally
                    csv_data = df.to_csv(index=False)
                    file_manager.save_file(selected_project, "semantic_core.csv", csv_data)
                    st.success(f"✅ Семантичне ядро оновлено! ({len(df)} ключів)")
                    st.dataframe(df.head(), use_container_width=True)
                else:
                    st.error("❌ Файл повинен містити колонку 'keyword'")
            except Exception as e:
                st.error(f"Помилка читання файлу: {e}")
        
        # Show current keywords
        current_csv = file_manager.read_file(selected_project, "semantic_core.csv")
        if current_csv:
            st.divider()
            st.write("**Поточні ключові слова:**")
            from io import StringIO
            import pandas as pd
            df = pd.read_csv(StringIO(current_csv))
            st.dataframe(df, use_container_width=True)


def _parse_cjm_markdown(md_text):
    """Parses a markdown table into a pandas DataFrame."""
    import pandas as pd
    import re
    
    lines = md_text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]
    
    if len(lines) < 3:
        return None
        
    # Find header row
    header_row = lines[0]
    if not header_row.startswith('|'):
        return None
        
    # Helper to clean cell content
    def clean_cell(cell):
        # Remove bold/italic markdown
        cell = re.sub(r'\*\*(.*?)\*\*', r'\1', cell) # Bold
        cell = re.sub(r'\*(.*?)\*', r'\1', cell)     # Italic
        return cell.strip()

    # Parse headers
    headers = [clean_cell(c) for c in header_row.strip('|').split('|')]
    
    # Parse data
    data = []
    for line in lines[2:]: # Skip header and separator
        if not line.startswith('|'):
            continue
            
        row = [clean_cell(c) for c in line.strip('|').split('|')]
        
        # Pad row if it's shorter than headers
        if len(row) < len(headers):
            row += [''] * (len(headers) - len(row))
        # Truncate row if it's longer
        elif len(row) > len(headers):
            row = row[:len(headers)]
            
        data.append(row)
        
    if data:
        return pd.DataFrame(data, columns=headers)
    return None
