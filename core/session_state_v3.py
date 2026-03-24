import streamlit as st


def init_session_v3():
    """
    Inicializa las variables globales para la versión V3 sin tocar la lógica V2.
    Reusa los mismos nombres de llaves principales (pagina_activa, rol_actual, etc.)
    para que las vistas V3 funcionen igual que las V2, pero con su propio flujo.
    """
    if "padre_id" not in st.session_state:
        st.session_state.padre_id = 1  # piloto

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

    # Estado académico V3 (nuevo): ciclo/bloque y desbloqueos
    if "v3_ciclo_id" not in st.session_state:
        st.session_state.v3_ciclo_id = "C1"
    if "v3_bloque_lecciones_habilitado" not in st.session_state:
        st.session_state.v3_bloque_lecciones_habilitado = False
    if "v3_album_categoria_activa" not in st.session_state:
        st.session_state.v3_album_categoria_activa = None
    if "v3_flash_msg" not in st.session_state:
        st.session_state.v3_flash_msg = None


def logout_v3():
    st.session_state.padre_id = None
    st.session_state.estudiante_id = None
    st.session_state.autenticado = False
    st.session_state.rol_actual = "guest"
    st.session_state.pagina_activa = "salon_entrada"
    st.rerun()

