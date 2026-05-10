import streamlit as st

from core.curriculum_v4 import CurriculumV4
from core import gamificacion
from database.db_queries_v4 import categoria_ok_75_por_ambas_actividades

# Reusamos la pantalla V2 por ahora (sin modificarla)
from views.salon_entrada import render_salon_entrada as _render_salon_entrada_v2


def render_salon_entrada_v4():
    # Misma experiencia que main: clave por emojis / «sin clave» sin cintillo V4 encima.
    if st.session_state.get("pendiente_confirmar_emoji") is not None:
        _render_salon_entrada_v2()
        return

    st.caption("Versión 4.0: flujo académico guiado por ciclos.")

    # Escalera/MAPA (si ya hay estudiante en sesión)
    est_id = st.session_state.get("estudiante_id")
    if est_id:
        st.session_state.v4_ciclo_id = gamificacion.ciclo_v4_activo(est_id)
        ciclo_id = st.session_state.get("v4_ciclo_id", "C1")
        idx = CurriculumV4.obtener_ciclo_idx_por_id(ciclo_id)
        cats = CurriculumV4.categorias_habilitadas_para_ciclo_idx(idx)
        bloque = CurriculumV4.obtener_bloque_por_ciclo_id(ciclo_id)

        st.markdown("### 🪜 Mi escalera de progreso (4.0)")
        completas = 0
        for c in cats:
            ok, _stats = categoria_ok_75_por_ambas_actividades(est_id, c)
            if ok:
                completas += 1
        st.info(
            f"**Ciclo actual:** {ciclo_id}  \n"
            f"**Álbum:** {completas}/{len(cats)} categorías superadas (75% en ambas actividades)  \n"
            f"**Próximas lecciones:** {', '.join(bloque)}"
        )
    _render_salon_entrada_v2()

