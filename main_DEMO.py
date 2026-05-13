import os

# Debe ejecutarse antes de importar database.* para no mezclar datos con lee_conmigo.db de producto.
_ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["LEE_CONMIGO_DB_PATH"] = os.path.join(_ROOT, "database", "lee_conmigo_demo.db")
os.environ.setdefault("LEE_CONMIGO_ADMIN_PIN", "demo-admin")

import streamlit as st

from database.db_config import init_db
from database.demo_bootstrap import ensure_demo_database
from core.session_state_demo import init_session_demo
from components.styles import apply_styles, set_page_config
from components.page_title import render_titulo_sidebar

from views_demo.salon_entrada_demo import render_salon_entrada_demo
from views_demo.padre.config_salon_demo import render_config_salon_demo
from views_demo.padre.zona_padres_demo import render_zona_padres_demo
from views_demo.padre.album_mgmt_demo import render_album_mgmt_demo
from views_demo.estudiante.hub_nino_demo import render_hub_nino_demo
from views_demo.estudiante.lecciones_nino_demo import render_lecciones_nino_demo
from views_demo.estudiante.album_nino_demo import (
    render_album_nino_demo,
    render_album_nino_categoria_demo,
)
from views_demo.estudiante.album_silabas_nino_demo import render_album_silabas_nino_demo
from views_demo.estudiante.album_abecedario_nino_demo import render_album_abecedario_nino_demo
from views_demo.estudiante.informe_sesion_demo import render_informe_sesion_demo
from views.estudiante.abecedario_matriz import render_abecedario_matriz
from views.docente.zona_docente import render_zona_docente
from views.tutor.zona_tutores import render_zona_tutores
from views.admin.zona_administradores import render_zona_administradores


def main():
    set_page_config()
    init_db()
    ensure_demo_database()
    init_session_demo()
    apply_styles()

    with st.sidebar:
        render_titulo_sidebar("Panel de Control DEMO")
        st.caption("Versión de demostración comercial")
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
        if st.button("👩‍🏫 Zona docentes", use_container_width=True, key="demo_sidebar_docente"):
            st.session_state.pagina_activa = "zona_docente"
            st.rerun()
        if st.button("🎓 Zona Tutores", use_container_width=True, key="demo_sidebar_tutor"):
            st.session_state.pagina_activa = "zona_tutores"
            st.rerun()
        if st.button("🛠️ Zona administradores", use_container_width=True, key="demo_sidebar_admin"):
            st.session_state.pagina_activa = "zona_admin"
            st.rerun()
        if st.button("👨‍👩‍👧 Zona de padres", use_container_width=True, key="demo_sidebar_zona"):
            st.session_state.pagina_activa = "zona_padres"
            st.rerun()
        if st.button(
            "➕ Registro de nuevos estudiantes",
            use_container_width=True,
            key="demo_sidebar_registro",
        ):
            st.session_state.pagina_activa = "config_salon"
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.session_state.pop("config_estudiante_id", None)
            st.rerun()

    pagina = st.session_state.pagina_activa
    if pagina == "salon_entrada":
        render_salon_entrada_demo()
    elif pagina == "config_salon":
        render_config_salon_demo()
    elif pagina == "zona_padres":
        render_zona_padres_demo()
    elif pagina == "zona_docente":
        render_zona_docente()
    elif pagina == "zona_tutores":
        render_zona_tutores()
    elif pagina == "zona_admin":
        render_zona_administradores()
    elif pagina == "album_mgmt":
        render_album_mgmt_demo()
    elif pagina == "hub_nino":
        render_hub_nino_demo()
    elif pagina == "lecciones_nino":
        render_lecciones_nino_demo()
    elif pagina == "album_nino":
        render_album_nino_demo()
    elif pagina == "album_nino_categoria":
        render_album_nino_categoria_demo()
    elif pagina == "album_silabas":
        render_album_silabas_nino_demo()
    elif pagina == "album_abecedario":
        render_album_abecedario_nino_demo()
    elif pagina == "informe_sesion":
        render_informe_sesion_demo()
    elif pagina == "abecedario_matriz":
        render_abecedario_matriz(titulo_extra="DEMO")


if __name__ == "__main__":
    main()
