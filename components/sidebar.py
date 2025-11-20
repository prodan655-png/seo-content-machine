import streamlit as st
from utils.state_manager import load_state

def render_sidebar(file_manager):
    """
    Renders the sidebar for project selection and management.
    
    Args:
        file_manager: FileManager instance
        
    Returns:
        selected_option: The name of the selected project or "Create New..."
    """
    st.sidebar.title("🚀 SEO Machine")
    
    # Project Selection Logic
    projects = file_manager.list_projects()
    
    # Session State for Project Selection
    if 'selected_project' not in st.session_state:
        st.session_state['selected_project'] = projects[0] if projects else None
    
    # Project Selector
    project_options = ["Create New..."] + projects
    # Find index of current selection
    try:
        index = project_options.index(st.session_state['selected_project']) if st.session_state['selected_project'] in project_options else 0
    except ValueError:
        index = 0
    
    selected_option = st.sidebar.selectbox("Select Project", project_options, index=index)
    
    # Auto-load state when project changes
    if selected_option != "Create New..." and selected_option != st.session_state.get('selected_project'):
        st.session_state['selected_project'] = selected_option
        # Load saved state
        saved_state = load_state(selected_option)
        for key, value in saved_state.items():
            st.session_state[key] = value
            
    # Delete Project Button (only show if a project is selected)
    if selected_option != "Create New..." and selected_option:
        st.sidebar.divider()
        if st.sidebar.button("🗑️ Видалити Проект", type="secondary", use_container_width=True):
            if st.sidebar.checkbox(f"Підтвердити видалення '{selected_option}'", key="confirm_delete"):
                if file_manager.delete_project(selected_option):
                    st.sidebar.success(f"Проект '{selected_option}' видалено!")
                    # Clear session state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
                else:
                    st.sidebar.error("Помилка видалення проекту")
                    
    return selected_option
