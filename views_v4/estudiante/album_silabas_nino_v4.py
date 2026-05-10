import streamlit as st

from views.estudiante.album_silabas_nino import render_album_silabas_nino as _render_album_silabas_nino_v2


def render_album_silabas_nino_v4():
    st.caption("Álbum sílabas (4.0): reusando pantalla V2 por ahora.")
    _render_album_silabas_nino_v2()

