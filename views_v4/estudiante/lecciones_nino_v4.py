import streamlit as st

from core import gamificacion
from database.db_queries_v4 import categoria_stats_ambas_actividades
from views.estudiante.lecciones_nino import render_lecciones_nino as _render_lecciones_nino_v2

DEMO_LECCIONES_ACTIVAS = ["M", "P"]


def _reset_indice_leccion_estudiante():
    est_id = st.session_state.get("estudiante_id")
    if est_id:
        st.session_state[f"est_{est_id}_indice_letra"] = 0
        # Limpiar estado interno de vocales guardado por V2 para evitar que
        # al cambiar de bloque quede "a medias" (res/pools/orden).
        prefix = f"est_{est_id}_vocal_"
        for k in list(st.session_state.keys()):
            if isinstance(k, str) and k.startswith(prefix):
                st.session_state.pop(k, None)
        # En V3 para vocales: primero mostramos 9 palabras (presentación),
        # luego completamos palabras y al final hacemos "escucha y toca".
        st.session_state[f"est_{est_id}_vocal_fase"] = "presenta"


def render_lecciones_nino_v4():
    id_est = st.session_state.get("estudiante_id")
    if id_est:
        st.session_state.v4_ciclo_id = gamificacion.ciclo_v4_activo(id_est)
    ciclo_id = st.session_state.get("v4_ciclo_id", "C1")

    # Gating: solo permitir entrar a lecciones si el álbum del ciclo está habilitado.
    # Si se intenta navegar directo (o quedó una navegación previa en session_state),
    # evitamos renderizar la lección y mostramos el mismo mensaje que el Hub.
    habilitado = False
    if id_est:
        try:
            idx = max(0, int(str(ciclo_id).strip().upper().replace("C", "")) - 1)
        except Exception:
            idx = 0
        categorias_inicio = ["Familia", "Juguetes", "En la cocina"]
        cats = categorias_inicio + []
        if idx > 0:
            # Mantiene el gating original de "álbum del ciclo completo" sin depender de CurriculumV4.
            cats = categorias_inicio
        if cats:
            habilitado = True
            for cat in cats:
                ok, _stats = categoria_stats_ambas_actividades(id_est, cat)
                if not ok:
                    habilitado = False
                    break
    st.session_state.v4_bloque_lecciones_habilitado = bool(habilitado)
    if not habilitado:
        st.caption("Completa el álbum del ciclo para desbloquear las lecciones.")
        if st.button("⬅️ Volver a Mi Ruta (4.0)", type="primary", use_container_width=True):
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
        st.stop()

    # DEMO: solo se habilitan las lecciones M y P.
    st.markdown("### 🔤 Lecciones DEMO")
    st.caption("Contenido disponible en esta demo: M y P.")

    demo_bloque = [s.upper() for s in DEMO_LECCIONES_ACTIVAS]
    if st.session_state.get("v3_letras_override") != demo_bloque:
        st.session_state["v3_letras_override"] = demo_bloque
        _reset_indice_leccion_estudiante()

    _render_lecciones_nino_v2()

    # Registrar trofeo de ciclo (3.2) en cuanto se cumplan los criterios (vocales + consonantes).
    if id_est:
        gamificacion.check_and_grant_lessons_ciclo_complete(id_est, ciclo_id)
        st.session_state.v4_ciclo_id = gamificacion.ciclo_v4_activo(id_est)

