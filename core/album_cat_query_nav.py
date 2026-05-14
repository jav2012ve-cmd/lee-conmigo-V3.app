"""Navegación por query string ?album_cat=… sin importar el módulo pesado del álbum completo."""

from urllib.parse import unquote

import streamlit as st

from core.album_categories import CATEGORIAS_ALBUM


def apply_album_cat_query_navigation():
    """Si la URL incluye ?album_cat=..., navega a la pantalla de imágenes de esa categoría."""
    try:
        if "album_cat" not in st.query_params:
            return
        raw = st.query_params.get("album_cat")
        if isinstance(raw, (list, tuple)):
            raw = raw[0]
        cand = unquote(str(raw))
        if cand not in CATEGORIAS_ALBUM:
            return
        st.session_state.album_nino_categoria = cand
        st.session_state.pagina_activa = "album_nino_categoria"
        try:
            del st.query_params["album_cat"]
        except Exception:
            pass
        st.rerun()
    except Exception:
        pass
