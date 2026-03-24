"""
Actividad al final del álbum por categoría: completar la palabra con las vocales que faltan.
Se muestran las consonantes en su lugar y huecos para las vocales; el niño elige las vocales (+ 1 innecesaria).
"""
import random
import streamlit as st
import base64
from database.db_queries import obtener_album_nino, actualizar_progreso_silabico
from core.album_categories import CATEGORIAS_ALBUM, nombre_para_album_y_tts, palabra_para_display
from core.asset_manager import AssetManager
from core.speech_engine import SpeechEngine
from core import gamificacion
from components.karaoke_ui import _autoplay_audio_bytes, render_palabra_karaoke_felicitacion

speech_engine = SpeechEngine()

VOCALES = ["A", "E", "I", "O", "U"]


def _get_image_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def _vocales_y_visible(palabra_str):
    """Devuelve (palabra_visible con _ por vocal, lista de vocales en orden)."""
    p = (palabra_str or "").strip().upper().translate(AssetManager._NORM_VOCAL)
    visible = []
    vocales_list = []
    for c in p:
        # Preservar el espacio entre palabras para que no se pierda al hacer split()
        # (antes: el espacio se colapsaba y el usuario veía "CASA MUÑECAS" como si fuera una sola palabra)
        if c == " ":
            visible.append("␣")
        elif c in "AEIOU":
            visible.append("_")
            vocales_list.append(c)
        else:
            visible.append(c)
    return " ".join(visible), vocales_list


def _palabras_con_al_menos_dos_vocales(categoria):
    """Lista de {palabra, ruta_img} de la categoría con al menos 2 vocales."""
    items = []
    vistos = set()
    fotos = obtener_album_nino(st.session_state.get("estudiante_id")) or []
    for palabra, _c, path in fotos:
        if (_c or "").strip() != categoria or not path:
            continue
        key = (palabra or "").strip().upper()
        if not key or key in vistos:
            continue
        _, vocales = _vocales_y_visible(palabra or "")
        if len(vocales) >= 2:
            items.append({"palabra": palabra_para_display((palabra or "").strip()), "ruta_img": path})
            vistos.add(key)
    for g in AssetManager.obtener_genericos_por_categoria(categoria):
        key = (g.get("palabra") or "").strip().upper()
        if not key or key in vistos:
            continue
        _, vocales = _vocales_y_visible(g.get("palabra") or "")
        if len(vocales) >= 2:
            items.append({"palabra": palabra_para_display((g["palabra"] or "").strip()), "ruta_img": g["ruta_img"]})
            vistos.add(key)
    return items


def render_album_silabas_nino():
    estudiante_id = st.session_state.get("estudiante_id")
    categoria = st.session_state.get("album_actividad_categoria") or ""
    nombre = st.session_state.get("nombre_nino", "Explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")

    if not categoria or categoria not in CATEGORIAS_ALBUM:
        st.warning("Elige una categoría desde el Álbum y luego el botón de la actividad.")
        if st.button("⬅️ Volver al Álbum"):
            st.session_state.pagina_activa = "album_nino"
            if "album_actividad_categoria" in st.session_state:
                del st.session_state["album_actividad_categoria"]
            st.rerun()
        return

    # Tope: 6 palabras a completar en esta actividad
    TOPE_PALABRAS = 6

    # Inicializar o obtener lista de palabras para esta sesión
    sk = "album_silabas_palabras"
    if sk not in st.session_state or st.session_state.get("album_silabas_cat") != categoria:
        palabras = _palabras_con_al_menos_dos_vocales(categoria)
        random.shuffle(palabras)
        st.session_state[sk] = palabras[:TOPE_PALABRAS]
        st.session_state["album_silabas_cat"] = categoria
        st.session_state["album_silabas_idx"] = 0
        st.session_state["album_silabas_completadas"] = 0
        st.session_state["album_silabas_errores_sesion"] = 0
        # Reiniciar premios de esta "sesión de intento"
        st.session_state.pop("album_silabas_premio_armar_dado", None)
        st.session_state.pop("album_silabas_fin", None)
        st.session_state.pop("album_silabas_ultimo_fallo", None)

    palabras_lista = st.session_state[sk]
    if not palabras_lista:
        st.info(f"No hay palabras con 2 o más vocales en **{categoria}**. ¡Revisa el álbum primero!")
        if st.button("⬅️ Volver al Álbum"):
            st.session_state.pagina_activa = "album_nino"
            st.rerun()
        return

    # Actividad "Escucha y Toca": escuchar palabra y elegir la imagen correcta (tras las 6 palabras)
    if st.session_state.get("album_escucha_toca_activo"):
        et_idx = st.session_state.get("album_escucha_toca_idx", 0)
        total_et = len(palabras_lista)

        # Globos y mensaje al llegar aquí tras un acierto (así se ven; antes del rerun no se llegaban a ver)
        if st.session_state.pop("album_et_mostrar_globos", False):
            st.balloons()
            st.success("¡Muy bien!")

        if et_idx >= total_et:
            if not st.session_state.get("album_et_premio_dado"):
                st.session_state["album_et_premio_dado"] = True
                errores_et = st.session_state.get("album_et_errores_sesion", 0)
                if estudiante_id:
                    gamificacion.on_activity_complete(estudiante_id, categoria, "EscuchaToca", errores_et)
            perfecto_et = st.session_state.get("album_et_errores_sesion", 0) == 0
            st.balloons()
            st.markdown(
                """
                <div style="text-align: center; padding: 24px; border-radius: 16px; background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); color: white; margin: 16px 0;">
                    <p style="font-size: 1.8rem; font-weight: bold; margin-bottom: 8px;">¡Escucha y Toca completado! 🎉</p>
                    <p style="font-size: 1.1rem; opacity: 0.95;">¡Lo lograste!</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if perfecto_et:
                st.success("⭐ ¡Perfecto! Sin errores. +5 estrellas.")
            if st.button("⬅️ Volver a la ruta", type="primary", use_container_width=True, key="volver_album_et_fin"):
                st.session_state.pop("album_escucha_toca_activo", None)
                st.session_state.pop("album_escucha_toca_idx", None)
                st.session_state.pop("album_et_play_idx", None)
                st.session_state.pop("album_et_premio_dado", None)
                for k in range(6):
                    st.session_state.pop(f"album_et_orden_{k}", None)
                st.session_state.pagina_activa = "hub_nino"
                st.rerun()
            return

        item_correcto = palabras_lista[et_idx]
        palabra_correcta = nombre_para_album_y_tts(item_correcto.get("palabra") or "") or (item_correcto.get("palabra") or "").strip()
        palabra_correcta_norm = (palabra_correcta or "").strip().upper().translate(AssetManager._NORM_VOCAL)

        # Orden fijo de las 3 opciones para esta pregunta (evita que el avance se pierda al rerun)
        orden_key = f"album_et_orden_{et_idx}"
        if orden_key not in st.session_state:
            otros_idx = [i for i in range(total_et) if i != et_idx]
            palabras_vistas = {palabra_correcta_norm}
            distractor_idx = []
            for i in otros_idx:
                pal_i = (nombre_para_album_y_tts(palabras_lista[i].get("palabra") or "") or (palabras_lista[i].get("palabra") or "").strip()).strip().upper().translate(AssetManager._NORM_VOCAL)
                if pal_i not in palabras_vistas:
                    palabras_vistas.add(pal_i)
                    distractor_idx.append(i)
                    if len(distractor_idx) >= 2:
                        break
            if len(distractor_idx) < 2:
                distractor_idx = (distractor_idx + [j for j in otros_idx if j not in distractor_idx])[:2]
            orden = [et_idx] + distractor_idx
            random.shuffle(orden)
            st.session_state[orden_key] = orden
        orden = st.session_state[orden_key]
        opciones = [palabras_lista[i] for i in orden]

        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 8px;">
                <span style="font-size: 1.6rem; font-weight: 800; color: {color_fav};">👂 Escucha y Toca</span>
            </div>
            <p style="text-align: center; color: #555; margin-bottom: 4px;">Escucha la palabra y toca la imagen que corresponde.</p>
            <p style="text-align: center; font-weight: 600; color: #333;">Pregunta {et_idx + 1} de {total_et}</p>
            """,
            unsafe_allow_html=True,
        )
        st.progress((et_idx + 1) / total_et)

        if st.session_state.get("album_et_play_idx") == et_idx:
            audio_rep = speech_engine.generar_audio(palabra_correcta)
            if audio_rep:
                try:
                    with open(audio_rep, "rb") as f:
                        _autoplay_audio_bytes(f.read(), mime="audio/mpeg")
                except Exception:
                    pass
            st.session_state.pop("album_et_play_idx", None)

        # Matriz 1x4: [botón escuchar] + [3 opciones]
        # Así el usuario entiende visualmente que primero escucha y luego toca.
        cols4 = st.columns([1, 1, 1, 1])
        with cols4[0]:
            if st.button("🔊 Escuchar", type="primary", use_container_width=True, key=f"et_play_{et_idx}"):
                st.session_state["album_et_play_idx"] = et_idx
                st.rerun()

        for i, opc in enumerate(opciones):
            with cols4[i + 1]:
                pal = nombre_para_album_y_tts(opc.get("palabra") or "") or (opc.get("palabra") or "").strip()
                ruta = opc.get("ruta_img")
                img_b64 = _get_image_base64(ruta) if ruta else None
                if img_b64:
                    ext = ".jpg" if (ruta or "").lower().endswith((".jpg", ".jpeg")) else ".png"
                    mime = "image/jpeg" if "jpg" in ext else "image/png"
                    st.markdown(
                        f'<div style="border: 2px dashed #ccc; border-radius: 12px; padding: 8px; background: #fafafa; margin-bottom: 8px;"><img src="data:{mime};base64,{img_b64}" style="width: 100%; height: 140px; object-fit: contain; border-radius: 8px;" /></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div style="border: 2px dashed #ccc; border-radius: 12px; height: 140px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; margin-bottom: 8px;"><span style="font-size: 2rem;">?</span></div>',
                        unsafe_allow_html=True,
                    )

                if st.button(pal.upper(), key=f"et_opcion_{et_idx}_{i}", use_container_width=True):
                    pal_norm = (pal or "").strip().upper().translate(AssetManager._NORM_VOCAL)
                    if pal_norm == palabra_correcta_norm:
                        # Registrar progreso para la actividad "Escucha y Toca"
                        if estudiante_id:
                            actualizar_progreso_silabico(estudiante_id, categoria, "EscuchaToca", True)
                            gamificacion.on_correct_answer(estudiante_id, categoria, "EscuchaToca")
                        st.session_state["album_escucha_toca_idx"] = et_idx + 1
                        st.session_state["album_et_mostrar_globos"] = True
                        st.rerun()
                    else:
                        if estudiante_id:
                            actualizar_progreso_silabico(estudiante_id, categoria, "EscuchaToca", False)
                        st.session_state["album_et_errores_sesion"] = st.session_state.get("album_et_errores_sesion", 0) + 1
                        st.error("¡Casi! Escucha de nuevo y elige la imagen correcta.")

        st.write("---")
        if st.button("⬅️ Volver a la ruta (salir de Escucha y Toca)", key="volver_album_et"):
            st.session_state.pop("album_escucha_toca_activo", None)
            st.session_state.pop("album_escucha_toca_idx", None)
            st.session_state.pop("album_et_play_idx", None)
            st.session_state.pop("album_et_premio_dado", None)
            for k in range(6):
                st.session_state.pop(f"album_et_orden_{k}", None)
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
        return

    # Si ya completó las 6 palabras, pantalla de fin
    if st.session_state.get("album_silabas_fin"):
        if estudiante_id and not st.session_state.get("album_silabas_premio_armar_dado"):
            st.session_state["album_silabas_premio_armar_dado"] = True
            gamificacion.on_activity_complete(estudiante_id, categoria, "ArmarPalabra", st.session_state.get("album_silabas_errores_sesion", 0))
        perfecto_armar = st.session_state.get("album_silabas_errores_sesion", 0) == 0
        st.balloons()
        st.markdown(
            """
            <div style="text-align: center; padding: 24px; border-radius: 16px; background: linear-gradient(135deg, #4CAF50 0%, #2e7d32 100%); color: white; margin: 16px 0;">
                <p style="font-size: 1.8rem; font-weight: bold; margin-bottom: 8px;">¡Completaste las 6 palabras! 🎉</p>
                <p style="font-size: 1.1rem; opacity: 0.95;">¡Muy bien!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if perfecto_armar:
            st.success("⭐ ¡Perfecto! Sin errores. +5 estrellas.")
        st.markdown("**¿Qué quieres hacer ahora?**")
        col_fin1, col_fin2 = st.columns(2)
        with col_fin1:
            if st.button("👂 Escucha y Toca", type="primary", use_container_width=True, key="btn_escucha_toca"):
                st.session_state["album_escucha_toca_activo"] = True
                st.session_state["album_escucha_toca_idx"] = 0
                st.session_state["album_et_errores_sesion"] = 0
                st.session_state.pop("album_et_premio_dado", None)
                st.rerun()
        with col_fin2:
            if st.button("⬅️ Volver a la ruta", use_container_width=True, key="volver_album_fin"):
                st.session_state.pop("album_silabas_fin", None)
                st.session_state.pop("album_silabas_completadas", None)
                st.session_state.pop("album_silabas_premio_armar_dado", None)
                st.session_state.pop("album_et_premio_dado", None)
                st.session_state.pagina_activa = "hub_nino"
                st.rerun()
        return

    # Si acabamos de acertar, mostrar pantalla de celebración (karaoke + audio) y no avanzar hasta que pulse Continuar
    if st.session_state.get("album_silabas_mostrar_ok"):
        palabra_ok = st.session_state.get("album_silabas_palabra_ok", "")
        st.balloons()
        frase_audio = f"¡Muy bien! {palabra_ok}"
        st.markdown(
            """
            <style>
            @keyframes karaoke-box {
                0% { opacity: 0; transform: scale(0.95); }
                100% { opacity: 1; transform: scale(1); }
            }
            .box-karaoke-album {
                display: inline-block;
                padding: 16px 32px;
                border-radius: 12px;
                background: linear-gradient(135deg, #4CAF50 0%, #2e7d32 100%);
                color: white;
                font-size: 1.6rem;
                font-weight: bold;
                box-shadow: 0 4px 14px rgba(46, 125, 50, 0.5);
                animation: karaoke-box 0.5s ease-out forwards;
            }
            </style>
            <p style="text-align: center; margin: 24px 0;"><span class="box-karaoke-album">¡Muy bien! ¡Lo lograste! 🎉</span></p>
            """,
            unsafe_allow_html=True,
        )
        render_palabra_karaoke_felicitacion(palabra_ok, unique_id="album_silabas_feliz")
        # Una sola reproducción: gTTS (voz femenina)
        audio_rep = speech_engine.generar_audio(frase_audio)
        if audio_rep:
            try:
                with open(audio_rep, "rb") as f:
                    _autoplay_audio_bytes(f.read(), mime="audio/mpeg")
            except Exception:
                pass
        completadas_actual = st.session_state.get("album_silabas_completadas", 0)
        completadas_proximas = completadas_actual + 1
        label_continuar = "👉 Continuar a Escucha y Toca" if completadas_proximas >= 6 else "➡️ Continuar"
        if st.button(label_continuar, type="primary", use_container_width=True, key="btn_continuar_album_ok"):
            st.session_state.pop("album_silabas_mostrar_ok", None)
            st.session_state.pop("album_silabas_palabra_ok", None)
            st.session_state.pop("album_silabas_ultimo_fallo", None)
            completadas = st.session_state.get("album_silabas_completadas", 0) + 1
            st.session_state["album_silabas_completadas"] = completadas
            st.session_state["album_silabas_idx"] = (st.session_state.get("album_silabas_idx", 0) + 1) % len(palabras_lista)
            if completadas >= 6 and estudiante_id and not st.session_state.get("album_silabas_premio_armar_dado"):
                st.session_state["album_silabas_premio_armar_dado"] = True
                errores_armar = st.session_state.get("album_silabas_errores_sesion", 0)
                gamificacion.on_activity_complete(estudiante_id, categoria, "ArmarPalabra", errores_armar)
            if completadas >= 6:
                st.session_state["album_escucha_toca_activo"] = True
                st.session_state["album_escucha_toca_idx"] = 0
                st.session_state["album_et_errores_sesion"] = 0
                st.session_state.pop("album_et_premio_dado", None)
                st.session_state.pop("album_silabas_fin", None)
                st.session_state.pop("album_et_mostrar_globos", None)
            st.rerun()
        st.write("---")
        if st.button("⬅️ Volver a la ruta", key="volver_album"):
            st.session_state.pop("album_silabas_mostrar_ok", None)
            st.session_state.pop("album_silabas_palabra_ok", None)
            st.session_state.pop("album_silabas_ultimo_fallo", None)
            st.session_state.pop("album_silabas_premio_armar_dado", None)
            st.session_state.pop("album_et_premio_dado", None)
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
        return

    idx = st.session_state.get("album_silabas_idx", 0) % len(palabras_lista)
    item = palabras_lista[idx]
    palabra = nombre_para_album_y_tts(item.get("palabra") or "") or (item.get("palabra") or "").strip()
    ruta_img = item.get("ruta_img")
    palabra_visible_base, vocales_orden = _vocales_y_visible(palabra)
    if len(vocales_orden) < 2:
        st.session_state["album_silabas_idx"] = (idx + 1) % len(palabras_lista)
        st.rerun()
        return

    # Pool de vocales: vocales de la palabra + 1 innecesaria
    pool_key = f"album_silabas_pool_{idx}"
    if pool_key not in st.session_state:
        distractor = next((v for v in VOCALES if v not in vocales_orden), "I")
        pool = list(vocales_orden) + [distractor]
        random.shuffle(pool)
        st.session_state[pool_key] = pool
    pool = st.session_state[pool_key]

    # Estado de slots (una por vocal) y posiciones del pool ya usadas
    slot_key = f"album_silabas_slots_{idx}"
    used_key = f"album_silabas_used_{idx}"
    if slot_key not in st.session_state:
        st.session_state[slot_key] = [""] * len(vocales_orden)
        st.session_state[used_key] = set()
    slots = st.session_state[slot_key]
    used_indices = st.session_state[used_key]

    st.markdown(
        f"<h2 style='text-align: center; color: {color_fav};'>📝 Armar la palabra · {categoria}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="text-align: center; margin: 0.5rem 0 1rem 0;">
            <span style="
                font-size: 2.2rem;
                font-weight: 800;
                letter-spacing: 0.1em;
                color: #1a1a2e;
                text-shadow: 0 2px 6px rgba(0,0,0,0.2);
                padding: 0.7rem 1.8rem;
                background: linear-gradient(135deg, #fff9e6 0%, #ffe8cc 100%);
                border-radius: 999px;
                display: inline-block;
                border: 3px solid #e8b84a;
                box-shadow: 0 4px 14px rgba(232,184,74,0.35);
            ">
                ¿Quién soy?
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Layout: imagen a la izquierda, resto a la derecha
    col_img, col_act = st.columns([1, 1.2])

    with col_img:
        # Imagen al 125% y recorte inferior para ocultar el cintillo del nombre en el recurso
        img_b64 = _get_image_base64(ruta_img) if ruta_img else None
        if img_b64:
            ext = ".jpg" if (ruta_img or "").lower().endswith((".jpg", ".jpeg")) else ".png"
            mime = "image/jpeg" if "jpg" in ext else "image/png"
            # Contenedor fijo; imagen escalada 125% y recortada por abajo (object-position: top)
            st.markdown(
                f'<div style="border: 3px solid #E0E0E0; border-radius: 12px; padding: 8px; background: #fff; height: 350px; overflow: hidden; box-sizing: border-box;"><img src="data:{mime};base64,{img_b64}" style="width: 100%; height: 437px; object-fit: cover; object-position: center top; border-radius: 8px; display: block;" /></div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Imagen no encontrada")

    with col_act:
        st.markdown("**Elige las letras que faltan. (Hay una que no va.)**")
        # Palabra con consonantes y huecos; rellenar con las vocales elegidas
        partes = palabra_visible_base.split()
        idx_slot = 0
        display_chars = []
        for part in partes:
            if part == "_":
                display_chars.append((slots[idx_slot] or "_") if idx_slot < len(slots) else "_")
                idx_slot += 1
            elif part == "␣":
                # Mostrar un “cuadro” para destacar el espacio entre palabras (no se llena)
                display_chars.append("▢")
            else:
                display_chars.append(part)
        palabra_mostrar = " ".join(display_chars)
        st.markdown(
            f'<div style="font-size: 2.2rem; font-weight: 800; letter-spacing: 0.15em; margin: 12px 0;">{palabra_mostrar.upper()}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**Elige las letras:**")
        clicked_pool_index = None
        num_pool = len(pool)
        pool_cols = st.columns(num_pool)
        for i in range(num_pool):
            v = pool[i]
            with pool_cols[i]:
                if i in used_indices:
                    st.markdown(
                        '<div style="min-height: 38px; border-radius: 8px; background: transparent;"></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(v, key=f"vocal_{idx}_{i}_{v}", use_container_width=True):
                        clicked_pool_index = i

        if clicked_pool_index is not None:
            first_empty = next((k for k in range(len(slots)) if not (slots[k] or "").strip()), None)
            if first_empty is not None:
                new_slots = list(slots)
                new_slots[first_empty] = pool[clicked_pool_index]
                st.session_state[slot_key] = new_slots
                st.session_state[used_key] = used_indices | {clicked_pool_index}
            st.rerun()

        # Botones Listo, Borrar, Saltar
        c1, c2, c3 = st.columns(3)
        with c1:
            listo = st.button("✓ Listo", key="btn_listo", use_container_width=True)
        with c2:
            borrar = st.button("↺ Borrar", key="btn_borrar", use_container_width=True)
        with c3:
            saltar = st.button("→ Saltar", key="btn_saltar", use_container_width=True)

    if borrar:
        st.session_state[slot_key] = [""] * len(vocales_orden)
        st.session_state[used_key] = set()
        st.session_state.pop("album_silabas_ultimo_fallo", None)
        st.rerun()

    if saltar:
        st.session_state.pop("album_silabas_ultimo_fallo", None)
        if slot_key in st.session_state:
            del st.session_state[slot_key]
        if used_key in st.session_state:
            del st.session_state[used_key]
        if pool_key in st.session_state:
            del st.session_state[pool_key]
        st.session_state["album_silabas_idx"] = (idx + 1) % len(palabras_lista)
        st.rerun()

    if listo:
        partes = palabra_visible_base.split()
        idx_s = 0
        letras_armadas = []
        for part in partes:
            if part == "_":
                letras_armadas.append((slots[idx_s] or "").strip().upper() if idx_s < len(slots) else "")
                idx_s += 1
            elif part == "␣":
                letras_armadas.append(" ")
            else:
                letras_armadas.append(part)
        palabra_armada = "".join(letras_armadas).translate(AssetManager._NORM_VOCAL)
        objetivo = (palabra or "").strip().upper().translate(AssetManager._NORM_VOCAL).replace(" ", "")
        es_acierto = palabra_armada.replace(" ", "") == objetivo
        if estudiante_id:
            actualizar_progreso_silabico(estudiante_id, categoria, "ArmarPalabra", es_acierto)
            if es_acierto:
                gamificacion.on_correct_answer(estudiante_id, categoria, "ArmarPalabra")
            else:
                st.session_state["album_silabas_errores_sesion"] = st.session_state.get("album_silabas_errores_sesion", 0) + 1
        if es_acierto:
            st.session_state.pop("album_silabas_ultimo_fallo", None)
            st.session_state["album_silabas_mostrar_ok"] = True
            # Asegurar acentuación correcta (mamá, ají, etc.) en el texto que se reproduce
            st.session_state["album_silabas_palabra_ok"] = palabra_para_display(palabra)
        else:
            st.error(f"Era: **{palabra}**. Intenta de nuevo.")
            st.session_state["album_silabas_ultimo_fallo"] = True
        if slot_key in st.session_state:
            del st.session_state[slot_key]
        if used_key in st.session_state:
            del st.session_state[used_key]
        if pool_key in st.session_state:
            del st.session_state[pool_key]
        # Si falla, no avanzar: se queda en la misma palabra hasta acertar
        st.rerun()

    st.write("---")
    # Si falló, no puede ir a otra página: debe reintentar (Borrar y volver a intentar)
    if not st.session_state.get("album_silabas_ultimo_fallo"):
        if st.button("⬅️ Volver a la ruta", key="volver_album"):
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
