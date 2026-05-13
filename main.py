import streamlit as st
from database.db_config import init_db
from core.session_state import init_session
from components.styles import apply_styles, set_page_config
from components.page_title import render_titulo_sidebar

# Importación de Vistas
from views.salon_entrada import render_salon_entrada
from views.padre.config_salon import render_config_salon
from views.padre.zona_padres import render_zona_padres
from views.padre.album_mgmt import render_album_mgmt
from views.estudiante.hub_nino import render_hub_nino
from views.estudiante.lecciones_nino import render_lecciones_nino
from views.estudiante.album_nino import (
    apply_album_cat_query_navigation,
    render_album_nino,
    render_album_nino_categoria,
)
from views.estudiante.album_silabas_nino import render_album_silabas_nino
from views.estudiante.album_abecedario_nino import render_album_abecedario_nino
from views.estudiante.informe_sesion import render_informe_sesion
from views.estudiante.abecedario_matriz import render_abecedario_matriz
from views.docente.zona_docente import render_zona_docente
from views.tutor.zona_tutores import render_zona_tutores


def main():
    # 1. Configuración técnica inicial
    set_page_config()
    init_db()       # Crea las tablas si no existen
    init_session()  # Prepara las variables de memoria
    apply_styles()  # Inyecta el CSS personalizado
    apply_album_cat_query_navigation()  # ?album_cat=… → pantalla de imágenes por categoría

    # 2. Sidebar: docentes, tutores (LeeConmigo), padres y registro siempre visibles
    with st.sidebar:
        render_titulo_sidebar("Panel de Control")
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] .stButton > button {
                width: 100%% !important; font-size: 1rem !important;
                padding: 0.6rem 1rem !important; min-height: 44px !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👩‍🏫 Zona docentes", use_container_width=True, key="sidebar_docente"):
            st.session_state.pagina_activa = "zona_docente"
            st.rerun()
        if st.button("🎓 Zona Tutores", use_container_width=True, key="sidebar_tutor"):
            st.session_state.pagina_activa = "zona_tutores"
            st.rerun()
        if st.button("🛠️ Zona administradores", use_container_width=True, key="sidebar_admin"):
            st.session_state.pagina_activa = "zona_admin"
            st.rerun()
        if st.button("👨‍👩‍👧 Zona de padres", use_container_width=True, key="sidebar_zona"):
            st.session_state.pagina_activa = "zona_padres"
            st.rerun()
        if st.button("➕ Registro de nuevos estudiantes", use_container_width=True, key="sidebar_registro"):
            st.session_state.pagina_activa = "config_salon"
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.session_state.pop("config_estudiante_id", None)
            st.rerun()

    # 3. Router de Pantallas (Lógica de Navegación)
    pagina = st.session_state.pagina_activa

    if pagina == 'salon_entrada':
        render_salon_entrada()
    
    elif pagina == 'config_salon':
        render_config_salon()

    elif pagina == 'zona_padres':
        render_zona_padres()

    elif pagina == "zona_docente":
        render_zona_docente()

    elif pagina == "zona_tutores":
        render_zona_tutores()

    elif pagina == "zona_admin":
        from views.admin.zona_administradores import render_zona_administradores

        render_zona_administradores()

    elif pagina == 'album_mgmt':
        render_album_mgmt()
        
    elif pagina == 'hub_nino':
        render_hub_nino()
        
    elif pagina == 'lecciones_nino':
        render_lecciones_nino()
        
    elif pagina == 'album_nino':
        render_album_nino()

    elif pagina == 'album_nino_categoria':
        render_album_nino_categoria()

    elif pagina == 'album_silabas':
        render_album_silabas_nino()

    elif pagina == 'album_abecedario':
        render_album_abecedario_nino()

    elif pagina == 'informe_sesion':
        render_informe_sesion()

    elif pagina == "abecedario_matriz":
        render_abecedario_matriz(titulo_extra="LeeConmigo")

if __name__ == "__main__":
    main()