import streamlit as st

from core.curriculum_v3 import CurriculumV3
from core import gamificacion
from database.db_queries_v3 import categoria_stats_ambas_actividades
from views.estudiante.lecciones_nino import render_lecciones_nino as _render_lecciones_nino_v2


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


def render_lecciones_nino_v3():
    id_est = st.session_state.get("estudiante_id")
    if id_est:
        st.session_state.v3_ciclo_id = gamificacion.ciclo_v3_activo(id_est)
    ciclo_id = st.session_state.get("v3_ciclo_id", "C1")
    bloque = CurriculumV3.obtener_bloque_por_ciclo_id(ciclo_id) or []

    # Gating: solo permitir entrar a lecciones si el álbum del ciclo está habilitado.
    # Si se intenta navegar directo (o quedó una navegación previa en session_state),
    # evitamos renderizar la lección y mostramos el mismo mensaje que el Hub.
    habilitado = False
    if id_est:
        try:
            idx = CurriculumV3.obtener_ciclo_idx_por_id(ciclo_id)
        except Exception:
            idx = 0
        cats = CurriculumV3.categorias_habilitadas_para_ciclo_idx(idx)
        if cats:
            habilitado = True
            for cat in cats:
                ok, _stats = categoria_stats_ambas_actividades(id_est, cat)
                if not ok:
                    habilitado = False
                    break
    st.session_state.v3_bloque_lecciones_habilitado = bool(habilitado)
    if not habilitado:
        st.caption("Completa el álbum del ciclo para desbloquear las lecciones.")
        if st.button("⬅️ Volver a Mi Ruta (V3)", type="primary", use_container_width=True):
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
        st.stop()

    # C1: lecciones de vocales por bloque pedagógico.
    if ciclo_id == "C1":
        opciones = [
            ("A-E-I", ["A", "E", "I"]),
            ("I-O-U", ["I", "O", "U"]),
            ("A-E-I-O-U", ["A", "E", "I", "O", "U"]),
        ]
        if "v3_leccion_bloque_idx" not in st.session_state:
            st.session_state["v3_leccion_bloque_idx"] = 0

        st.markdown("### 🔤 Lecciones del Ciclo 1 (Vocales)")
        cols = st.columns(3)
        for i, (nombre, letras) in enumerate(opciones):
            with cols[i]:
                tipo = "primary" if st.session_state.get("v3_leccion_bloque_idx", 0) == i else "secondary"
                if st.button(nombre, key=f"v3_c1_bloque_{i}", type=tipo, use_container_width=True):
                    st.session_state["v3_leccion_bloque_idx"] = i
                    st.session_state["v3_letras_override"] = letras
                    _reset_indice_leccion_estudiante()
                    st.rerun()

        idx = int(st.session_state.get("v3_leccion_bloque_idx", 0))
        idx = max(0, min(idx, len(opciones) - 1))
        st.session_state["v3_letras_override"] = opciones[idx][1]

        # Si entramos a lecciones desde el Hub sin tocar el botón del bloque,
        # este reset garantiza que el bloque arranque en el estado V3 correcto.
        if st.session_state.get("v3_lecciones_applied_block_idx") != idx:
            st.session_state["v3_lecciones_applied_block_idx"] = idx
            _reset_indice_leccion_estudiante()
        st.caption(f"Bloque activo: {opciones[idx][0]}")
    else:
        # C2+ : consonantes/sílabas según bloque del ciclo.
        letras = [x for x in bloque if isinstance(x, str) and len(x) == 1 and x.isalpha()]
        st.session_state["v3_letras_override"] = [s.upper() for s in letras]
        if bloque:
            st.caption(f"Lecciones V3 del ciclo {ciclo_id}: {', '.join(bloque)}")

    _render_lecciones_nino_v2()

    # Registrar trofeo de ciclo (3.2) en cuanto se cumplan los criterios (vocales + consonantes).
    if id_est:
        gamificacion.check_and_grant_lessons_ciclo_complete(id_est, ciclo_id)
        st.session_state.v3_ciclo_id = gamificacion.ciclo_v3_activo(id_est)

