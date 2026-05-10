import streamlit as st

from database.db_config import init_db
from core.session_state_v3 import init_session_v3
from components.styles import apply_styles, set_page_config
from components.page_title import render_titulo_sidebar

# Importación de Vistas (V3)
from views_v3.salon_entrada_v3 import render_salon_entrada_v3
from views_v3.padre.config_salon_v3 import render_config_salon_v3
from views_v3.padre.zona_padres_v3 import render_zona_padres_v3
from views_v3.padre.album_mgmt_v3 import render_album_mgmt_v3
from views_v3.estudiante.hub_nino_v3 import render_hub_nino_v3
from views_v3.estudiante.lecciones_nino_v3 import render_lecciones_nino_v3
from views_v3.estudiante.album_nino_v3 import render_album_nino_v3
from views_v3.estudiante.album_silabas_nino_v3 import render_album_silabas_nino_v3
from views_v3.estudiante.album_abecedario_nino_v3 import render_album_abecedario_nino_v3
from views_v3.estudiante.informe_sesion_v3 import render_informe_sesion_v3
from views.estudiante.abecedario_matriz import render_abecedario_matriz
from views.docente.zona_docente import render_zona_docente
from views.tutor.zona_tutores import render_zona_tutores


def main():
    # 1. Configuración técnica inicial
    set_page_config()
    init_db()          # Reusa DB existente (V2)
    init_session_v3()  # Sesión independiente V3
    apply_styles()

    # 2. Sidebar: docentes, tutores, padres y registro siempre visibles
    with st.sidebar:
        render_titulo_sidebar("Panel de Control (V3)")
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] .stButton > button {
                width: 100% !important; font-size: 1rem !important;
                padding: 0.6rem 1rem !important; min-height: 44px !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👩‍🏫 Zona docentes", use_container_width=True, key="v3_sidebar_docente"):
            st.session_state.pagina_activa = "zona_docente"
            st.rerun()
        if st.button("🎓 Zona Tutores", use_container_width=True, key="v3_sidebar_tutor"):
            st.session_state.pagina_activa = "zona_tutores"
            st.rerun()
        if st.button("👨‍👩‍👧 Zona de padres", use_container_width=True, key="v3_sidebar_zona"):
            st.session_state.pagina_activa = "zona_padres"
            st.rerun()
        if st.button("➕ Registro de nuevos estudiantes", use_container_width=True, key="v3_sidebar_registro"):
            st.session_state.pagina_activa = "config_salon"
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.session_state.pop("config_estudiante_id", None)
            st.rerun()

    # 3. Router de Pantallas
    pagina = st.session_state.pagina_activa

    if pagina == "salon_entrada":
        render_salon_entrada_v3()
    elif pagina == "config_salon":
        render_config_salon_v3()
    elif pagina == "zona_padres":
        render_zona_padres_v3()
    elif pagina == "zona_docente":
        render_zona_docente()
    elif pagina == "zona_tutores":
        render_zona_tutores()
    elif pagina == "album_mgmt":
        render_album_mgmt_v3()
    elif pagina == "hub_nino":
        render_hub_nino_v3()
    elif pagina == "lecciones_nino":
        render_lecciones_nino_v3()
    elif pagina == "album_nino":
        render_album_nino_v3()
    elif pagina == "album_silabas":
        render_album_silabas_nino_v3()
    elif pagina == "album_abecedario":
        render_album_abecedario_nino_v3()
    elif pagina == "informe_sesion":
        render_informe_sesion_v3()
    elif pagina == "abecedario_matriz":
        render_abecedario_matriz(titulo_extra="V3")


if __name__ == "__main__":
    main()

