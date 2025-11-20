import json
import os

def save_state(project_name, state_data):
    """
    Save session state to a JSON file for persistence.
    
    Args:
        project_name: Name of the project
        state_data: Dictionary of state data to save
    """
    project_dir = f"projects/{project_name}"
    os.makedirs(project_dir, exist_ok=True)
    
    state_file = f"{project_dir}/state.json"
    
    # Convert non-serializable objects to serializable format
    serializable_data = {}
    for key, value in state_data.items():
        try:
            json.dumps(value)  # Test if serializable
            serializable_data[key] = value
        except (TypeError, ValueError):
            # Skip non-serializable items
            pass
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)

def load_state(project_name):
    """
    Load session state from a JSON file.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Dictionary of state data or empty dict if file doesn't exist
    """
    state_file = f"projects/{project_name}/state.json"
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # print(f"Error loading state: {e}")
            return {}
    return {}
