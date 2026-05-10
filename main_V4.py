import streamlit as st

from database.db_config import init_db
from core.session_state_v4 import init_session_v4
from components.styles import apply_styles, set_page_config
from components.page_title import render_titulo_sidebar

from views_v4.salon_entrada_v4 import render_salon_entrada_v4
from views_v4.padre.config_salon_v4 import render_config_salon_v4
from views_v4.padre.zona_padres_v4 import render_zona_padres_v4
from views_v4.padre.album_mgmt_v4 import render_album_mgmt_v4
from views_v4.estudiante.hub_nino_v4 import render_hub_nino_v4
from views_v4.estudiante.lecciones_nino_v4 import render_lecciones_nino_v4
from views_v4.estudiante.album_nino_v4 import render_album_nino_v4
from views_v4.estudiante.album_silabas_nino_v4 import render_album_silabas_nino_v4
from views_v4.estudiante.album_abecedario_nino_v4 import render_album_abecedario_nino_v4
from views_v4.estudiante.informe_sesion_v4 import render_informe_sesion_v4
from views.estudiante.abecedario_matriz import render_abecedario_matriz
from views.docente.zona_docente import render_zona_docente
from views.tutor.zona_tutores import render_zona_tutores


def main():
    set_page_config()
    init_db()
    init_session_v4()
    apply_styles()

    with st.sidebar:
        render_titulo_sidebar("Panel de Control (4.0)")
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
        if st.button("👩‍🏫 Zona docentes", use_container_width=True, key="v4_sidebar_docente"):
            st.session_state.pagina_activa = "zona_docente"
            st.rerun()
        if st.button("🎓 Zona Tutores", use_container_width=True, key="v4_sidebar_tutor"):
            st.session_state.pagina_activa = "zona_tutores"
            st.rerun()
        if st.button("👨‍👩‍👧 Zona de padres", use_container_width=True, key="v4_sidebar_zona"):
            st.session_state.pagina_activa = "zona_padres"
            st.rerun()
        if st.button("➕ Registro de nuevos estudiantes", use_container_width=True, key="v4_sidebar_registro"):
            st.session_state.pagina_activa = "config_salon"
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.session_state.pop("config_estudiante_id", None)
            st.rerun()

    pagina = st.session_state.pagina_activa

    if pagina == "salon_entrada":
        render_salon_entrada_v4()
    elif pagina == "config_salon":
        render_config_salon_v4()
    elif pagina == "zona_padres":
        render_zona_padres_v4()
    elif pagina == "zona_docente":
        render_zona_docente()
    elif pagina == "zona_tutores":
        render_zona_tutores()
    elif pagina == "album_mgmt":
        render_album_mgmt_v4()
    elif pagina == "hub_nino":
        render_hub_nino_v4()
    elif pagina == "lecciones_nino":
        render_lecciones_nino_v4()
    elif pagina == "album_nino":
        render_album_nino_v4()
    elif pagina == "album_silabas":
        render_album_silabas_nino_v4()
    elif pagina == "album_abecedario":
        render_album_abecedario_nino_v4()
    elif pagina == "informe_sesion":
        render_informe_sesion_v4()
    elif pagina == "abecedario_matriz":
        render_abecedario_matriz(titulo_extra="4.0")


if __name__ == "__main__":
    main()
