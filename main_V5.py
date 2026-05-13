"""
LeeConmigo 5.0 — instancia limpia (sin registros ni fotos heredadas).

Usa la base `database/lee_conmigo_v5.db` (solo esquema al crear el archivo).
Para volver a cero, cierra la app y borra ese archivo; al reiniciar se recrea vacío.
"""
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["LEE_CONMIGO_DB_PATH"] = os.path.join(_ROOT, "database", "lee_conmigo_v5.db")

import streamlit as st

from database.db_config import init_db
from core.session_state_v5 import init_session_v5
from components.styles import apply_styles, set_page_config
from components.page_title import render_titulo_sidebar

from views_v5.salon_entrada_v5 import render_salon_entrada_v5
from views_v5.padre.config_salon_v5 import render_config_salon_v5
from views_v5.padre.zona_padres_v5 import render_zona_padres_v5
from views_v5.padre.album_mgmt_v5 import render_album_mgmt_v5
from views_v5.estudiante.hub_nino_v5 import render_hub_nino_v5
from views_v5.estudiante.lecciones_nino_v5 import render_lecciones_nino_v5
from views_v5.estudiante.album_nino_v5 import render_album_nino_v5
from views_v5.estudiante.album_silabas_nino_v5 import render_album_silabas_nino_v5
from views_v5.estudiante.album_abecedario_nino_v5 import render_album_abecedario_nino_v5
from views_v5.estudiante.informe_sesion_v5 import render_informe_sesion_v5
from views.estudiante.abecedario_matriz import render_abecedario_matriz
from views.docente.zona_docente import render_zona_docente
from views.tutor.zona_tutores import render_zona_tutores
from views.admin.zona_administradores import render_zona_administradores


def main():
    set_page_config()
    init_db()
    init_session_v5()
    apply_styles()

    with st.sidebar:
        render_titulo_sidebar("Panel de Control (5.0)")
        st.caption("Base nueva: sin datos previos; registra tutores y niños desde aquí.")
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
        if st.button("👩‍🏫 Zona docentes", use_container_width=True, key="v5_sidebar_docente"):
            st.session_state.pagina_activa = "zona_docente"
            st.rerun()
        if st.button("🎓 Zona Tutores", use_container_width=True, key="v5_sidebar_tutor"):
            st.session_state.pagina_activa = "zona_tutores"
            st.rerun()
        if st.button("🛠️ Zona administradores", use_container_width=True, key="v5_sidebar_admin"):
            st.session_state.pagina_activa = "zona_admin"
            st.rerun()
        if st.button("👨‍👩‍👧 Zona de padres", use_container_width=True, key="v5_sidebar_zona"):
            st.session_state.pagina_activa = "zona_padres"
            st.rerun()
        if st.button(
            "➕ Registro de nuevos estudiantes",
            use_container_width=True,
            key="v5_sidebar_registro",
        ):
            st.session_state.pagina_activa = "config_salon"
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.session_state.pop("config_estudiante_id", None)
            st.rerun()

    pagina = st.session_state.pagina_activa

    if pagina == "salon_entrada":
        render_salon_entrada_v5()
    elif pagina == "config_salon":
        render_config_salon_v5()
    elif pagina == "zona_padres":
        render_zona_padres_v5()
    elif pagina == "zona_docente":
        render_zona_docente()
    elif pagina == "zona_tutores":
        render_zona_tutores()
    elif pagina == "zona_admin":
        render_zona_administradores()
    elif pagina == "album_mgmt":
        render_album_mgmt_v5()
    elif pagina == "hub_nino":
        render_hub_nino_v5()
    elif pagina == "lecciones_nino":
        render_lecciones_nino_v5()
    elif pagina == "album_nino":
        render_album_nino_v5()
    elif pagina == "album_silabas":
        render_album_silabas_nino_v5()
    elif pagina == "album_abecedario":
        render_album_abecedario_nino_v5()
    elif pagina == "informe_sesion":
        render_informe_sesion_v5()
    elif pagina == "abecedario_matriz":
        render_abecedario_matriz(titulo_extra="5.0")


if __name__ == "__main__":
    main()
