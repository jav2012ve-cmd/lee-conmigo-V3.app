import random
import os
import streamlit as st

from components.page_title import render_encabezado_logo_titulo_acciones

from database.db_queries import obtener_album_nino, guardar_en_album_reemplazando
from database.db_queries_v3 import categoria_stats_ambas_actividades
from core.asset_manager import AssetManager
from components.cards import render_album_card_karaoke, render_album_card_placeholder
from core.album_categories import (
    CATEGORIAS_CON_SFX_TARJETA,
    nombre_para_album_y_tts,
    fila_album_coincide_categoria,
)
from core.curriculum_v3 import CurriculumV3
from core import gamificacion

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_AVATARES_FAMILIA_DIR = os.path.join(_ROOT_DIR, "assets", "avatars_familia")


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


def _mensaje_ruta_v3():
    """
    Mensaje guía (didáctico) al iniciar la actividad.
    - Si hay un mensaje flash (p. ej. 'has liberado...'), lo muestra una vez.
    - Si no, explica el siguiente objetivo del ciclo.
    """
    flash = st.session_state.pop("v3_flash_msg", None)
    if flash:
        st.success(flash)
        return

    ciclo_id = st.session_state.get("v3_ciclo_id", "C1")
    bloque = CurriculumV3.obtener_bloque_por_ciclo_id(ciclo_id)
    habilitado = bool(st.session_state.get("v3_bloque_lecciones_habilitado"))
    if habilitado:
        st.info(f"✅ Ya liberaste las lecciones del **{ciclo_id}**. Sigue con: **{', '.join(bloque)}**.")
    else:
        st.info(
            f"Ruta: completa tu **Álbum** en las categorías habilitadas para liberar las lecciones: **{', '.join(bloque)}**."
        )


def render_album_nino_v3():
    est_id = st.session_state.get("estudiante_id")
    if est_id:
        st.session_state.v3_ciclo_id = gamificacion.ciclo_v3_activo(est_id)

    nombre = st.session_state.get("nombre_nino", "Pequeño explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")

    titulo = f"El Álbum de {(nombre or '').strip() or 'Pequeño explorador'} (V3)"

    def _acciones_v3_album():
        if st.button("Volver al inicio", use_container_width=True, key="v3_album_hdr_hub"):
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
        if st.button("Abecedario (9×3)", use_container_width=True, key="v3_album_hdr_abecedario"):
            st.session_state.pagina_activa = "abecedario_matriz"
            st.rerun()

    render_encabezado_logo_titulo_acciones(
        titulo,
        color_fav=color_fav,
        logo_height=192,
        slot_acciones=_acciones_v3_album,
    )

    _mensaje_ruta_v3()

    st.write("")
    st.markdown("**Categorías disponibles (según tu ciclo)**")

    ciclo_id = st.session_state.get("v3_ciclo_id", "C1")
    idx_ciclo = CurriculumV3.obtener_ciclo_idx_por_id(ciclo_id)
    categorias = CurriculumV3.categorias_habilitadas_para_ciclo_idx(idx_ciclo)

    # Estado de dominio por categoría (75% en ambas actividades) para restringir avance secuencial
    estado_cats = []
    min_ac = None
    for cat in categorias:
        ok, stats = categoria_stats_ambas_actividades(est_id, cat)
        estado_cats.append({"cat": cat, "ok": ok, "stats": stats})

    # Primera categoría NO superada (a partir de ahí todo queda bloqueado)
    primera_pendiente = None
    for e in estado_cats:
        if not e["ok"]:
            primera_pendiente = e["cat"]
            break

    # Botones de categorías (sin desplegable), solo navegables hasta la primera pendiente
    activa = st.session_state.get("v3_album_categoria_activa")
    if activa not in categorias:
        activa = categorias[0] if categorias else None
        st.session_state.v3_album_categoria_activa = activa

    num_cols = 3
    cols = st.columns(num_cols)
    for i, e in enumerate(estado_cats):
        cat = e["cat"]
        label = f"✅ {cat}" if e["ok"] else cat
        disabled = False
        if primera_pendiente is not None:
            # Solo se puede ir a categorías antes o igual a la primera pendiente; las siguientes quedan bloqueadas
            idx_cat = categorias.index(cat)
            idx_prim = categorias.index(primera_pendiente)
            if idx_cat > idx_prim:
                disabled = True
        with cols[i % num_cols]:
            if st.button(label, use_container_width=True, key=f"v3_cat_btn_{cat}", disabled=disabled):
                st.session_state.v3_album_categoria_activa = cat
                st.rerun()

    st.write("---")
    categoria_sel = st.session_state.get("v3_album_categoria_activa")
    if not categoria_sel:
        st.info("Elige una categoría para ver tus imágenes.")
    else:
        st.markdown(f"### {categoria_sel}")

        fotos = obtener_album_nino(st.session_state.estudiante_id) or []
        fotos_cat = [f for f in fotos if fila_album_coincide_categoria(f[1], categoria_sel, f[0])]
        genericos_cat = AssetManager.obtener_genericos_por_categoria(categoria_sel)

        cache_key_fam = f"v3_album_items_{categoria_sel}"
        if categoria_sel == "Familia":
            n_fp = len(fotos_cat)
            av_top = _listar_avatares_familia()
            with st.container(border=True):
                st.markdown("#### 👥 Avatares de familia")
                st.caption(
                    "Si prefieres **no subir fotos reales**, elige un dibujo para cada familiar "
                    "(MAMÁ, PAPÁ, abuelos…). Son imágenes incluidas en la aplicación."
                )
                if not av_top:
                    st.warning(
                        "Aún no hay dibujos en **assets/avatars_familia**. "
                        "Quien instala la app puede añadir allí archivos .png o .jpg."
                    )
                else:
                    st.success(
                        f"Tienes **{len(av_top)}** personajes disponibles. "
                        f"Fotos propias en Familia: **{n_fp}**."
                    )
                    pc = st.columns(min(6, len(av_top)))
                    for i, av in enumerate(av_top[:6]):
                        with pc[i]:
                            st.image(av["path"], caption=av["label"][:18], use_container_width=True)
                    c1, c2, c3 = st.columns([1, 1, 1.2])
                    with c1:
                        pw = st.text_input(
                            "Palabra en el álbum (ej: MAMÁ)",
                            key="v3_album_avatar_palabra_familia",
                            placeholder="MAMÁ",
                        )
                        pw = (pw or "").strip().upper()
                    with c2:
                        ix = st.selectbox(
                            "Elige el dibujo",
                            range(len(av_top)),
                            format_func=lambda i: av_top[i]["label"],
                            key="v3_album_avatar_familia_sel",
                        )
                    with c3:
                        st.write("")
                        st.write("")
                        if st.button("Guardar en mi álbum", type="primary", key="v3_album_avatar_guardar_btn", use_container_width=True):
                            if not pw:
                                st.warning("Escribe un nombre (palabra clave).")
                            else:
                                ok = guardar_en_album_reemplazando(
                                    st.session_state.estudiante_id,
                                    pw,
                                    "Familia",
                                    av_top[ix]["path"],
                                )
                                if ok:
                                    st.session_state.pop(cache_key_fam, None)
                                    st.success(f"Listo: **{pw}** usa el avatar elegido.")
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
                            unique_id=f"v3_album_placeholder_{categoria_sel}_{idx}",
                            size=size_card,
                        )
                    else:
                        nombre_visible = nombre_para_album_y_tts(item.get("palabra")) or "Imagen"
                        render_album_card_karaoke(
                            item["ruta_img"],
                            nombre_visible,
                            unique_id=f"v3_album_{categoria_sel}_{idx}",
                            size=size_card,
                            show_label_below=show_label_below,
                            categoria=categoria_sel,
                            sonidos_tarjeta_habilitados=(categoria_sel in CATEGORIAS_CON_SFX_TARJETA),
                        )

            # Actividad (se mantiene igual: manda a album_silabas)
            if not es_familia or len([i for i in items if not i.get("placeholder")]) >= 2:
                st.write("---")
                if st.button("📝 Jugar: Armar la palabra con sílabas", key="v3_album_btn_silabas", use_container_width=True):
                    st.session_state.album_actividad_categoria = categoria_sel
                    st.session_state.pagina_activa = "album_silabas"
                    st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al Inicio", use_container_width=True, key="v3_album_volver"):
        st.session_state.pagina_activa = "hub_nino"
        st.rerun()

