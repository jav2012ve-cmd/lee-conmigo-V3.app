"""
Estado de sesión para main_DEMO.

Este módulo no ejecuta consultas SQL: solo inicializa claves de `st.session_state`.
Las lecturas pesadas a SQLite deben ir en las vistas o en `database/demo_read_cache.py`
con TTL, y cargarse de forma diferida según la pantalla (ver `init_session_demo`).

Estrategia de carga diferida (lazy) recomendada:
- Mantener aquí solo flags de navegación, roles y overrides (p. ej. `v3_letras_override`).
- No volcar perfil completo del estudiante al arrancar: las vistas `hub_nino`, `lecciones_nino`,
  etc. ya llaman a `db_queries` cuando se renderizan.
- Si en el futuro se necesita prefetch (p. ej. prellenar sidebar), añadir una función
  `prefetch_demo_data_for_page(pagina: str)` invocada al final de `main_DEMO` según
  `st.session_state.pagina_activa`, y guardar resultados en claves acotadas
  (`demo_prefetch_hub`, …) con TTL en session_state o en `demo_read_cache`.
"""

import streamlit as st

# Solo estas consonantes en lecciones (`views.estudiante.lecciones_nino`: v3_letras_override).
DEMO_LETRAS_LECCIONES = ["M", "P"]


def init_session_demo(*, lazy: bool = True) -> None:
    """
    Inicializa variables de sesión para la app DEMO.

    lazy: reservado para no precargar datos de estudiante en bloque. Hoy no hay prefetch
    pesado; las vistas cargan bajo demanda. Si `lazy=False`, se puede llamar a hooks de
    prefetch sin bloquear el arranque (implementar cuando haga falta).
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

    if "demo_album_categoria_activa" not in st.session_state:
        st.session_state.demo_album_categoria_activa = None
    if "demo_flash_msg" not in st.session_state:
        st.session_state.demo_flash_msg = None

    st.session_state["v3_letras_override"] = list(DEMO_LETRAS_LECCIONES)

    if not lazy:
        _prefetch_demo_heavy_optional()


def _prefetch_demo_heavy_optional() -> None:
    """Hook para futuros precargas (perfil/álbum) cuando lazy=False."""
    # Intencionalmente vacío: evita SELECT al arranque de la app DEMO.
    pass


def logout_demo():
    st.session_state.padre_id = None
    st.session_state.estudiante_id = None
    st.session_state.autenticado = False
    st.session_state.rol_actual = "guest"
    st.session_state.pagina_activa = "salon_entrada"
    st.rerun()
