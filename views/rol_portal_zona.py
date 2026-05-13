"""
Acceso con contraseña a Zona docentes / Zona tutores (cédula inicial desde Configuración del salón).
"""

from __future__ import annotations

import html
from collections.abc import Callable

import streamlit as st

from components.page_title import render_titulo_pagina
from core import gamificacion
from database.db_queries import (
    actualizar_password_docente_tutor,
    obtener_credencial_docente_tutor,
    verificar_password_docente_tutor,
)

_KEYS = {
    "docente": {
        "ok": "docente_acceso_ok",
        "change": "docente_pw_change_required",
        "filtro": "docente_filtro_nombre",
        "input_nombre": "docente_input_nombre_grupo",
        "input_clave": "docente_input_clave_acceso",
        "btn_login": "docente_btn_entrar_portal",
        "btn_buscar": "docente_btn_buscar",
        "btn_logout": "docente_btn_cerrar_sesion_portal",
        "btn_volver_vacio": "docente_volver_salon_vacio",
        "btn_volver_sin": "docente_volver_sin_resultados",
        "btn_volver": "docente_volver_salon",
        "informe_prefix": "docente_informe_",
    },
    "tutor": {
        "ok": "tutor_acceso_ok",
        "change": "tutor_pw_change_required",
        "filtro": "tutor_filtro_nombre",
        "input_nombre": "tutor_input_nombre",
        "input_clave": "tutor_input_clave_acceso",
        "btn_login": "tutor_btn_entrar_portal",
        "btn_buscar": "tutor_btn_buscar",
        "btn_logout": "tutor_btn_cerrar_sesion_portal",
        "btn_volver_vacio": "tutor_volver_salon_vacio",
        "btn_volver_sin": "tutor_volver_sin_resultados",
        "btn_volver": "tutor_volver_salon",
        "informe_prefix": "tutor_informe_",
    },
}


def _limpiar_sesion_portal(rol: str):
    k = _KEYS[rol]
    st.session_state[k["ok"]] = False
    st.session_state[k["change"]] = False
    st.session_state.pop(k["filtro"], None)


def render_zona_con_acceso_rol(
    *,
    rol: str,
    titulo_pagina: str,
    caption_md: str,
    label_nombre: str,
    placeholder_nombre: str,
    label_listado: str,
    mensaje_sin_credencial: str,
    mensaje_sin_alumnos: str,
    obtener_alumnos: Callable[[str], list],
):
    assert rol in _KEYS
    k = _KEYS[rol]

    render_titulo_pagina(titulo_pagina)
    st.markdown(caption_md)

    if st.session_state.get(k["change"]):
        nombre_bloqueado = (st.session_state.get(k["filtro"]) or "").strip()
        st.info(
            "Es tu **primer acceso** con la cédula registrada. Define una **nueva contraseña** "
            "(mínimo 6 caracteres; puedes usar letras y números)."
        )
        st.markdown(f"**Perfil:** {html.escape(nombre_bloqueado)}")
        n1 = st.text_input("Nueva contraseña", type="password", key=f"{rol}_nueva_pw_1")
        n2 = st.text_input("Repetir contraseña", type="password", key=f"{rol}_nueva_pw_2")
        if st.button("Guardar contraseña y continuar", type="primary", key=f"{rol}_btn_guardar_nueva_pw"):
            if len((n1 or "").strip()) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            elif (n1 or "").strip() != (n2 or "").strip():
                st.error("Las contraseñas no coinciden.")
            else:
                if actualizar_password_docente_tutor(rol, nombre_bloqueado, n1.strip()):
                    st.session_state[k["change"]] = False
                    st.session_state[k["ok"]] = True
                    st.success("Contraseña actualizada. Ya puedes consultar el listado.")
                    st.rerun()
                else:
                    st.error("No se pudo guardar. Intenta de nuevo.")
        if st.button("Cerrar sesión", key=f"{rol}_btn_cancelar_cambio_pw"):
            _limpiar_sesion_portal(rol)
            st.rerun()
        return

    if not st.session_state.get(k["ok"]):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            nombre_doc = st.text_input(
                label_nombre,
                value=st.session_state.get(k["filtro"], "") or "",
                key=k["input_nombre"],
                placeholder=placeholder_nombre,
            )
            clave_in = st.text_input(
                "Contraseña (por defecto: **cédula** registrada en el perfil del niño)",
                value="",
                type="password",
                key=k["input_clave"],
                placeholder="Cédula o contraseña nueva si ya la cambiaste",
            )
        with col_b:
            st.write("")
            st.write("")
            entrar = st.button("Entrar", type="primary", use_container_width=True, key=k["btn_login"])

        if entrar:
            nom = (nombre_doc or "").strip()
            if not nom:
                st.warning("Escribe el nombre de docente o tutor que figura en los perfiles.")
            elif not (clave_in or "").strip():
                st.warning("Escribe la contraseña (la cédula que registró el tutor).")
            else:
                cred = obtener_credencial_docente_tutor(rol, nom)
                alumnos_prev = obtener_alumnos(nom)
                if not cred:
                    if alumnos_prev:
                        st.error(mensaje_sin_credencial)
                    else:
                        st.error(
                            "No hay perfiles con ese nombre o aún no está registrada la cédula. "
                            "Revisa la escritura o pide al tutor que complete los datos en **Configuración del salón**."
                        )
                elif not verificar_password_docente_tutor(rol, nom, clave_in.strip()):
                    st.error("Contraseña incorrecta.")
                else:
                    st.session_state[k["filtro"]] = nom
                    if cred["must_change_password"]:
                        st.session_state[k["change"]] = True
                        st.session_state[k["ok"]] = False
                    else:
                        st.session_state[k["ok"]] = True
                        st.session_state[k["change"]] = False
                    st.rerun()

        if st.button("⬅️ Volver al salón", key=k["btn_volver_vacio"]):
            st.session_state.pagina_activa = "salon_entrada"
            _limpiar_sesion_portal(rol)
            st.rerun()
        return

    # Sesión autenticada: listado
    filtro = (st.session_state.get(k["filtro"]) or "").strip()
    if not filtro:
        _limpiar_sesion_portal(rol)
        st.rerun()
        return

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"### {label_listado} **{html.escape(filtro)}**")
    with c2:
        if st.button("Cerrar sesión", use_container_width=True, key=k["btn_logout"]):
            _limpiar_sesion_portal(rol)
            st.rerun()

    alumnos = obtener_alumnos(filtro)
    st.caption(f"{len(alumnos)} estudiante(s)")
    if not alumnos:
        st.warning(mensaje_sin_alumnos)
        if st.button("⬅️ Volver al salón", key=k["btn_volver_sin"]):
            st.session_state.pagina_activa = "salon_entrada"
            _limpiar_sesion_portal(rol)
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
            c1b, c2b, c3b = st.columns([2.2, 1.2, 1])
            with c1b:
                st.markdown(f"**{html.escape(nom)}**  \nÚltimo ingreso: `{html.escape(str(ult))}`")
            with c2b:
                st.metric("Estrellas", estrellas)
            with c3b:
                st.caption(f"Ciclo: {html.escape(ciclo)}")
            if st.button(
                "Ver informe de sesión",
                key=f"{k['informe_prefix']}{a['id']}",
                use_container_width=True,
            ):
                st.session_state.estudiante_id = a["id"]
                st.session_state.nombre_nino = (a["primer_nombre"] or "").strip() or nom
                st.session_state.pagina_activa = "informe_sesion"
                st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al salón", key=k["btn_volver"]):
        st.session_state.pagina_activa = "salon_entrada"
        _limpiar_sesion_portal(rol)
        st.rerun()
