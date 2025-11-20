import streamlit as st

def apply_styles():
    """
    Applies global CSS styles to the Streamlit app.
    Uses CSS variables to adapt to Light/Dark modes automatically.
    """
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global Font Settings */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* --- ADAPTIVE CARD STYLES --- */
        /* We use a slightly transparent background for cards to blend with the theme */
        .stMetric, .stInfo, .stSuccess, .stWarning, .stError {
            background-color: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* --- BUTTONS --- */
        /* Primary Button */
        .stButton button[kind="primary"] {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        }

        /* Secondary Button */
        .stButton button[kind="secondary"] {
            border-radius: 8px;
            border: 1px solid rgba(128, 128, 128, 0.3);
            background-color: transparent;
        }
        .stButton button[kind="secondary"]:hover {
            border-color: var(--primary-color);
            color: var(--primary-color);
        }

        /* --- INPUTS --- */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            border-radius: 8px;
            border: 1px solid rgba(128, 128, 128, 0.3);
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(var(--primary-color), 0.2);
        }

        /* --- EXPANDERS --- */
        .streamlit-expanderHeader {
            background-color: var(--secondary-background-color);
            border-radius: 8px;
            border: 1px solid rgba(128, 128, 128, 0.1);
        }
        
        /* --- HEADERS --- */
        h1, h2, h3 {
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        h1 {
            background: linear-gradient(90deg, var(--primary-color), #8e44ad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding-bottom: 10px;
        }

        /* --- CUSTOM CLASSES --- */
        .card {
            background-color: var(--secondary-background-color);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.1);
            margin-bottom: 20px;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-color);
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: rgba(128, 128, 128, 0.8);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

    </style>
    """, unsafe_allow_html=True)
