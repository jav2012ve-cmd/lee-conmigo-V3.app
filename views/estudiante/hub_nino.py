import html

import streamlit as st
import database.db_queries as db_queries

from components.page_title import logo_markup_html
from components.styles import apply_fondo_pagina_principal_hub

# Intentamos importar componentes avanzados, si fallan, la app sigue funcionando
try:
    from core.curriculum import Curriculum
    import components.styles as styles
    HAS_EXTENSIONS = True
except ImportError:
    HAS_EXTENSIONS = False

def render_hub_nino():
    """
    Dashboard principal del niño. 
    Versión INTEGRADA y BLINDADA contra errores de índice.
    """
    apply_fondo_pagina_principal_hub()
    # 1. RECUPERACIÓN DE EMERGENCIA (Tu lógica original)
    id_est_sesion = st.session_state.get('estudiante_id')
    
    if not id_est_sesion and st.session_state.get('padre_id'):
        ninos = db_queries.obtener_estudiantes_por_padre(st.session_state.padre_id)
        if ninos:
            id_est_sesion = ninos[-1][0] 
            st.session_state.estudiante_id = id_est_sesion

    # Registrar último ingreso (para el informe en Zona de padres)
    if id_est_sesion:
        db_queries.actualizar_ultimo_ingreso(id_est_sesion)

    # 2. CONSULTAR PERFIL
    info = db_queries.obtener_perfil_completo_nino(id_est_sesion)

    if info:
        # Mapeo según tabla estudiantes: 2=primer_nombre, 11=color_favorito, 16=ciclo_actual (12=animal_favorito)
        nombre = info[2] if len(info) > 2 else "Explorador"
        color_fav = info[11] if len(info) > 11 else "#4CAF50"
        ciclo_actual = info[16] if len(info) > 16 and info[16] else "Ciclo 1"
    else:
        nombre, color_fav, ciclo_actual = "Pequeño Explorador", "#4CAF50", "Ciclo 1"

    # Sincronización de estados
    st.session_state.color_favorito = color_fav
    st.session_state.nombre_nino = nombre
    st.session_state.ciclo_actual = ciclo_actual

    # Avance de lecciones por estudiante (cada niño tiene su propio indice_letra)
    if HAS_EXTENSIONS:
        letras_override = st.session_state.get("v3_letras_override")
        if isinstance(letras_override, list) and letras_override:
            letras_disponibles = [str(x).strip().upper() for x in letras_override if str(x).strip()]
        else:
            letras_disponibles = Curriculum.obtener_letras_por_ciclo(ciclo_actual)
        k_indice = f"est_{id_est_sesion}_indice_letra" if id_est_sesion else "indice_letra"
        if k_indice not in st.session_state or st.session_state[k_indice] >= len(letras_disponibles):
            st.session_state[k_indice] = 0
        styles.apply_styles()

    # 3. DISEÑO DE LA INTERFAZ (Tu diseño original con inyección de color dinámica)
    _lg = logo_markup_html(height_px=208, margin_right=0)
    _nom_raw = (nombre or "Explorador").strip() or "Explorador"
    _nom_raw = _nom_raw.lstrip("¡").rstrip("!").strip() or "Explorador"
    _nom = html.escape(_nom_raw)
    _cic = html.escape((ciclo_actual or "").strip() or "Ciclo 1")
    st.markdown(
        f"""
        <div style='padding: 24px 28px; border-radius: 25px;
             background-color: {color_fav}20; border: 5px solid {color_fav};'>
            <div style="display:grid;grid-template-columns:auto 1fr;gap:1.25rem 1.75rem;
                 align-items:center;max-width:100%;">
              <div style="display:flex;align-items:center;justify-content:center;min-width:0;">
                {_lg}
              </div>
              <div style="text-align:left;min-width:11rem;max-width:100%;">
                <h1 style='color: {color_fav}; font-size: clamp(1.6rem, 4vw, 2.6rem); margin: 0 0 0.35rem 0; line-height:1.15;overflow-wrap:break-word;'>
                  ¡Hola, {_nom}!
                </h1>
                <p style='font-size: clamp(1rem, 2.2vw, 1.35rem); color: #333; margin: 0; line-height:1.35;'>
                  Estás en el <b>{_cic}</b>. ¡Es hora de leer!
                </p>
              </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    # 4. BOTONES DE ACCIÓN: una fila, tres columnas iguales (Álbum | Lecciones | Abecedario)
    fotos = db_queries.obtener_album_nino(id_est_sesion) or []
    tiene_fotos = len(fotos) > 0

    col_album, col_lecciones, col_abecedario = st.columns(3)

    with col_album:
        st.markdown("<h2 style='text-align: center;'>Mi Álbum</h2>", unsafe_allow_html=True)
        if st.button("MIS FOTOS FAVORITAS", use_container_width=True, key="btn_album_v2"):
            st.session_state.pagina_activa = "album_nino"
            st.rerun()

    with col_lecciones:
        st.markdown("<h2 style='text-align: center;'>Mis Lecciones</h2>", unsafe_allow_html=True)
        if tiene_fotos:
            if st.button("¿Comenzamos?", use_container_width=True, key="btn_leccion_v2"):
                st.session_state.pagina_activa = "lecciones_nino"
                st.rerun()
        else:
            st.info("Sube fotos para desbloquear tus lecciones.")
            st.button("🔒 BLOQUEADO", disabled=True, use_container_width=True)

    with col_abecedario:
        st.markdown("<h2 style='text-align: center;'>Abecedario</h2>", unsafe_allow_html=True)
        if st.button(
            "Ver el abecedario",
            use_container_width=True,
            key="hub_v2_ir_abecedario_matriz",
        ):
            st.session_state.pagina_activa = "abecedario_matriz"
            st.rerun()

    # 5. SALIDA: volver al salón (el informe solo se ve en Zona de padres)
    st.write("---")
    if st.button("🏠 Volver al Salón"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()