import streamlit as st

def init_session():
    """
    Inicializa las variables globales necesarias para que la App
    funcione como un sistema con memoria.
    """
    # 1. Seguridad y Autenticación
    if 'padre_id' not in st.session_state:
        st.session_state.padre_id = 1 # IMPORTANTE: Que sea 1, no None
    
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    # 2. Perfil del Estudiante Activo
    if 'estudiante_id' not in st.session_state:
        st.session_state.estudiante_id = None
    
    if 'nombre_nino' not in st.session_state:
        st.session_state.nombre_nino = ""

    # 3. Navegación y Roles
    # Roles: 'guest', 'padre', 'estudiante'
    if 'rol_actual' not in st.session_state:
        st.session_state.rol_actual = 'guest'
    
    # Control de pantalla activa (Router)
    if 'pagina_activa' not in st.session_state:
        st.session_state.pagina_activa = 'salon_entrada'

    # 4. Estado Académico (Cache para evitar consultas constantes a DB)
    if 'ciclo_actual' not in st.session_state or not st.session_state.ciclo_actual:
        st.session_state.ciclo_actual = "Ciclo 1"  # Valor inicial robusto

def logout():
    """Limpia la sesión para volver al inicio."""
    st.session_state.padre_id = None
    st.session_state.estudiante_id = None
    st.session_state.autenticado = False
    st.session_state.rol_actual = 'guest'
    st.session_state.pagina_activa = 'salon_entrada'
    st.rerun()