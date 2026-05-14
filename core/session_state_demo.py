"""
Estado de sesión para main_DEMO.

Reglas de rendimiento y arquitectura:
- Este módulo NO importa `database.*` y NO ejecuta SELECT ni ninguna otra consulta SQL.
  Cualquier lectura a BD debe vivir en vistas o en `database/demo_read_cache.py` con
  `@st.cache_data` / TTL según corresponda.
- `init_session_demo(lazy=True)` solo materializa claves de navegación y flags; no precarga
  perfiles ni álbumes. Las vistas cargan datos bajo demanda al renderizarse.

Estrategia de carga diferida (lazy) recomendada:
- Mantener aquí solo flags de navegación, roles y overrides (p. ej. `v3_letras_override`).
- Si en el futuro se necesita prefetch por pantalla, añadir `prefetch_demo_data_for_page(pagina)`
  invocada desde `main_DEMO` (no desde aquí con SQL directo) y delegar en funciones cacheadas.
"""

import streamlit as st

# Solo estas consonantes en lecciones (`views.estudiante.lecciones_nino`: v3_letras_override).
DEMO_LETRAS_LECCIONES = ["M", "P"]


def init_session_demo(*, lazy: bool = True) -> None:
    """
    Inicializa variables de sesión para la app DEMO (sin acceso a base de datos).

    lazy: si es False, se puede activar prefetch explícito vía `_prefetch_demo_heavy_optional`
    (reservado; no ejecuta SQL desde este archivo).
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
    """
    Reservado para precarga explícita cuando lazy=False.
    No implementar consultas SQL aquí: usar vistas o `database/demo_read_cache.py`.
    """
    return


def logout_demo():
    st.session_state.padre_id = None
    st.session_state.estudiante_id = None
    st.session_state.autenticado = False
    st.session_state.rol_actual = "guest"
    st.session_state.pagina_activa = "salon_entrada"
    st.rerun()
