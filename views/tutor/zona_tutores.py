"""
Zona Tutores: maestros/tutores que acompañan en LeeConmigo (campo nombre_tutor del perfil).
Puede coincidir con la docente de aula (nombre_docente) o ser otra persona.
"""
import html

import streamlit as st

from components.page_title import render_titulo_pagina
from database.db_queries import obtener_estudiantes_por_tutor
from core import gamificacion


def render_zona_tutores():
    render_titulo_pagina("Zona Tutores")
    st.caption(
        "Introduce el **mismo nombre de tutor LeeConmigo** que figura en el perfil del niño "
        "(lo registran los padres en Configuración del salón). "
        "No tiene que coincidir con la docente de aula."
    )

    col_a, col_b = st.columns([2, 1])
    with col_a:
        nombre_tut = st.text_input(
            "Nombre del tutor en LeeConmigo",
            value=st.session_state.get("tutor_filtro_nombre", ""),
            key="tutor_input_nombre",
            placeholder="Ej: Profe Luis",
        )
    with col_b:
        st.write("")
        st.write("")
        buscar = st.button("Ver alumnos", type="primary", use_container_width=True, key="tutor_btn_buscar")

    if buscar:
        st.session_state.tutor_filtro_nombre = (nombre_tut or "").strip()
        st.rerun()

    filtro = (st.session_state.get("tutor_filtro_nombre") or "").strip()
    if not filtro:
        st.info("Escribe un nombre y pulsa **Ver alumnos** para listar a quienes tienes asignados.")
        if st.button("⬅️ Volver al salón", key="tutor_volver_salon_vacio"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    alumnos = obtener_estudiantes_por_tutor(filtro)
    st.markdown(f"### Tutor: **{html.escape(filtro)}** — {len(alumnos)} estudiante(s)")
    if not alumnos:
        st.warning(
            "No hay perfiles con ese nombre de tutor. Revisa la escritura o pide a la familia "
            "que lo registre en el perfil del niño (Zona de padres → Configuración)."
        )
        if st.button("⬅️ Volver al salón", key="tutor_volver_sin_resultados"):
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
            if st.button("Ver informe de sesión", key=f"tutor_informe_{a['id']}", use_container_width=True):
                st.session_state.estudiante_id = a["id"]
                st.session_state.nombre_nino = (a["primer_nombre"] or "").strip() or nom
                st.session_state.pagina_activa = "informe_sesion"
                st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al salón", key="tutor_volver_salon"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
