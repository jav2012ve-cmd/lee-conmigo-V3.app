"""
Arranque de BD para Streamlit DEMO: evita repetir init_db + ensure_demo_database en cada rerun.

La clave de caché incluye la ruta absoluta de la BD y el valor de LEE_CONMIGO_DEMO_RESET para que,
si se fuerza reset por entorno, se vuelva a ejecutar el bootstrap.
"""

from __future__ import annotations

import os

import streamlit as st


@st.cache_resource(show_spinner=False)
def warm_demo_streamlit_database(db_path_abs: str, demo_reset_env: str) -> bool:
    """
    Crea esquema (init_db) y asegura datos seed de demo (ensure_demo_database) una vez por clave.
    Devuelve True como marcador serializable.
    """
    from database.db_config import init_db
    from database.demo_bootstrap import ensure_demo_database

    init_db()
    ensure_demo_database()
    return True
