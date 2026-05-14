import re

import streamlit as st


def _safe_theme_hex(val) -> str:
    """Color de tema para CSS: solo #RGB / #RRGGBB / #RRGGBBAA hex; evita inyección."""
    v = (val or "#4A90E2").strip()
    if not v.startswith("#"):
        v = "#" + v
    if re.fullmatch(r"#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?([0-9A-Fa-f]{2})?", v):
        return v[:16]
    return "#4A90E2"


@st.cache_data(show_spinner=False)
def _leeconmigo_static_css_template() -> str:
    """
    CSS de aplicación sin el color dinámico del niño (marcador __LC_MAIN__).
    Se cachea por proceso: no se reconstruye el bloque enorme en cada rerun.
    """
    return """
        <style>
        /* 1. Fuente: sistema (evita @import a Google en cada rerun de Streamlit). */
        html, body, [class*="css"] {{
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #2C3E50;
            font-size: 18px;
        }}
        h1, .stMarkdown h1 {{ font-size: 2rem !important; }}
        h2, .stMarkdown h2 {{ font-size: 1.6rem !important; }}
        h3, .stMarkdown h3 {{ font-size: 1.35rem !important; }}
        .stMarkdown p, .stMarkdown caption {{ font-size: 1.1rem !important; }}
        .stSelectbox label, .stTextInput label {{ font-size: 1.2rem !important; }}
        .stSelectbox div[data-baseweb="select"], .stSelectbox span {{ font-size: 1.15rem !important; }}
        .stCaptionContainer {{ font-size: 1.1rem !important; }}

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
            color: __LC_MAIN__;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}

        section[data-testid="stMain"] .stButton > button {{
            width: 100%;
            box-sizing: border-box !important;
            border-radius: 20px;
            min-height: 4.25rem !important;
            padding: 0.35rem 0.6rem !important;
            background-color: __LC_MAIN__;
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
        section[data-testid="stMain"] .stButton > button p,
        section[data-testid="stMain"] .stButton > button span,
        section[data-testid="stMain"] .stButton > button div {{
            font-size: var(--lc-main-btn-font, 1.55rem) !important;
            line-height: 1.15 !important;
            margin: 0 !important;
        }}
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

        .parent-container {{
            background-color: #F7F9FB;
            padding: 20px;
            border-radius: 15px;
            border-left: 5px solid #2C3E50;
        }}
        </style>
        """


def apply_fondo_pagina_principal_hub():
    """Fondo con imagen retirado (antes Fondo_Logo.png en data-URI): aligera la página."""
    return


def apply_styles():
    """
    Inyecta CSS personalizado para transformar la interfaz estándar
    de Streamlit en una plataforma educativa infantil.
    El bloque grande es estático y se cachea; solo se sustituye el color de acento por rerun.
    """
    raw = st.session_state.get("color_favorito", "#4A90E2")
    main_color = _safe_theme_hex(raw if isinstance(raw, str) else "#4A90E2")
    tpl = _leeconmigo_static_css_template()
    st.markdown(tpl.replace("__LC_MAIN__", main_color), unsafe_allow_html=True)


def set_page_config():
    """Configuración básica de la pestaña del navegador."""
    st.set_page_config(
        page_title="LeeConmigo - Alfabetización Emocional",
        page_icon="📖",
        layout="wide"
    )