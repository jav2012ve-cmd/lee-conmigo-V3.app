"""Gestión de álbum 5.0: en Familia (roles predefinidos) solo avatares de galería; otras categorías permiten subir foto."""
import os
import streamlit as st

from components.page_title import render_titulo_pagina
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
DEMO_ALBUM_CATEGORIAS_ACTIVAS = [
    "Familia",
    "Juguetes",
    "En la cocina",
    "Instrumentos musicales",
]

# Orden en pantalla: un bloque por familiar (misma palabra clave que en el álbum del niño)
_FAMILIA_ROLES_ORDEN = [
    "MAMÁ",
    "PAPÁ",
    "ABUELA",
    "ABUELO",
    "TÍA",
    "TÍO",
    "PRIMA",
    "PRIMO",
    "HERMANA",
    "HERMANO",
]

_CATEGORIAS_DEMO = [c for c in CATEGORIAS_ALBUM if c in DEMO_ALBUM_CATEGORIAS_ACTIVAS]

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


def _solo_avatares_por_rol(palabra_upper, todos):
    """Solo dibujos que coinciden con el rol (nombre de archivo / etiqueta); sin rellenar con toda la galería."""
    if not todos:
        return []
    p = (palabra_upper or "").strip().upper()
    tokens = _ROL_A_TOKENS_BUSQUEDA.get(p)
    if not tokens:
        return []
    out = []
    for av in todos:
        base = os.path.basename(av.get("path") or "")
        blob = f"{av.get('label', '')} {base}".lower()
        if any(t in blob for t in tokens):
            out.append(av)
    return out


def _paths_misma_imagen(a, b):
    try:
        return os.path.normpath(os.path.abspath(a)) == os.path.normpath(os.path.abspath(b))
    except Exception:
        return False


def _slug_key_rol(rol):
    return (
        (rol or "")
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ñ", "N")
    )


def _resolver_ruta_album_padre(path):
    if not path or not isinstance(path, str):
        return None
    p = path.strip()
    if os.path.isfile(p):
        return os.path.normpath(os.path.abspath(p))
    rel = os.path.join(_ROOT_DIR, p.replace("/", os.sep).lstrip("\\/"))
    if os.path.isfile(rel):
        return os.path.normpath(os.path.abspath(rel))
    return None


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


def render_album_mgmt_v5():
    render_titulo_pagina("Gestión del álbum (5.0)")
    st.write(
        "**5.0** usa una base nueva: no hay fotos ni perfiles heredados. "
        "Solo se gestionan **cuatro álbumes** (Familia, Juguetes, En la cocina e Instrumentos musicales). "
        "En Familia no se suben fotos personales; solo avatares de la galería del sistema."
    )

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

    if estudiante_seleccionado_id != st.session_state.album_estudiante_id:
        st.session_state.album_estudiante_id = estudiante_seleccionado_id
        st.session_state.album_estudiante_nombre = estudiante_seleccionado_nombre

    if not estudiante_seleccionado_id:
        st.info("Elige un estudiante de la lista para continuar.")
        if st.button("⬅️ Volver al Salón"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    acceso_ok = estudiante_seleccionado_id in (st.session_state.album_acceso_confirmado_ids or [])

    if not acceso_ok:
        clave_album_est, _ = obtener_claves_estudiante(estudiante_seleccionado_id)
        pin_padre = obtener_pin_padre(padre_id)
        nombre_nino = estudiante_seleccionado_nombre or "el niño"

        if clave_album_est:
            st.subheader("🔐 Clave de acceso al álbum")
            st.caption(f"Para gestionar el álbum de **{nombre_nino}**, introduce la clave definida en su perfil.")
            clave_ingresada = st.text_input("Clave del álbum", type="password", key="album_clave_input_v5", placeholder="Clave del perfil del niño")
            if st.button("Confirmar acceso", key="album_conf_clave_v5"):
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
            pin_ingresado = st.text_input("PIN", type="password", key="album_pin_input_v5", placeholder="Ej: 1234")
            if st.button("Confirmar acceso", key="album_conf_pin_v5"):
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
            if st.button("Sí, soy el tutor. Acceder al álbum", key="album_conf_tutor_v5"):
                if estudiante_seleccionado_id not in (st.session_state.album_acceso_confirmado_ids or []):
                    st.session_state.album_acceso_confirmado_ids = list(
                        st.session_state.album_acceso_confirmado_ids or []
                    ) + [estudiante_seleccionado_id]
                st.rerun()
        if st.button("⬅️ Volver al Salón", key="album_volver_salon_gate_v5"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    id_est = st.session_state.album_estudiante_id
    nombre_nino = st.session_state.get("album_estudiante_nombre") or "el niño"

    todos_av = _listar_avatares_familia()
    _n_av_gallery = len(todos_av)
    with st.container(border=True):
        st.markdown("##### 👥 Avatares de familia (5.0)")
        st.caption(
            "Para **Familia** usa el bloque de abajo: **un dibujo por familiar** (MAMÁ, ABUELA…). "
            "Para el resto de categorías, sube una foto desde el otro apartado."
        )
        if _n_av_gallery:
            st.success(f"Galería disponible: **{_n_av_gallery}** personajes en `assets/avatars_familia`.")
        else:
            st.warning("Aún no hay imágenes en **assets/avatars_familia**; sin ellas no podrás completar entradas de familia.")

    with st.expander("👥 Familia — elegir avatar por familiar", expanded=True):
        if not todos_av:
            st.warning("No hay archivos en **assets/avatars_familia**.")
        else:
            st.caption(
                "Para cada familiar solo verás **dibujos de ese rol** (según el nombre del archivo en la galería). "
                "Pulsa **Elegir** bajo la imagen que quieras; se guarda al instante."
            )
            fotos_album = obtener_album_nino(id_est) or []
            for idx_rol, rol in enumerate(_FAMILIA_ROLES_ORDEN):
                slug = _slug_key_rol(rol)
                ruta_db = None
                for palabra_a, cat_a, path_a in fotos_album:
                    if (cat_a or "").strip() == "Familia" and (palabra_a or "").strip().upper() == rol:
                        ruta_db = path_a
                        break
                ruta_res = _resolver_ruta_album_padre(ruta_db) if ruta_db else None
                lista_rol = _solo_avatares_por_rol(rol, todos_av)
                with st.expander(
                    f"**{rol}** — elegir dibujo ({len(lista_rol)} disponible(s))",
                    expanded=(idx_rol == 0),
                ):
                    if not lista_rol:
                        st.warning(
                            f"No hay imágenes en la galería que coincidan con **{rol}**. "
                            "Añade archivos en `assets/avatars_familia` cuyo nombre sugiera ese personaje "
                            "(por ejemplo: mama, abuela, tio…)."
                        )
                        continue
                    st.caption(
                        "Solo se muestran dibujos filtrados para este familiar. "
                        "Pulsa **Elegir** debajo de la imagen preferida."
                    )
                    ncols = 6
                    for row0 in range(0, len(lista_rol), ncols):
                        row_items = lista_rol[row0 : row0 + ncols]
                        gcols = st.columns(ncols)
                        for j, av in enumerate(row_items):
                            global_idx = row0 + j
                            with gcols[j]:
                                st.image(av["path"], use_container_width=True)
                                cap = av["label"][:20] + ("…" if len(av["label"]) > 20 else "")
                                st.caption(cap)
                                if ruta_res and _paths_misma_imagen(av["path"], ruta_res):
                                    st.caption("✓ En el álbum")
                                if st.button(
                                    "Elegir",
                                    key=f"padre_v5_av_pick_{id_est}_{slug}_{global_idx}",
                                    use_container_width=True,
                                    type="primary"
                                    if (ruta_res and _paths_misma_imagen(av["path"], ruta_res))
                                    else "secondary",
                                ):
                                    ok = guardar_en_album_reemplazando(
                                        id_est,
                                        rol,
                                        "Familia",
                                        av["path"],
                                    )
                                    if ok:
                                        st.success(f"✅ **{rol}** guardado.")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error("❌ No se pudo guardar.")

    with st.expander("➕ Añadir foto al álbum (no disponible en 5.0 para estas categorías)", expanded=False):
        st.info(
            "En 5.0 no está permitida la subida de fotos personales para estas categorías. "
            "El niño solo puede representarse con avatares de la galería."
        )
        st.caption(f"Álbumes activos en 5.0: {', '.join(_CATEGORIAS_DEMO)}")

    st.divider()

    st.subheader(f"Fotos actuales en el álbum de {nombre_nino}")
    fotos = obtener_album_nino(id_est)

    if fotos:
        for cat in _CATEGORIAS_DEMO:
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
        st.info("El álbum está vacío. ¡Empieza añadiendo la primera entrada!")

    if st.button("⬅️ Volver al Salón", key="album_volver_salon_v5"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
