import streamlit as st
import os
import unicodedata
from database.db_queries import (
    obtener_estudiantes_por_padre,
    obtener_album_nino,
    obtener_album_nino_varios,
    obtener_claves_estudiante,
    obtener_avatar_estudiante,
)
from database.db_config import using_demo_database
from components.cards import render_selector_avatar
from components.styles import apply_fondo_pagina_principal_hub
from core.branding import ruta_logo_app

# Mismo conjunto de 9 emojis que en config_salon para la clave del niño (matriz 3x3)
EMOJIS_CLAVE = ["🐱", "🐶", "🌟", "❤️", "🌈", "🎈", "🦋", "⚽", "🍎"]

# Raíz del proyecto (views/ → subir 2 niveles): misma idea que hub V3 para rutas guardadas relativas en BD.
_PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _salon_estudiantes_por_padre(padre_id):
    if using_demo_database():
        from database.demo_read_cache import demo_obtener_estudiantes_por_padre

        return demo_obtener_estudiantes_por_padre(padre_id) or []
    return obtener_estudiantes_por_padre(padre_id) or []


def _salon_album_nino_varios(ids_list):
    if not ids_list:
        return obtener_album_nino_varios([])
    if using_demo_database():
        from database.demo_read_cache import demo_obtener_album_nino_varios

        tup = tuple(sorted({int(i) for i in ids_list}))
        return demo_obtener_album_nino_varios(tup)
    return obtener_album_nino_varios(ids_list)


def _salon_avatar_estudiante(est_id):
    if using_demo_database():
        from database.demo_read_cache import demo_obtener_avatar_estudiante

        return demo_obtener_avatar_estudiante(est_id)
    return obtener_avatar_estudiante(est_id)


@st.cache_data(show_spinner=False)
def _logo_ancho_pantalla_doble_cached(ruta: str, mtime: float) -> int:
    """Ancho en px: 200 % del ancho intrínseco de la imagen (máx. 960, mín. 220)."""
    try:
        from PIL import Image

        with Image.open(ruta) as im:
            w, _ = im.size
        if w <= 0:
            return 440
        return int(min(max(w * 2, 220), 960))
    except Exception:
        return 520


def _logo_ancho_pantalla_doble(ruta: str) -> int:
    if not ruta or not os.path.isfile(ruta):
        return 520
    try:
        mt = os.path.getmtime(ruta)
    except OSError:
        return 520
    return _logo_ancho_pantalla_doble_cached(ruta, mt)


def _resolver_ruta_archivo(path):
    """Ruta absoluta si el archivo existe (absoluta, relativa a cwd o relativa al proyecto)."""
    if not path or not isinstance(path, str):
        return None
    p = path.strip()
    if os.path.isfile(p):
        return os.path.normpath(p)
    rel = os.path.join(_PROJ_ROOT, p.replace("/", os.sep).lstrip("\\/"))
    if os.path.isfile(rel):
        return os.path.normpath(rel)
    return None


def _foto_archivo_salon_por_id(id_est):
    """Si existe assets/avatares/est_{id}.* (foto del Salón), úsala aunque avatar_path en BD venga vacío o desfasado."""
    av_dir = os.path.join(_PROJ_ROOT, "assets", "avatares")
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        cand = os.path.join(av_dir, f"est_{id_est}{ext}")
        if os.path.isfile(cand):
            return os.path.normpath(cand)
    return None


def _foto_perfil_estudiante(id_est, primer_nombre, nombre_completo, avatar_path, album_rows=None):
    """
    avatar_path en BD o foto del álbum cuya palabra coincida con el primer nombre o el nombre completo.
    Resuelve rutas relativas (p. ej. assets/avatares/est_1.jpg) para que funcione aunque cambie el cwd.
    """
    r = _resolver_ruta_archivo(avatar_path)
    if r:
        return r
    r = _foto_archivo_salon_por_id(id_est)
    if r:
        return r
    album = (obtener_album_nino(id_est) or []) if album_rows is None else album_rows
    claves = {
        (primer_nombre or "").strip().upper(),
        (nombre_completo or "").strip().upper(),
    }
    claves.discard("")
    for palabra, _cat, img_path in album:
        pk = (palabra or "").strip().upper()
        if pk not in claves:
            continue
        r = _resolver_ruta_archivo(img_path)
        if r:
            return r
    return None

def render_salon_entrada():
    apply_fondo_pagina_principal_hub()
    # Cabecera: 1 fila × 3 columnas (izquierda / logo / derecha)
    col_titulo, col_logo, col_pregunta = st.columns([1, 1, 1], gap="small")
    with col_titulo:
        st.markdown(
            "<div style='text-align:left; padding-top:0.35rem;'><h2 style='margin:0; font-size:1.35rem;'>"
            "🏫 Bienvenidos al Salon</h2></div>",
            unsafe_allow_html=True,
        )
    with col_logo:
        _logo = ruta_logo_app()
        if _logo:
            _pad_l, _logo_col, _pad_r = st.columns([0.35, 5, 0.35])
            with _logo_col:
                _w = _logo_ancho_pantalla_doble(_logo)
                st.image(_logo, width=_w, use_container_width=False)
        else:
            st.caption(
                "Coloca el logo en **assets/genericos/fondos/** "
                "(p. ej. **LogoLeeConmigo.png** o **LogoLeeCommigo.png**; también .jpg / .webp)."
            )
    with col_pregunta:
        st.markdown(
            "<div style='text-align:right; padding-top:0.35rem;'><h2 style='margin:0; font-size:1.35rem;'>"
            "¿Quien va aprender?</h2></div>",
            unsafe_allow_html=True,
        )

    # 1. Obtener ID del padre (con respaldo por si la sesión falló)
    if 'padre_id' not in st.session_state or st.session_state.padre_id is None:
        st.session_state.padre_id = 1  # Forzamos el ID 1 para el piloto
    padre_id = st.session_state.padre_id
    estudiantes = _salon_estudiantes_por_padre(padre_id)

    if not estudiantes:
        st.info("Aún no hay estudiantes registrados. Usa **Registro** para crear el primer perfil.")
        if st.button("➕ Registro (nuevo estudiante)"):
            st.session_state.pagina_activa = 'config_salon'
            st.session_state.config_selector_nino = "➕ Crear nuevo perfil"
            st.session_state.pop("config_estudiante_id", None)
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
                    /* Botonera inferior (Volver / Continuar sin clave): texto normal, no celda emoji */
                    #botonera-clave-abajo ~ div [data-testid="stHorizontalBlock"] .stButton > button,
                    #botonera-clave-abajo ~ div [data-testid="stHorizontalBlock"] .stButton > button * {
                        font-size: 1.05rem !important;
                        line-height: 1.25 !important;
                        min-height: 2.75rem !important;
                        height: auto !important;
                        padding: 0.5rem 0.85rem !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    """
                    <style>
                    section[data-testid="stMain"] button[kind="primary"],
                    section[data-testid="stMain"] button[kind="primary"] * {
                        font-size: clamp(2.85rem, 9vmin, 3.55rem) !important;
                        line-height: 1 !important;
                    }
                    section[data-testid="stMain"] button[kind="primary"] {
                        min-height: 3.95rem !important;
                        max-height: 3.95rem !important;
                        height: 3.95rem !important;
                        padding: 0.05rem 0.35rem !important;
                        box-sizing: border-box !important;
                        overflow: hidden !important;
                        background-color: #E3F2FD !important;
                        color: #1565C0 !important;
                        border-radius: 20px !important;
                        display: inline-flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")
                cols = st.columns(3)
                for i, emoji in enumerate(EMOJIS_CLAVE):
                    with cols[i % 3]:
                        if st.button(emoji, key=f"clave_btn_{pendiente_id}_{i}", use_container_width=True, type="primary"):
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
    _albumes_salon = _salon_album_nino_varios([d[0] for d in estudiantes_salon])

    # Entrada tocando la foto (enlace ?salon_entrar=id): más fiable que superponer un st.button con CSS
    _qp_entrar = st.query_params.get("salon_entrar")
    if _qp_entrar is not None and str(_qp_entrar).strip() != "":
        try:
            _id_entrar = int(str(_qp_entrar).strip())
        except ValueError:
            _id_entrar = None
        _ids_salon = {d[0] for d in estudiantes_salon}
        if _id_entrar is not None and _id_entrar in _ids_salon:
            _datos_e = next(d for d in estudiantes_salon if d[0] == _id_entrar)
            _nombre_e = _nombre_completo(_datos_e)
            _, _clave_emoji_e = obtener_claves_estudiante(_id_entrar)
            if _clave_emoji_e:
                st.session_state.pendiente_confirmar_emoji = _id_entrar
                st.session_state.pendiente_confirmar_nombre = _nombre_e
            else:
                st.session_state.estudiante_id = _id_entrar
                st.session_state.nombre_nino = _nombre_e
                st.session_state.pagina_activa = "hub_nino"
        try:
            del st.query_params["salon_entrar"]
        except Exception:
            pass
        st.rerun()

    # 2. Cuadrícula con fotos: enlace en foto + nombre; pie con botones normales
    st.caption("Toca tu foto o tu nombre para entrar. Si tienes clave de emojis, te la pediremos a continuación.")
    st.markdown(
        """
        <style>
        /* Pie del salón (Zona padres / Registro): solo secondary */
        section[data-testid="stMain"] .block-container [data-testid="column"] .stButton > button[kind="secondary"],
        section[data-testid="stMain"] .block-container [data-testid="column"] .stButton > button[kind="secondary"] p,
        section[data-testid="stMain"] .block-container [data-testid="column"] .stButton > button[kind="secondary"] span,
        section[data-testid="stMain"] .block-container [data-testid="column"] .stButton > button[kind="secondary"] div {
            font-size: 1rem !important;
            line-height: 1.25 !important;
            min-height: 48px !important;
            height: auto !important;
            max-height: none !important;
            width: 100% !important;
            padding: 0.5rem 0.75rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    num_est = len(estudiantes_salon)
    cols = st.columns(min(num_est, 4))

    for i, datos in enumerate(estudiantes_salon):
        id_est = datos[0]
        primer_nombre = datos[1] if len(datos) > 1 else ""
        # Ruta desde BD (más fiable que la tupla si hubo recarga / migración)
        avatar_db = _salon_avatar_estudiante(id_est)
        if not avatar_db and len(datos) > 4 and datos[4]:
            avatar_db = (datos[4] or "").strip() or None
        nombre_completo = _nombre_completo(datos)
        img_path = _foto_perfil_estudiante(
            id_est, primer_nombre, nombre_completo, avatar_db, album_rows=_albumes_salon.get(id_est, [])
        )
        with cols[i % 4]:
            render_selector_avatar(img_path, nombre_completo, salon_entrar_id=id_est)

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
            st.session_state.pop("config_estudiante_id", None)
            st.rerun()