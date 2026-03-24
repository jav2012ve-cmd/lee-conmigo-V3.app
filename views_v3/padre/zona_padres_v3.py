import streamlit as st
from views.padre.zona_padres import render_zona_padres as _render_zona_padres_v2


def render_zona_padres_v3():
    st.caption("Zona de padres (V3): reusando pantalla V2 por ahora.")
    _render_zona_padres_v2()

