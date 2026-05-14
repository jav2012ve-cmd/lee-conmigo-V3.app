"""Pantalla dedicada: elegir el avatar del niño para el Salón (registro o edición de perfil)."""

import os

import streamlit as st

from components.page_title import render_titulo_pagina
from database.db_queries import obtener_perfil_completo_nino

from views.padre import config_salon as cs


def render_config_salon_avatares():
    render_titulo_pagina("Galería de avatares")
    config_est_id = st.session_state.get("config_estudiante_id")
    estudiante_id_actual = config_est_id
    perfil = obtener_perfil_completo_nino(estudiante_id_actual) if estudiante_id_actual else None

    def _v(row, idx, default=""):
        if row is None or idx >= len(row):
            return default
        v = row[idx]
        return v if v is not None else default

    st.caption(
        "El dibujo que elijas es el que verá el niño en el **Salón** al tocar su foto. "
        "Las imágenes están en **assets/avatars_nino** (carpetas **nino** y **nina**)."
    )

    if st.button("⬅️ Volver al registro del perfil", key="avatares_volver_arriba"):
        st.session_state.pagina_activa = "config_salon"
        st.rerun()

    st.write("---")

    avatares_nino = cs._listar_avatares_nino()
    _kid = estudiante_id_actual or "new"
    path_key = f"config_avatar_nino_path_{_kid}"
    filtro_key = f"config_avatar_nino_filtro_{_kid}"

    if not avatares_nino:
        st.warning(
            "Aún no hay dibujos en **assets/avatars_nino**. "
            "Añade archivos .png o .jpg en las subcarpetas **nino** y **nina**."
        )
        return

    ruta_vis = None
    if estudiante_id_actual and perfil:
        ruta_vis = cs._foto_perfil_estudiante(
            estudiante_id_actual, _v(perfil, 2, ""), _v(perfil, 15, "")
        )
    cs._asegurar_sesion_avatar_path(path_key, ruta_vis, avatares_nino)

    n_nino = sum(1 for a in avatares_nino if a.get("genero") == "nino")
    n_nina = sum(1 for a in avatares_nino if a.get("genero") == "nina")
    st.caption(
        f"**{len(avatares_nino)}** personajes ({n_nino} niño(s), {n_nina} niña(s), el resto en «Todos»). "
        "Pulsa **Elegir** debajo de un dibujo; luego vuelve al registro y **guarda el perfil** para aplicar cambios."
    )
    filtro = st.radio(
        "Mostrar avatares",
        ["Todos", "Niños", "Niñas"],
        horizontal=True,
        key=filtro_key,
    )
    opts = cs._filtrar_avatares_nino_por_vista(avatares_nino, filtro)
    if not opts:
        st.warning(
            f"No hay imágenes clasificadas como **{filtro.lower()}**. "
            "Usa carpetas **nino** / **nina** o elige «Todos»."
        )
        opts = list(avatares_nino)
    opts_paths = [a["path"] for a in opts]
    curr = st.session_state.get(path_key)
    if curr not in opts_paths:
        st.session_state[path_key] = opts_paths[0]
    sel_preview = st.session_state.get(path_key) or opts_paths[0]
    if sel_preview and os.path.lexists(sel_preview):
        st.image(sel_preview, width=200, caption="Vista previa (Salón)")
    st.markdown("**Elige el avatar**")
    # Miniaturas con ancho fijo: menos píxeles por rerun que use_container_width (más fluido en OneDrive).
    ncols = 4
    _thumb_w = 130
    for row0 in range(0, len(opts), ncols):
        row_items = opts[row0 : row0 + ncols]
        gcols = st.columns(ncols)
        for j, av in enumerate(row_items):
            with gcols[j]:
                es_sel = cs._normalizar_ruta_abs(av["path"]) == cs._normalizar_ruta_abs(
                    st.session_state.get(path_key)
                )
                st.image(av["path"], width=_thumb_w)
                cap = av["label"][:18] + ("…" if len(av["label"]) > 18 else "")
                st.caption(f"**{cap}**" if es_sel else cap)
                idx_av = row0 + j
                btn_key = f"avatar_elegir_pag_{_kid}_{filtro}_{idx_av}"
                if st.button("Elegir", key=btn_key, use_container_width=True, type="secondary"):
                    st.session_state[path_key] = av["path"]
                    st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al registro del perfil", key="avatares_volver_abajo", use_container_width=True):
        st.session_state.pagina_activa = "config_salon"
        st.rerun()
