import streamlit as st

# Solo estas consonantes en lecciones (`views.estudiante.lecciones_nino`: v3_letras_override).
DEMO_LETRAS_LECCIONES = ["M", "P"]


def init_session_demo():
    if "padre_id" not in st.session_state:
        st.session_state.padre_id = 1
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "estudiante_id" not in st.session_state:
        st.session_state.estudiante_id = None
    if "nombre_nino" not in st.session_state:
        st.session_state.nombre_nino = ""
    if "rol_actual" not in st.session_state:
        st.session_state.rol_actual = "guest"
    if "pagina_activa" not in st.session_state:
        st.session_state.pagina_activa = "salon_entrada"

    if "docente_acceso_ok" not in st.session_state:
        st.session_state.docente_acceso_ok = False
    if "docente_pw_change_required" not in st.session_state:
        st.session_state.docente_pw_change_required = False
    if "tutor_acceso_ok" not in st.session_state:
        st.session_state.tutor_acceso_ok = False
    if "tutor_pw_change_required" not in st.session_state:
        st.session_state.tutor_pw_change_required = False

    if "demo_album_categoria_activa" not in st.session_state:
        st.session_state.demo_album_categoria_activa = None
    if "demo_flash_msg" not in st.session_state:
        st.session_state.demo_flash_msg = None

    st.session_state["v3_letras_override"] = list(DEMO_LETRAS_LECCIONES)


def logout_demo():
    st.session_state.padre_id = None
    st.session_state.estudiante_id = None
    st.session_state.autenticado = False
    st.session_state.rol_actual = "guest"
    st.session_state.pagina_activa = "salon_entrada"
    st.rerun()
