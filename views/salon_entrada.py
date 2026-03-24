import streamlit as st
import os
import unicodedata
from database.db_queries import (
    obtener_estudiantes_por_padre,
    obtener_album_nino,
    obtener_claves_estudiante,
)
from components.cards import render_selector_avatar

# Mismo conjunto de 9 emojis que en config_salon para la clave del niño (matriz 3x3)
EMOJIS_CLAVE = ["🐱", "🐶", "🌟", "❤️", "🌈", "🎈", "🦋", "⚽", "🍎"]

def _foto_perfil_estudiante(id_est, nombre, avatar_path):
    """Solo usa avatar_path o una foto del álbum cuya palabra clave sea el nombre del niño (ej. CAMILA). No usa otras fotos del álbum (ej. Tía Johana)."""
    if avatar_path and os.path.isfile(avatar_path):
        return avatar_path
    album = obtener_album_nino(id_est) or []
    nombre_upper = (nombre or "").strip().upper()
    for palabra, _cat, img_path in album:
        if img_path and os.path.isfile(img_path) and (palabra or "").strip().upper() == nombre_upper:
            return img_path
    return None

def render_salon_entrada():
    st.markdown("<h1 style='text-align: center;'>🏫 ¡Bienvenidos al Salón!</h1>", unsafe_allow_html=True)

    # 1. Obtener ID del padre (con respaldo por si la sesión falló)
    if 'padre_id' not in st.session_state or st.session_state.padre_id is None:
        st.session_state.padre_id = 1  # Forzamos el ID 1 para el piloto
    padre_id = st.session_state.padre_id
    estudiantes = obtener_estudiantes_por_padre(padre_id)

    if not estudiantes:
        st.info("Aún no hay estudiantes registrados. Usa **Registro** para crear el primer perfil.")
        if st.button("➕ Registro (nuevo estudiante)"):
            st.session_state.pagina_activa = 'config_salon'
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.rerun()
        return

    # 1b. Después de la bienvenida: espacio para que cada estudiante ingrese su código de emojis y acceda a lecciones o álbum
    pendiente_id = st.session_state.get("pendiente_confirmar_emoji")
    pendiente_nombre = st.session_state.get("pendiente_confirmar_nombre", "")
    if pendiente_id is not None:
        _, clave_emoji = obtener_claves_estudiante(pendiente_id)
        # Si no tiene clave configurada: ofrecer el espacio con opción de continuar sin clave
        if not clave_emoji:
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 24px;">
                    <p style="font-size: 2.5rem; margin-bottom: 4px;">🦉 <span style="font-weight: 800; color: #e65100;">Lee Conmigo IA</span></p>
                    <p style="font-size: 0.95rem; color: #666;">Aprende a leer con las personas que amas.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div style="text-align: center; margin-bottom: 16px;">
                    <p style="font-size: 1.8rem; font-weight: 700; color: #333;">Hola {pendiente_nombre} ✋</p>
                    <p style="font-size: 1.1rem; color: #555;">Aún no tienes una clave de emojis.</p>
                    <p style="font-size: 0.95rem; color: #777;">El tutor puede configurarla en <strong>Configuración</strong> → perfil de {pendiente_nombre} → Claves de acceso.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Continuar sin clave", type="primary", key="btn_sin_clave"):
                    st.session_state.estudiante_id = pendiente_id
                    st.session_state.nombre_nino = pendiente_nombre
                    st.session_state.pop("pendiente_confirmar_emoji", None)
                    st.session_state.pop("pendiente_confirmar_nombre", None)
                    st.session_state.pagina_activa = "hub_nino"
                    st.rerun()
            with col_b:
                if st.button("⬅️ Volver al Salón", key="btn_volver_sin_clave"):
                    st.session_state.pop("pendiente_confirmar_emoji", None)
                    st.session_state.pop("pendiente_confirmar_nombre", None)
                    st.rerun()
            return

        # Estado de la clave ingresada (lista de hasta 3 emojis)
        if "clave_ingresada_salon" not in st.session_state:
            st.session_state.clave_ingresada_salon = []
        lista = st.session_state.clave_ingresada_salon
        esperado = clave_emoji.split("|") if clave_emoji else []

        # Layout en dos columnas: izquierda bienvenida, derecha matriz de emojis
        col_left, col_right = st.columns([1.3, 1])

        with col_left:
            # Cabecera: logo + Lee Conmigo IA + tagline
            st.markdown(
                f"""
                <div style="text-align: left; margin-bottom: 16px;">
                    <p style="font-size: 2.8rem; margin-bottom: 4px;">🦉 <span style="font-weight: 800; color: #e65100;">Lee Conmigo IA</span></p>
                    <p style="font-size: 1.05rem; color: #666;">Aprende a leer con las personas que amas.</p>
                </div>
                <div style="text-align: left; margin-bottom: 8px;">
                    <p style="font-size: 2.2rem; font-weight: 700; color: #333;">Hola {pendiente_nombre} 👋</p>
                    <p style="font-size: 1.3rem; color: #555;">Ingresa tu clave secreta (toca 3 emojis):</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Tres círculos de progreso (verde = completado, gris = pendiente), justo debajo de la bienvenida
            n_ok = len(lista)
            circulos = "".join(
                f'<span style="display: inline-block; width: 36px; height: 36px; border-radius: 50%; margin: 0 10px; background: {"#4CAF50" if i < n_ok else "transparent"}; border: 4px solid {"#4CAF50" if i < n_ok else "#ccc"};"></span>'
                for i in range(3)
            )
            st.markdown(f'<div style="text-align: left; margin-bottom: 24px;">{circulos}</div>', unsafe_allow_html=True)

        # Validar al completar los 3 (normalización robusta: NFC + quitar selectores de variación U+FE0F)
        if len(lista) == 3:
            def _normalizar_emoji(txt):
                txt = (txt or "").strip()
                txt = unicodedata.normalize("NFC", txt)
                return "".join(c for c in txt if c != "\uFE0F")
            def _clave_normalizada(s):
                partes = [(x or "").strip() for x in (s or "").split("|")[:3]]
                return "|".join(_normalizar_emoji(p) for p in partes)
            ingresado = "|".join(lista)
            if _clave_normalizada(ingresado) == _clave_normalizada(clave_emoji or ""):
                st.session_state.estudiante_id = pendiente_id
                st.session_state.nombre_nino = pendiente_nombre
                st.session_state.pop("pendiente_confirmar_emoji", None)
                st.session_state.pop("pendiente_confirmar_nombre", None)
                st.session_state.pop("clave_ingresada_salon", None)
                st.session_state.pagina_activa = "hub_nino"
                st.rerun()
            else:
                st.session_state.clave_ingresada_salon = []
                st.error("Clave incorrecta. Intenta de nuevo.")
                st.rerun()

        # Matriz 3x3 de emojis para la clave (misma disposición que siempre)
        if len(lista) < 3:
            with col_right:
                st.markdown(
                """
                <style>
                main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"] .stButton > button,
                main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"] .stButton > button * {
                    font-size: 5rem !important;
                    line-height: 1 !important;
                }
                main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"] .stButton > button {
                    min-height: 5.5rem !important;
                    min-width: 5rem !important;
                    padding: 0.5rem !important;
                    border-radius: 20px !important;
                    background: #E3F2FD !important;
                    color: #333 !important;
                    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
                main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="column"] .stButton > button:hover {
                    background: #90CAF9 !important;
                    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.35);
                }
                main [data-testid="stHorizontalBlock"]:last-of-type [data-testid="column"] .stButton > button,
                main [data-testid="stHorizontalBlock"]:last-of-type [data-testid="column"] .stButton > button * {
                    font-size: 1rem !important;
                    min-height: 2.5rem !important;
                    padding: 0.25rem 1rem !important;
                    background: #f0f0f0 !important;
                    color: #333 !important;
                    box-shadow: none !important;
                }
                </style>
                """,
                    unsafe_allow_html=True,
                )
                st.write("")
                cols = st.columns(3)
                for i, emoji in enumerate(EMOJIS_CLAVE):
                    with cols[i % 3]:
                        if st.button(emoji, key=f"clave_btn_{pendiente_id}_{i}", use_container_width=True):
                            st.session_state.clave_ingresada_salon = (st.session_state.get("clave_ingresada_salon") or []) + [emoji]
                            st.rerun()
                st.write("")

        st.write("")
        st.markdown('<div id="botonera-clave-abajo"></div>', unsafe_allow_html=True)
        col_volver, col_sin = st.columns(2)
        with col_volver:
            if st.button("⬅️ Volver", key="btn_volver_clave"):
                st.session_state.pop("pendiente_confirmar_emoji", None)
                st.session_state.pop("pendiente_confirmar_nombre", None)
                st.session_state.pop("clave_ingresada_salon", None)
                st.rerun()
        with col_sin:
            if st.button("Continuar sin clave", key="btn_sin_clave_entrar"):
                st.session_state.estudiante_id = pendiente_id
                st.session_state.nombre_nino = pendiente_nombre
                st.session_state.pop("pendiente_confirmar_emoji", None)
                st.session_state.pop("pendiente_confirmar_nombre", None)
                st.session_state.pop("clave_ingresada_salon", None)
                st.session_state.pagina_activa = "hub_nino"
                st.rerun()
        return

    # Nombre completo (primer + segundo + apellidos) para la lista
    def _nombre_completo(datos):
        p = (datos[1] or "").strip()
        s = (datos[2] or "").strip() if len(datos) > 2 else ""
        a = (datos[3] or "").strip() if len(datos) > 3 else ""
        return (" ".join(filter(None, [p, s, a]))).strip() or p

    # Un solo registro por persona: mismo (primer_nombre, segundo_nombre, apellidos) → quedarse con id más reciente (evita 3 José Javier)
    vistos = {}
    for datos in estudiantes:
        p = (datos[1] or "").strip()
        s = (datos[2] or "").strip() if len(datos) > 2 else ""
        a = (datos[3] or "").strip() if len(datos) > 3 else ""
        key = (p, s, a)
        id_est = datos[0]
        if key not in vistos or id_est > vistos[key][0]:
            vistos[key] = datos
    estudiantes_salon = list(vistos.values())

    # 2. Cuadrícula con fotos: cada estudiante elige su perfil (botones del mismo tamaño)
    st.subheader("¿Quién va a jugar?")
    st.caption("Toca tu nombre y luego ingresa tu clave de 3 emojis para acceder a tus lecciones y tu álbum.")
    st.markdown("""
        <style>
        /* Igualar tamaño de botones "¡Soy ...!" en la cuadrícula de estudiantes */
        .block-container [data-testid="column"] .stButton > button {
            min-height: 48px !important; width: 100%% !important;
            font-size: 1rem !important; padding: 0.5rem 0.75rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    st.write("")
    num_est = len(estudiantes_salon)
    cols = st.columns(min(num_est, 4))

    for i, datos in enumerate(estudiantes_salon):
        id_est = datos[0]
        primer_nombre = datos[1] if len(datos) > 1 else ""
        avatar_db = datos[4] if (len(datos) > 4 and datos[4]) else None
        nombre_completo = _nombre_completo(datos)
        img_path = _foto_perfil_estudiante(id_est, primer_nombre, avatar_db)
        with cols[i % 4]:
            render_selector_avatar(img_path, nombre_completo)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if st.button(f"¡Soy {nombre_completo}!", key=f"btn_nino_{id_est}", use_container_width=True):
                    _, clave_emoji = obtener_claves_estudiante(id_est)
                    if clave_emoji:
                        st.session_state.pendiente_confirmar_emoji = id_est
                        st.session_state.pendiente_confirmar_nombre = nombre_completo
                    else:
                        st.session_state.estudiante_id = id_est
                        st.session_state.nombre_nino = nombre_completo
                        st.session_state.pagina_activa = 'hub_nino'
                    st.rerun()

    st.write("---")
    st.caption("Para editar perfiles, ver informes de avance o registrar nuevos niños:")
    col_zona, col_registro = st.columns(2)
    with col_zona:
        if st.button("👨‍👩‍👧 Zona de padres", key="btn_zona_padres", use_container_width=True):
            st.session_state.pagina_activa = "zona_padres"
            st.rerun()
    with col_registro:
        if st.button("➕ Registro (nuevo estudiante)", key="btn_registro_nuevo", use_container_width=True):
            st.session_state.pagina_activa = "config_salon"
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.rerun()