import streamlit as st

def render_dashboard(selected_project, file_manager, assets):
    """
    Renders the Dashboard page showing project statistics.
    
    Args:
        selected_project: Name of the currently selected project
        file_manager: FileManager instance
        assets: List of asset filenames
    """
    st.title("📊 Панель Керування")
    st.markdown(f"### Поточний проект: **{selected_project}**")
    
    # Real Metrics
    project_path = file_manager.get_project_path(selected_project)
    total_files = len(list(project_path.glob("*.*")))
    assets_count = len(assets)
    
    # Check ToV status
    tov = file_manager.read_file(selected_project, "tov.md")
    tov_status = "✅ Заповнено" if len(tov) > 50 else "⚠️ Порожньо"
    
    # Metrics with tooltips
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📂 Файлів у проекті", 
            value=total_files,
            help="Загальна кількість файлів у папці проекту (статті, зображення, конфіги)."
        )
        
    with col2:
        st.metric(
            label="🖼️ Асетів", 
            value=assets_count,
            help="Кількість завантажених зображень та інших медіа-файлів."
        )
        
    with col3:
        st.metric(
            label="📢 Статус ToV", 
            value="Заповнено" if len(tov) > 50 else "Порожньо",
            delta="OK" if len(tov) > 50 else "Потрібно заповнити",
            help="Чи налаштований Tone of Voice для цього проекту. Це критично для якості генерації."
        )

    st.divider()
    st.subheader("📚 Збережені Статті")
    
    # List articles
    articles_dir = file_manager.get_project_path(selected_project) / "articles"
    if articles_dir.exists():
        articles = sorted(list(articles_dir.glob("*.md")), reverse=True)
        
        if not articles:
            st.info("Немає збережених статей.")
        else:
            for article_path in articles:
                with st.expander(f"📄 {article_path.name}"):
                    content = article_path.read_text(encoding='utf-8')
                    st.markdown(content[:500] + "...") # Preview
                    
                    col_d1, col_d2 = st.columns([1, 4])
                    with col_d1:
                        st.download_button(
                            label="💾 Завантажити MD",
                            data=content,
                            file_name=article_path.name,
                            mime="text/markdown",
                            key=f"dl_{article_path.name}"
                        )
    else:
        st.info("Папка зі статтями ще не створена.")
