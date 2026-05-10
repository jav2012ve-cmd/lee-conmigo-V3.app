import base64
import html
import mimetypes
import os
import random
from urllib.parse import quote, unquote

import streamlit as st
from database.db_queries import obtener_album_nino, guardar_en_album_reemplazando
from core.album_categories import (
    CATEGORIAS_ALBUM,
    CATEGORIAS_CON_SFX_TARJETA,
    nombre_para_album_y_tts,
    fila_album_coincide_categoria,
    ruta_portada_album_categoria,
)
from core.asset_manager import AssetManager
from components.cards import render_album_card_karaoke, render_album_card_placeholder
from components.page_title import render_encabezado_logo_titulo_acciones

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_AVATARES_FAMILIA_DIR = os.path.join(_ROOT_DIR, "assets", "avatars_familia")
_PORTADAS_ALBUM_DIR = os.path.join(_ROOT_DIR, "assets", "album_categorias")
# Objetos mostrados por categoría en el álbum (vista usada por main.py)
_ALBUM_ITEMS_POR_CATEGORIA = 18


def _prioridad_imagen_album(path):
    p = (path or "").replace("\\", "/").lower()
    existe = os.path.isfile(path or "")
    if p.startswith("assets/uploads/") and existe:
        return 0
    if existe:
        return 1
    if p.startswith("assets/avatars_familia/"):
        return 2
    return 3


@st.cache_data(show_spinner=False)
def _portada_data_uri_cached(ruta_abs: str, mtime: float) -> str:
    with open(ruta_abs, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode("ascii")
    mime = mimetypes.guess_type(ruta_abs)[0] or "image/jpeg"
    return f"data:{mime};base64,{b64}"


def _listar_avatares_familia():
    avatares = []
    try:
        if not os.path.isdir(_AVATARES_FAMILIA_DIR):
            return []
        for name in sorted(os.listdir(_AVATARES_FAMILIA_DIR)):
            lower = name.lower()
            if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                label = os.path.splitext(name)[0].replace("_", " ").replace("-", " ").strip()
                path_abs = os.path.join(_AVATARES_FAMILIA_DIR, name)
                if os.path.isfile(path_abs):
                    avatares.append({"label": label.title() or name, "path": path_abs})
    except Exception:
        return []
    return avatares


def apply_album_cat_query_navigation():
    """Si la URL incluye ?album_cat=..., navega a la pantalla de imágenes de esa categoría."""
    try:
        if "album_cat" not in st.query_params:
            return
        raw = st.query_params.get("album_cat")
        if isinstance(raw, (list, tuple)):
            raw = raw[0]
        cand = unquote(str(raw))
        if cand not in CATEGORIAS_ALBUM:
            return
        st.session_state.album_nino_categoria = cand
        st.session_state.pagina_activa = "album_nino_categoria"
        try:
            del st.query_params["album_cat"]
        except Exception:
            pass
        st.rerun()
    except Exception:
        pass


def render_album_nino_categoria():
    """Pantalla dedicada: imágenes de la categoría elegida (desde la cuadrícula de portadas)."""
    nombre = st.session_state.get("nombre_nino", "Pequeño explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")
    categoria_sel = st.session_state.get("album_nino_categoria")

    if not categoria_sel or categoria_sel not in CATEGORIAS_ALBUM:
        st.warning("No se pudo cargar la categoría.")
        if st.button("⬅️ Volver al álbum", use_container_width=True, key="album_cat_invalid_volver"):
            st.session_state.album_nino_categoria = None
            st.session_state.pagina_activa = "album_nino"
            st.rerun()
        return

    def _acciones_categoria():
        if st.button("Volver al álbum", use_container_width=True, key="album_cat_volver_grid"):
            st.session_state.album_nino_categoria = None
            st.session_state.pagina_activa = "album_nino"
            st.rerun()

    render_encabezado_logo_titulo_acciones(
        categoria_sel,
        color_fav=color_fav,
        logo_height=176,
        slot_acciones=_acciones_categoria,
    )
    st.caption(f"Álbum de {nombre} · {categoria_sel}")

    st.write("---")

    # Fotos del álbum personal (DB) para esta categoría
    fotos = obtener_album_nino(st.session_state.estudiante_id) or []
    fotos_cat = [f for f in fotos if fila_album_coincide_categoria(f[1], categoria_sel, f[0])]
    # Imágenes genéricas de assets/genericos para esta categoría
    genericos_cat = AssetManager.obtener_genericos_por_categoria(categoria_sel)

    cache_key_fam = f"album_items_{categoria_sel}"
    # Familia: avatares visibles arriba (antes de la cuadrícula), no solo al final de página
    if categoria_sel == "Familia":
        n_fotos_propias_top = len(fotos_cat)
        avatares_top = _listar_avatares_familia()
        with st.container(border=True):
            st.markdown("#### 👥 Avatares de familia")
            st.caption(
                "Opción recomendada si prefieres **no subir fotos reales**: elige un dibujo para cada familiar "
                "(MAMÁ, PAPÁ, abuelos…). Son imágenes incluidas en la aplicación."
            )
            if not avatares_top:
                st.warning(
                    "Aún no hay dibujos en la carpeta del proyecto **assets/avatars_familia**. "
                    "Quien instala la app puede añadir allí archivos .png o .jpg."
                )
            else:
                st.success(
                    f"Tienes **{len(avatares_top)}** personajes disponibles. "
                    f"Fotos propias guardadas en Familia: **{n_fotos_propias_top}**."
                )
                prev_cols = st.columns(min(6, len(avatares_top)))
                for i, av in enumerate(avatares_top[:6]):
                    with prev_cols[i]:
                        st.image(av["path"], caption=av["label"][:18], use_container_width=True)
                c1, c2, c3 = st.columns([1, 1, 1.2])
                with c1:
                    palabra_av = st.text_input(
                        "Palabra para el álbum (ej: MAMÁ)",
                        key="album_avatar_palabra_familia",
                        placeholder="MAMÁ",
                    )
                    palabra_av = (palabra_av or "").strip().upper()
                with c2:
                    idx_av = st.selectbox(
                        "Elige el dibujo",
                        range(len(avatares_top)),
                        format_func=lambda i: avatares_top[i]["label"],
                        key="album_avatar_familia_sel",
                    )
                with c3:
                    st.write("")
                    st.write("")
                    if st.button("Guardar en mi álbum", type="primary", key="album_avatar_guardar_btn", use_container_width=True):
                        if not palabra_av:
                            st.warning("Escribí un nombre (palabra clave) para guardar.")
                        else:
                            ok = guardar_en_album_reemplazando(
                                st.session_state.estudiante_id,
                                palabra_av,
                                "Familia",
                                avatares_top[idx_av]["path"],
                            )
                            if ok:
                                st.session_state.pop(cache_key_fam, None)
                                st.success(f"Listo: **{palabra_av}** usa el avatar elegido.")
                                st.rerun()
                            else:
                                st.error("No se pudo guardar.")

    # Unir: primero las del álbum del niño, luego las genéricas (sin duplicar palabra)
    # Regla de prioridad para familia: foto personal existente > avatar > genérico.
    vistos = set()
    items = []
    mejores_album = {}
    for palabra, _c, path in fotos_cat:
        key = (palabra or "").strip().upper()
        if not key or not path:
            continue
        prio = _prioridad_imagen_album(path)
        actual = mejores_album.get(key)
        if actual is None or prio < actual["prio"]:
            mejores_album[key] = {"palabra": palabra, "ruta_img": path, "prio": prio}
    for key, item in mejores_album.items():
        if item["prio"] <= 2:
            items.append({"palabra": item["palabra"], "ruta_img": item["ruta_img"], "origen": "album"})
            vistos.add(key)
    for g in genericos_cat:
        key = (g.get("palabra") or "").strip().upper()
        if key and key not in vistos:
            items.append({"palabra": g["palabra"], "ruta_img": g["ruta_img"], "origen": "generico"})
            vistos.add(key)

    es_familia = categoria_sel == "Familia"
    # Selección aleatoria por categoría; se guarda en sesión para no cambiar al interactuar (karaoke).
    cache_key = cache_key_fam
    if cache_key not in st.session_state:
        real_items = [i for i in items if not i.get("placeholder")]
        random.shuffle(real_items)
        if es_familia:
            st.session_state[cache_key] = real_items
        else:
            sel = real_items[:_ALBUM_ITEMS_POR_CATEGORIA]
            while len(sel) < _ALBUM_ITEMS_POR_CATEGORIA:
                sel.append({"placeholder": True, "ruta_img": None, "palabra": None})
            st.session_state[cache_key] = sel
    items = st.session_state[cache_key]
    if not items:
        st.info(f"Aún no hay imágenes en **{categoria_sel}**. ¡Pronto habrá más!")
    else:
        num_cols = 3
        size_card = "xlarge" if es_familia else "normal"
        show_label_below = es_familia
        cols = st.columns(num_cols)
        for idx, item in enumerate(items):
            with cols[idx % num_cols]:
                if item.get("placeholder"):
                    render_album_card_placeholder(
                        unique_id=f"album_placeholder_{categoria_sel}_{idx}",
                        size=size_card,
                    )
                else:
                    nombre_visible = nombre_para_album_y_tts(item.get("palabra")) or "Imagen"
                    render_album_card_karaoke(
                        item["ruta_img"],
                        nombre_visible,
                        unique_id=f"album_{categoria_sel}_{idx}",
                        size=size_card,
                        show_label_below=show_label_below,
                        categoria=categoria_sel,
                        sonidos_tarjeta_habilitados=(categoria_sel in CATEGORIAS_CON_SFX_TARJETA),
                    )

        # Botón para ir a la actividad "Armar la palabra" (solo si hay imágenes reales)
        if not es_familia or len([i for i in items if not i.get("placeholder")]) >= 2:
            st.write("---")
            if st.button("📝 Jugar: Armar la palabra con sílabas", key="album_btn_silabas_categoria", use_container_width=True):
                st.session_state.album_actividad_categoria = categoria_sel
                st.session_state.pagina_activa = "album_silabas"
                st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al Inicio", use_container_width=True, key="album_cat_volver_hub"):
        st.session_state.album_nino_categoria = None
        st.session_state.pagina_activa = "hub_nino"
        st.rerun()


def render_album_nino():
    nombre = st.session_state.get("nombre_nino", "Pequeño explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")
    titulo = f"El Álbum de {(nombre or '').strip() or 'Pequeño explorador'}"

    def _acciones_album():
        if st.button(
            "Mi abecedario — elegir mis imágenes por letra",
            use_container_width=True,
            key="album_btn_abecedario",
        ):
            st.session_state.pop("album_abecedario_ver_estado", None)
            st.session_state.pagina_activa = "album_abecedario"
            st.rerun()
        if st.button("Ver estado de mi abecedario", use_container_width=True, key="album_btn_abecedario_estado"):
            st.session_state["album_abecedario_ver_estado"] = True
            st.session_state.pagina_activa = "album_abecedario"
            st.rerun()

    render_encabezado_logo_titulo_acciones(
        titulo,
        color_fav=color_fav,
        logo_height=192,
        slot_acciones=_acciones_album,
        subtitulo="Ver por categoría",
        caption_bajo_titulo="Pulsa la imagen de cada categoría para abrir su álbum.",
    )

    st.write("---")

    cats_ordenadas = sorted(CATEGORIAS_ALBUM, key=lambda c: (c or "").lower())
    if "album_nino_categoria" not in st.session_state:
        st.session_state.album_nino_categoria = None

    num_cols_grid = 4
    for fila in range(0, len(cats_ordenadas), num_cols_grid):
        celdas = cats_ordenadas[fila : fila + num_cols_grid]
        cols = st.columns(num_cols_grid)
        for j, cat in enumerate(celdas):
            with cols[j]:
                ruta_portada = ruta_portada_album_categoria(cat, _PORTADAS_ALBUM_DIR)
                with st.container(border=True):
                    if ruta_portada and os.path.isfile(ruta_portada):
                        mtime = os.path.getmtime(ruta_portada)
                        data_uri = _portada_data_uri_cached(ruta_portada, mtime)
                        href = f"?album_cat={quote(cat)}"
                        st.markdown(
                            f'<a href="{href}" target="_self" style="display:block;text-decoration:none;">'
                            f'<img src="{data_uri}" alt="{html.escape(cat)}" '
                            f'style="width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;"/></a>',
                            unsafe_allow_html=True,
                        )
                    else:
                        cat_esc = html.escape(cat)
                        href = f"?album_cat={quote(cat)}"
                        st.markdown(
                            f'<a href="{href}" target="_self" style="display:block;text-decoration:none;">'
                            f'<div style="aspect-ratio:4/3;min-height:80px;background:linear-gradient(160deg,#e8eef8,#dde4f0);'
                            f"border-radius:10px;display:flex;align-items:center;justify-content:center;"
                            f'text-align:center;padding:12px;font-size:0.9rem;color:#334;">'
                            f"<b>{cat_esc}</b></div></a>",
                            unsafe_allow_html=True,
                        )

    st.write("---")
    if st.button("⬅️ Volver al Inicio", use_container_width=True):
        st.session_state.album_nino_categoria = None
        st.session_state.pagina_activa = "hub_nino"
        st.rerun()
