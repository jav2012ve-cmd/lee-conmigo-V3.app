import streamlit as st

from components.page_title import render_titulo_pagina
import os
from database.db_queries import (
    guardar_en_album_reemplazando,
    obtener_album_nino,
    obtener_estudiantes_por_padre,
    obtener_pin_padre,
    obtener_claves_estudiante,
)
from core.album_categories import CATEGORIAS_ALBUM

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_AVATARES_FAMILIA_DIR = os.path.join(_ROOT_DIR, "assets", "avatars_familia")
_FAMILIA_ROLES_AVATAR = {
    "PAPÁ",
    "PAPA",
    "MAMÁ",
    "MAMA",
    "ABUELA",
    "ABUELO",
    "TÍA",
    "TIA",
    "TÍO",
    "TIO",
    "PRIMA",
    "PRIMO",
    "HERMANA",
    "HERMANO",
}

# Palabras clave en nombre de archivo / etiqueta para sugerir avatares según el rol
_ROL_A_TOKENS_BUSQUEDA = {
    "ABUELA": ("abuela", "abuelita", "grandma", "granny", "nonna"),
    "ABUELO": ("abuelo", "abuelito", "grandpa", "grandfather", "nonno"),
    "MAMÁ": ("mama", "mamá", "madre", "mother", "mom"),
    "MAMA": ("mama", "mamá", "madre", "mother", "mom"),
    "PAPÁ": ("papa", "papá", "padre", "father", "dad"),
    "PAPA": ("papa", "papá", "padre", "father", "dad"),
    "TÍA": ("tia", "tía", "aunt"),
    "TIA": ("tia", "tía", "aunt"),
    "TÍO": ("tio", "tío", "uncle"),
    "TIO": ("tio", "tío", "uncle"),
    "PRIMA": ("prima", "cousin"),
    "PRIMO": ("primo", "cousin"),
    "HERMANA": ("hermana", "sister"),
    "HERMANO": ("hermano", "brother"),
}


def _filtrar_avatares_por_rol_familia(palabra_upper, todos):
    """Devuelve avatares cuyo nombre sugiere el rol; si no hay coincidencias, devuelve la lista completa."""
    if not todos:
        return []
    p = (palabra_upper or "").strip().upper()
    tokens = _ROL_A_TOKENS_BUSQUEDA.get(p)
    if not tokens:
        return list(todos)
    out = []
    for av in todos:
        base = os.path.basename(av.get("path") or "")
        blob = f"{av.get('label', '')} {base}".lower()
        if any(t in blob for t in tokens):
            out.append(av)
    return out if out else list(todos)


def _listar_avatares_familia():
    avatares = []
    try:
        if not os.path.isdir(_AVATARES_FAMILIA_DIR):
            return []
        for name in sorted(os.listdir(_AVATARES_FAMILIA_DIR)):
            lower = name.lower()
            if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                nombre = os.path.splitext(name)[0].replace("_", " ").replace("-", " ").strip()
                avatares.append({"label": nombre.title() or name, "path": os.path.join(_AVATARES_FAMILIA_DIR, name)})
    except Exception:
        return []
    return avatares


def render_album_mgmt():
    render_titulo_pagina("Gestión del Álbum Familiar")
    st.write("Sube las fotos que el niño usará para aprender. ¡Recuerda que el vínculo emocional es la clave!")

    padre_id = st.session_state.get("padre_id") or 1
    estudiantes = obtener_estudiantes_por_padre(padre_id) or []

    if not estudiantes:
        st.warning("⚠️ No hay perfiles de estudiante. Crea uno en la Configuración del Salón.")
        if st.button("Ir a Configuración"):
            st.session_state.pagina_activa = "config_salon"
            st.rerun()
        return

    def _nombre_completo(e):
        p = (e[1] or "").strip()
        s = (e[2] or "").strip() if len(e) > 2 else ""
        a = (e[3] or "").strip() if len(e) > 3 else ""
        return (" ".join(filter(None, [p, s, a]))).strip() or p

    # Opciones por nombre completo (único con " (id X)" si hay repetidos)
    opciones = ["— Elige un estudiante —"]
    mapa_display_a_id = {}
    for e in estudiantes:
        id_est = e[0]
        nombre_completo = _nombre_completo(e)
        display = nombre_completo
        if display in mapa_display_a_id:
            display = f"{nombre_completo} (id {id_est})"
        opciones.append(display)
        mapa_display_a_id[display] = id_est

    if "album_estudiante_id" not in st.session_state:
        st.session_state.album_estudiante_id = None
    if "album_acceso_confirmado_ids" not in st.session_state:
        st.session_state.album_acceso_confirmado_ids = []

    idx_sel = st.selectbox(
        "**Selecciona el estudiante** cuyo álbum quieres gestionar",
        range(len(opciones)),
        format_func=lambda i: opciones[i],
    )
    estudiante_seleccionado_id = mapa_display_a_id.get(opciones[idx_sel]) if idx_sel > 0 else None
    estudiante_seleccionado_nombre = opciones[idx_sel] if idx_sel > 0 else None

    # Al cambiar de estudiante, usamos el elegido (no confirmado aún si es otro)
    if estudiante_seleccionado_id != st.session_state.album_estudiante_id:
        st.session_state.album_estudiante_id = estudiante_seleccionado_id
        st.session_state.album_estudiante_nombre = estudiante_seleccionado_nombre

    if not estudiante_seleccionado_id:
        st.info("Elige un estudiante de la lista para continuar.")
        if st.button("⬅️ Volver al Salón"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    # Paso 2: confirmación o clave de acceso (clave del álbum del niño, o PIN del padre)
    acceso_ok = estudiante_seleccionado_id in (st.session_state.album_acceso_confirmado_ids or [])

    if not acceso_ok:
        clave_album_est, _ = obtener_claves_estudiante(estudiante_seleccionado_id)
        pin_padre = obtener_pin_padre(padre_id)
        nombre_nino = estudiante_seleccionado_nombre or "el niño"

        if clave_album_est:
            st.subheader("🔐 Clave de acceso al álbum")
            st.caption(f"Para gestionar el álbum de **{nombre_nino}**, introduce la clave definida en su perfil.")
            clave_ingresada = st.text_input("Clave del álbum", type="password", key="album_clave_input", placeholder="Clave del perfil del niño")
            if st.button("Confirmar acceso"):
                if (clave_ingresada or "").strip() == clave_album_est:
                    if estudiante_seleccionado_id not in st.session_state.album_acceso_confirmado_ids:
                        st.session_state.album_acceso_confirmado_ids = list(
                            st.session_state.album_acceso_confirmado_ids or []
                        ) + [estudiante_seleccionado_id]
                    st.success("Acceso confirmado.")
                    st.rerun()
                else:
                    st.error("Clave incorrecta. Vuelve a intentarlo.")
        elif pin_padre:
            st.subheader("🔐 Clave de acceso")
            st.caption(f"Para gestionar el álbum de **{nombre_nino}**, introduce tu PIN de tutor.")
            pin_ingresado = st.text_input("PIN", type="password", key="album_pin_input", placeholder="Ej: 1234")
            if st.button("Confirmar acceso"):
                if (pin_ingresado or "").strip() == pin_padre:
                    if estudiante_seleccionado_id not in st.session_state.album_acceso_confirmado_ids:
                        st.session_state.album_acceso_confirmado_ids = list(
                            st.session_state.album_acceso_confirmado_ids or []
                        ) + [estudiante_seleccionado_id]
                    st.success("Acceso confirmado.")
                    st.rerun()
                else:
                    st.error("PIN incorrecto. Vuelve a intentarlo.")
        else:
            st.subheader("Confirmación")
            st.caption(f"Confirma que eres el tutor de **{nombre_nino}** para gestionar su álbum.")
            if st.button("Sí, soy el tutor. Acceder al álbum"):
                if estudiante_seleccionado_id not in (st.session_state.album_acceso_confirmado_ids or []):
                    st.session_state.album_acceso_confirmado_ids = list(
                        st.session_state.album_acceso_confirmado_ids or []
                    ) + [estudiante_seleccionado_id]
                st.rerun()
        if st.button("⬅️ Volver al Salón"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    # Paso 3: gestión del álbum (estudiante ya seleccionado y acceso confirmado)
    id_est = st.session_state.album_estudiante_id
    nombre_nino = st.session_state.get("album_estudiante_nombre") or "el niño"

    _n_av_gallery = len(_listar_avatares_familia())
    with st.container(border=True):
        st.markdown("##### 👥 Avatares de familia (más visibles)")
        st.caption(
            "En **Familia**, al escribir MAMÁ, PAPÁ, ABUELA, etc., el formulario muestra **miniaturas de la galería** "
            "para elegir el dibujo adecuado (o puedes subir una foto)."
        )
        if _n_av_gallery:
            st.success(f"Galería disponible: **{_n_av_gallery}** personajes en `assets/avatars_familia`.")
        else:
            st.warning("Aún no hay imágenes en **assets/avatars_familia**; sin ellas no aparecerá la galería.")

    with st.expander("➕ Añadir nueva foto al álbum", expanded=True):
        with st.form("upload_foto_form"):
            col1, col2 = st.columns(2)
            with col1:
                palabra = st.text_input("Palabra Clave (ej: MAMÁ, DADO, REX)").strip().upper()
            with col2:
                categoria = st.selectbox("Categoría", CATEGORIAS_ALBUM)

            uploaded_file = None
            usar_avatar_familia = False
            avatar_path = ""
            avatar_label = ""
            palabra_normalizada = (palabra or "").strip().upper()

            if categoria == "Familia" and palabra_normalizada in _FAMILIA_ROLES_AVATAR:
                todos_av = _listar_avatares_familia()
                sugeridos = _filtrar_avatares_por_rol_familia(palabra_normalizada, todos_av)
                hay_sugerencia = bool(todos_av) and len(sugeridos) < len(todos_av) and len(sugeridos) > 0

                st.markdown(f"**👥 Familia — {palabra_normalizada}**")
                st.caption(
                    "Puedes elegir un **dibujo de la galería** (se muestran miniaturas) o **subir una foto** desde tu dispositivo."
                )
                modo_fam = st.radio(
                    "¿Cómo añades la imagen?",
                    ["Elegir dibujo de la galería (ver personajes)", "Subir foto desde el dispositivo"],
                    horizontal=True,
                    key=f"modo_fam_album_{id_est}",
                )

                if modo_fam.startswith("Elegir dibujo"):
                    usar_avatar_familia = True
                    if not todos_av:
                        st.warning("No hay archivos en **assets/avatars_familia**.")
                    else:
                        ver_todos = st.checkbox(
                            "Mostrar **todos** los personajes de la galería (además de los sugeridos para este rol)",
                            value=not hay_sugerencia,
                            key=f"ver_todos_av_{id_est}",
                        )
                        lista_sel = list(todos_av) if ver_todos else list(sugeridos)
                        if hay_sugerencia and not ver_todos:
                            st.info(
                                f"Mostrando **{len(lista_sel)}** dibujos sugeridos para «{palabra_normalizada}». "
                                f"Activa la casilla de arriba para ver los **{len(todos_av)}** personajes."
                            )
                        elif ver_todos:
                            st.caption(f"Galería completa: **{len(lista_sel)}** personajes.")

                        ncols = 6
                        for row0 in range(0, len(lista_sel), ncols):
                            row_items = lista_sel[row0 : row0 + ncols]
                            gcols = st.columns(ncols)
                            for j, av in enumerate(row_items):
                                with gcols[j]:
                                    st.image(av["path"], use_container_width=True)
                                    st.caption(av["label"][:24] + ("…" if len(av["label"]) > 24 else ""))

                        idx_avatar = st.selectbox(
                            "Selecciona el dibujo (debe coincidir con la miniatura elegida)",
                            range(len(lista_sel)),
                            format_func=lambda i: lista_sel[i]["label"],
                            key=f"avatar_familia_sel_{id_est}",
                        )
                        avatar_path = lista_sel[idx_avatar]["path"]
                        avatar_label = lista_sel[idx_avatar]["label"]
                else:
                    uploaded_file = st.file_uploader("Elige una foto", type=["png", "jpg", "jpeg"])
            else:
                uploaded_file = st.file_uploader("Elige una foto", type=["png", "jpg", "jpeg"])

            submit = st.form_submit_button("💾 Guardar en el Álbum")

            if submit:
                if palabra:
                    try:
                        file_path = ""
                        if uploaded_file:
                            user_path = os.path.join("assets", "uploads", str(id_est))
                            os.makedirs(user_path, exist_ok=True)
                            file_extension = os.path.splitext(uploaded_file.name)[1]
                            file_name = f"{categoria}_{palabra.replace(' ', '_')}{file_extension}"
                            file_path = os.path.join(user_path, file_name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                        elif usar_avatar_familia and avatar_path:
                            file_path = avatar_path
                        else:
                            st.warning("⚠️ Sube una foto o elige un avatar de familia.")
                            return

                        exito = guardar_en_album_reemplazando(id_est, palabra, categoria, file_path)
                        if exito:
                            if uploaded_file:
                                st.success(f"✅ ¡'{palabra}' ha sido guardada con foto personal!")
                            else:
                                st.success(f"✅ ¡'{palabra}' usará el avatar: {avatar_label}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Error al registrar en la base de datos.")
                    except Exception as e:
                        st.error(f"❌ Error al guardar el archivo: {e}")
                else:
                    st.warning("⚠️ Por favor, escribe una palabra y luego sube una foto o elige un avatar.")

    st.divider()

    st.subheader(f"Fotos actuales en el álbum de {nombre_nino}")
    fotos = obtener_album_nino(id_est)

    if fotos:
        for cat in CATEGORIAS_ALBUM:
            fotos_cat = [f for f in fotos if (f[1] or "").strip() == cat]
            if not fotos_cat:
                continue
            st.markdown(f"**{cat}**")
            cols = st.columns(4)
            for i, (palabra_db, cat_db, path_db) in enumerate(fotos_cat):
                with cols[i % 4]:
                    if os.path.exists(path_db):
                        st.image(path_db, caption=f"{palabra_db}", use_container_width=True)
                    else:
                        st.error(f"Archivo no encontrado: {palabra_db}")
            st.write("")
    else:
        st.info("El álbum está vacío. ¡Empieza subiendo la primera foto!")

    if st.button("⬅️ Volver al Salón"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
