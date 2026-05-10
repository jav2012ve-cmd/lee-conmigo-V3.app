"""
Zona docentes: consulta del desempeño del grupo asociado al nombre de docente
guardado en cada perfil de estudiante (campo nombre_docente).
"""
import html

import streamlit as st

from components.page_title import render_titulo_pagina
from database.db_queries import obtener_estudiantes_por_docente
from core import gamificacion


def render_zona_docente():
    render_titulo_pagina("Zona docentes")
    st.caption(
        "Introduce el **mismo nombre de docente o grupo** que figura en el perfil de cada niño "
        "(lo registran los tutores al crear o editar el perfil en Configuración del salón)."
    )

    col_a, col_b = st.columns([2, 1])
    with col_a:
        nombre_doc = st.text_input(
            "Nombre de la docente o del grupo",
            value=st.session_state.get("docente_filtro_nombre", ""),
            key="docente_input_nombre_grupo",
            placeholder="Ej: Profe Ana · 1º A",
        )
    with col_b:
        st.write("")
        st.write("")
        buscar = st.button("Ver grupo", type="primary", use_container_width=True, key="docente_btn_buscar")

    if buscar:
        st.session_state.docente_filtro_nombre = (nombre_doc or "").strip()
        st.rerun()

    filtro = (st.session_state.get("docente_filtro_nombre") or "").strip()
    if not filtro:
        st.info("Escribe un nombre y pulsa **Ver grupo** para listar a los estudiantes asignados.")
        if st.button("⬅️ Volver al salón", key="docente_volver_salon_vacio"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    alumnos = obtener_estudiantes_por_docente(filtro)
    st.markdown(f"### Grupo: **{html.escape(filtro)}** — {len(alumnos)} estudiante(s)")
    if not alumnos:
        st.warning("No hay perfiles con ese nombre de docente/grupo. Revisa la escritura o pide al tutor que lo actualice en la configuración del niño.")
        if st.button("⬅️ Volver al salón", key="docente_volver_sin_resultados"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    for a in alumnos:
        nom = " ".join(
            filter(
                None,
                [
                    (a["primer_nombre"] or "").strip(),
                    (a["segundo_nombre"] or "").strip(),
                    (a["apellidos"] or "").strip(),
                ],
            )
        ).strip() or "Sin nombre"
        estrellas = gamificacion.get_stars(a["id"])
        ult = a.get("ultimo_ingreso") or "—"
        ciclo = (a.get("ciclo_actual") or "").strip() or "—"
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.2, 1.2, 1])
            with c1:
                st.markdown(f"**{html.escape(nom)}**  \nÚltimo ingreso: `{html.escape(str(ult))}`")
            with c2:
                st.metric("Estrellas", estrellas)
            with c3:
                st.caption(f"Ciclo: {html.escape(ciclo)}")
            if st.button("Ver informe de sesión", key=f"docente_informe_{a['id']}", use_container_width=True):
                st.session_state.estudiante_id = a["id"]
                st.session_state.nombre_nino = (a["primer_nombre"] or "").strip() or nom
                st.session_state.pagina_activa = "informe_sesion"
                st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al salón", key="docente_volver_salon"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
