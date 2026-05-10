import streamlit as st
from views.padre.zona_padres import render_zona_padres


def render_zona_padres_demo():
    st.caption("DEMO comercial")
    render_zona_padres()
