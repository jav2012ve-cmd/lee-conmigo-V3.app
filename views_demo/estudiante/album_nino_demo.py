import base64
import html
import mimetypes
import os
from urllib.parse import quote

import streamlit as st

from core.album_categories import CATEGORIAS_ALBUM, ruta_portada_album_categoria
from core.asset_manager import AssetManager
from components.page_title import render_encabezado_logo_titulo_acciones
from views.estudiante.album_nino import render_album_nino_categoria

DEMO_CATEGORIAS_ACTIVAS = [
    "Familia",
    "Juguetes",
    "En la cocina",
    "Instrumentos musicales",
]
# Misma raíz que views/estudiante/album_nino.py: LeeConmigoV4 (dos niveles desde views_demo/estudiante/)
_PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_PORTADAS_ALBUM_DIR = os.path.join(_PROJ_ROOT, "assets", "album_categorias")


def _resolver_ruta_proyecto(path):
    if not path or not isinstance(path, str):
        return None
    p = path.strip()
    if os.path.isfile(p):
        return os.path.normpath(os.path.abspath(p))
    rel = os.path.join(_PROJ_ROOT, p.replace("/", os.sep).lstrip("\\/"))
    if os.path.isfile(rel):
        return os.path.normpath(rel)
    return None


def _ruta_tapa_categoria(cat):
    """
    Portada oficial en assets/album_categorias/; si no existe, primera imagen genérica de la categoría.
    """
    ruta = ruta_portada_album_categoria(cat, _PORTADAS_ALBUM_DIR)
    if ruta and os.path.isfile(ruta):
        return ruta
    genericos = AssetManager.obtener_genericos_por_categoria(cat)
    if genericos:
        cand = _resolver_ruta_proyecto(genericos[0].get("ruta_img"))
        if cand:
            return cand
    return None


def _data_uri_imagen(path, max_bytes=1_800_000):
    """Data URI para poder enlazar la tapa (solo categorías liberadas); evita archivos enormes."""
    try:
        if os.path.getsize(path) > max_bytes:
            return None
    except OSError:
        return None
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def render_album_nino_demo():
    # Navegacion por query param como en la vista original.
    cat_q = st.query_params.get("album_cat")
    cat_q = str(cat_q).strip() if cat_q else ""
    if cat_q:
        if cat_q in DEMO_CATEGORIAS_ACTIVAS:
            st.session_state.album_nino_categoria = cat_q
            st.session_state.pagina_activa = "album_nino_categoria"
            try:
                del st.query_params["album_cat"]
            except Exception:
                pass
            st.rerun()
        else:
            st.warning("Este album esta bloqueado en la DEMO.")
            try:
                del st.query_params["album_cat"]
            except Exception:
                pass

    nombre = st.session_state.get("nombre_nino", "Pequeño explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")
    titulo = f"El Álbum de {(nombre or '').strip() or 'Pequeño explorador'} (DEMO)"

    def _acciones_demo_album():
        if st.button(
            "Mi abecedario — elegir mis imágenes por letra",
            use_container_width=True,
            key="demo_album_btn_abecedario",
        ):
            st.session_state.pop("album_abecedario_ver_estado", None)
            st.session_state.pagina_activa = "album_abecedario"
            st.rerun()
        if st.button("Ver estado de mi abecedario", use_container_width=True, key="demo_album_btn_abecedario_estado"):
            st.session_state["album_abecedario_ver_estado"] = True
            st.session_state.pagina_activa = "album_abecedario"
            st.rerun()

    render_encabezado_logo_titulo_acciones(
        titulo,
        color_fav=color_fav,
        logo_height=192,
        slot_acciones=_acciones_demo_album,
        subtitulo="Ver por categoría",
        caption_bajo_titulo="Pulsa la imagen de cada categoría para abrir su álbum.",
    )
    st.caption("Activos: Familia, Juguetes, En la cocina e Instrumentos musicales.")
    st.caption("Solo las categorías liberadas se abren al pulsar la imagen de la tapa.")
    st.write("---")

    cats_ordenadas = sorted(CATEGORIAS_ALBUM, key=lambda c: (c or "").lower())
    num_cols_grid = 4
    for fila in range(0, len(cats_ordenadas), num_cols_grid):
        celdas = cats_ordenadas[fila : fila + num_cols_grid]
        cols = st.columns(num_cols_grid)
        for j, cat in enumerate(celdas):
            with cols[j]:
                ruta_tapa = _ruta_tapa_categoria(cat)
                activa = cat in DEMO_CATEGORIAS_ACTIVAS
                with st.container(border=True):
                    st.markdown(f"**{cat}**")
                    if ruta_tapa:
                        if activa:
                            href = f"?album_cat={quote(cat)}"
                            data_uri = _data_uri_imagen(ruta_tapa)
                            if data_uri:
                                st.markdown(
                                    f'<a href="{href}" target="_self" style="display:block;text-decoration:none;" '
                                    f'title="Abrir {html.escape(cat)}">'
                                    f'<img src="{data_uri}" alt="{html.escape(cat)}" '
                                    "style=\"width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;"
                                    'border:2px solid #2e7d32;"/></a>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.image(ruta_tapa, use_container_width=True)
                                st.markdown(
                                    f'<a href="{href}" target="_self"><b>Abrir álbum</b></a>',
                                    unsafe_allow_html=True,
                                )
                        else:
                            data_uri = _data_uri_imagen(ruta_tapa)
                            if data_uri:
                                st.markdown(
                                    f'<img src="{data_uri}" alt="{html.escape(cat)}" '
                                    "style=\"width:100%;border-radius:10px;aspect-ratio:4/3;object-fit:cover;"
                                    'opacity:0.55;filter:grayscale(25%);"/>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.image(ruta_tapa, use_container_width=True)
                            st.caption("🔒 Bloqueado en DEMO")
                    else:
                        st.markdown(
                            f"<div style='aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;"
                            f"background:#eef1f6;border-radius:10px;color:#334;padding:12px;text-align:center;'>"
                            f"<b>{html.escape(cat)}</b><br/><span style='font-size:0.8rem;'>Sin tapa disponible</span></div>",
                            unsafe_allow_html=True,
                        )
                        if activa:
                            href = f"?album_cat={quote(cat)}"
                            st.markdown(f'<a href="{href}" target="_self">Abrir</a>', unsafe_allow_html=True)
                        else:
                            st.caption("🔒 Bloqueado en DEMO")

    st.write("---")
    if st.button("⬅️ Volver al Inicio", use_container_width=True, key="demo_album_volver_hub"):
        st.session_state.pagina_activa = "hub_nino"
        st.rerun()


def render_album_nino_categoria_demo():
    cat = st.session_state.get("album_nino_categoria")
    if cat not in DEMO_CATEGORIAS_ACTIVAS:
        st.warning("Este album esta bloqueado en la DEMO.")
        st.session_state.pagina_activa = "album_nino"
        st.rerun()
        return
    render_album_nino_categoria()
