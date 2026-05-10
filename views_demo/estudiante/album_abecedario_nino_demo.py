import streamlit as st
from views.estudiante.album_abecedario_nino import render_album_abecedario_nino


def render_album_abecedario_nino_demo():
    st.caption("DEMO comercial")
    render_album_abecedario_nino()
