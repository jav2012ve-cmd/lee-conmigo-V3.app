import streamlit as st

from views.estudiante.album_abecedario_nino import render_album_abecedario_nino as _render_album_abecedario_nino_v2


def render_album_abecedario_nino_v3():
    st.caption("Álbum abecedario (V3): reusando pantalla V2 por ahora.")
    _render_album_abecedario_nino_v2()

