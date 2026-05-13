"""
Zona administradores: alta de credenciales para docentes y tutores LeeConmigo
(mismo criterio que en Configuración del salón y que en Zona docentes / Zona tutores).
"""

from __future__ import annotations

import html

import streamlit as st

from components.page_title import render_titulo_pagina
from core.admin_portal import resolver_pin_administrador
from core.password_utils import normalizar_cedula_o_clave_numerica
from database.db_queries import listar_credenciales_docente_tutor, upsert_credencial_cedula_docente_tutor


def render_zona_administradores():
    render_titulo_pagina("Zona administradores")
    pin_cfg = resolver_pin_administrador()

    if not pin_cfg:
        st.error(
            "No hay **PIN de administrador** configurado. Define la variable de entorno "
            "`LEE_CONMIGO_ADMIN_PIN` o la clave `admin_portal_pin` en **Secrets** (Streamlit Cloud), "
            "por ejemplo: `admin_portal_pin = \"tu_pin_secreto\"` en `secrets.toml`."
        )
        if st.button("⬅️ Volver al salón", key="admin_volver_sin_pin"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    if not st.session_state.get("admin_acceso_ok"):
        st.caption(
            "Gestiona las credenciales con las que docentes y tutores entran a **Zona docentes** y **Zona Tutores**. "
            "El **nombre** debe coincidir exactamente con el que luego se escriba en los perfiles de los niños "
            "(sin distinguir mayúsculas). La **cédula** es la contraseña inicial."
        )
        pin_in = st.text_input("PIN de administrador", type="password", key="admin_pin_input")
        if st.button("Entrar", type="primary", key="admin_btn_entrar"):
            if (pin_in or "").strip() == pin_cfg:
                st.session_state.admin_acceso_ok = True
                st.rerun()
            else:
                st.error("PIN incorrecto.")
        if st.button("⬅️ Volver al salón", key="admin_volver_login"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    st.success("Sesión de administrador activa.")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader("Registrar o actualizar credencial")
    with c2:
        if st.button("Cerrar sesión admin", use_container_width=True, key="admin_btn_logout"):
            st.session_state.admin_acceso_ok = False
            st.rerun()

    rol = st.radio(
        "Tipo de perfil",
        options=["docente", "tutor"],
        format_func=lambda x: "Docente / grupo escolar" if x == "docente" else "Tutor LeeConmigo",
        horizontal=True,
        key="admin_radio_rol",
    )
    nombre = st.text_input(
        "Nombre tal como lo usarán en la app",
        key="admin_input_nombre",
        placeholder="Ej: Profe Ana · 1º A  (docente)  o  Profe Luis (tutor)",
        help="Debe ser el mismo texto que figurará en el perfil del niño (nombre docente o nombre tutor).",
    )
    cedula = st.text_input(
        "Cédula (contraseña inicial; solo números, mínimo 5 dígitos)",
        type="password",
        key="admin_input_cedula",
    )
    if st.button("Guardar credencial", type="primary", key="admin_btn_guardar_cred"):
        nom = (nombre or "").strip()
        digits = normalizar_cedula_o_clave_numerica(cedula or "")
        if not nom:
            st.warning("Escribe el nombre del perfil.")
        elif len(digits) < 5:
            st.warning("La cédula debe tener al menos 5 dígitos (puedes pegarla con puntos o guiones).")
        else:
            upsert_credencial_cedula_docente_tutor(rol, nom, digits)
            st.success(
                f"Credencial guardada para **{html.escape(rol)}** / **{html.escape(nom)}**. "
                "En el primer acceso deberán cambiar la contraseña."
            )
            st.rerun()

    st.write("---")
    st.subheader("Credenciales registradas")
    rows = listar_credenciales_docente_tutor()
    if not rows:
        st.info("Aún no hay credenciales. Usa el formulario de arriba para crear la primera.")
    else:
        st.caption(
            "La columna **Nombre (clave)** es la forma normalizada usada internamente; "
            "debe coincidir con el texto guardado en los perfiles (mayúsculas y espacios laterales no importan)."
        )
        for r in rows:
            rol_l = "Docente" if r["rol"] == "docente" else "Tutor"
            mc = "Sí (primer acceso)" if r["debe_cambiar_pw"] else "No"
            with st.container(border=True):
                st.markdown(
                    f"**{rol_l}** · `{html.escape(r['nombre_clave'])}`  \n"
                    f"Cambio obligatorio en acceso: **{mc}** · Actualizado: `{html.escape(str(r['actualizado']))}`"
                )

    st.write("---")
    if st.button("⬅️ Volver al salón", key="admin_volver_salon"):
        st.session_state.pagina_activa = "salon_entrada"
        st.session_state.admin_acceso_ok = False
        st.rerun()
