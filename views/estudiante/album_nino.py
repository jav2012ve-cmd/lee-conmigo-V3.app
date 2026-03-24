import random
import streamlit as st
from database.db_queries import obtener_album_nino
from core.album_categories import CATEGORIAS_ALBUM, nombre_para_album_y_tts
from core.asset_manager import AssetManager
from components.cards import render_album_card_karaoke, render_album_card_placeholder


def render_album_nino():
    nombre = st.session_state.get("nombre_nino", "Pequeño explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")

    st.markdown(
        f"<h1 style='text-align: center; color: {color_fav};'>🖼️ El Álbum de {nombre}</h1>",
        unsafe_allow_html=True,
    )

    # Sección: Mi abecedario (elegir 2 imágenes por letra)
    col_abecedario_1, col_abecedario_2 = st.columns(2)
    with col_abecedario_1:
        if st.button("📖 Mi abecedario — elegir mis imágenes por letra", use_container_width=True, key="album_btn_abecedario"):
            st.session_state.pop("album_abecedario_ver_estado", None)
            st.session_state.pagina_activa = "album_abecedario"
            st.rerun()
    with col_abecedario_2:
        if st.button("📊 Ver estado de mi abecedario", use_container_width=True, key="album_btn_abecedario_estado"):
            st.session_state["album_abecedario_ver_estado"] = True
            st.session_state.pagina_activa = "album_abecedario"
            st.rerun()

    st.write("---")
    st.markdown("**Ver por categoría**")
    # Menú desplegable para elegir categoría
    opciones = ["— Elige una categoría —"] + CATEGORIAS_ALBUM
    idx_sel = st.selectbox(
        "¿Qué quieres revisar?",
        range(len(opciones)),
        format_func=lambda i: opciones[i],
        key="album_categoria_sel",
    )
    categoria_sel = opciones[idx_sel] if idx_sel > 0 else None

    if not categoria_sel:
        st.info("Selecciona una categoría del menú para ver las imágenes.")
    else:
        # Fotos del álbum personal (DB) para esta categoría
        fotos = obtener_album_nino(st.session_state.estudiante_id) or []
        fotos_cat = [f for f in fotos if (f[1] or "").strip() == categoria_sel]
        # Imágenes genéricas de assets/genericos para esta categoría
        genericos_cat = AssetManager.obtener_genericos_por_categoria(categoria_sel)

        # Unir: primero las del álbum del niño, luego las genéricas (sin duplicar palabra)
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
        # Selección aleatoria por categoría; se guarda en sesión para no cambiar al interactuar (karaoke).
        cache_key = f"album_items_{categoria_sel}"
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
                        )

            # Botón para ir a la actividad "Armar la palabra" (solo si hay imágenes reales)
            if not es_familia or len([i for i in items if not i.get("placeholder")]) >= 2:
                st.write("---")
                if st.button("📝 Jugar: Armar la palabra con sílabas", key="album_btn_silabas", use_container_width=True):
                    st.session_state.album_actividad_categoria = categoria_sel
                    st.session_state.pagina_activa = "album_silabas"
                    st.rerun()

    st.write("---")
    if st.button("⬅️ Volver al Inicio", use_container_width=True):
        st.session_state.pagina_activa = "hub_nino"
        st.rerun()
