import streamlit as st
from views.estudiante.hub_nino import render_hub_nino


def render_hub_nino_demo():
    st.caption("DEMO comercial")
    st.info("Lecciones DEMO habilitadas: M y P.")
    render_hub_nino()
