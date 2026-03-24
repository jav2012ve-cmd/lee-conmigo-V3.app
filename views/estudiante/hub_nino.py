import streamlit as st
import database.db_queries as db_queries

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
        letras_disponibles = Curriculum.obtener_letras_por_ciclo(ciclo_actual)
        k_indice = f"est_{id_est_sesion}_indice_letra" if id_est_sesion else "indice_letra"
        if k_indice not in st.session_state or st.session_state[k_indice] >= len(letras_disponibles):
            st.session_state[k_indice] = 0
        styles.apply_styles()

    # 3. DISEÑO DE LA INTERFAZ (Tu diseño original con inyección de color dinámica)
    st.markdown(f"""
        <div style='text-align: center; padding: 30px; border-radius: 25px; 
             background-color: {color_fav}20; border: 5px solid {color_fav};'>
            <h1 style='color: {color_fav}; font-size: 50px; margin-bottom: 0;'>¡Hola, {nombre}! 👋</h1>
            <p style='font-size: 24px; color: #333;'>Estás en el <b>{ciclo_actual}</b>. ¡Es hora de leer!</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("")
    # 4. BOTONES DE ACCIÓN (Con validación de fotos - Regla de Oro #1)
    fotos = db_queries.obtener_album_nino(id_est_sesion) or []
    tiene_fotos = len(fotos) > 0

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<h2 style='text-align: center;'>🖼️ Mi Álbum</h2>", unsafe_allow_html=True)
        # Botón más grande y vistoso (estilo por primera columna)
        st.markdown("""
            <style>
            [data-testid="column"]:nth-of-type(1) .stButton > button {
                font-size: 1.5rem !important; font-weight: 700 !important;
                padding: 16px 28px !important; border-radius: 14px !important;
                box-shadow: 0 4px 16px rgba(0,0,0,0.15); border-width: 3px !important;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.button("MIS FOTOS FAVORITAS", use_container_width=True, key="btn_album_v2"):
            st.session_state.pagina_activa = 'album_nino'
            st.rerun()

    with col2:
        st.markdown(f"<h2 style='text-align: center;'>🔤 Mis Lecciones</h2>", unsafe_allow_html=True)
        
        if tiene_fotos:
            if st.button("¿Comenzamos?", use_container_width=True, key="btn_leccion_v2"):
                st.session_state.pagina_activa = 'lecciones_nino'
                st.rerun()
        else:
            st.info("Sube fotos para desbloquear tus lecciones.")
            st.button("🔒 BLOQUEADO", disabled=True, use_container_width=True)

    # 5. SALIDA: volver al salón (el informe solo se ve en Zona de padres)
    st.write("---")
    if st.button("🏠 Volver al Salón"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()