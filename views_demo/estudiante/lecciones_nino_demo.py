import streamlit as st
from core.session_state_demo import DEMO_LETRAS_LECCIONES
from views.estudiante.lecciones_nino import render_lecciones_nino


def render_lecciones_nino_demo():
    st.caption("DEMO comercial: solo lecciones M y P.")
    st.session_state["v3_letras_override"] = list(DEMO_LETRAS_LECCIONES)
    render_lecciones_nino()
