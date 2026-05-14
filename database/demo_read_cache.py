"""
Lecturas SELECT frecuentes en la ruta DEMO, con TTL para reducir SQLite en cada rerun de Streamlit.

Solo deben usarse cuando `using_demo_database()` es True (lee_conmigo_demo.db).
Tras escrituras importantes, llamar `clear_demo_read_cache()` si se requiere frescor inmediato.
"""

from __future__ import annotations

import streamlit as st
from typing import Tuple


def clear_demo_read_cache() -> None:
    """Invalida cachés de lectura demo (p. ej. tras crear/editar perfil desde la misma sesión)."""
    for fn in (
        demo_obtener_estudiantes_por_padre,
        demo_obtener_album_nino_varios,
        demo_obtener_avatar_estudiante,
    ):
        try:
            fn.clear()
        except Exception:
            pass


@st.cache_data(show_spinner=False, ttl=60)
def demo_obtener_estudiantes_por_padre(padre_id: int):
    from database.db_queries import obtener_estudiantes_por_padre

    return obtener_estudiantes_por_padre(padre_id)


@st.cache_data(show_spinner=False, ttl=45)
def demo_obtener_album_nino_varios(ids_key: Tuple[int, ...]):
    from database.db_queries import obtener_album_nino_varios

    return obtener_album_nino_varios(list(ids_key))


@st.cache_data(show_spinner=False, ttl=45)
def demo_obtener_avatar_estudiante(estudiante_id: int):
    from database.db_queries import obtener_avatar_estudiante

    return obtener_avatar_estudiante(estudiante_id)
