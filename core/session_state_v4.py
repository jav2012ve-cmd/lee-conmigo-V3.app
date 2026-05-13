import streamlit as st


def init_session_v4():
    """
    Estado global para la versión 4.0 (LeeConmigoV4). Misma convención de llaves
    principales que V2/V3 (pagina_activa, rol_actual, etc.).
    """
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
    if "admin_acceso_ok" not in st.session_state:
        st.session_state.admin_acceso_ok = False

    if "v4_ciclo_id" not in st.session_state:
        st.session_state.v4_ciclo_id = "C1"
    if "v4_bloque_lecciones_habilitado" not in st.session_state:
        st.session_state.v4_bloque_lecciones_habilitado = False
    if "v4_album_categoria_activa" not in st.session_state:
        st.session_state.v4_album_categoria_activa = None
    if "v4_flash_msg" not in st.session_state:
        st.session_state.v4_flash_msg = None


def logout_v4():
    st.session_state.padre_id = None
    st.session_state.estudiante_id = None
    st.session_state.autenticado = False
    st.session_state.rol_actual = "guest"
    st.session_state.pagina_activa = "salon_entrada"
    st.rerun()
