import streamlit as st
from views.padre.zona_padres import render_zona_padres as _render_zona_padres_v2


def render_zona_padres_v5():
    st.caption("Zona de padres (5.0): reusando pantalla V2 por ahora.")
    _render_zona_padres_v2()

