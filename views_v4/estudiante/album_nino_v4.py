import random
import os
import streamlit as st

from components.page_title import render_encabezado_logo_titulo_acciones

from database.db_queries import obtener_album_nino, guardar_en_album_reemplazando
from database.db_queries_v4 import categoria_stats_ambas_actividades
from core.asset_manager import AssetManager
from components.cards import render_album_card_karaoke, render_album_card_placeholder
from core.album_categories import (
    CATEGORIAS_ALBUM,
    CATEGORIAS_CON_SFX_TARJETA,
    nombre_para_album_y_tts,
    fila_album_coincide_categoria,
)
from core.curriculum_v4 import CurriculumV4
from core import gamificacion
from core.avatares_paths import listar_avatares_familia_galeria as _listar_avatares_familia

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Misma lógica que views_v4/padre/album_mgmt_padre_v4: palabra clave → tokens en nombre de archivo
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

# Orden en pantalla: un bloque por familiar; la palabra guardada en el álbum es esta (mayúsculas)
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

DEMO_ALBUM_CATEGORIAS_ACTIVAS = [
    "Familia",
    "Juguetes",
    "En la cocina",
    "Instrumentos musicales",
]


def _solo_avatares_por_rol(palabra_upper, todos):
    """Solo dibujos que coinciden con el rol (nombre de archivo / etiqueta)."""
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


def _resolver_ruta_album_nino(path):
    if not path or not isinstance(path, str):
        return None
    p = path.strip()
    if os.path.isfile(p):
        return os.path.normpath(os.path.abspath(p))
    rel = os.path.join(_ROOT_DIR, p.replace("/", os.sep).lstrip("\\/"))
    if os.path.isfile(rel):
        return os.path.normpath(os.path.abspath(rel))
    return None


def _paths_misma_imagen(a, b):
    try:
        return os.path.normpath(os.path.abspath(a)) == os.path.normpath(os.path.abspath(b))
    except Exception:
        return False


def _slug_key_rol(rol):
    """Claves ASCII únicas para widgets de Streamlit."""
    return (
        (rol or "")
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ñ", "N")
    )


def _mensaje_ruta_v4():
    """
    Mensaje guía (didáctico) al iniciar la actividad.
    - Si hay un mensaje flash (p. ej. 'has liberado...'), lo muestra una vez.
    - Si no, explica el siguiente objetivo del ciclo.
    """
    flash = st.session_state.pop("v4_flash_msg", None)
    if flash:
        st.success(flash)
        return

    ciclo_id = st.session_state.get("v4_ciclo_id", "C1")
    bloque = CurriculumV4.obtener_bloque_por_ciclo_id(ciclo_id)
    habilitado = bool(st.session_state.get("v4_bloque_lecciones_habilitado"))
    if habilitado:
        st.info(f"✅ Ya liberaste las lecciones del **{ciclo_id}**. Sigue con: **{', '.join(bloque)}**.")
    else:
        st.info(
            f"Ruta: completa tu **Álbum** en las categorías habilitadas para liberar las lecciones: **{', '.join(bloque)}**."
        )


def render_album_nino_v4():
    est_id = st.session_state.get("estudiante_id")
    if est_id:
        st.session_state.v4_ciclo_id = gamificacion.ciclo_v4_activo(est_id)

    nombre = st.session_state.get("nombre_nino", "Pequeño explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")

    titulo = f"El Álbum de {(nombre or '').strip() or 'Pequeño explorador'} (4.0)"

    def _acciones_v4_album():
        if st.button("Volver al inicio", use_container_width=True, key="v4_album_hdr_hub"):
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
        if st.button("Abecedario (9×3)", use_container_width=True, key="v4_album_hdr_abecedario"):
            st.session_state.pagina_activa = "abecedario_matriz"
            st.rerun()

    render_encabezado_logo_titulo_acciones(
        titulo,
        color_fav=color_fav,
        logo_height=192,
        slot_acciones=_acciones_v4_album,
    )

    _mensaje_ruta_v4()

    st.write("")
    st.markdown("**Categorías del álbum (DEMO)**")
    st.caption("Solo se muestran las cuatro categorías habilitadas en esta versión.")

    categorias_catalogo = list(CATEGORIAS_ALBUM)
    categorias_activas = [c for c in DEMO_ALBUM_CATEGORIAS_ACTIVAS if c in categorias_catalogo]
    if not categorias_activas:
        st.error("No hay categorías DEMO reconocidas en el catálogo de álbum.")
        return

    # Solo categorías DEMO: progreso 75% en ambas actividades por categoría.
    estado_cats = []
    for cat in categorias_activas:
        ok, stats = categoria_stats_ambas_actividades(est_id, cat)
        estado_cats.append({"cat": cat, "ok": ok, "stats": stats})

    # Primera categoría DEMO no superada (bloqueo secuencial respecto al orden DEMO).
    primera_pendiente = None
    for e in estado_cats:
        if not e["ok"]:
            primera_pendiente = e["cat"]
            break

    activa = st.session_state.get("v4_album_categoria_activa")
    if activa not in categorias_activas:
        activa = categorias_activas[0]
        st.session_state.v4_album_categoria_activa = activa

    num_cols = 3
    cols = st.columns(num_cols)
    for i, e in enumerate(estado_cats):
        cat = e["cat"]
        label = f"✅ {cat}" if e["ok"] else cat
        disabled = False
        if primera_pendiente is not None:
            idx_cat = categorias_activas.index(cat)
            idx_prim = categorias_activas.index(primera_pendiente)
            if idx_cat > idx_prim:
                disabled = True
        with cols[i % num_cols]:
            if st.button(label, use_container_width=True, key=f"v4_cat_btn_{cat}", disabled=disabled):
                st.session_state.v4_album_categoria_activa = cat
                st.rerun()

    st.write("---")
    categoria_sel = st.session_state.get("v4_album_categoria_activa")
    if not categoria_sel:
        st.info("Elige una categoría para ver tus imágenes.")
    elif categoria_sel not in categorias_activas:
        st.warning("Este álbum está bloqueado en la DEMO.")
    else:
        st.markdown(f"### {categoria_sel}")

        fotos = obtener_album_nino(st.session_state.estudiante_id) or []
        fotos_cat = [f for f in fotos if fila_album_coincide_categoria(f[1], categoria_sel, f[0])]
        genericos_cat = AssetManager.obtener_genericos_por_categoria(categoria_sel)

        cache_key_fam = f"v4_album_items_{categoria_sel}"
        if categoria_sel == "Familia":
            n_fp = len(fotos_cat)
            todos_av = _listar_avatares_familia()
            with st.container(border=True):
                st.markdown("#### 👥 Avatares de familia")
                st.caption(
                    "Para cada familiar solo verás **dibujos de ese rol** (según el nombre del archivo). "
                    "Pulsa **Elegir** bajo la imagen que quieras; se guarda al instante."
                )
                if not todos_av:
                    st.warning(
                        "Aún no hay dibujos en **assets/avatars_familia**. "
                        "Quien instala la app puede añadir allí archivos .png o .jpg."
                    )
                else:
                    st.success(
                        f"Galería: **{len(todos_av)}** personajes. "
                        f"Entradas ya guardadas en Familia: **{n_fp}**."
                    )
                    est_id = st.session_state.estudiante_id
                    fotos_para_fam = obtener_album_nino(est_id) or []
                    for idx_rol, rol in enumerate(_FAMILIA_ROLES_ORDEN):
                        slug = _slug_key_rol(rol)
                        ruta_db = None
                        for palabra_a, cat_a, path_a in fotos_para_fam:
                            if (cat_a or "").strip() == "Familia" and (palabra_a or "").strip().upper() == rol:
                                ruta_db = path_a
                                break
                        ruta_res = _resolver_ruta_album_nino(ruta_db) if ruta_db else None
                        lista_rol = _solo_avatares_por_rol(rol, todos_av)
                        with st.expander(
                            f"**{rol}** — elegir dibujo ({len(lista_rol)} disponible(s))",
                            expanded=(idx_rol == 0),
                        ):
                            if not lista_rol:
                                st.warning(
                                    f"No hay dibujos para **{rol}** en la galería. "
                                    "Hace falta un archivo en `assets/avatars_familia` cuyo nombre coincida con ese personaje."
                                )
                                continue
                            st.caption("Pulsa **Elegir** debajo de la imagen que prefieras.")
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
                                            st.caption("✓ En tu álbum")
                                        if st.button(
                                            "Elegir",
                                            key=f"v4_album_av_pick_{est_id}_{slug}_{global_idx}",
                                            use_container_width=True,
                                            type="primary"
                                            if (ruta_res and _paths_misma_imagen(av["path"], ruta_res))
                                            else "secondary",
                                        ):
                                            ok = guardar_en_album_reemplazando(
                                                est_id,
                                                rol,
                                                "Familia",
                                                av["path"],
                                            )
                                            if ok:
                                                st.session_state.pop(cache_key_fam, None)
                                                st.success(f"Listo: **{rol}** guardado.")
                                                st.rerun()
                                            else:
                                                st.error("No se pudo guardar.")

        vistos = set()
        items = []
        for palabra, _c, path in fotos_cat:
            key = (palabra or "").strip().upper()
            if key and key not in vistos:
                items.append({"palabra": palabra, "ruta_img": path, "origen": "album"})
                vistos.add(key)
        for g in genericos_cat:
            key = (g.get("palabra") or "").strip().upper()
            if key and key not in vistos:
                items.append({"palabra": g["palabra"], "ruta_img": g["ruta_img"], "origen": "generico"})
                vistos.add(key)

        es_familia = categoria_sel == "Familia"
        cache_key = cache_key_fam
        if cache_key not in st.session_state:
            real_items = [i for i in items if not i.get("placeholder")]
            random.shuffle(real_items)
            if es_familia:
                st.session_state[cache_key] = real_items
            else:
                sel = real_items[:9]
                while len(sel) < 9:
                    sel.append({"placeholder": True, "ruta_img": None, "palabra": None})
                st.session_state[cache_key] = sel
        items = st.session_state[cache_key]

        if not items:
            st.info(f"Aún no hay imágenes en **{categoria_sel}**. ¡Pronto habrá más!")
        else:
            grid_cols = st.columns(3)
            size_card = "xlarge" if es_familia else "normal"
            show_label_below = es_familia
            for idx, item in enumerate(items):
                with grid_cols[idx % 3]:
                    if item.get("placeholder"):
                        render_album_card_placeholder(
                            unique_id=f"v4_album_placeholder_{categoria_sel}_{idx}",
                            size=size_card,
                        )
                    else:
                        nombre_visible = nombre_para_album_y_tts(item.get("palabra")) or "Imagen"
                        render_album_card_karaoke(
                            item["ruta_img"],
                            nombre_visible,
                            unique_id=f"v4_album_{categoria_sel}_{idx}",
                            size=size_card,
                            show_label_below=show_label_below,
                            categoria=categoria_sel,
                            sonidos_tarjeta_habilitados=(categoria_sel in CATEGORIAS_CON_SFX_TARJETA),
                        )

            # Actividad (se mantiene igual: manda a album_silabas)
            if not es_familia or len([i for i in items if not i.get("placeholder")]) >= 2:
                st.write("---")
                if st.button("📝 Jugar: Armar la palabra con sílabas", key="v4_album_btn_silabas", use_container_width=True):
                    st.session_state.album_actividad_categoria = categoria_sel
                    st.session_state.pagina_activa = "album_silabas"
                    st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al Inicio", use_container_width=True, key="v4_album_volver"):
        st.session_state.pagina_activa = "hub_nino"
        st.rerun()

