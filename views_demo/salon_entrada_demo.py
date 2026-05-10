import streamlit as st
from views.salon_entrada import render_salon_entrada


def render_salon_entrada_demo():
    st.caption("DEMO comercial")
    render_salon_entrada()
