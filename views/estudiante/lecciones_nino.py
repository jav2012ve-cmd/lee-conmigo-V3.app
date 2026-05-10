import html
import os
import random
import base64
import json
import streamlit as st
from core.curriculum import Curriculum
from core import gamificacion
from core.asset_manager import AssetManager
from core.album_categories import palabra_para_display
from core.speech_engine import SpeechEngine
from components.cards import render_polaroid_click_to_play, render_album_card_karaoke
from components.page_title import logo_markup_html, render_encabezado_logo_titulo_acciones
from components.karaoke_ui import segmentar_palabra, render_selector_silaba, _autoplay_audio_bytes, render_palabra_karaoke_felicitacion, render_frase_karaoke, render_silabas_karaoke, render_silabas_matriz_9x9
from database.db_queries import (
    actualizar_progreso_silabico,
    vocal_fase_avance,
    obtener_perfil_completo_nino,
    obtener_avatar_estudiante,
    obtener_album_nino,
    pdf_job_crear,
    pdf_job_obtener,
    obtener_fase_leccion_consonante,
    guardar_fase_leccion_consonante,
)

try:
    from core.leccion_pdf import generar_pdf_leccion
    from core.pdf_jobs import ejecutar_job_en_background
    PDF_LECCION_DISPONIBLE = True
except Exception:
    PDF_LECCION_DISPONIBLE = False
    ejecutar_job_en_background = None

speech_engine = SpeechEngine()

# Caché para reducir tiempo de respuesta en cada clic (TTL 2 min para datos de DB/recursos)
@st.cache_data(ttl=120)
def _cached_perfil(estudiante_id):
    return obtener_perfil_completo_nino(estudiante_id)


@st.cache_data(ttl=120)
def _cached_album(estudiante_id):
    return obtener_album_nino(estudiante_id) or []


@st.cache_data(ttl=120)
def _cached_recursos(estudiante_id, fonema, total):
    return AssetManager.obtener_recursos_lectura(estudiante_id, fonema, total=total)


@st.cache_data(ttl=120)
def _cached_recursos_terminan(estudiante_id, vocal, total):
    return AssetManager.obtener_recursos_que_terminan_en(estudiante_id, vocal, total=total)


@st.cache_data(ttl=3600)
def _cached_fondo_b64(path):
    if not path or not os.path.isfile(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _key_est(estudiante_id, nombre):
    """Prefijo de session_state por estudiante para que el avance sea independiente."""
    return f"est_{estudiante_id}_{nombre}" if estudiante_id else nombre


# Flujo guiado consonantes (principal → armar → escucha); también en BD (guardar_fase_leccion_consonante)
FASES_CONSONANTE_VALIDAS = (
    "principal",
    "actividad_armar_1",
    "actividad_armar_2",
    "escucha_palabras",
    "escucha_frases",
)


def _set_paso_consonante(estudiante_id, letra, fase):
    """Persiste el paso del recorrido por letra (session + SQLite)."""
    fase_ok = fase if fase in FASES_CONSONANTE_VALIDAS else "principal"
    k = _key_est(estudiante_id, f"leccion_consonant_paso_{letra}")
    st.session_state[k] = fase_ok
    guardar_fase_leccion_consonante(estudiante_id, letra, fase_ok)


def _construir_palabras_armar(recursos_lectura, silabas_letra, cantidad=6):
    """
    Construye una lista de hasta `cantidad` palabras de 2 sílabas para la actividad
    "armar palabra". Cada ítem tiene: palabra, ruta_img, silabas [s1, s2], distractor.
    """
    if not silabas_letra:
        return []
    silabas_upper = [s.upper() for s in silabas_letra]
    resultado = []
    vistos = set()
    for r in recursos_lectura or []:
        palabra = (r.get("palabra") or "").strip()
        if not palabra or palabra.upper() in vistos:
            continue
        silabas = segmentar_palabra(palabra)
        if len(silabas) != 2:
            continue
        vistos.add(palabra.upper())
        # Distractor: una sílaba de la letra (Ma, Me, Mi...) que no esté en la palabra
        silabas_palabra_upper = (silabas[0].upper(), silabas[1].upper())
        candidatos = [s for s in silabas_upper if s not in silabas_palabra_upper]
        if not candidatos:
            continue
        distractor = random.choice(candidatos)
        # Para mostrar con formato bonito (primera mayúscula)
        resultado.append({
            "palabra": palabra,
            "ruta_img": r.get("ruta_img") or "",
            "silabas": silabas,
            "distractor": distractor,
        })
        if len(resultado) >= cantidad:
            break
    return resultado


def _render_actividad_armar_palabras(palabras_list, letra_actual, estudiante_id, color_fav, paso_actual, on_siguiente):
    """
    Renderiza la actividad "Armar palabra": imagen a la izquierda, slots + 3 sílabas + Listo/Borrar/Saltar.
    on_siguiente() se llama al hacer "Listo" correcto en la última palabra o "Siguiente actividad".
    """
    if not palabras_list:
        st.info("No hay suficientes palabras de 2 sílabas para esta letra. Puedes saltar la actividad.")
        if st.button("Continuar ➡️", key=f"armar_skip_{paso_actual}_{letra_actual}"):
            on_siguiente()
            st.rerun()
        return

    k_idx = _key_est(estudiante_id, f"armar_idx_{paso_actual}_{letra_actual}")
    idx = st.session_state.get(k_idx, 0)
    idx = max(0, min(idx, len(palabras_list) - 1))
    item = palabras_list[idx]
    palabra = item["palabra"]
    silabas_correctas = item["silabas"]
    distractor = item["distractor"]
    k_opciones = _key_est(estudiante_id, f"armar_opciones_{paso_actual}_{letra_actual}_{idx}")
    if k_opciones not in st.session_state:
        opciones = [silabas_correctas[0], silabas_correctas[1], distractor]
        random.shuffle(opciones)
        st.session_state[k_opciones] = opciones
    opciones = st.session_state[k_opciones]

    k_slot1 = _key_est(estudiante_id, f"armar_s1_{paso_actual}_{letra_actual}_{idx}")
    k_slot2 = _key_est(estudiante_id, f"armar_s2_{paso_actual}_{letra_actual}_{idx}")
    slot1 = st.session_state.get(k_slot1, "")
    slot2 = st.session_state.get(k_slot2, "")
    k_mostrar_acierto = _key_est(estudiante_id, f"armar_acierto_{paso_actual}_{letra_actual}")
    k_ya_sono = _key_est(estudiante_id, f"armar_ya_sono_{paso_actual}_{letra_actual}")
    mostrar_felicitacion = st.session_state.get(k_mostrar_acierto) == idx

    col_img, col_ui = st.columns([1, 1.2])
    with col_img:
        if item.get("ruta_img") and os.path.isfile(item["ruta_img"]):
            # Mostrar solo la parte superior de la imagen (sin el cintillo con el nombre) para no dar la respuesta
            try:
                with open(item["ruta_img"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                mime = "image/png" if item["ruta_img"].lower().endswith(".png") else "image/jpeg"
                st.markdown(
                    f'<div style="height:270px; overflow:hidden; border-radius:16px; background:#f0f0f0;">'
                    f'<img src="data:{mime};base64,{b64}" style="width:100%; height:auto; min-height:270px; object-fit:cover; object-position:top;" /></div>',
                    unsafe_allow_html=True,
                )
            except Exception:
                st.image(item["ruta_img"], use_container_width=True)
        else:
            # Sin imagen: placeholder neutro (no mostrar la palabra para no dar la respuesta)
            st.markdown(
                '<div style="min-height:270px; background:#f0f0f0; border-radius:16px; display:flex; align-items:center; justify-content:center; color:#999;">¿Qué palabra es?</div>',
                unsafe_allow_html=True,
            )

    with col_ui:
        if mostrar_felicitacion:
            # Pantalla de acierto: globos + karaoke + siguiente palabra
            st.balloons()
            if st.session_state.get(k_ya_sono) != idx:
                try:
                    audio_path = speech_engine.generar_audio(palabra)
                    if audio_path and os.path.isfile(audio_path):
                        with open(audio_path, "rb") as f:
                            _autoplay_audio_bytes(f.read(), mime="audio/mpeg")
                except Exception:
                    pass
                st.session_state[k_ya_sono] = idx
            st.success("¡Muy bien!")
            render_palabra_karaoke_felicitacion(palabra, unique_id=f"armar_feliz_{paso_actual}_{letra_actual}_{idx}")
            st.write("")
            if st.button("Siguiente palabra ➡️", key=f"armar_siguiente_{paso_actual}_{letra_actual}_{idx}", use_container_width=True):
                st.session_state.pop(k_mostrar_acierto, None)
                st.session_state.pop(k_ya_sono, None)
                st.session_state.pop(k_slot1, None)
                st.session_state.pop(k_slot2, None)
                st.session_state[k_idx] = idx + 1
                if idx + 1 >= len(palabras_list):
                    on_siguiente()
                st.rerun()
        else:
            st.markdown("**1. Arrastra aquí:**")
            slot_display_1 = slot1 if slot1 else "—"
            slot_display_2 = slot2 if slot2 else "—"
            st.markdown(
                f"""
                <div style="display:flex; gap:12px; margin-bottom:16px;">
                    <div style="flex:1; border:2px dashed #ccc; border-radius:12px; padding:14px; text-align:center; font-size:1.2rem; color:#333;">{slot_display_1}</div>
                    <div style="flex:1; border:2px dashed #ccc; border-radius:12px; padding:14px; text-align:center; font-size:1.2rem; color:#333;">{slot_display_2}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("**2. Elige las sílabas:**")
            # En Streamlit no hay arrastre real: al hacer clic en una sílaba se asigna al primer slot vacío
            cols_sil = st.columns(3)
            for i, sil in enumerate(opciones):
                with cols_sil[i]:
                    if st.button(sil, key=f"armar_sil_{paso_actual}_{letra_actual}_{idx}_{i}", use_container_width=True):
                        if not slot1:
                            st.session_state[k_slot1] = sil
                        elif not slot2:
                            st.session_state[k_slot2] = sil
                        st.rerun()

            st.write("")
            col_listo, col_borrar, col_saltar = st.columns(3)
            with col_borrar:
                if st.button("🔄 Borrar", key=f"armar_borrar_{paso_actual}_{letra_actual}_{idx}", use_container_width=True):
                    st.session_state.pop(k_slot1, None)
                    st.session_state.pop(k_slot2, None)
                    st.rerun()
            with col_saltar:
                if st.button("⏭️ Saltar", key=f"armar_saltar_{paso_actual}_{letra_actual}_{idx}", use_container_width=True):
                    st.session_state[k_idx] = idx + 1
                    if idx + 1 >= len(palabras_list):
                        on_siguiente()
                    st.rerun()
            with col_listo:
                if st.button("✓ Listo", key=f"armar_listo_{paso_actual}_{letra_actual}_{idx}", use_container_width=True):
                    formado = ((slot1 or "") + (slot2 or "")).upper().replace(" ", "")
                    esperado = "".join(silabas_correctas).upper()
                    if formado == esperado:
                        st.session_state.pop(k_slot1, None)
                        st.session_state.pop(k_slot2, None)
                        st.session_state[k_mostrar_acierto] = idx
                        st.rerun()
                    else:
                        st.warning("Revisa las sílabas. ¡Tú puedes!")
                        st.rerun()

    # Indicador de progreso (palabra X de 6)
    st.caption(f"Palabra {idx + 1} de {len(palabras_list)}")


def _render_actividad_escucha_opciones(
    items,
    paso_actual,
    estudiante_id,
    letra_actual,
    on_siguiente,
    titulo: str,
):
    """
    Actividad de reconocimiento auditivo tipo "Escucha y toca".
    items puede ser lista de dicts {"texto": str, "ruta_img": str} (palabras) o de strings (frases).
    Al acertar (solo palabras): se muestra imagen, efecto karaoke y globos.
    """
    total = len(items)
    if total == 0:
        st.info("No hay suficientes elementos para esta actividad. Puedes continuar.")
        if st.button("Continuar ➡️", key=f"escucha_skip_{paso_actual}_{letra_actual}"):
            on_siguiente()
            st.rerun()
        return

    # Normalizar: items pueden ser dicts (palabras con imagen) o strings (frases)
    es_palabras = items and isinstance(items[0], dict)
    textos_items = [it["texto"] if isinstance(it, dict) else it for it in items]

    k_idx = _key_est(estudiante_id, f"escucha_idx_{paso_actual}_{letra_actual}")
    idx = max(0, min(st.session_state.get(k_idx, 0), total - 1))
    item_actual = items[idx]
    texto_objetivo = item_actual["texto"] if isinstance(item_actual, dict) else item_actual
    ruta_img = item_actual.get("ruta_img", "") if isinstance(item_actual, dict) else ""

    k_mostrar_acierto = _key_est(estudiante_id, f"escucha_acierto_{paso_actual}_{letra_actual}")
    mostrar_felicitacion = st.session_state.get(k_mostrar_acierto) == idx

    if mostrar_felicitacion and es_palabras:
        # Pantalla de acierto: una fila con 3 columnas — imagen | karaoke | Siguiente
        st.balloons()
        st.markdown(f"### 🔊 {titulo}")
        st.success("¡Muy bien!")
        col_img, col_karaoke, col_btn = st.columns([1, 1.25, 1])
        with col_img:
            if ruta_img and os.path.isfile(ruta_img):
                st.image(ruta_img, use_container_width=True)
            else:
                st.markdown(
                    '<div style="min-height:100px; background:#f0f0f0; border-radius:16px; display:flex; align-items:center; justify-content:center; color:#999;">✓</div>',
                    unsafe_allow_html=True,
                )
        with col_karaoke:
            render_palabra_karaoke_felicitacion(
                texto_objetivo, unique_id=f"escucha_feliz_{paso_actual}_{letra_actual}_{idx}"
            )
        with col_btn:
            # Botón acotado a la tercera columna (no ancho completo de página)
            st.markdown("<div style='min-height:24px'></div>", unsafe_allow_html=True)
            if st.button(
                "Siguiente ➡️",
                key=f"escucha_siguiente_{paso_actual}_{letra_actual}_{idx}",
                use_container_width=True,
            ):
                st.session_state.pop(k_mostrar_acierto, None)
                st.session_state[k_idx] = idx + 1
                st.session_state.pop(_key_est(estudiante_id, f"escucha_opts_{paso_actual}_{letra_actual}_{idx}"), None)
                if idx + 1 >= total:
                    on_siguiente()
                st.rerun()
        return

    st.markdown(f"### 🔊 {titulo}")
    st.caption(f"Pregunta {idx + 1} de {total}")

    # Botón de reproducir audio
    if st.button("▶️ Escuchar de nuevo", key=f"escucha_play_{paso_actual}_{letra_actual}_{idx}", use_container_width=True):
        try:
            audio_path = speech_engine.generar_audio(texto_objetivo)
            if audio_path and os.path.isfile(audio_path):
                with open(audio_path, "rb") as f:
                    _autoplay_audio_bytes(f.read(), mime="audio/mpeg")
        except Exception:
            pass

    st.write("")

    # Construir opciones (correcta + 2 distractores) usando textos
    k_opts = _key_est(estudiante_id, f"escucha_opts_{paso_actual}_{letra_actual}_{idx}")
    if k_opts not in st.session_state:
        restantes = [t for t in textos_items if t != texto_objetivo]
        distractores = random.sample(restantes, k=min(2, len(restantes))) if restantes else []
        opciones = [texto_objetivo] + distractores
        while len(opciones) < 3:
            opciones.append(texto_objetivo)
        random.shuffle(opciones)
        st.session_state[k_opts] = opciones
    opciones = st.session_state[k_opts]

    cols = st.columns(3)
    for i, texto in enumerate(opciones):
        with cols[i]:
            # Tarjeta con signo de interrogación (como la app) y el texto abajo
            st.markdown(
                """
                <div style="
                    border: 2px dashed #d0d0d0;
                    border-radius: 16px;
                    min-height: 90px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 8px;
                    background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
                ">
                    <span style="font-size: 2.2rem; color: #ff4081;">?</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(texto, key=f"escucha_opt_{paso_actual}_{letra_actual}_{idx}_{i}", use_container_width=True):
                if texto == texto_objetivo:
                    if es_palabras:
                        st.session_state[k_mostrar_acierto] = idx
                    else:
                        st.session_state[k_idx] = idx + 1
                        st.session_state.pop(k_opts, None)
                        if idx + 1 >= total:
                            on_siguiente()
                    st.rerun()
                else:
                    st.warning("Escucha de nuevo y vuelve a intentarlo.")
                    st.rerun()


def _construir_items_escucha_palabras(recursos_lectura, cantidad=6):
    """Devuelve hasta `cantidad` palabras distintas con imagen para la actividad de escucha."""
    vistos = set()
    items = []
    for r in recursos_lectura or []:
        palabra = (r.get("palabra") or "").strip()
        if not palabra:
            continue
        p_norm = palabra.upper()
        if p_norm in vistos:
            continue
        vistos.add(p_norm)
        items.append({
            "texto": palabra_para_display(palabra) or palabra,
            "ruta_img": (r.get("ruta_img") or "").strip(),
        })
        if len(items) >= cantidad:
            break
    return items


def _construir_items_escucha_frases(letra_actual, estudiante_id):
    """Devuelve hasta 3 frases mágicas personalizadas para la actividad de escucha."""
    L = letra_actual.upper()
    frases_tpl = Curriculum.FRASES_MAGICAS.get(L, [])
    if not frases_tpl:
        frases_tpl = Curriculum.FRASES_MAGICAS_VOCAL.get(L, [])
    if not frases_tpl:
        return []
    perfil = _cached_perfil(estudiante_id)
    nombre_nino = (st.session_state.get("nombre_nino") or (perfil[2] if perfil and len(perfil) > 2 else "")) if perfil else st.session_state.get("nombre_nino", "")
    nombre_mama_raw = (perfil[7] if perfil and len(perfil) > 7 else "") or ""
    mama_display = f"Mamá {(nombre_mama_raw or '').strip()}" if (nombre_mama_raw or "").strip() else "mamá"
    frases = []
    for tpl in frases_tpl:
        try:
            f = tpl.format(nombre=nombre_nino or "Yo", mama=mama_display)
        except KeyError:
            f = tpl.replace("{nombre}", nombre_nino or "Yo").replace("{mama}", mama_display)
        frases.append(f)
        if len(frases) >= 3:
            break
    return frases


def _fondo_vocales_data_url():
    """Devuelve data URL de la imagen de fondo para páginas de vocales (fondo.png o cualquier .png en assets/)."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets_dir = os.path.join(base, "assets")
    candidatos = [
        os.path.join(base, "assets", "fondo.png"),
        os.path.join(base, "fondo.png"),
        "assets/fondo.png",
        "fondo.png",
    ]
    # Añadir cualquier .png en assets/ (p. ej. imagen guardada con otro nombre)
    if os.path.isdir(assets_dir):
        try:
            for f in os.listdir(assets_dir):
                if f.lower().endswith(".png"):
                    candidatos.append(os.path.join(assets_dir, f))
        except Exception:
            pass
    for path in candidatos:
        if os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                return f"data:image/png;base64,{b64}"
            except Exception:
                pass
    return None


def _fondo_ruta_leccion_motivo(fondos_list, k_fondo):
    idx_fondo = st.session_state.get(k_fondo, 0)
    if idx_fondo > 0 and fondos_list and idx_fondo <= len(fondos_list):
        return fondos_list[idx_fondo - 1].get("ruta", "") or ""
    return ""


def _render_leccion_motivo_select(estudiante_id, opciones_fondo, k_fondo):
    idx_fondo = st.session_state.get(k_fondo, 0)
    st.caption("Motivo de la hoja")
    nuevo_idx = st.selectbox(
        "Elige tu motivo",
        range(len(opciones_fondo)),
        index=min(idx_fondo, len(opciones_fondo) - 1),
        format_func=lambda i: opciones_fondo[i],
        key="leccion_motivo_sel",
    )
    if nuevo_idx != idx_fondo:
        st.session_state[k_fondo] = nuevo_idx
        st.session_state.pop(_key_est(estudiante_id, "leccion_pdf_bytes"), None)
        st.rerun()


def _render_leccion_pdf_bloque(
    estudiante_id,
    letra_actual,
    silabas_letra,
    color_fav,
    fondos_list,
    k_fondo,
):
    fondo_ruta = _fondo_ruta_leccion_motivo(fondos_list, k_fondo)
    st.caption("Tu libro de lecturas")
    if PDF_LECCION_DISPONIBLE and ejecutar_job_en_background:
        k_pdf = _key_est(estudiante_id, "leccion_pdf_bytes")
        k_job = _key_est(estudiante_id, "leccion_pdf_job_id")
        job_id = st.session_state.get(k_job)

        if job_id:
            job = pdf_job_obtener(job_id)
            if job and job.get("status") == "ready" and job.get("pdf_blob"):
                st.session_state[k_pdf] = job["pdf_blob"]
                st.session_state.pop(k_job, None)
                st.rerun()
            elif job and job.get("status") == "failed":
                st.error(f"No se pudo crear el PDF: {job.get('error_msg', 'Error desconocido')}")
                st.session_state.pop(k_job, None)
            else:
                st.info("Tu hoja se está generando. Puedes seguir practicando.")
                if st.button("Comprobar si ya está listo", use_container_width=True, key="comprobar_pdf_leccion"):
                    st.rerun()

        if st.session_state.get(k_pdf):
            nombre_sano = (st.session_state.get("nombre_nino") or "lecturas").strip().split()[0]
            nombre_sano = "".join(c for c in nombre_sano if c.isalnum() or c in "áéíóúñ") or "lecturas"
            st.download_button(
                label="Descargar hoja para imprimir",
                data=st.session_state[k_pdf],
                file_name=f"leccion_{letra_actual}_{nombre_sano}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="descargar_pdf_leccion",
            )
            if st.button("Otra hoja", key="regenerar_pdf_leccion", use_container_width=True):
                st.session_state.pop(k_pdf, None)
                st.session_state.pop(k_job, None)
                st.rerun()
        elif not job_id:
            if st.button("Crear lección para imprimir", use_container_width=True, key="imprimir_leccion"):
                try:
                    nombre_est = st.session_state.get("nombre_nino", "") or ""
                    perfil = _cached_perfil(estudiante_id)
                    if perfil and len(perfil) > 2:
                        nombre_est = (perfil[2] or "").strip() or nombre_est
                    recursos_pdf = _cached_recursos(estudiante_id, letra_actual, 9)
                    palabras_pdf = [
                        {"palabra": (r.get("palabra") or "").strip(), "ruta_img": (r.get("ruta_img") or "").strip()}
                        for r in recursos_pdf
                        if (r.get("palabra") or "").strip()
                    ]
                    frases_pdf = []
                    frases_tpl = Curriculum.FRASES_MAGICAS.get(letra_actual.upper(), [])
                    if frases_tpl:
                        nombre_nino_pdf = nombre_est
                        mama_display = "mamá"
                        if perfil and len(perfil) > 2:
                            nombre_nino_pdf = (perfil[2] or "").strip() or nombre_nino_pdf
                        if perfil and len(perfil) > 7 and (perfil[7] or "").strip():
                            mama_display = f"Mamá {(perfil[7] or '').strip()}"
                        for tpl in frases_tpl:
                            try:
                                f = tpl.format(nombre=nombre_nino_pdf or "Yo", mama=mama_display)
                            except KeyError:
                                f = tpl.replace("{nombre}", nombre_nino_pdf or "Yo").replace("{mama}", mama_display)
                            frases_pdf.append(f)
                    foto_est = obtener_avatar_estudiante(estudiante_id)
                    album_nino = _cached_album(estudiante_id)
                    foto_mama_ruta = None
                    nombre_mama_buscar = (perfil[7] or "").strip() if perfil and len(perfil) > 7 else ""
                    for (palabra_clave, _cat, img_path) in album_nino:
                        if not img_path or not (palabra_clave or "").strip():
                            continue
                        p = (palabra_clave or "").upper().replace("Á", "A")
                        if "MAMA" in p or "MAMÁ" in (palabra_clave or "").upper():
                            foto_mama_ruta = img_path
                            break
                        if nombre_mama_buscar and (
                            nombre_mama_buscar.upper() in p or nombre_mama_buscar in (palabra_clave or "")
                        ):
                            foto_mama_ruta = img_path
                            break
                    params = {
                        "letra": letra_actual,
                        "silabas": silabas_letra,
                        "nombre_estudiante": nombre_est,
                        "fondo_ruta": fondo_ruta or "",
                        "color_hex": color_fav,
                        "palabras": palabras_pdf,
                        "frases": frases_pdf,
                        "foto_estudiante": foto_est or "",
                        "foto_mama": foto_mama_ruta or "",
                    }
                    new_job_id = pdf_job_crear(estudiante_id, "leccion", json.dumps(params))
                    if new_job_id:
                        st.session_state[k_job] = new_job_id
                        ejecutar_job_en_background(new_job_id)
                except Exception as e:
                    st.error(f"No se pudo encolar el PDF: {e}")
                st.rerun()
    elif PDF_LECCION_DISPONIBLE:
        k_pdf = _key_est(estudiante_id, "leccion_pdf_bytes")
        if st.session_state.get("leccion_preparar_pdf"):
            with st.spinner("Creando tu hoja…"):
                try:
                    nombre_est = st.session_state.get("nombre_nino", "") or ""
                    perfil = _cached_perfil(estudiante_id)
                    if perfil and len(perfil) > 2:
                        nombre_est = (perfil[2] or "").strip() or nombre_est
                    recursos_pdf = _cached_recursos(estudiante_id, letra_actual, 9)
                    palabras_pdf = [
                        {"palabra": (r.get("palabra") or "").strip(), "ruta_img": (r.get("ruta_img") or "").strip()}
                        for r in recursos_pdf
                        if (r.get("palabra") or "").strip()
                    ]
                    frases_pdf = []
                    frases_tpl = Curriculum.FRASES_MAGICAS.get(letra_actual.upper(), [])
                    if frases_tpl:
                        nombre_nino_pdf = (perfil[2] or "").strip() or nombre_est if perfil and len(perfil) > 2 else nombre_est
                        mama_display = "mamá"
                        if perfil and len(perfil) > 7 and (perfil[7] or "").strip():
                            mama_display = f"Mamá {(perfil[7] or '').strip()}"
                        for tpl in frases_tpl:
                            try:
                                f = tpl.format(nombre=nombre_nino_pdf or "Yo", mama=mama_display)
                            except KeyError:
                                f = tpl.replace("{nombre}", nombre_nino_pdf or "Yo").replace("{mama}", mama_display)
                            frases_pdf.append(f)
                    foto_est = obtener_avatar_estudiante(estudiante_id)
                    album_nino = _cached_album(estudiante_id)
                    foto_mama_ruta = None
                    nombre_mama_buscar = (perfil[7] or "").strip() if perfil and len(perfil) > 7 else ""
                    for (palabra_clave, _cat, img_path) in (album_nino or []):
                        if not img_path or not (palabra_clave or "").strip():
                            continue
                        p = (palabra_clave or "").upper().replace("Á", "A")
                        if "MAMA" in p or "MAMÁ" in (palabra_clave or "").upper():
                            foto_mama_ruta = img_path
                            break
                        if nombre_mama_buscar and (
                            nombre_mama_buscar.upper() in p or nombre_mama_buscar in (palabra_clave or "")
                        ):
                            foto_mama_ruta = img_path
                            break
                    pdf_bytes = generar_pdf_leccion(
                        letra_actual,
                        silabas_letra,
                        nombre_estudiante=nombre_est,
                        fondo_ruta=fondo_ruta or "",
                        color_hex=color_fav,
                        palabras=palabras_pdf,
                        frases=frases_pdf,
                        foto_estudiante=foto_est or "",
                        foto_mama=foto_mama_ruta or "",
                    )
                    st.session_state[k_pdf] = pdf_bytes
                except Exception as e:
                    st.error(f"No se pudo crear el PDF: {e}")
                st.session_state["leccion_preparar_pdf"] = False
            st.rerun()
        if st.session_state.get(k_pdf):
            nombre_sano = (st.session_state.get("nombre_nino") or "lecturas").strip().split()[0]
            nombre_sano = "".join(c for c in nombre_sano if c.isalnum() or c in "áéíóúñ") or "lecturas"
            st.download_button(
                label="Descargar hoja para imprimir",
                data=st.session_state[k_pdf],
                file_name=f"leccion_{letra_actual}_{nombre_sano}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="descargar_pdf_leccion",
            )
            if st.button("Otra hoja", key="regenerar_pdf_leccion", use_container_width=True):
                st.session_state.pop(k_pdf, None)
                st.rerun()
        else:
            if st.button("Crear lección para imprimir", use_container_width=True, key="imprimir_leccion"):
                st.session_state["leccion_preparar_pdf"] = True
                st.rerun()
    else:
        st.caption("PDF no disponible")


def _render_leccion_motivo_y_pdf_column(
    estudiante_id,
    letra_actual,
    silabas_letra,
    color_fav,
    fondos_list,
    opciones_fondo,
    k_fondo,
):
    """Motivo + PDF apilados (celda derecha del encabezado 1×3)."""
    _render_leccion_motivo_select(estudiante_id, opciones_fondo, k_fondo)
    _render_leccion_pdf_bloque(estudiante_id, letra_actual, silabas_letra, color_fav, fondos_list, k_fondo)


def render_lecciones_nino():
    # 1. Configuración Inicial y Datos de Sesión
    ciclo = st.session_state.get('ciclo_actual', 'Ciclo 1') or 'Ciclo 1'
    estudiante_id = st.session_state.get('estudiante_id')
    letras_disponibles = Curriculum.obtener_letras_por_ciclo(ciclo)
    # V3 puede inyectar un bloque explícito de letras sin depender de ciclos V2.
    letras_override = st.session_state.get("v3_letras_override")
    if isinstance(letras_override, list) and letras_override:
        letras_disponibles = [str(x).strip().upper() for x in letras_override if str(x).strip()]
    if not letras_disponibles and ciclo != 'Ciclo 1':
        ciclo = 'Ciclo 1'
        st.session_state.ciclo_actual = ciclo
        letras_disponibles = Curriculum.obtener_letras_por_ciclo(ciclo)
    gen_w, gen_h = AssetManager.obtener_tamano_promedio_genericos()
    card_max_w = int(gen_w * 1.2)
    card_h = int(gen_h * 1.2) + 60
    card_h_row = int(gen_h * 1.05) + 60

    if not estudiante_id:
        st.error("No encontramos al estudiante activo. Volvamos al inicio.")
        if st.button("Volver al inicio"):
            st.session_state.pagina_activa = 'hub_nino'
            st.rerun()
        return

    # Claves de session_state por estudiante (cada niño tiene su propio avance)
    k_indice = _key_est(estudiante_id, "indice_letra")
    k_vocal_fase = _key_est(estudiante_id, "vocal_fase")

    if not letras_disponibles:
        st.error("Ups, no encontramos letras para este ciclo.")
        if st.button("Volver al Inicio"):
            st.session_state.pagina_activa = 'hub_nino'
            st.rerun()
        return

    if k_indice not in st.session_state or st.session_state[k_indice] >= len(letras_disponibles):
        st.session_state[k_indice] = 0

    # V3 — consonantes: misma regla que "Mi Ruta" (Directa ≥75% + aciertos mínimos).
    # Si `indice_letra` vuelve a 0 (nueva sesión / Hub) pero M ya está superada en BD,
    # situar en la primera letra del bloque que aún no lo está (p. ej. P), no repetir M.
    _ov_c = st.session_state.get("v3_letras_override")
    if (
        estudiante_id
        and isinstance(_ov_c, list)
        and _ov_c
        and not all(str(x).strip().upper() in "AEIOU" for x in _ov_c)
    ):
        ii = st.session_state[k_indice]
        if 0 <= ii < len(letras_disponibles):
            L_cur = letras_disponibles[ii]
            ac, er, pct = gamificacion.obtener_stats_directa(estudiante_id, L_cur)
            if gamificacion._is_aciertos_75_y_pct(ac, er, pct):
                nxt = None
                for j, L in enumerate(letras_disponibles):
                    ac2, er2, pct2 = gamificacion.obtener_stats_directa(estudiante_id, L)
                    if not gamificacion._is_aciertos_75_y_pct(ac2, er2, pct2):
                        nxt = j
                        break
                if nxt is not None:
                    st.session_state[k_indice] = nxt

    # 2. Selección de la letra actual
    letra_actual = letras_disponibles[st.session_state[k_indice]]
    es_vocal = letra_actual.upper() in ["A", "E", "I", "O", "U"]

    silabas_consonante_mejorado = (not es_vocal) and bool(
        Curriculum.SILABAS_POR_CONSONANTE.get((letra_actual or "").strip().upper())
    )
    silabas_letra_consonante = (
        Curriculum.SILABAS_POR_CONSONANTE.get((letra_actual or "").strip().upper())
        if silabas_consonante_mejorado
        else None
    )
    k_paso_consonante = None
    fondos_list_sc: list = []
    opciones_fondo_sc = ["Sin motivo"]
    k_fondo_sc = None
    idx_fondo_sc = 0
    fondo_ruta_sc = ""
    if silabas_consonante_mejorado:
        k_paso_c = _key_est(estudiante_id, f"leccion_consonant_paso_{letra_actual}")
        if k_paso_c not in st.session_state:
            fase_db = obtener_fase_leccion_consonante(estudiante_id, letra_actual)
            st.session_state[k_paso_c] = fase_db if fase_db else "principal"
        elif st.session_state[k_paso_c] not in FASES_CONSONANTE_VALIDAS:
            st.session_state[k_paso_c] = "principal"
        k_paso_consonante = st.session_state[k_paso_c]
        fondos_list_sc = AssetManager.obtener_fondos_abecedario()
        opciones_fondo_sc = ["Sin motivo"] + [f.get("nombre", "Fondo") for f in fondos_list_sc]
        k_fondo_sc = _key_est(estudiante_id, "leccion_fondo_idx")
        if k_fondo_sc not in st.session_state:
            st.session_state[k_fondo_sc] = 0
        idx_fondo_sc = st.session_state[k_fondo_sc]
        if idx_fondo_sc > 0 and fondos_list_sc and idx_fondo_sc <= len(fondos_list_sc):
            fondo_ruta_sc = fondos_list_sc[idx_fondo_sc - 1].get("ruta", "") or ""
        if fondo_ruta_sc and os.path.isfile(fondo_ruta_sc):
            try:
                b64_fondo = _cached_fondo_b64(fondo_ruta_sc)
                mime_fondo = "image/png" if fondo_ruta_sc.lower().endswith(".png") else "image/jpeg"
                st.markdown(
                    f"""
                    <style>
                    [data-testid="stAppViewContainer"] {{
                        background-image: url("data:{mime_fondo};base64,{b64_fondo}");
                        background-size: cover;
                        background-position: center;
                        background-attachment: fixed;
                    }}
                    [data-testid="stAppViewContainer"]::before {{
                        content: "";
                        position: fixed;
                        top: 0; left: 0; right: 0; bottom: 0;
                        background: rgba(255, 255, 255, 0.78);
                        pointer-events: none;
                        z-index: 0;
                    }}
                    [data-testid="stAppViewContainer"] > section {{ position: relative; z-index: 1; }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception:
                pass

    usar_hdr_3 = bool(silabas_consonante_mejorado and k_paso_consonante == "principal")

    # Fondo decorativo en páginas de vocales (fondo.png)
    if es_vocal:
        fondo_url = _fondo_vocales_data_url()
        if fondo_url:
            st.markdown(
                f"""
                <style>
                [data-testid="stAppViewContainer"] {{
                    background-image: url("{fondo_url}");
                    background-size: cover;
                    background-position: center;
                    background-attachment: fixed;
                }}
                [data-testid="stAppViewContainer"]::before {{
                    content: "";
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(255, 255, 255, 0.75);
                    pointer-events: none;
                    z-index: 0;
                }}
                [data-testid="stAppViewContainer"] > section {{ position: relative; z-index: 1; }}
                </style>
                """,
                unsafe_allow_html=True,
            )

    # Cabecera: vocales o consonantes (1×3 en fase principal con matriz de sílabas)
    if usar_hdr_3:
        color_hdr = st.session_state.get("color_favorito", "#4A90E2") or "#4A90E2"
        titulo_txt = f"La letra {(letra_actual or '').strip()}"
        html_centro_leccion = (
            '<p style="margin:0.45rem 0 0 0;font-size:0.92rem;color:#444;line-height:1.4;">'
            "Explora la <b>matriz de sílabas</b>, lee las tarjetas con tus papás y usa la columna derecha para "
            "el <b>fondo de la pantalla</b> y tu <b>lección en PDF</b>.</p>"
        )

        def _slot_motivo_pdf_hdr():
            _render_leccion_motivo_y_pdf_column(
                estudiante_id,
                letra_actual,
                silabas_letra_consonante,
                color_hdr,
                fondos_list_sc,
                opciones_fondo_sc,
                k_fondo_sc,
            )

        render_encabezado_logo_titulo_acciones(
            titulo_txt,
            color_fav=color_hdr,
            logo_height=192,
            slot_acciones=_slot_motivo_pdf_hdr,
            html_adicional_centro=html_centro_leccion,
            column_weights=(0.95, 1.55, 1.05),
        )
    else:
        _lg = logo_markup_html(height_px=88, margin_right=0)
        if es_vocal:
            letras_override = st.session_state.get("v3_letras_override")
            if isinstance(letras_override, list) and letras_override and all(
                str(x).upper() in ["A", "E", "I", "O", "U"] for x in letras_override
            ):
                titulo_letras = "-".join([str(x).upper() for x in letras_override])
                titulo_esc = html.escape(titulo_letras)
                st.markdown(
                    f"<div style='display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;'>"
                    f"{_lg}<h1 style='text-align: center; margin:0;'>Aprendamos las letras {titulo_esc}</h1></div>",
                    unsafe_allow_html=True,
                )
            else:
                letra_esc = html.escape(str(letra_actual or "").strip())
                st.markdown(
                    f"<div style='display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;'>"
                    f"{_lg}<h1 style='text-align: center; margin:0;'>Aprendamos la letra {letra_esc}</h1></div>",
                    unsafe_allow_html=True,
                )
        else:
            letra_esc = html.escape(str(letra_actual or "").strip())
            st.markdown(
                f"<div style='display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;margin-bottom:0.25rem;'>"
                f"{_lg}<h1 style='text-align: center; margin:0;'>La letra {letra_esc}</h1></div>",
                unsafe_allow_html=True,
            )

    # 3. Obtener recursos (vocales: objetivo 9 palabras por vocal)
    recursos = None
    if es_vocal:
        recursos = _cached_recursos(estudiante_id, letra_actual, 9)

    recurso = (recursos[0] if recursos else None) or AssetManager.obtener_recurso_lectura(estudiante_id, letra_actual)

    if recurso:
        # --- VOCAL (V3): presenta (9) -> completa -> termina (9) -> siguiente vocal ---
        if es_vocal and recursos:
            st.write("")
            # Restaurar fase desde la base de datos para no repetir "empieza"
            avance = vocal_fase_avance(estudiante_id, letra_actual)
            if avance == "completo":
                # Evitar loop infinito si TODAS las vocales del bloque están completas
                idx_actual = st.session_state[k_indice]
                next_idx = None
                for step in range(len(letras_disponibles)):
                    cand_idx = (idx_actual + step) % len(letras_disponibles)
                    if vocal_fase_avance(estudiante_id, letras_disponibles[cand_idx]) != "completo":
                        next_idx = cand_idx
                        break

                if next_idx is None:
                    st.success("¡Ya completaste estas vocales! ✅")
                    st.caption("Puedes volver al salón o cambiar de bloque.")
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("🏠 Volver al Salón", key="btn_vocales_done_home"):
                            st.session_state.pagina_activa = "hub_nino"
                            st.rerun()
                    with colB:
                        if st.button("🔄 Cambiar de bloque", key="btn_vocales_done_change"):
                            # Vuelve a renderizar desde arriba (los botones de bloques están en V3 wrapper)
                            st.session_state.pagina_activa = "lecciones_nino"
                            st.rerun()
                    st.stop()

                st.session_state[k_indice] = next_idx
                if vocal_fase_avance(estudiante_id, letras_disponibles[next_idx]) == "termina":
                    st.session_state[k_vocal_fase] = "termina"
                else:
                    # En V3, el estado inicial para vocales es "presenta".
                    st.session_state[k_vocal_fase] = "presenta" if st.session_state.get("v3_letras_override") else "empieza"
                st.rerun()
            if avance == "termina" and st.session_state.get(k_vocal_fase) not in ("termina", "completa"):
                st.session_state[k_vocal_fase] = "termina"
            if st.session_state.get(k_vocal_fase) not in ("empieza", "presenta", "termina", "completa"):
                st.session_state[k_vocal_fase] = "empieza"
            vocal_fase = st.session_state[k_vocal_fase]
            # Inicialización para evitar UnboundLocalError en la fase V3 "presenta".
            # En esa fase mostramos la presentación manualmente (3x3) y no usamos lista_recursos.
            lista_recursos = []

            k_orden_vocal = _key_est(estudiante_id, f"vocal_orden_{letra_actual}")
            if k_orden_vocal not in st.session_state:
                st.session_state[k_orden_vocal] = random.sample(["A", "E", "I", "O", "U"], 5)
            opciones_vocales = st.session_state[k_orden_vocal]

            # Botones de vocales más grandes y compactos
            st.markdown(
                """
                <style>
                .stButton > button {
                    font-size: 2.2rem !important;
                    min-height: 4em !important;
                    padding: 0.5rem 1rem !important;
                    border-radius: 16px !important;
                }
                [data-testid="column"] { padding: 0 0.4rem !important; }
                </style>
                """,
                unsafe_allow_html=True,
            )

            texto_instruccion = "Selecciona la letra con la que empieza mi nombre." if vocal_fase == "empieza" else "Selecciona la letra con la que termina mi nombre."
            color_fav = st.session_state.get("color_favorito", "#4A90E2")

            def _render_escucha_atencion(c):
                st.markdown(
                    f"""
                    <div style="
                        font-size: 1.75rem;
                        font-weight: 800;
                        color: #1a1a2e;
                        background: linear-gradient(135deg, {c}22 0%, {c}44 100%);
                        border: 3px solid {c};
                        border-radius: 16px;
                        padding: 14px 20px;
                        text-align: center;
                        margin-bottom: 12px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    ">
                        ¡Escucha con atención!
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            def _render_instruccion_grande():
                st.markdown(
                    f"""
                    <div style="
                        font-size: 1.75rem;
                        font-weight: 800;
                        color: #1a1a2e;
                        background: linear-gradient(135deg, {color_fav}22 0%, {color_fav}44 100%);
                        border: 3px solid {color_fav};
                        border-radius: 16px;
                        padding: 14px 20px;
                        text-align: center;
                        margin-bottom: 12px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    ">
                        {texto_instruccion}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            VOCALES_ORDEN = ["A", "E", "I", "O", "U"]
            idx_actual = VOCALES_ORDEN.index(letra_actual.upper()) if letra_actual.upper() in VOCALES_ORDEN else 0
            siguiente_vocal = VOCALES_ORDEN[(idx_actual + 1) % 5]

            def _render_opciones_vocales(row_key: str, correcta_fila: str, es_vocal_actual: bool, palabra_fila: str, indice_fila: int):
                _render_instruccion_grande()
                cols = st.columns(len(opciones_vocales))
                for idx, op in enumerate(opciones_vocales):
                    if cols[idx].button(op, key=f"{row_key}_btn_{op}"):
                        ok = op == correcta_fila
                        st.session_state[_key_est(estudiante_id, f"{row_key}_res")] = ok
                        if ok:
                            st.session_state["_reproducir_prefijo"] = prefijo
                            st.session_state["_reproducir_i"] = indice_fila
                            st.session_state["_reproducir_palabra"] = palabra_fila
                            st.session_state["_reproducir_vocal"] = correcta_fila
                            st.session_state["_reproducir_empieza"] = vocal_fase == "empieza"
                        if es_vocal_actual:
                            tipo = "VocalInicio" if vocal_fase == "empieza" else "VocalFin"
                            actualizar_progreso_silabico(estudiante_id, letra_actual, tipo, ok)
                        st.rerun()

            # Recursos según fase: 9 de la vocal actual.
            # Orden fijo en session_state para que al reproducir audio (rerun) no cambien las posiciones.
            def _construir_lista_estable(prefijo_key, lista_actual, lista_sig):
                lista_combinada = lista_actual + lista_sig
                orden_key = _key_est(estudiante_id, f"vocal_orden_fila_{prefijo_key}")
                if orden_key not in st.session_state or len(st.session_state[orden_key]) != len(lista_combinada):
                    orden = list(range(len(lista_combinada)))
                    random.shuffle(orden)
                    st.session_state[orden_key] = orden
                orden = st.session_state[orden_key]
                return [lista_combinada[i] for i in orden]

            # --- Fase "completa": palabra en letras; elegir vocales que faltan (+ 1 innecesaria)
            def _vocales_y_visible(palabra_str):
                """Devuelve (palabra_visible con _ por vocal, lista de vocales en orden)."""
                p = (palabra_str or "").strip().upper().translate(AssetManager._NORM_VOCAL)
                visible = []
                vocales_list = []
                for c in p:
                    if c in "AEIOU":
                        visible.append("_")
                        vocales_list.append(c)
                    else:
                        visible.append(c)
                return " ".join(visible), vocales_list

            def _cortar_palabra_para_vocales(palabra_str: str) -> str:
                """
                Para mantener la actividad corta y efectiva:
                si viene algo como "Abuela Margarita", usamos solo "Abuela".
                """
                p = (palabra_str or "").strip()
                if not p:
                    return ""
                # Tomar el primer "token" separado por espacios.
                p = p.split()[0].strip()
                # Si viene con guiones (p. ej. "A-vi-ón"), usamos solo la primera parte.
                if "-" in p:
                    p = p.split("-", 1)[0].strip()
                return p

            if vocal_fase == "completa":
                recursos_fin = _cached_recursos_terminan(estudiante_id, letra_actual, 5)
                recursos_inicio = _cached_recursos(estudiante_id, letra_actual, 5)
                lista_mix = []
                for r in (recursos_inicio or []):
                    p_full = (r.get("palabra") or "").strip()
                    p = _cortar_palabra_para_vocales(p_full)
                    if len(p) > 0:
                        visible, vocales = _vocales_y_visible(p)
                        if len(vocales) >= 1:
                            lista_mix.append(dict(r, palabra=p, palabra_visible=visible, vocales_orden=vocales))
                for r in (recursos_fin or []):
                    p_full = (r.get("palabra") or "").strip()
                    p = _cortar_palabra_para_vocales(p_full)
                    if len(p) > 0 and not any((x.get("palabra") or "").strip() == p for x in lista_mix):
                        visible, vocales = _vocales_y_visible(p)
                        if len(vocales) >= 1:
                            lista_mix.append(dict(r, palabra=p, palabra_visible=visible, vocales_orden=vocales))
                recursos_completa = lista_mix[:9]
                if not recursos_completa:
                    if st.button(
                        "Ir a escucha y toca ➡️",
                        key=f"btn_siguiente_vocal_desde_completa_{letra_actual}_{estudiante_id}",
                    ):
                        st.session_state[k_vocal_fase] = "termina"
                        st.rerun()
                else:
                    prefijo_completa = f"vocal_completa_{letra_actual}"
                    k_orden_completa = _key_est(estudiante_id, f"{prefijo_completa}_orden")
                    if k_orden_completa not in st.session_state or len(st.session_state[k_orden_completa]) != len(recursos_completa):
                        st.session_state[k_orden_completa] = random.sample(range(len(recursos_completa)), len(recursos_completa))
                    orden_c = st.session_state[k_orden_completa]
                    lista_completa = [recursos_completa[j] for j in orden_c]
                    texto_instruccion_completa = "Elige las letras que faltan. (Hay una que no va.)"
                    VOCALES = ["A", "E", "I", "O", "U"]
                    for i, r in enumerate(lista_completa):
                        palabra = (r.get("palabra") or "").strip()
                        vocales_orden = r.get("vocales_orden") or []
                        palabra_visible_base = r.get("palabra_visible") or "_"
                        row_key_c = f"{prefijo_completa}_{i}"
                        res_c = st.session_state.get(_key_est(estudiante_id, f"{row_key_c}_res"))
                        slot_key_c = _key_est(estudiante_id, f"{row_key_c}_slots")
                        used_key_c = _key_est(estudiante_id, f"{row_key_c}_used")
                        if slot_key_c not in st.session_state:
                            st.session_state[slot_key_c] = [""] * len(vocales_orden)
                            st.session_state[used_key_c] = set()
                        slots_c = st.session_state[slot_key_c]
                        used_c = st.session_state[used_key_c]
                        distractor = next((v for v in VOCALES if v not in vocales_orden), "I")
                        pool_base = list(vocales_orden) + [distractor]
                        k_pool = _key_est(estudiante_id, f"{row_key_c}_pool")
                        if k_pool not in st.session_state or len(st.session_state[k_pool]) != len(pool_base):
                            st.session_state[k_pool] = random.sample(pool_base, len(pool_base))
                        pool_c = st.session_state[k_pool]

                        img_col, cont_col = st.columns([1.1, 2.2])
                        with img_col:
                            _render_escucha_atencion(color_fav)
                            audio_path_c = speech_engine.generar_audio(palabra)
                            render_polaroid_click_to_play(
                                r["ruta_img"],
                                texto_tts=palabra,
                                audio_path=audio_path_c,
                                es_acierto=res_c,
                                mostrar_top_pct=80,
                                width_pct=100,
                                max_width_px=card_max_w,
                                height_px=card_h_row,
                            )
                        with cont_col:
                            st.markdown(
                                f'<div style="font-size: 1.5rem; font-weight: 700; color: #1a1a2e; margin-bottom: 10px;">{texto_instruccion_completa}</div>',
                                unsafe_allow_html=True,
                            )
                            # Mostrar palabra con huecos rellenados
                            partes = palabra_visible_base.split()
                            idx_slot = 0
                            display_chars = []
                            for part in partes:
                                if part == "_":
                                    display_chars.append((slots_c[idx_slot] or "_") if idx_slot < len(slots_c) else "_")
                                    idx_slot += 1
                                else:
                                    display_chars.append(part)
                            palabra_mostrar = " ".join(display_chars)
                            st.markdown(
                                f'<div style="font-size: 2.5rem; font-weight: 800; letter-spacing: 0.2em; margin: 12px 0;">{palabra_mostrar.upper()}</div>',
                                unsafe_allow_html=True,
                            )
                            if res_c is True:
                                # Globos solo en el primer render de felicitación (no en cada rerun/letra)
                                if st.session_state.get("_reproducir_completa_key") == row_key_c:
                                    st.balloons()
                                if st.session_state.get("_reproducir_completa_key") == row_key_c:
                                    palabra_rep = st.session_state.get("_reproducir_completa_palabra", palabra)
                                    frase_audio = f"¡Muy bien! {palabra_rep}"
                                    # Mensaje visible con efecto tipo karaoke (caja que se destaca)
                                    st.markdown(
                                        """
                                        <style>
                                        @keyframes karaoke-box {
                                            0% { opacity: 0; transform: scale(0.95); }
                                            100% { opacity: 1; transform: scale(1); }
                                        }
                                        .box-karaoke-completa {
                                            display: inline-block;
                                            padding: 12px 24px;
                                            border-radius: 12px;
                                            background: linear-gradient(135deg, #4CAF50 0%, #2e7d32 100%);
                                            color: white;
                                            font-size: 1.4rem;
                                            font-weight: bold;
                                            box-shadow: 0 4px 14px rgba(46, 125, 50, 0.5);
                                            animation: karaoke-box 0.5s ease-out forwards;
                                        }
                                        </style>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                                    st.markdown(
                                        f'<p style="text-align: center; margin: 16px 0;"><span class="box-karaoke-completa">¡Muy bien!</span></p>',
                                        unsafe_allow_html=True,
                                    )
                                    # Asegurar acentuación correcta (mamá, ají, etc.) para karaoke y audio
                                    palabra_rep_disp = palabra_para_display(palabra_rep)
                                    render_palabra_karaoke_felicitacion(palabra_rep_disp, unique_id=f"lecciones_completa_{row_key_c}")
                                    # Reproducir "¡Muy bien! [palabra]" solo con gTTS (voz femenina, una sola reproducción)
                                    frase_audio = f"¡Muy bien! {palabra_rep_disp}"
                                    audio_rep = speech_engine.generar_audio(frase_audio)
                                    if audio_rep:
                                        try:
                                            with open(audio_rep, "rb") as f:
                                                _autoplay_audio_bytes(f.read(), mime="audio/mpeg")
                                        except Exception:
                                            pass
                                    st.session_state.pop("_reproducir_completa_key", None)
                                    st.session_state.pop("_reproducir_completa_palabra", None)
                            elif res_c is False:
                                st.error("Intenta otra vez")
                                if st.button(
                                    "🔄 Reintentar esta palabra",
                                    key=f"{row_key_c}_reintentar",
                                    use_container_width=True,
                                ):
                                    st.session_state.pop(_key_est(estudiante_id, f"{row_key_c}_res"), None)
                                    st.session_state[slot_key_c] = [""] * len(vocales_orden)
                                    st.session_state[used_key_c] = set()
                                    st.session_state.pop(k_pool, None)
                                    st.rerun()
                            # Botones de vocales (por índice para vocales repetidas)
                            clicked_pool_idx = None
                            num_pool = len(pool_c)
                            cols_v = st.columns(num_pool)
                            for j in range(num_pool):
                                with cols_v[j]:
                                    if j in used_c:
                                        st.markdown('<div style="min-height: 38px;"></div>', unsafe_allow_html=True)
                                    else:
                                        if st.button(pool_c[j], key=f"{row_key_c}_v_{i}_{j}_{pool_c[j]}"):
                                            clicked_pool_idx = j
                            if clicked_pool_idx is not None:
                                first_empty = next((k for k in range(len(slots_c)) if not (slots_c[k] or "").strip()), None)
                                if first_empty is not None:
                                    new_slots = list(slots_c)
                                    new_slots[first_empty] = pool_c[clicked_pool_idx]
                                    st.session_state[slot_key_c] = new_slots
                                    st.session_state[used_key_c] = used_c | {clicked_pool_idx}
                                    # Si había error, al cambiar elección volvemos a evaluar al llenar de nuevo
                                    if res_c is False:
                                        st.session_state.pop(_key_est(estudiante_id, f"{row_key_c}_res"), None)
                                st.rerun()
                            # Al completar todos los huecos: reconstruir palabra y evaluar
                            if len(slots_c) and all((s or "").strip() for s in slots_c):
                                partes = palabra_visible_base.split()
                                idx_s = 0
                                letras_armadas = []
                                for part in partes:
                                    if part == "_":
                                        letras_armadas.append((slots_c[idx_s] or "").strip().upper() if idx_s < len(slots_c) else "")
                                        idx_s += 1
                                    else:
                                        letras_armadas.append(part)
                                palabra_armada = "".join(letras_armadas).translate(AssetManager._NORM_VOCAL)
                                objetivo = (palabra or "").strip().upper().translate(AssetManager._NORM_VOCAL).replace(" ", "")
                                ok = palabra_armada.replace(" ", "") == objetivo
                                # Solo evaluar una vez por “llenado”; si falló, Reintentar o nueva letra en slot limpia res
                                if res_c is None:
                                    st.session_state[_key_est(estudiante_id, f"{row_key_c}_res")] = ok
                                    if ok:
                                        actualizar_progreso_silabico(estudiante_id, letra_actual, "VocalCompleta", True)
                                        st.session_state["_reproducir_completa_key"] = row_key_c
                                        st.session_state["_reproducir_completa_palabra"] = palabra
                                    else:
                                        actualizar_progreso_silabico(estudiante_id, letra_actual, "VocalCompleta", False)
                                    st.rerun()
                        st.write("---")
                    completadas_completa = all(st.session_state.get(_key_est(estudiante_id, f"{prefijo_completa}_{i}_res")) is True for i in range(len(lista_completa)))
                    if completadas_completa:
                        k_balloons_todas = _key_est(estudiante_id, f"balloons_completa_todas_{letra_actual}")
                        if not st.session_state.get(k_balloons_todas):
                            st.balloons()
                            st.session_state[k_balloons_todas] = True
                        st.markdown(
                            """
                            <style>
                            @keyframes karaoke-reveal {
                                0% { background-size: 0% 100%; }
                                100% { background-size: 100% 100%; }
                            }
                            .mensaje-karaoke {
                                text-align: center; font-size: 1.5rem; font-weight: bold;
                                background: linear-gradient(90deg, #4CAF50 50%, #2e7d32 50%);
                                background-size: 0% 100%;
                                background-repeat: no-repeat;
                                -webkit-background-clip: text;
                                background-clip: text;
                                color: #1b5e20;
                                animation: karaoke-reveal 1.2s ease-out forwards;
                            }
                            </style>
                            <p class="mensaje-karaoke">¡Completaste todas las palabras! 🎉</p>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.write("")
                        if st.button(
                            "Ir a escucha y toca ➡️",
                            key=f"btn_siguiente_vocal_completa_{letra_actual}_{estudiante_id}",
                        ):
                            # Si venimos de V3, al cambiar a la fase final marcamos
                            # progreso de "inicio" para que el gating/progresión sea consistente.
                            if st.session_state.get("v3_letras_override"):
                                if vocal_fase_avance(estudiante_id, letra_actual) == "empieza":
                                    for _ in range(4):
                                        actualizar_progreso_silabico(estudiante_id, letra_actual, "VocalInicio", True)
                            st.session_state.pop(_key_est(estudiante_id, f"balloons_completa_todas_{letra_actual}"), None)
                            st.session_state[k_vocal_fase] = "termina"
                            for i in range(len(lista_completa)):
                                row_key_c = f"{prefijo_completa}_{i}"
                                st.session_state.pop(_key_est(estudiante_id, f"{row_key_c}_res"), None)
                                st.session_state.pop(_key_est(estudiante_id, f"{row_key_c}_slots"), None)
                                st.session_state.pop(_key_est(estudiante_id, f"{row_key_c}_used"), None)
                                st.session_state.pop(_key_est(estudiante_id, f"{row_key_c}_pool"), None)
                            st.session_state.pop(k_orden_completa, None)
                            st.rerun()
                lista_recursos = []  # no mostrar filas empieza/termina en fase completa
            elif vocal_fase == "presenta":
                # V3: presentación sin opciones (solo mostrar 9 palabras que comienzan con la vocal)
                if recursos:
                    st.markdown("### 📖 Leo con mis papás...")
                    palabras_presenta = recursos[:9]

                    # Matriz 3x3: usar las mismas tarjetas que consonantes ("Leo con mis papás")
                    # (reduce el tamaño y mantiene el mismo flujo de karaoke al hacer clic)
                    for row in range(3):
                        row_cols = st.columns(3)
                        for col_idx in range(3):
                            i = row * 3 + col_idx
                            if i >= len(palabras_presenta):
                                continue
                            r = palabras_presenta[i]
                            with row_cols[col_idx]:
                                img_path = (r.get("ruta_img") or "").strip()
                                palabra_r = (r.get("palabra") or "").strip()
                                if palabra_r:
                                    render_album_card_karaoke(
                                        img_path,
                                        palabra_r,
                                        unique_id=f"v3_presenta_card_{letra_actual}_{i}",
                                        size="normal",
                                        show_label_below=True,
                                    )

                    st.write("")

                    # Frases mágicas (mismo bloque que consonantes)
                    frases_plantillas = []  # En vocales al inicio omitimos frases mágicas
                    if frases_plantillas:
                        st.markdown("### ✨ Frases mágicas")
                        perfil = _cached_perfil(estudiante_id)
                        nombre_nino = (st.session_state.get("nombre_nino") or (perfil[2] if perfil and len(perfil) > 2 else "")) if perfil else st.session_state.get("nombre_nino", "")
                        nombre_mama_raw = (perfil[7] if perfil and len(perfil) > 7 else "") or ""
                        mama_display = f"Mamá {(nombre_mama_raw or '').strip()}" if (nombre_mama_raw or "").strip() else "mamá"
                        frases_render = []
                        for tpl in frases_plantillas:
                            try:
                                f = tpl.format(nombre=nombre_nino or "Yo", mama=mama_display)
                            except KeyError:
                                f = tpl.replace("{nombre}", nombre_nino or "Yo").replace("{mama}", mama_display)
                            frases_render.append(f)
                        frases_render = frases_render[:3]

                        k_frase_idx = _key_est(estudiante_id, f"vocal_frase_idx_{letra_actual}")
                        frase_idx_actual = st.session_state.get(k_frase_idx)
                        cols_frase = st.columns(3)
                        for i, frase in enumerate(frases_render):
                            with cols_frase[i]:
                                if frase_idx_actual == i:
                                    k_audio_frase = _key_est(estudiante_id, f"audio_vocal_frase_{letra_actual}_{i}")
                                    if k_audio_frase not in st.session_state:
                                        st.session_state[k_audio_frase] = speech_engine.generar_audio(frase)
                                    audio_frase = st.session_state[k_audio_frase]
                                    render_frase_karaoke(
                                        frase,
                                        audio_path=audio_frase,
                                        unique_id=f"vocal_frase_{letra_actual}_{i}",
                                    )
                                    if st.button("Cerrar", key=f"cerrar_vocal_frase_{letra_actual}_{i}"):
                                        st.session_state.pop(k_frase_idx, None)
                                        st.rerun()
                                else:
                                    if st.button(f'"{frase}"', key=f"vocal_frase_btn_{letra_actual}_{i}", use_container_width=True):
                                        st.session_state[k_frase_idx] = i
                                        st.rerun()

                if st.button("Continuar a completar palabras ✏️", key=f"btn_v3_presenta_{letra_actual}"):
                    st.session_state[k_vocal_fase] = "completa"
                    st.rerun()
            elif vocal_fase == "empieza":
                lista_actual = [dict(r, vocal_correcta=letra_actual.upper(), es_vocal_actual=True) for r in recursos[:9]]
                lista_sig = []
                prefijo = f"vocal_{letra_actual}"
                lista_recursos = _construir_lista_estable(prefijo, lista_actual, lista_sig)
                indices_vocal_actual = [i for i, r in enumerate(lista_recursos) if r.get("es_vocal_actual", True)]
            else:
                recursos_terminan = _cached_recursos_terminan(estudiante_id, letra_actual, 9)
                if not recursos_terminan:
                    st.info(f"No hay palabras que terminen con **{letra_actual}** en el álbum ni en la biblioteca. Puedes pasar a la siguiente vocal.")
                    if st.button("¡Siguiente vocal! ➡️", key="btn_siguiente_vocal_skip"):
                        st.session_state[k_vocal_fase] = "presenta" if st.session_state.get("v3_letras_override") else "empieza"
                        st.session_state[k_indice] = (st.session_state[k_indice] + 1) % len(letras_disponibles)
                        st.session_state.pop(_key_est(estudiante_id, f"vocal_orden_{letra_actual}"), None)
                        st.rerun()
                    lista_recursos = []
                    indices_vocal_actual = []
                else:
                    lista_actual = [dict(r, vocal_correcta=letra_actual.upper(), es_vocal_actual=True) for r in recursos_terminan[:9]]
                    lista_sig = []
                    prefijo = f"vocal_termina_{letra_actual}"
                    lista_recursos = _construir_lista_estable(prefijo, lista_actual, lista_sig)
                    indices_vocal_actual = [i for i, r in enumerate(lista_recursos) if r.get("es_vocal_actual", True)]

            if lista_recursos:
                for i, r in enumerate(lista_recursos):
                    row_key = f"{prefijo}_{i}"
                    res = st.session_state.get(_key_est(estudiante_id, f"{row_key}_res"))

                    img_col, instr_col, opts_col = st.columns([1.1, 0.5, 2.2])
                    with img_col:
                        _render_escucha_atencion(color_fav)
                        audio_path = speech_engine.generar_audio(r["palabra"])
                        pal_disp = palabra_para_display(r["palabra"]) or (r.get("palabra") or "").strip()
                        if res is True:
                            # Tras acertar: imagen + karaoke + el polaroid permite volver a oír la palabra
                            st.balloons()
                            render_polaroid_click_to_play(
                                r["ruta_img"],
                                texto_tts=r["palabra"],
                                audio_path=audio_path,
                                es_acierto=True,
                                mostrar_top_pct=80,
                                width_pct=100,
                                max_width_px=card_max_w,
                                height_px=card_h_row,
                            )
                            render_palabra_karaoke_felicitacion(
                                pal_disp,
                                unique_id=f"vocal_escucha_ok_{prefijo}_{i}_{estudiante_id}",
                            )
                        else:
                            # Escucha y toca: sin imagen; solo la palabra (texto) + botón para escuchar
                            if st.button(
                                "▶️ Escuchar la palabra",
                                key=f"vocal_escucha_audio_{prefijo}_{i}_{estudiante_id}",
                                use_container_width=True,
                            ):
                                if audio_path and os.path.isfile(audio_path):
                                    try:
                                        with open(audio_path, "rb") as f:
                                            _autoplay_audio_bytes(f.read(), mime="audio/mpeg")
                                    except Exception:
                                        pass
                            st.markdown(
                                f"""
                                <div style="
                                    font-size: 2rem;
                                    font-weight: 800;
                                    text-align: center;
                                    color: #1a1a2e;
                                    padding: 20px 16px;
                                    border: 2px dashed #bdbdbd;
                                    border-radius: 16px;
                                    background: linear-gradient(180deg, #fafafa 0%, #f0f0f0 100%);
                                    min-height: 120px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                ">{pal_disp}</div>
                                """,
                                unsafe_allow_html=True,
                            )
                    with instr_col:
                        if res is True:
                            st.success("¡Bien!")
                            # Reproducir palabra y remarcar por qué es correcta (empieza/termina con la vocal)
                            if (st.session_state.get("_reproducir_prefijo") == prefijo and
                                st.session_state.get("_reproducir_i") == i):
                                palabra_rep = st.session_state.get("_reproducir_palabra", r["palabra"])
                                vocal_rep = st.session_state.get("_reproducir_vocal", r["vocal_correcta"])
                                empieza = st.session_state.get("_reproducir_empieza", vocal_fase == "empieza")
                                if empieza:
                                    frase_rep = f"¡Correcto! {palabra_rep} empieza con {vocal_rep}"
                                    st.markdown(
                                        f"<p style='font-size: 1rem; font-weight: bold; color: #2e7d32;'>"
                                        f"¡Correcto! <strong>{palabra_rep}</strong> empieza con <strong>{vocal_rep}</strong></p>",
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    frase_rep = f"¡Correcto! {palabra_rep} termina en {vocal_rep}"
                                    st.markdown(
                                        f"<p style='font-size: 1rem; font-weight: bold; color: #2e7d32;'>"
                                        f"¡Correcto! <strong>{palabra_rep}</strong> termina en <strong>{vocal_rep}</strong></p>",
                                        unsafe_allow_html=True,
                                    )
                                audio_path_rep = speech_engine.generar_audio(frase_rep)
                                if audio_path_rep:
                                    try:
                                        with open(audio_path_rep, "rb") as f:
                                            _autoplay_audio_bytes(f.read(), mime="audio/mpeg")
                                    except Exception:
                                        pass
                                st.session_state.pop("_reproducir_prefijo", None)
                                st.session_state.pop("_reproducir_i", None)
                                st.session_state.pop("_reproducir_palabra", None)
                                st.session_state.pop("_reproducir_vocal", None)
                                st.session_state.pop("_reproducir_empieza", None)
                        elif res is False:
                            st.error("Intenta otra vez")
                    with opts_col:
                        _render_opciones_vocales(row_key, r["vocal_correcta"], r.get("es_vocal_actual", True), r["palabra"], i)
                    st.write("---")

                completadas = all(st.session_state.get(_key_est(estudiante_id, f"{prefijo}_{i}_res")) is True for i in indices_vocal_actual)
                if completadas:
                    st.balloons()
                    if vocal_fase == "empieza":
                        st.markdown(
                            "<p style='text-align: center; font-size: 1.5rem; font-weight: bold; color: #2e7d32;'>"
                            "¡Completaste las palabras que comienzan con la letra! 🎉</p>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<p style='text-align: center; font-size: 1.5rem; font-weight: bold; color: #2e7d32;'>"
                            "¡Completaste las palabras que terminan con la letra! 🎉</p>",
                            unsafe_allow_html=True,
                        )
                    st.write("")
                    if vocal_fase == "empieza":
                        if st.button("Completar palabras ✏️", key="btn_continuar_termina"):
                            st.session_state[k_vocal_fase] = "completa"
                            st.rerun()
                    else:
                        st.caption("¡Excelente! Ya completaste escucha y toca. Puedes pasar a la siguiente vocal.")
                        if st.button("¡Siguiente vocal! ➡️", key="btn_ir_completa"):
                            st.session_state[k_vocal_fase] = "presenta" if st.session_state.get("v3_letras_override") else "empieza"
                            st.session_state[k_indice] = (st.session_state[k_indice] + 1) % len(letras_disponibles)
                            st.session_state.pop(_key_est(estudiante_id, f"vocal_orden_{letra_actual}"), None)
                            st.rerun()

        # --- CONSONANTES: flujo mejorado (sílabas + Vamos a leer + Frases mágicas) o flujo clásico ---
        else:
            silabas_letra = Curriculum.SILABAS_POR_CONSONANTE.get(letra_actual.upper())
            frases_plantillas = Curriculum.FRASES_MAGICAS.get(letra_actual.upper(), [])

            if silabas_letra:
                color_fav = st.session_state.get("color_favorito", "#4A90E2")
                # ----- Motivos (fondo) e Imprimir lección -----
                if not usar_hdr_3:
                    fondos_list = AssetManager.obtener_fondos_abecedario()
                    opciones_fondo = ["Sin motivo"] + [f.get("nombre", "Fondo") for f in fondos_list]
                    k_fondo = _key_est(estudiante_id, "leccion_fondo_idx")
                    if k_fondo not in st.session_state:
                        st.session_state[k_fondo] = 0
                    idx_fondo = st.session_state[k_fondo]
                    fondo_ruta = ""
                    if idx_fondo > 0 and fondos_list and idx_fondo <= len(fondos_list):
                        fondo_ruta = fondos_list[idx_fondo - 1].get("ruta", "") or ""

                    if fondo_ruta and os.path.isfile(fondo_ruta):
                        try:
                            b64_fondo = _cached_fondo_b64(fondo_ruta)
                            mime_fondo = "image/png" if fondo_ruta.lower().endswith(".png") else "image/jpeg"
                            st.markdown(
                                f"""
                                <style>
                                [data-testid="stAppViewContainer"] {{
                                    background-image: url("data:{mime_fondo};base64,{b64_fondo}");
                                    background-size: cover;
                                    background-position: center;
                                    background-attachment: fixed;
                                }}
                                [data-testid="stAppViewContainer"]::before {{
                                    content: "";
                                    position: fixed;
                                    top: 0; left: 0; right: 0; bottom: 0;
                                    background: rgba(255, 255, 255, 0.78);
                                    pointer-events: none;
                                    z-index: 0;
                                }}
                                [data-testid="stAppViewContainer"] > section {{ position: relative; z-index: 1; }}
                                </style>
                                """,
                                unsafe_allow_html=True,
                            )
                        except Exception:
                            pass

                k_paso = _key_est(estudiante_id, f"leccion_consonant_paso_{letra_actual}")

                if st.session_state[k_paso] == "principal":
                    if not usar_hdr_3:
                        col_motivos, col_imprimir, _ = st.columns([1.2, 1, 1])
                        with col_motivos:
                            _render_leccion_motivo_select(estudiante_id, opciones_fondo, k_fondo)
                        with col_imprimir:
                            _render_leccion_pdf_bloque(
                                estudiante_id, letra_actual, silabas_letra, color_fav, fondos_list, k_fondo
                            )
                    st.write("")

                    # ----- Encabezado: M m a un lado + matriz 3x3 con sílabas en (1,1), (1,3), (2,2), (3,1), (3,3); misma altura -----
                    ALTURA_LETRA = 260
                    k_orden_sil = _key_est(estudiante_id, f"consonant_silabas_{letra_actual}")
                    if k_orden_sil not in st.session_state or len(st.session_state[k_orden_sil]) != len(silabas_letra):
                        st.session_state[k_orden_sil] = random.sample(silabas_letra, len(silabas_letra))
                    silabas_mostrar = st.session_state[k_orden_sil]
                    col_letra, col_matriz = st.columns([1, 1.4])
                    with col_letra:
                        st.markdown(
                            f"""
                            <div style="
                                display: flex; align-items: center; justify-content: center;
                                min-height: {ALTURA_LETRA}px;
                                background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
                                border: 2px solid #e0e0e0;
                                border-radius: 20px;
                                padding: 1rem;
                                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                            ">
                                <span style="font-size: 4.2rem; font-weight: 800; color: #c62828;">{letra_actual.upper()}</span>
                                <span style="font-size: 4.2rem; font-weight: 800; color: #c62828;"> {letra_actual.lower()}</span>
                            </div>
                            <p style="text-align: center; margin: 0.25rem 0 0 0; font-size: 0.9rem; color: #666;">Toca cada sílaba en la matriz</p>
                            """,
                            unsafe_allow_html=True,
                        )
                    with col_matriz:
                        render_silabas_matriz_9x9(silabas_mostrar, color_hex=color_fav, unique_id=f"matriz_{letra_actual}", altura_minima=ALTURA_LETRA)
                    st.write("")

                    # ----- Leo con mis papás...: 9 palabras; karaoke sobre la imagen (clic oculta imagen y muestra karaoke) -----
                    st.markdown("### 📖 Leo con mis papás...")
                    recursos_lectura = _cached_recursos(estudiante_id, letra_actual, 9)
                    if recursos_lectura:
                        # Grid 3 columnas x 3 filas (9 palabras)
                        for fila in range(0, len(recursos_lectura), 3):
                            cols_cards = st.columns(3)
                            for c, idx in enumerate(range(fila, min(fila + 3, len(recursos_lectura)))):
                                r = recursos_lectura[idx]
                                palabra_r = (r.get("palabra") or "").strip()
                                img_path = r.get("ruta_img")
                                with cols_cards[c]:
                                    # Tarjeta: al hacer clic en la imagen se oculta y se muestra el karaoke en su lugar
                                    render_album_card_karaoke(
                                        img_path,
                                        palabra_r,
                                        unique_id=f"leccion_{letra_actual}_{idx}",
                                        size="normal",
                                        show_label_below=True,
                                    )
                            st.write("")
                    else:
                        st.caption(f"No hay palabras para la letra **{letra_actual}** en el álbum ni en la biblioteca.")

                    st.write("---")

                    # ----- Frases mágicas: karaoke en la misma columna que la oración -----
                    if frases_plantillas:
                        st.markdown("### ✨ Frases mágicas")
                        perfil = _cached_perfil(estudiante_id)
                        nombre_nino = (st.session_state.get("nombre_nino") or (perfil[2] if perfil and len(perfil) > 2 else "")) if perfil else st.session_state.get("nombre_nino", "")
                        nombre_mama_raw = (perfil[7] if perfil and len(perfil) > 7 else "") or ""
                        mama_display = f"Mamá {(nombre_mama_raw or '').strip()}" if (nombre_mama_raw or "").strip() else "mamá"
                        frases_render = []
                        for tpl in frases_plantillas:
                            try:
                                f = tpl.format(nombre=nombre_nino or "Yo", mama=mama_display)
                            except KeyError:
                                f = tpl.replace("{nombre}", nombre_nino or "Yo").replace("{mama}", mama_display)
                            frases_render.append(f)

                        k_frase_idx = _key_est(estudiante_id, "leccion_frase_idx")
                        frase_idx_actual = st.session_state.get(k_frase_idx)
                        cols_frase = st.columns(3)
                        for i, frase in enumerate(frases_render):
                            with cols_frase[i]:
                                if frase_idx_actual == i:
                                    # Karaoke: reutilizar audio en session_state para no regenerar en cada rerun
                                    k_audio_frase = _key_est(estudiante_id, f"audio_frase_{letra_actual}_{i}")
                                    if k_audio_frase not in st.session_state:
                                        st.session_state[k_audio_frase] = speech_engine.generar_audio(frase)
                                    audio_frase = st.session_state[k_audio_frase]
                                    render_frase_karaoke(frase, audio_path=audio_frase, unique_id=f"frase_{letra_actual}_{i}")
                                    if st.button("Cerrar", key=f"cerrar_frase_{letra_actual}_{i}"):
                                        st.session_state.pop(k_frase_idx, None)
                                        st.rerun()
                                else:
                                    if st.button(f'"{frase}"', key=f"frase_m_{letra_actual}_{i}", use_container_width=True):
                                        st.session_state[k_frase_idx] = i
                                        st.rerun()

                    st.write("---")
                    # Dos actividades "armar palabras" antes de ir a la siguiente letra
                    if st.button("Continuar a la actividad ➡️", key="btn_ir_actividad_armar"):
                        _set_paso_consonante(estudiante_id, letra_actual, "actividad_armar_1")
                        st.session_state.pop(_key_est(estudiante_id, f"armar_idx_actividad_armar_1_{letra_actual}"), None)
                        st.session_state.pop(_key_est(estudiante_id, f"armar_idx_actividad_armar_2_{letra_actual}"), None)
                        st.rerun()
                else:
                    paso_actual = st.session_state[k_paso]

                    # Actividades de construcción de palabras (1 y 2)
                    if paso_actual in ("actividad_armar_1", "actividad_armar_2"):
                        recursos_act = _cached_recursos(estudiante_id, letra_actual, 15)
                        titulo_act = "Actividad 1: Arma la palabra" if paso_actual == "actividad_armar_1" else "Actividad 2: Arma la palabra"
                        st.markdown(f"### 🧩 {titulo_act}")
                        st.caption("Elige dos sílabas para formar la palabra. Hay una sílaba que no necesitas.")
                        if paso_actual == "actividad_armar_1":
                            k_lista = _key_est(estudiante_id, f"armar_lista_1_{letra_actual}")
                            if k_lista not in st.session_state:
                                st.session_state[k_lista] = _construir_palabras_armar(recursos_act, silabas_letra, cantidad=6)
                            palabras_act = st.session_state[k_lista]
                        else:
                            k_lista = _key_est(estudiante_id, f"armar_lista_2_{letra_actual}")
                            if k_lista not in st.session_state:
                                # Segunda actividad: otras 6 palabras (evitar repetir las de la lista 1)
                                lista1 = st.session_state.get(_key_est(estudiante_id, f"armar_lista_1_{letra_actual}"), [])
                                ya_usadas = {p["palabra"].upper() for p in lista1}
                                candidatos = [r for r in (recursos_act or []) if (r.get("palabra") or "").strip().upper() not in ya_usadas]
                                st.session_state[k_lista] = _construir_palabras_armar(candidatos, silabas_letra, cantidad=6)
                            palabras_act = st.session_state[k_lista]

                        def ir_siguiente():
                            if paso_actual == "actividad_armar_1":
                                _set_paso_consonante(estudiante_id, letra_actual, "actividad_armar_2")
                                st.session_state.pop(_key_est(estudiante_id, f"armar_idx_actividad_armar_2_{letra_actual}"), None)
                            else:
                                # Después de la segunda actividad de armar palabras, pasamos a Escucha y Toca (palabras)
                                _set_paso_consonante(estudiante_id, letra_actual, "escucha_palabras")
                                # Limpiar estado de actividades de armado
                                for k in list(st.session_state.keys()):
                                    if isinstance(k, str) and f"armar_" in k and letra_actual in k:
                                        st.session_state.pop(k, None)

                        _render_actividad_armar_palabras(
                            palabras_act, letra_actual, estudiante_id, color_fav, paso_actual, ir_siguiente
                        )

                        if paso_actual == "actividad_armar_1":
                            if st.button("Siguiente actividad ➡️", key="btn_siguiente_actividad"):
                                _set_paso_consonante(estudiante_id, letra_actual, "actividad_armar_2")
                                st.session_state.pop(_key_est(estudiante_id, f"armar_idx_actividad_armar_2_{letra_actual}"), None)
                                st.rerun()
                        else:
                            if st.button("Escucha y toca ➡️", key="btn_ir_escucha_palabras"):
                                _set_paso_consonante(estudiante_id, letra_actual, "escucha_palabras")
                                for k in list(st.session_state.keys()):
                                    if isinstance(k, str) and f"armar_" in k and letra_actual in k:
                                        st.session_state.pop(k, None)
                                st.rerun()

                    # Actividades de escucha: primero palabras, luego frases
                    elif paso_actual == "escucha_palabras":
                        recursos_act = _cached_recursos(estudiante_id, letra_actual, 20)
                        k_items = _key_est(estudiante_id, f"escucha_palabras_items_{letra_actual}")
                        if k_items not in st.session_state:
                            st.session_state[k_items] = _construir_items_escucha_palabras(recursos_act, cantidad=6)
                        items = st.session_state[k_items]

                        def ir_siguiente_escucha_palabras():
                            _set_paso_consonante(estudiante_id, letra_actual, "escucha_frases")
                            st.rerun()

                        _render_actividad_escucha_opciones(
                            items,
                            paso_actual="escucha_palabras",
                            estudiante_id=estudiante_id,
                            letra_actual=letra_actual,
                            on_siguiente=ir_siguiente_escucha_palabras,
                            titulo="Escucha y toca la palabra",
                        )

                        if st.button("Pasar a frases ➡️", key="btn_ir_escucha_frases_manual"):
                            ir_siguiente_escucha_palabras()

                    elif paso_actual == "escucha_frases":
                        k_items_f = _key_est(estudiante_id, f"escucha_frases_items_{letra_actual}")
                        if k_items_f not in st.session_state:
                            st.session_state[k_items_f] = _construir_items_escucha_frases(letra_actual, estudiante_id)
                        items_f = st.session_state[k_items_f]

                        def ir_siguiente_escucha_frases():
                            # Termina toda la secuencia de actividades para esta consonante
                            _set_paso_consonante(estudiante_id, letra_actual, "principal")
                            st.session_state[k_indice] = (st.session_state[k_indice] + 1) % len(letras_disponibles)
                            # k_orden_sil solo existe en algunas ramas; usar la key derivada
                            # evita NameError cuando venimos desde el flujo "escucha_frases".
                            st.session_state.pop(_key_est(estudiante_id, f"consonant_silabas_{letra_actual}"), None)
                            st.session_state.pop(_key_est(estudiante_id, "leccion_frase_idx"), None)
                            st.session_state.pop(_key_est(estudiante_id, "leccion_pdf_bytes"), None)
                            # Limpiar estado de actividades de escucha para esta letra
                            for k in list(st.session_state.keys()):
                                if isinstance(k, str) and (f"escucha_" in k) and letra_actual in k:
                                    st.session_state.pop(k, None)
                            st.rerun()

                        _render_actividad_escucha_opciones(
                            items_f,
                            paso_actual="escucha_frases",
                            estudiante_id=estudiante_id,
                            letra_actual=letra_actual,
                            on_siguiente=ir_siguiente_escucha_frases,
                            titulo="Escucha y toca la frase",
                        )

                        if st.button("¡Siguiente letra! ➡️", key="btn_siguiente_consonant"):
                            ir_siguiente_escucha_frases()
            else:
                # Flujo clásico: una palabra + selector de sílaba (cuando no hay silabas_letra para esta consonante)
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    _color = st.session_state.get("color_favorito", "#4A90E2")
                    st.markdown(
                        f"""
                        <div style="
                            font-size: 1.75rem;
                            font-weight: 800;
                            color: #1a1a2e;
                            background: linear-gradient(135deg, {_color}22 0%, {_color}44 100%);
                            border: 3px solid {_color};
                            border-radius: 16px;
                            padding: 14px 20px;
                            text-align: center;
                            margin-bottom: 12px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        ">
                            ¡Escucha con atención!
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    audio_path = speech_engine.generar_audio(recurso["palabra"])
                    render_polaroid_click_to_play(
                        recurso["ruta_img"],
                        texto_tts=recurso["palabra"],
                        audio_path=audio_path,
                        es_acierto=st.session_state.get(_key_est(estudiante_id, "ultimo_resultado")),
                        mostrar_top_pct=80,
                        width_pct=100,
                        max_width_px=card_max_w,
                        height_px=card_h,
                    )
                with col2:
                    palabra_separada = segmentar_palabra(recurso["palabra"])
                    st.write("---")
                    silaba_correcta = palabra_separada[0]
                    opciones = [silaba_correcta, "BA", "TE"]
                    resultado = render_selector_silaba(opciones, silaba_correcta)
                    if resultado is not None:
                        actualizar_progreso_silabico(estudiante_id, letra_actual, "Directa", resultado)
                        # Evento 2.4: superar lección individual (por letra)
                        # Se evalúa con progreso acumulado en 'progreso_lecciones'.
                        gamificacion.check_and_grant_letter_mastery(estudiante_id, letra_actual)
                        st.session_state[_key_est(estudiante_id, "ultimo_resultado")] = resultado
                        if resultado:
                            st.balloons()
                            if st.button("¡Siguiente letra! ➡️"):
                                st.session_state[k_indice] = (st.session_state[k_indice] + 1) % len(letras_disponibles)
                                st.session_state.pop(_key_est(estudiante_id, "ultimo_resultado"), None)
                                st.rerun()
                        else:
                            st.error("¡Casi! Inténtalo de nuevo.")

    else:
        # Si no hay foto personal ni genérica para esa letra
        st.warning(f"No tenemos fotos para la letra '{letra_actual}'.")
        if st.button("Saltar letra"):
            st.session_state[k_indice] = (st.session_state[k_indice] + 1) % len(letras_disponibles)
            st.rerun()

    # Botón flotante para salir
    if st.button("🔙 Salir de la lección", key="btn_salir"):
        st.session_state.pagina_activa = 'hub_nino'
        st.rerun()