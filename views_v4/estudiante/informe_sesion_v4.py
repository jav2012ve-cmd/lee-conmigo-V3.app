import streamlit as st

from views.estudiante.informe_sesion import render_informe_sesion as _render_informe_sesion_v2


def render_informe_sesion_v4():
    st.caption("Informe de sesión (4.0): reusando pantalla V2 por ahora.")
    _render_informe_sesion_v2()

