import streamlit as st

def apply_styles():
    """
    Inyecta CSS personalizado para transformar la interfaz estándar 
    de Streamlit en una plataforma educativa infantil.
    """
    
    # Intentamos obtener el color favorito de la sesión, si no, usamos un azul suave
    main_color = st.session_state.get('color_favorito', '#4A90E2')
    
    st.markdown(f"""
        <style>
        /* 1. Fuente Escolar y General */
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Open Sans', sans-serif;
            color: #2C3E50;
            font-size: 18px;
        }}
        /* Títulos y texto más grandes para mejor lectura */
        h1, .stMarkdown h1 {{ font-size: 2rem !important; }}
        h2, .stMarkdown h2 {{ font-size: 1.6rem !important; }}
        h3, .stMarkdown h3 {{ font-size: 1.35rem !important; }}
        .stMarkdown p, .stMarkdown caption {{ font-size: 1.1rem !important; }}
        /* Selectbox e inputs más legibles (nombre completo con apellidos) */
        .stSelectbox label, .stTextInput label {{ font-size: 1.2rem !important; }}
        .stSelectbox div[data-baseweb="select"], .stSelectbox span {{ font-size: 1.15rem !important; }}
        /* Captions y mensajes */
        .stCaptionContainer {{ font-size: 1.1rem !important; }}

        /* 2. Estilo para Tarjetas Polaroid (Álbum) */
        .polaroid-card {{
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            text-align: center;
            border: 1px solid #E0E0E0;
            margin-bottom: 20px;
        }}
        
        .polaroid-img {{
            width: 100%;
            height: auto;
            border-radius: 5px;
            margin-bottom: 10px;
        }}

        .polaroid-text {{
            font-size: 1.5rem;
            font-weight: bold;
            color: {main_color};
            text-transform: uppercase;
            letter-spacing: 2px;
        }}

        /* 3. Botones grandes (texto y emojis más visibles en toda la app y en el sidebar) */
        .stButton>button {{
            width: 100%;
            border-radius: 20px;
            min-height: 3.5em;
            background-color: {main_color};
            color: white;
            font-size: 1.5rem !important;
            font-weight: bold;
            border: none;
            transition: 0.3s;
            line-height: 1.4;
        }}
        [data-testid="stSidebar"] .stButton>button {{
            font-size: 1.5rem !important;
            min-height: 3.5em !important;
        }}
        .stButton>button:hover {{
            transform: scale(1.05);
            background-color: #357ABD;
        }}

        /* 4. Resaltado de Sílabas (Karaoke) */
        .syllable-highlight {{
            background-color: yellow;
            padding: 2px 5px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 40px;
        }}
        
        .syllable-normal {{
            font-size: 40px;
            color: #333;
        }}

        /* 5. Estilo para el área de Padres (Dashboard) */
        .parent-container {{
            background-color: #F7F9FB;
            padding: 20px;
            border-radius: 15px;
            border-left: 5px solid #2C3E50;
        }}
        </style>
    """, unsafe_allow_html=True)

def set_page_config():
    """Configuración básica de la pestaña del navegador."""
    st.set_page_config(
        page_title="LeeConmigo - Alfabetización Emocional",
        page_icon="📖",
        layout="wide"
    )