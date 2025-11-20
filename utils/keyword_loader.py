import pandas as pd
import os

def load_keywords_from_csv(project_name, file_manager, top_n=5):
    """
    Load top N keywords from semantic_core.csv
    
    Args:
        project_name: Name of the project
        file_manager: FileManager instance
        top_n: Number of top keywords to return (default: 5)
        
    Returns:
        List of keyword strings
    """
    try:
        csv_content = file_manager.read_file(project_name, "semantic_core.csv")
        if not csv_content:
            return []
        
        # Parse CSV
        from io import StringIO
        df = pd.read_csv(StringIO(csv_content))
        
        # Check if required columns exist
        if 'keyword' not in df.columns:
            return []
        
        # Sort by volume (if available) or just take first N
        if 'volume' in df.columns:
            df = df.sort_values('volume', ascending=False)
        
        # Get top N keywords
        keywords = df['keyword'].head(top_n).tolist()
        
        return keywords
        
    except Exception as e:
        # print(f"Error loading keywords: {e}")
        return []
