import streamlit as st
from views.padre.album_mgmt import render_album_mgmt as _render_album_mgmt_v2


def render_album_mgmt_v3():
    st.caption("Gestión de álbum (V3): reusando pantalla V2 por ahora.")
    _render_album_mgmt_v2()

