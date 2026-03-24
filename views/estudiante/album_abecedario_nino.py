"""
Mi abecedario: el estudiante elige 2 imágenes por letra (de hasta 6 opciones) para construir su abecedario.
Al seleccionar 2 imágenes se muestra la letra entre ambas; clic en cualquier imagen activa el efecto karaoke.
"""
import os
import re
import time
import json
import streamlit as st
from database.db_queries import (
    guardar_abecedario_letra,
    obtener_abecedario_estudiante,
    obtener_avatar_estudiante,
    obtener_album_nino,
    obtener_perfil_completo_nino,
    pdf_job_crear,
    pdf_job_obtener,
)
from core.asset_manager import AssetManager
from components.cards import render_album_card_karaoke, get_image_base64

try:
    from core.abecedario_pdf import generar_pdf_abecedario
    from core.pdf_jobs import ejecutar_job_en_background
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False
    ejecutar_job_en_background = None


MAX_OPCIONES_POR_LETRA = 6
ELEGIR_POR_LETRA = 2


def _foto_estudiante_abecedario(estudiante_id: int, nombre: str) -> str:
    """Ruta de la foto del estudiante para la portada: avatar_path o foto del álbum con palabra = nombre."""
    avatar = obtener_avatar_estudiante(estudiante_id)
    if avatar and os.path.isfile(avatar):
        return avatar
    album = obtener_album_nino(estudiante_id) or []
    nombre_upper = (nombre or "").strip().split()[0] if (nombre or "").strip() else ""
    nombre_upper = nombre_upper.upper()
    for palabra, _cat, img_path in album:
        if img_path and os.path.isfile(img_path) and (palabra or "").strip().upper() == nombre_upper:
            return img_path
    return ""


def _inject_libro_css(color_fav: str, fondo_data_url: str = ""):
    """Estilos de libro infantil; opcional fondo como fondo de la portada (página con la foto)."""
    bg_css = ""
    if fondo_data_url:
        # Fondo visible en toda la portada (página donde está la foto del estudiante)
        bg_css = (
            ".libro-portada { background-image: url(" + fondo_data_url + "); "
            "background-size: cover; background-position: center; background-repeat: no-repeat; "
            "min-height: 380px; position: relative; } "
            ".libro-portada::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; "
            "background: rgba(253, 252, 250, 0.75); border-radius: 4px; pointer-events: none; } "
            ".libro-portada > * { position: relative; z-index: 1; } "
            ".libro-container { padding: 0.5rem 0; } "
            ".libro-spread { background: rgba(253, 252, 250, 0.95); } "
        )
    st.markdown(
        f"""
        <style>
        .libro-container {{ max-width: 880px; margin: 0 auto; font-family: 'Segoe UI', 'Georgia', system-ui, serif; }}
        {bg_css}
        .libro-portada {{ border-radius: 4px; padding: 2rem 2rem 1.5rem; margin-bottom: 0; box-shadow: 0 2px 2px rgba(0,0,0,0.04); background: linear-gradient(165deg, #faf7f2 0%, #f5efe6 50%, #faf7f2 100%); }}
        .libro-portada-foto {{ width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 4px solid {color_fav}; margin: 0 auto 1rem; display: block; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .libro-titulo {{ text-align: center; font-size: 1.85rem; font-weight: 800; color: {color_fav}; letter-spacing: 0.03em; margin: 0 0 0.2rem 0; }}
        .libro-subtitulo {{ text-align: center; color: #6b5b4f; font-size: 0.95rem; margin: 0 0 0.8rem 0; }}
        .libro-parrafo-intro {{ text-align: center; color: #7a6a5a; font-size: 0.9rem; margin: 0 0 1.4rem 0; max-width: 720px; margin-left: auto; margin-right: auto; line-height: 1.4; }}
        .libro-aviso-legal {{ text-align: justify; color: #6b5b4f; font-size: 0.7rem; margin: 1.2rem 0 0 0; max-width: 720px; margin-left: auto; margin-right: auto; line-height: 1.35; }}
        .libro-progress {{ text-align: center; margin: 1rem 0; font-size: 0.9rem; color: #6b5b4f; }}
        .libro-spread {{ display: flex; align-items: stretch; min-height: 220px; margin-bottom: 24px; background: #fdfcfa; border-radius: 4px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); overflow: hidden; break-inside: avoid; border: 1px solid #e8e2da; }}
        .libro-spread-letra-centro {{ display: flex; align-items: stretch; }}
        .libro-spread-letra-centro .libro-pagina {{ flex: 1; min-width: 0; }}
        .libro-spread-letra-centro .libro-pagina-centro-letra {{ flex: 0 0 auto; width: 100px; display: flex; align-items: center; justify-content: center; background: linear-gradient(180deg, {color_fav}18 0%, {color_fav}28 100%); border-left: 1px solid #e8e2da; border-right: 1px solid #e8e2da; }}
        .libro-pagina {{ flex: 1; padding: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: #fdfcfa; position: relative; }}
        .libro-pagina-izq {{ border-right: none; }}
        .libro-spread:not(.libro-spread-letra-centro) .libro-pagina-izq {{ border-right: 1px solid #e8e2da; }}
        .libro-spine {{ width: 8px; background: linear-gradient(90deg, #e8e2da 0%, #d4ccc2 50%, #e8e2da 100%); flex-shrink: 0; }}
        .libro-letra {{ font-size: 4.5rem; font-weight: 900; line-height: 1; color: {color_fav}; text-shadow: 2px 2px 0 rgba(0,0,0,0.06); margin-bottom: 12px; font-family: Georgia, 'Times New Roman', serif; }}
        .libro-letra-placeholder {{ color: #c4b9a8; }}
        .libro-imagen-y-palabra {{ display: inline-flex; flex-direction: column; align-items: center; width: 100%; max-width: 200px; }}
        .libro-ilustracion {{ width: 100%; max-width: 200px; max-height: 180px; border-radius: 12px; object-fit: cover; box-shadow: 0 3px 12px rgba(0,0,0,0.1); }}
        .libro-ilustracion-placeholder {{ width: 100%; max-width: 200px; height: 160px; background: linear-gradient(145deg, #f0ebe4 0%, #e8e2da 100%); border: 2px dashed #c4b9a8; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #a89888; font-size: 0.85rem; text-align: center; padding: 12px; }}
        .libro-palabra {{ font-size: 1.05rem; font-weight: 700; color: #3d3630; margin-top: 10px; text-align: center; line-height: 1.2; width: 100%; }}
        .libro-palabra-placeholder {{ color: #a89888; font-weight: 500; }}
        .libro-print-hint {{ text-align: center; font-size: 0.8rem; color: #9a8f82; margin-top: 1.5rem; }}
        @media print {{
            .no-print {{ display: none !important; }}
            .libro-container {{ max-width: 100%; }}
            .libro-spread {{ box-shadow: none; border: 1px solid #ddd; page-break-inside: avoid; }}
            .libro-portada {{ box-shadow: none; }}
            body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _build_spread_html(letra: str, par: list, color_fav: str) -> str:
    """Construye el HTML de una doble página: letra en el centro, misma altura que las 2 imágenes."""
    completo = par and len(par) == 2
    letra_cls = "libro-letra" if completo else "libro-letra libro-letra-placeholder"
    if completo:
        pal1 = (par[0].get("palabra") or "?").strip()
        pal2 = (par[1].get("palabra") or "?").strip()
        ruta1 = par[0].get("ruta_img") or ""
        ruta2 = par[1].get("ruta_img") or ""
        img1_b64 = get_image_base64(ruta1) if ruta1 else None
        img2_b64 = get_image_base64(ruta2) if ruta2 else None
        img1_src = f'data:image/png;base64,{img1_b64}' if img1_b64 else ""
        img2_src = f'data:image/png;base64,{img2_b64}' if img2_b64 else ""
        img1 = f'<img class="libro-ilustracion" src="{img1_src}" alt="{pal1}">' if img1_src else f'<div class="libro-ilustracion-placeholder">Sin imagen</div>'
        img2 = f'<img class="libro-ilustracion" src="{img2_src}" alt="{pal2}">' if img2_src else f'<div class="libro-ilustracion-placeholder">Sin imagen</div>'
        cap1 = f'<div class="libro-palabra">{pal1}</div>'
        cap2 = f'<div class="libro-palabra">{pal2}</div>'
    else:
        img1 = '<div class="libro-ilustracion-placeholder">Elige tu primera imagen</div>'
        img2 = '<div class="libro-ilustracion-placeholder">Elige tu segunda imagen</div>'
        cap1 = '<div class="libro-palabra libro-palabra-placeholder">—</div>'
        cap2 = '<div class="libro-palabra libro-palabra-placeholder">—</div>'
    # Letra en el centro; cada imagen con su palabra en bloque centrado
    return f"""
    <div class="libro-spread libro-spread-letra-centro">
        <div class="libro-pagina libro-pagina-izq">
            <div class="libro-imagen-y-palabra">{img1}{cap1}</div>
        </div>
        <div class="libro-spine"></div>
        <div class="libro-pagina libro-pagina-centro-letra">
            <div class="{letra_cls}">{letra}</div>
        </div>
        <div class="libro-spine"></div>
        <div class="libro-pagina">
            <div class="libro-imagen-y-palabra">{img2}{cap2}</div>
        </div>
    </div>
    """


def _render_estado_abecedario(letras_disponibles, abecedario_guardado, color_fav, nombre="Explorador", foto_ruta="", fondo_ruta=None, nombre_portada=None, nombre_reconozca=None):
    """Muestra el abecedario como libro en construcción: cada letra es una doble página (spread)."""
    nombre_portada = nombre_portada or nombre
    nombre_reconozca = nombre_reconozca or (nombre or "Explorador").strip().split()[0] if (nombre or "").strip() else "el niño"
    total = len(letras_disponibles)
    completas = sum(1 for letra in letras_disponibles if len(abecedario_guardado.get(letra, [])) == 2)

    fondo_data = ""
    if fondo_ruta:
        b64 = get_image_base64(fondo_ruta)
        if b64:
            ext = "png" if (fondo_ruta or "").lower().endswith(".png") else "jpeg"
            fondo_data = f"data:image/{ext};base64,{b64}"
    _inject_libro_css(color_fav, fondo_data)

    foto_html = ""
    if foto_ruta:
        b64 = get_image_base64(foto_ruta)
        if b64:
            ext = "png" if (foto_ruta or "").lower().endswith(".png") else "jpeg"
            foto_html = f'<img class="libro-portada-foto" src="data:image/{ext};base64,{b64}" alt="Foto de {nombre}">'

    spreads = []
    for letra in letras_disponibles:
        par = abecedario_guardado.get(letra, [])
        spreads.append(_build_spread_html(letra, par, color_fav))

    st.markdown(
        f"""
        <div class="libro-container">
        <div class="libro-portada">
            {foto_html}
            <h1 class="libro-titulo">Mi abecedario</h1>
            <p class="libro-subtitulo">Libro de {nombre_portada}</p>
            <p class="libro-parrafo-intro">
                Este abecedario ha sido creado especialmente para {nombre_portada}, integrando su mundo favorito con tecnología de Inteligencia Artificial.
                Diseñado como un complemento de Lee Conmigo IA, cada página busca que {nombre_reconozca} se reconozca como el héroe de su propio aprendizaje,
                facilitando la memorización a través de la emoción y el juego.
            </p>
            <p class="libro-aviso-legal">
                Los contenidos, ilustraciones y diseños presentados en este abecedario son propiedad intelectual de LeeConmigo IA y el ecosistema AprendeConNosotros IA.
                Este material ha sido creado con fines estrictamente educativos y personalizados, por lo que su distribución comercial, reproducción total o parcial por parte de editoriales o terceros, así como su alteración sin autorización expresa, queda prohibida.
                Los desarrolladores no se hacen responsables del uso indebido del material fuera del entorno pedagógico sugerido, ni de interpretaciones derivadas de los elementos gráficos generados por Inteligencia Artificial.
            </p>
            <p class="libro-progress">Tienes <strong>{completas}</strong> de <strong>{total}</strong> letras con sus ilustraciones. Las páginas en blanco esperan tus dibujos.</p>
        </div>
        {"".join(spreads)}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("💡 Imprime (Ctrl+P) para tener tu libro en papel.")
    st.write("")
    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        if st.button("✏️ Continuar eligiendo letras", use_container_width=True, key="estado_continuar"):
            st.session_state.pop("album_abecedario_ver_estado", None)
            st.rerun()
    with c2:
        if st.button("⬅️ Volver al Álbum", use_container_width=True, key="estado_volver_album"):
            st.session_state.pop("album_abecedario_ver_estado", None)
            st.session_state.pagina_activa = "album_nino"
            st.rerun()


def _render_abecedario_completo(estudiante_id, letras_disponibles, abecedario_guardado, color_fav, nombre="Explorador", foto_ruta="", fondo_ruta=None, nombre_portada=None, nombre_reconozca=None):
    """Muestra el abecedario completo: letra en el centro a la misma altura que las imágenes, con karaoke."""
    nombre_portada = nombre_portada or nombre
    nombre_reconozca = nombre_reconozca or (nombre or "Explorador").strip().split()[0] if (nombre or "").strip() else "el niño"
    fondo_data = ""
    if fondo_ruta:
        b64 = get_image_base64(fondo_ruta)
        if b64:
            ext = "png" if (fondo_ruta or "").lower().endswith(".png") else "jpeg"
            fondo_data = f"data:image/{ext};base64,{b64}"
    _inject_libro_css(color_fav, fondo_data)
    altura_letra_px = 380  # mismo alto que tarjeta karaoke "large"

    foto_html = ""
    if foto_ruta:
        b64 = get_image_base64(foto_ruta)
        if b64:
            ext = "png" if (foto_ruta or "").lower().endswith(".png") else "jpeg"
            foto_html = f'<img class="libro-portada-foto" src="data:image/{ext};base64,{b64}" alt="Foto de {nombre}">'

    st.markdown(
        f"""
        <div class="libro-container">
        <div class="libro-portada">
            {foto_html}
            <h1 class="libro-titulo">Mi abecedario</h1>
            <p class="libro-subtitulo">Por {nombre_portada} · Toca cada imagen para escuchar la palabra con karaoke</p>
            <p class="libro-parrafo-intro">
                Este abecedario ha sido creado especialmente para {nombre_portada}, integrando su mundo favorito con tecnología de Inteligencia Artificial.
                Diseñado como un complemento de Lee Conmigo IA, cada página busca que {nombre_reconozca} se reconozca como el héroe de su propio aprendizaje,
                facilitando la memorización a través de la emoción y el juego.
            </p>
            <p class="libro-aviso-legal">
                Los contenidos, ilustraciones y diseños presentados en este abecedario son propiedad intelectual de LeeConmigo IA y el ecosistema AprendeConNosotros IA.
                Este material ha sido creado con fines estrictamente educativos y personalizados, por lo que su distribución comercial, reproducción total o parcial por parte de editoriales o terceros, así como su alteración sin autorización expresa, queda prohibida.
                Los desarrolladores no se hacen responsables del uso indebido del material fuera del entorno pedagógico sugerido, ni de interpretaciones derivadas de los elementos gráficos generados por Inteligencia Artificial.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    for letra in letras_disponibles:
        par = abecedario_guardado.get(letra, [])
        if len(par) != 2:
            continue
        pal1 = (par[0].get("palabra") or "").strip() or "?"
        pal2 = (par[1].get("palabra") or "").strip() or "?"
        ruta1 = par[0].get("ruta_img")
        ruta2 = par[1].get("ruta_img")
        col_izq, col_letra, col_der = st.columns([1, 0.7, 1])
        with col_izq:
            render_album_card_karaoke(
                ruta1, pal1,
                unique_id=f"abecedario_completo_{letra}_0",
                size="large",
                show_label_below=True,
            )
        with col_letra:
            st.markdown(
                f"""
                <div style="
                    display: flex; align-items: center; justify-content: center;
                    min-height: {altura_letra_px}px; background: linear-gradient(135deg, {color_fav}22 0%, {color_fav}44 100%);
                    border: 4px solid {color_fav}; border-radius: 20px;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
                ">
                    <span style="font-size: 5rem; font-weight: 900; color: {color_fav}; text-shadow: 0 2px 8px rgba(0,0,0,0.2);">{letra}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_der:
            render_album_card_karaoke(
                ruta2, pal2,
                unique_id=f"abecedario_completo_{letra}_1",
                size="large",
                show_label_below=True,
            )
        st.write("")

    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("💡 Imprime (Ctrl+P o Cmd+P) para tener tu libro en papel.")
    st.write("")
    st.markdown('<div class="no-print">', unsafe_allow_html=True)

    if st.button("✏️ Cambiar imágenes de mi abecedario", use_container_width=True, key="abecedario_editar"):
        st.session_state.pop("album_abecedario_mostrar_completo", None)
        st.session_state["album_abecedario_editar"] = True
        st.session_state["album_abecedario_idx"] = 0
        st.rerun()
    if st.button("⬅️ Volver al Álbum", use_container_width=True, key="volver_album_completo"):
        st.session_state.pop("album_abecedario_mostrar_completo", None)
        st.session_state.pop("album_abecedario_editar", None)
        st.session_state.pagina_activa = "album_nino"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _nombres_abecedario(estudiante_id: int, nombre_sesion: str):
    """Devuelve (nombre_portada, nombre_reconozca): portada = primer + segundo si existe; reconozca = solo primer."""
    perfil = obtener_perfil_completo_nino(estudiante_id) if estudiante_id else None
    primer = (perfil[2] or "").strip() if perfil and len(perfil) > 2 else (nombre_sesion or "Explorador").strip() or "Explorador"
    segundo = (perfil[3] or "").strip() if perfil and len(perfil) > 3 else ""
    nombre_portada = f"{primer} {segundo}".strip() if segundo else primer
    nombre_reconozca = primer
    return nombre_portada, nombre_reconozca


def render_album_abecedario_nino():
    estudiante_id = st.session_state.get("estudiante_id")
    nombre = st.session_state.get("nombre_nino", "Explorador")
    color_fav = st.session_state.get("color_favorito", "#4A90E2")
    nombre_portada, nombre_reconozca = _nombres_abecedario(estudiante_id or 0, nombre)

    if not estudiante_id:
        st.warning("No hay estudiante en sesión.")
        if st.button("⬅️ Volver al Álbum"):
            st.session_state.pagina_activa = "album_nino"
            st.rerun()
        return

    por_letra = AssetManager.obtener_genericos_por_letra()
    letras_disponibles = sorted(por_letra.keys())
    if not letras_disponibles:
        st.info("Aún no hay imágenes por letra. Pronto podrás crear tu abecedario.")
        if st.button("⬅️ Volver al Álbum"):
            st.session_state.pagina_activa = "album_nino"
            st.rerun()
        return

    abecedario_guardado = obtener_abecedario_estudiante(estudiante_id)

    fondos = AssetManager.obtener_fondos_abecedario()
    opciones_fondo = ["Elige tu motivo"] + [f["nombre"] for f in fondos]
    foto_ruta = _foto_estudiante_abecedario(estudiante_id, nombre)
    letras_con_dos = [letra for letra in letras_disponibles if len(abecedario_guardado.get(letra, [])) == 2]

    # idx_fondo desde sesión (el selector se dibuja debajo del primer botón)
    idx_fondo = st.session_state.get("abecedario_idx_fondo", 0)
    if idx_fondo >= len(opciones_fondo):
        idx_fondo = 0
        st.session_state["abecedario_idx_fondo"] = 0
    fondo_ruta = None if idx_fondo == 0 or not fondos else fondos[idx_fondo - 1]["ruta"]
    st.session_state["abecedario_fondo_ruta"] = fondo_ruta
    if not fondos:
        st.caption("Para añadir motivos: coloca imágenes (jpg, png, webp) en **assets/genericos/fondos/**.")

    # Vista "Ver estado del abecedario"
    if st.session_state.get("album_abecedario_ver_estado"):
        _render_estado_abecedario(letras_disponibles, abecedario_guardado, color_fav, nombre, foto_ruta, fondo_ruta, nombre_portada, nombre_reconozca)
        return

    # Primera letra que aún no tiene 2 imágenes
    primera_falta_idx = next(
        (i for i, letra in enumerate(letras_disponibles) if len(abecedario_guardado.get(letra, [])) != 2),
        None,
    )
    todas_completas = primera_falta_idx is None

    # Al iniciar: ir a la primera letra que falta; si todas completas, mostrar abecedario completo
    if "album_abecedario_idx" not in st.session_state:
        st.session_state["album_abecedario_idx"] = primera_falta_idx if primera_falta_idx is not None else 0
    # Si ya estamos en vista "completo" o todas están completas y no estamos en modo editar
    if st.session_state.get("album_abecedario_mostrar_completo"):
        _render_abecedario_completo(estudiante_id, letras_disponibles, abecedario_guardado, color_fav, nombre, foto_ruta, fondo_ruta, nombre_portada, nombre_reconozca)
        return

    if todas_completas and not st.session_state.get("album_abecedario_editar"):
        # Todas las letras tienen 2 imágenes: mostrar abecedario completo
        st.session_state["album_abecedario_mostrar_completo"] = True
        st.rerun()
        return

    # Índice de letra actual (si entramos de nuevo y había quedado en una ya completada, ir a la primera que falta)
    idx = st.session_state["album_abecedario_idx"] % len(letras_disponibles)
    if len(abecedario_guardado.get(letras_disponibles[idx], [])) == 2 and primera_falta_idx is not None:
        idx = primera_falta_idx
        st.session_state["album_abecedario_idx"] = idx
    letra_actual = letras_disponibles[idx]

    # Opciones para esta letra (máximo 6)
    opciones = (por_letra.get(letra_actual) or [])[:MAX_OPCIONES_POR_LETRA]
    if not opciones:
        st.session_state["album_abecedario_idx"] = (idx + 1) % len(letras_disponibles)
        st.rerun()
        return

    # Selección actual para esta letra (índices de opciones elegidas, máx 2)
    sel_key = f"album_abecedario_sel_{letra_actual}"
    if sel_key not in st.session_state:
        guardadas = obtener_abecedario_estudiante(estudiante_id).get(letra_actual, [])
        if len(guardadas) == 2:
            # Restaurar selección desde DB: buscar índices de opciones que coincidan con guardadas
            sel_idx = []
            for g in guardadas:
                path_g = (g.get("ruta_img") or "").strip()
                for i, opc in enumerate(opciones):
                    if (opc.get("ruta_img") or "").strip() == path_g:
                        sel_idx.append(i)
                        break
            st.session_state[sel_key] = sel_idx[:2]
        else:
            st.session_state[sel_key] = []
    seleccionados = st.session_state[sel_key]

    # Las 2 imágenes a mostrar alrededor de la letra: las elegidas en sesión o las guardadas
    if len(seleccionados) == 2:
        elegidas_para_mostrar = [opciones[i] for i in seleccionados]
    else:
        elegidas_para_mostrar = obtener_abecedario_estudiante(estudiante_id).get(letra_actual, [])

    opciones_letras = [f"{letras_disponibles[i]} — {i+1}/{len(letras_disponibles)}" for i in range(len(letras_disponibles))]

    # Mensaje de guardado justo después de pasar a la siguiente letra (visible de inmediato)
    letra_guardada = st.session_state.pop("album_abecedario_letra_guardada", None)
    if letra_guardada:
        st.success(f"✓ Guardado para la letra **{letra_guardada}**. Ahora elige para **{letra_actual}**.")

    # Fila de 3 botones: PDF (y motivo debajo) | Ver estado | Completando (y letra debajo)
    col_pdf, col_estado, col_letra = st.columns(3)
    with col_pdf:
        if PDF_DISPONIBLE and ejecutar_job_en_background and letras_con_dos:
            if st.session_state.get("abecedario_pdf_fondo_idx") != idx_fondo:
                st.session_state.pop("abecedario_pdf_bytes", None)
                st.session_state.pop("abecedario_pdf_job_id", None)
                st.session_state["abecedario_pdf_fondo_idx"] = idx_fondo
            job_id = st.session_state.get("abecedario_pdf_job_id")
            if job_id:
                job = pdf_job_obtener(job_id)
                if job and job.get("status") == "ready" and job.get("pdf_blob"):
                    st.session_state["abecedario_pdf_bytes"] = job["pdf_blob"]
                    st.session_state.pop("abecedario_pdf_job_id", None)
                    st.rerun()
                elif job and job.get("status") == "failed":
                    st.error(f"No se pudo generar el PDF: {job.get('error_msg', 'Error desconocido')}")
                    st.session_state.pop("abecedario_pdf_job_id", None)
                else:
                    st.info("⏳ Tu PDF se está generando. Puedes seguir editando el álbum.")
                    if st.button("🔄 Comprobar si ya está listo", use_container_width=True, key="comprobar_pdf_abecedario"):
                        st.rerun()
            if st.session_state.get("abecedario_pdf_bytes"):
                nombre_sano = (nombre or "").strip().split()[0] if (nombre or "").strip() else "abecedario"
                nombre_sano = re.sub(r"[^\wáéíóúñÑ]", "", nombre_sano) or "abecedario"
                st.download_button(
                    label="📥 Descargar PDF para imprimir",
                    data=st.session_state["abecedario_pdf_bytes"],
                    file_name=f"abecedario_de_{nombre_sano}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="descargar_pdf_abecedario",
                )
                if st.button("🔄 Generar de nuevo", key="regenerar_pdf", use_container_width=True):
                    st.session_state.pop("abecedario_pdf_bytes", None)
                    st.session_state.pop("abecedario_pdf_job_id", None)
                    st.rerun()
            elif not job_id:
                if st.button("📥 Crear y descargar PDF para imprimir", use_container_width=True, key="crear_pdf_abecedario"):
                    try:
                        params = {
                            "nombre_portada": nombre_portada,
                            "letras_disponibles": letras_disponibles,
                            "abecedario_guardado": abecedario_guardado,
                            "color_fav": color_fav,
                            "foto_ruta": foto_ruta or "",
                            "fondo_ruta": fondo_ruta or "",
                            "nombre_para_reconozca": nombre_reconozca or "",
                        }
                        new_job_id = pdf_job_crear(estudiante_id, "abecedario", json.dumps(params))
                        if new_job_id:
                            st.session_state["abecedario_pdf_job_id"] = new_job_id
                            ejecutar_job_en_background(new_job_id)
                    except Exception as e:
                        st.error(f"No se pudo encolar el PDF: {e}")
                    st.rerun()
        elif PDF_DISPONIBLE and letras_con_dos:
            # Fallback: generación en primer plano si pdf_jobs no está disponible
            if st.session_state.get("abecedario_pdf_fondo_idx") != idx_fondo:
                st.session_state.pop("abecedario_pdf_bytes", None)
                st.session_state["abecedario_pdf_fondo_idx"] = idx_fondo
            if st.session_state.get("abecedario_preparar_pdf"):
                with st.spinner("Creando tu PDF…"):
                    try:
                        pdf_bytes = generar_pdf_abecedario(
                            nombre_portada, letras_disponibles, abecedario_guardado, color_fav,
                            foto_ruta=foto_ruta or "", fondo_ruta=fondo_ruta or "",
                            nombre_para_reconozca=nombre_reconozca,
                        )
                        st.session_state["abecedario_pdf_bytes"] = pdf_bytes
                    except Exception as e:
                        st.error(f"No se pudo generar el PDF: {e}")
                    st.session_state["abecedario_preparar_pdf"] = False
                st.rerun()
            if st.session_state.get("abecedario_pdf_bytes"):
                nombre_sano = (nombre or "").strip().split()[0] if (nombre or "").strip() else "abecedario"
                nombre_sano = re.sub(r"[^\wáéíóúñÑ]", "", nombre_sano) or "abecedario"
                st.download_button(
                    label="📥 Descargar PDF para imprimir",
                    data=st.session_state["abecedario_pdf_bytes"],
                    file_name=f"abecedario_de_{nombre_sano}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="descargar_pdf_abecedario",
                )
                if st.button("🔄 Generar de nuevo", key="regenerar_pdf", use_container_width=True):
                    st.session_state.pop("abecedario_pdf_bytes", None)
                    st.rerun()
            else:
                if st.button("📥 Crear y descargar PDF para imprimir", use_container_width=True, key="crear_pdf_abecedario"):
                    st.session_state["abecedario_preparar_pdf"] = True
                    st.rerun()
        st.caption("Motivo del abecedario")
        nuevo_idx_fondo = st.selectbox(
            "Elige tu motivo",
            range(len(opciones_fondo)),
            index=idx_fondo,
            format_func=lambda i: opciones_fondo[i],
            key="abecedario_fondo_sel",
        )
        st.session_state["abecedario_idx_fondo"] = nuevo_idx_fondo
        if nuevo_idx_fondo != idx_fondo:
            if nuevo_idx_fondo != 0:
                with st.spinner("Estamos creando tu abecedario…"):
                    time.sleep(1.0)
            st.rerun()
    with col_estado:
        if st.button("📊 Ver estado de mi abecedario", use_container_width=True, key="abecedario_ver_estado"):
            st.session_state["album_abecedario_ver_estado"] = True
            st.rerun()
    with col_letra:
        st.markdown("**✏️ Completando mi abecedario**")
        nuevo_idx = st.selectbox(
            "Letra",
            range(len(letras_disponibles)),
            index=idx,
            format_func=lambda i: opciones_letras[i],
            key="abecedario_selector_letra",
        )
        if nuevo_idx != idx:
            st.session_state["album_abecedario_idx"] = nuevo_idx
            st.rerun()

    st.write("---")

    st.markdown(
        f"<h2 style='text-align: center; color: {color_fav};'>📖 Mi abecedario</h2>",
        unsafe_allow_html=True,
    )
    st.write("---")

    # Bloque: letra en el centro, misma altura que las 2 imágenes (karaoke al tocar cada imagen)
    if len(elegidas_para_mostrar) == 2:
        st.markdown("<p style='text-align: center; color: #555; margin-bottom: 8px;'>Toca cada imagen para escuchar la palabra con efecto karaoke.</p>", unsafe_allow_html=True)
        # Altura de la tarjeta karaoke "large" con cintillo (~380px) para alinear la letra al mismo alto
        altura_letra_px = 380
        col_izq, col_letra, col_der = st.columns([1, 0.7, 1])
        with col_izq:
            op1 = elegidas_para_mostrar[0]
            render_album_card_karaoke(
                op1.get("ruta_img"),
                (op1.get("palabra") or "").strip() or "?",
                unique_id=f"abecedario_sel_izq_{letra_actual}",
                size="large",
                show_label_below=True,
            )
        with col_letra:
            st.markdown(
                f"""
                <div style="
                    display: flex; align-items: center; justify-content: center;
                    min-height: {altura_letra_px}px; background: linear-gradient(135deg, {color_fav}22 0%, {color_fav}44 100%);
                    border: 4px solid {color_fav}; border-radius: 20px;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
                ">
                    <span style="font-size: 6rem; font-weight: 900; color: {color_fav}; text-shadow: 0 2px 8px rgba(0,0,0,0.2);">{letra_actual}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_der:
            op2 = elegidas_para_mostrar[1]
            render_album_card_karaoke(
                op2.get("ruta_img"),
                (op2.get("palabra") or "").strip() or "?",
                unique_id=f"abecedario_sel_der_{letra_actual}",
                size="large",
                show_label_below=True,
            )
        st.write("---")

    st.markdown("**Elige 2 imágenes para esta letra (toca la imagen para escuchar la palabra).**")

    # Grid de opciones: hasta 6 imágenes, cada una con tarjeta karaoke + botón Elegir
    n_cols = 3
    cols = st.columns(n_cols)
    for i, opc in enumerate(opciones):
        with cols[i % n_cols]:
            pal = (opc.get("palabra") or "").strip() or "?"
            ruta = opc.get("ruta_img")
            seleccionado = i in seleccionados
            render_album_card_karaoke(
                ruta,
                pal,
                unique_id=f"abecedario_opt_{letra_actual}_{i}",
                size="normal",
                show_label_below=True,
            )
            if st.button(f"{'✓ Elegida' if seleccionado else 'Elegir'}", key=f"abecedario_opt_{letra_actual}_{i}", use_container_width=True):
                if seleccionado:
                    seleccionados.remove(i)
                else:
                    if len(seleccionados) < ELEGIR_POR_LETRA:
                        seleccionados.append(i)
                    else:
                        seleccionados.pop(0)
                        seleccionados.append(i)
                st.session_state[sel_key] = sorted(seleccionados)
                st.rerun()

    st.write("---")
    if len(seleccionados) == ELEGIR_POR_LETRA:
        elegidas = [opciones[i] for i in seleccionados]
        if st.button("💾 Guardar mis 2 imágenes para esta letra", type="primary", use_container_width=True, key="abecedario_guardar"):
            with st.spinner("Guardando…"):
                if guardar_abecedario_letra(estudiante_id, letra_actual, elegidas):
                    st.session_state["album_abecedario_letra_guardada"] = letra_actual
                    # ¿Quedó el abecedario completo?
                    nuevo_guardado = obtener_abecedario_estudiante(estudiante_id)
                    if all(len(nuevo_guardado.get(letra, [])) == 2 for letra in letras_disponibles):
                        st.session_state["album_abecedario_mostrar_completo"] = True
                    else:
                        st.session_state["album_abecedario_idx"] = (idx + 1) % len(letras_disponibles)
                    st.rerun()
                else:
                    st.error("No se pudo guardar.")
    else:
        st.caption(f"Elige {ELEGIR_POR_LETRA - len(seleccionados)} imagen más para esta letra.")

    st.write("---")
    if st.button("⬅️ Volver al Álbum", use_container_width=True):
        st.session_state.pagina_activa = "album_nino"
        st.rerun()
