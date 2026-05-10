import streamlit as st
from views.padre.config_salon import render_config_salon as _render_config_salon_v2


def render_config_salon_v3():
    st.caption("Configuración (V3): reusando pantalla V2 por ahora.")
    _render_config_salon_v2()

