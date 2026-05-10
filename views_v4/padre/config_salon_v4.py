import streamlit as st
from views.padre.config_salon import render_config_salon as _render_config_salon_v2


def render_config_salon_v4():
    st.caption("Configuración (4.0): reusando pantalla V2 por ahora.")
    _render_config_salon_v2()

