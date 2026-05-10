import streamlit as st
from views.estudiante.informe_sesion import render_informe_sesion


def render_informe_sesion_demo():
    st.caption("DEMO comercial")
    render_informe_sesion()
