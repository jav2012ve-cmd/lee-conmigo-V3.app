import base64
import os

import streamlit as st

# Fondo visual LeeConmigo: salón de entrada, hub del niño, etc.
# Archivo: `assets/genericos/fondos/Fondo_Logo.png`
_FONDO_LOGO_HUB = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "assets",
    "genericos",
    "fondos",
    "Fondo_Logo.png",
)


def apply_fondo_pagina_principal_hub():
    """
    Aplica `Fondo_Logo.png` como fondo de la app (entrada al salón, hub del niño).
    Ruta: assets/genericos/fondos/Fondo_Logo.png bajo la raíz del proyecto.
    """
    path = _FONDO_LOGO_HUB
    if not os.path.isfile(path):
        return
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    except OSError:
        return
    ext = path.lower().rsplit(".", 1)[-1] if "." in path else "png"
    if ext == "png":
        mime = "image/png"
    elif ext in ("jpg", "jpeg"):
        mime = "image/jpeg"
    elif ext == "webp":
        mime = "image/webp"
    else:
        mime = "image/png"
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:{mime};base64,{b64}");
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(255, 255, 255, 0.78);
            pointer-events: none;
            z-index: 0;
        }}
        [data-testid="stAppViewContainer"] > section {{ position: relative; z-index: 1; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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

        /* 3. Botones en el área principal: centrado; altura en rem (no em). Tamaño base con --lc-main-btn-font (p. ej. 3rem solo en matriz emoji en config/salón) */
        section[data-testid="stMain"] .stButton > button {{
            width: 100%;
            box-sizing: border-box !important;
            border-radius: 20px;
            min-height: 4.25rem !important;
            padding: 0.35rem 0.6rem !important;
            background-color: {main_color};
            color: white;
            font-size: var(--lc-main-btn-font, 1.55rem) !important;
            font-weight: bold;
            border: none;
            transition: 0.3s;
            line-height: 1.15 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
        }}
        /* Base Web suele envolver el texto en div/p; sin esto el emoji queda en tamaño de tema */
        section[data-testid="stMain"] .stButton > button p,
        section[data-testid="stMain"] .stButton > button span,
        section[data-testid="stMain"] .stButton > button div {{
            font-size: var(--lc-main-btn-font, 1.55rem) !important;
            line-height: 1.15 !important;
            margin: 0 !important;
        }}
        /* Formularios: texto legible, sin celdas tipo emoji */
        section[data-testid="stMain"] [data-testid="stForm"] .stButton > button,
        section[data-testid="stMain"] [data-testid="stForm"] .stButton > button *,
        section[data-testid="stMain"] form .stButton > button,
        section[data-testid="stMain"] form .stButton > button *,
        section[data-testid="stMain"] [data-testid="stForm"] button[kind="primary"],
        section[data-testid="stMain"] [data-testid="stForm"] button[kind="primary"] *,
        section[data-testid="stMain"] form button[kind="primary"],
        section[data-testid="stMain"] form button[kind="primary"] * {{
            font-size: 1.08rem !important;
            font-weight: 600 !important;
            min-height: 2.75rem !important;
            height: auto !important;
            padding: 0.5rem 0.85rem !important;
            line-height: 1.25 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        /* Sidebar: no hereda el tamaño grande del main */
        [data-testid="stSidebar"] .stButton > button {{
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            min-height: 3rem !important;
            height: auto !important;
            padding: 0.55rem 0.9rem !important;
            line-height: 1.25 !important;
            display: block !important;
            white-space: normal !important;
        }}
        section[data-testid="stMain"] .stButton > button:hover {{
            transform: scale(1.05);
            background-color: #357ABD;
        }}
        /* Botones primary (p. ej. hub): tamaño razonable. La matriz emoji usa primary solo ahí y la vista inyecta CSS más específico después. */
        section[data-testid="stMain"] button[kind="primary"],
        section[data-testid="stMain"] button[kind="primary"] * {{
            font-size: 1.12rem !important;
            line-height: 1.25 !important;
        }}
        section[data-testid="stMain"] button[kind="primary"] {{
            min-height: 2.85rem !important;
            height: auto !important;
            max-height: none !important;
            padding: 0.5rem 0.85rem !important;
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