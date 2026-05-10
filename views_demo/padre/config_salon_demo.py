import streamlit as st
from views.padre.config_salon import render_config_salon


def render_config_salon_demo():
    st.caption("DEMO: registro con avatar de galeria")
    render_config_salon()
