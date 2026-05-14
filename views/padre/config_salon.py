import streamlit as st
import os
import html
from pathlib import Path

from components.page_title import render_titulo_pagina
import unicodedata
from components.colores import OPCIONES_COLOR_FAVORITO
from database.db_queries import (
    crear_estudiante,
    actualizar_estudiante,
    actualizar_avatar_estudiante,
    obtener_album_nino,
    obtener_perfil_completo_nino,
    obtener_nombre_docente,
    obtener_nombre_tutor,
    listar_familiares,
    agregar_familiar,
    eliminar_familiar,
    reiniciar_avance_estudiante,
    existe_estudiante_con_nombre,
)


def _repo_root():
    """Raíz del repo aunque cambie la profundidad de views/ (busca database/db_config.py)."""
    cur = Path(__file__).resolve().parent
    for _ in range(10):
        if (cur / "database" / "db_config.py").is_file():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return Path(__file__).resolve().parents[2]


_PROJ_ROOT = str(_repo_root())
_AVATARES_NINO_DIR = os.path.join(_PROJ_ROOT, "assets", "avatars_nino")
_IMG_EXTS_AVATAR = (".jpg", ".jpeg", ".png", ".webp")


def _normalizar_ruta_abs(p):
    if not p or not isinstance(p, str):
        return None
    try:
        return os.path.normpath(os.path.abspath(p.strip()))
    except Exception:
        return None


def _infer_genero_desde_ruta(path_abs):
    """Clasifica avatares en nino / nina según carpeta o prefijo del archivo (resto = solo en «Todos»)."""
    p = (path_abs or "").replace("\\", "/").lower()
    for seg in p.split("/"):
        s = seg.split(".")[0]
        if s in ("nina", "niña", "girl", "girls", "ninas", "niñas"):
            return "nina"
        if s in ("nino", "niño", "boy", "boys", "ninos", "niños"):
            return "nino"
    base = os.path.basename(p)
    if base.startswith(("nina_", "niña_", "girl_")) or "_nina_" in base or "_niña_" in base:
        return "nina"
    if base.startswith(("nino_", "niño_", "boy_")) or "_nino_" in base or "_niño_" in base:
        return "nino"
    return None


def _listar_avatares_nino():
    """Recorre assets/avatars_nino (incluye subcarpetas nino / nina). Cada ítem: label, path, genero."""
    avatares = []
    try:
        os.makedirs(_AVATARES_NINO_DIR, exist_ok=True)
        if not os.path.isdir(_AVATARES_NINO_DIR):
            return []
        for root, _dirs, files in os.walk(_AVATARES_NINO_DIR):
            for name in sorted(files):
                lower = name.lower()
                if not lower.endswith(_IMG_EXTS_AVATAR):
                    continue
                path_abs = os.path.join(root, name)
                # No usar os.path.isfile: en OneDrive/archivos "solo en la nube" puede ser False aunque el nombre exista.
                if not os.path.lexists(path_abs):
                    continue
                label = os.path.splitext(name)[0].replace("_", " ").replace("-", " ").strip()
                genero = _infer_genero_desde_ruta(path_abs)
                avatares.append({"label": label.title() or name, "path": path_abs, "genero": genero})
        avatares.sort(key=lambda x: (x.get("genero") is None, x.get("genero") or "", (x.get("label") or "").lower()))
    except OSError:
        return []
    return avatares


def _filtrar_avatares_nino_por_vista(lista, filtro):
    if filtro == "Niños":
        return [a for a in lista if a.get("genero") == "nino"]
    if filtro == "Niñas":
        return [a for a in lista if a.get("genero") == "nina"]
    return list(lista)


def _asegurar_sesion_avatar_path(path_key, ruta_actual_resuelta, lista_avatares):
    if not lista_avatares:
        return
    por_norm = {_normalizar_ruta_abs(a["path"]): a["path"] for a in lista_avatares}
    if path_key not in st.session_state:
        ra = _normalizar_ruta_abs(ruta_actual_resuelta)
        if ra and ra in por_norm:
            st.session_state[path_key] = por_norm[ra]
        else:
            st.session_state[path_key] = lista_avatares[0]["path"]


def _resolver_ruta_archivo(path):
    if not path or not isinstance(path, str):
        return None
    p = path.strip()
    if os.path.isfile(p):
        return os.path.normpath(p)
    rel = os.path.join(_PROJ_ROOT, p.replace("/", os.sep).lstrip("\\/"))
    if os.path.isfile(rel):
        return os.path.normpath(rel)
    return None


def _foto_perfil_estudiante(id_est, nombre, avatar_path):
    """Solo usa avatar_path o una foto del álbum cuya palabra clave sea el nombre del niño. No usa otras fotos (ej. familiares)."""
    r = _resolver_ruta_archivo(avatar_path)
    if r:
        return r
    album = obtener_album_nino(id_est) or []
    nombre_upper = (nombre or "").strip().upper()
    for palabra, _cat, img_path in album:
        if (palabra or "").strip().upper() != nombre_upper:
            continue
        r = _resolver_ruta_archivo(img_path)
        if r:
            return r
    return None

TIPOS_FAMILIAR = ["Abuela", "Abuelo", "Tía", "Tío", "Primo", "Prima", "Hermano", "Hermana", "Otro"]

# 9 emojis para la clave del estudiante (elegir 3 en orden); matriz 3x3
EMOJIS_CLAVE = ["🐱", "🐶", "🌟", "❤️", "🌈", "🎈", "🦋", "⚽", "🍎"]


def _norm_emoji_token(t):
    t = (t or "").strip()
    t = unicodedata.normalize("NFC", t)
    return "".join(c for c in t if c != "\uFE0F")


def _clave_guardada_a_lista_emoji(clave_guardada):
    """Mapea la clave de BD a símbolos de EMOJIS_CLAVE (evita fallar por NFC/NFD o U+FE0F vs la lista)."""
    out = []
    if not (clave_guardada or "").strip():
        return out
    for raw in (clave_guardada or "").split("|"):
        raw_n = _norm_emoji_token(raw)
        if not raw_n:
            continue
        found = None
        for ref in EMOJIS_CLAVE:
            if _norm_emoji_token(ref) == raw_n:
                found = ref
                break
        if found is not None:
            out.append(found)
        if len(out) >= 3:
            break
    return out[:3]


def render_config_salon():
    # Quitar restos de widgets retirados (cédulas/correo); evita caché confusa al actualizar la app.
    for _k in ("input_cedula_docente", "input_cedula_tutor", "input_email_tutor"):
        st.session_state.pop(_k, None)

    render_titulo_pagina("Configuración del perfil del niño")
    st.caption("Inscribe un nuevo estudiante. Para ver o editar datos con PIN, usa **Zona de padres** desde el Salón.")
    padre_id = st.session_state.get("padre_id") or 1
    # Perfil en edición: `config_estudiante_id` (familiares, etc.). Debe limpiarse al ir a "Crear nuevo perfil"
    # (main/salón) y fijarse al editar desde Zona de padres; si no, se mezclan datos entre alumnos del salón.
    config_est_id = st.session_state.get("config_estudiante_id")
    if config_est_id:
        estudiante_id_actual = config_est_id
        perfil = obtener_perfil_completo_nino(estudiante_id_actual)
        st.info("Perfil creado. Puedes agregar familiares abajo y guardar de nuevo si editas datos.")
    else:
        estudiante_id_actual = None
        perfil = None
        st.info("Completa todos los campos. Esta información se usará para crear las lecciones personalizadas.")

    # Valores por defecto (solo creación)
    def _v(row, idx, default=""):
        if row is None or idx >= len(row):
            return default
        v = row[idx]
        return v if v is not None else default

    # Clave del niño: matriz de emojis con 3 espacios arriba que se van llenando
    perfil_emoji_key = estudiante_id_actual if estudiante_id_actual else "new"
    if st.session_state.get("config_emoji_perfil_key") != perfil_emoji_key:
        clave_guardada = _v(perfil, 20, "")
        st.session_state.config_emoji_clave = _clave_guardada_a_lista_emoji(clave_guardada)
        st.session_state.config_emoji_perfil_key = perfil_emoji_key
    lista_emoji = st.session_state.get("config_emoji_clave") or []

    # Inicializar selección de avatar en sesión (la galería completa está en página aparte).
    _gal_ini = _listar_avatares_nino()
    _kid_ini = estudiante_id_actual or "new"
    _pk_ini = f"config_avatar_nino_path_{_kid_ini}"
    if _gal_ini:
        _rvis = None
        if estudiante_id_actual and perfil:
            _rvis = _foto_perfil_estudiante(estudiante_id_actual, _v(perfil, 2, ""), _v(perfil, 15, ""))
        _asegurar_sesion_avatar_path(_pk_ini, _rvis, _gal_ini)

    # Misma experiencia visual que la pantalla de clave del Salón (dos columnas: bienvenida + círculos | matriz 3×3).
    _nombre_saludo = ""
    if estudiante_id_actual and perfil:
        _nombre_saludo = " ".join(
            x
            for x in [
                (_v(perfil, 2) or "").strip(),
                (_v(perfil, 3) or "").strip(),
                (_v(perfil, 21) or "").strip(),
            ]
            if x
        ).strip()
    if not _nombre_saludo:
        _nombre_saludo = "tu hijo o hija"
    _nombre_esc = html.escape(_nombre_saludo)

    col_clave_left, col_clave_right = st.columns([1.3, 1])
    n_ok = len(lista_emoji)

    with col_clave_left:
        st.markdown(
            f"""
            <div style="text-align: left; margin-bottom: 16px;">
                <p style="font-size: 2.8rem; margin-bottom: 4px;">🦉 <span style="font-weight: 800; color: #e65100;">Lee Conmigo IA</span></p>
                <p style="font-size: 1.05rem; color: #666;">Aprende a leer con las personas que amas.</p>
            </div>
            <div style="text-align: left; margin-bottom: 8px;">
                <p style="font-size: 2.2rem; font-weight: 700; color: #333;">Hola {_nombre_esc} 👋</p>
                <p style="font-size: 1.3rem; color: #555;">Ingresa tu clave secreta (toca 3 emojis):</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        circulos = "".join(
            f'<span style="display: inline-block; width: 36px; height: 36px; border-radius: 50%; margin: 0 10px; background: {"#4CAF50" if i < n_ok else "transparent"}; border: 4px solid {"#4CAF50" if i < n_ok else "#ccc"};"></span>'
            for i in range(3)
        )
        st.markdown(f'<div style="text-align: left; margin-bottom: 16px;">{circulos}</div>', unsafe_allow_html=True)
        if lista_emoji:
            if st.button("🗑️ Quitar último emoji", key=f"emoji_quitar_{perfil_emoji_key}"):
                st.session_state.config_emoji_clave = lista_emoji[:-1]
                st.rerun()

    with col_clave_right:
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
        for fila in range(3):
            cols = st.columns(3)
            for col in range(3):
                idx = fila * 3 + col
                if idx < len(EMOJIS_CLAVE):
                    with cols[col]:
                        if st.button(
                            EMOJIS_CLAVE[idx],
                            key=f"emoji_grid_{perfil_emoji_key}_{idx}",
                            use_container_width=True,
                            type="primary",
                        ):
                            if len(lista_emoji) < 3:
                                st.session_state.config_emoji_clave = lista_emoji + [EMOJIS_CLAVE[idx]]
                                st.rerun()
        st.write("")

    st.write("---")
    with st.expander("📷 Foto del niño en el Salón (opcional)", expanded=False):
        _gal_top = _listar_avatares_nino()
        _kid_top = estudiante_id_actual or "new"
        _pk_top = f"config_avatar_nino_path_{_kid_top}"
        _sel_top = st.session_state.get(_pk_top)
        if _gal_top and _sel_top and os.path.lexists(_sel_top):
            _bn = os.path.basename(_sel_top)
            _lbl = os.path.splitext(_bn)[0].replace("_", " ").replace("-", " ").strip() or _bn
            st.caption(
                f"Selección actual: **{_lbl}**. La galería con todas las imágenes está en otra pantalla; "
                "al volver, **guarda el perfil** para aplicar cambios."
            )
        elif not _gal_top:
            st.caption("Aún no hay imágenes en `assets/avatars_nino` (carpetas **nino** / **nina**).")
        else:
            st.caption("Abre la galería para elegir el personaje que verá el niño en el Salón.")
        if st.button("🖼️ Abrir galería de avatares", key="btn_ir_galeria_avatares"):
            st.session_state.pagina_activa = "config_salon_avatares"
            st.rerun()

    with st.form("form_registro_alumno", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Primer Nombre (Ej: Ignacio)", value=_v(perfil, 2, ""), key="input_nombre")
            segundo_nombre = st.text_input("Segundo Nombre", value=_v(perfil, 3, ""), key="input_segundo_nombre")
            apellidos = st.text_input("Apellidos", value=_v(perfil, 21, ""), key="input_apellidos", placeholder="Ej: García López")
            edad = st.number_input("Edad", min_value=3, max_value=15, value=int(_v(perfil, 4, 6) or 6), key="input_edad")
            opts_genero = ["Masculino", "Femenino", "Otro"]
            idx_g = opts_genero.index(_v(perfil, 5, "Masculino")) if _v(perfil, 5) in opts_genero else 0
            genero = st.selectbox("Género", opts_genero, index=idx_g, key="input_genero")
            ciudad = st.text_input("Ciudad donde vive", value=_v(perfil, 6, ""), key="input_ciudad")
        with col2:
            mama = st.text_input("Nombre de la Mamá", value=_v(perfil, 7, ""), key="input_mama")
            papa = st.text_input("Nombre del Papá", value=_v(perfil, 8, ""), key="input_papa")
            hermanos = st.text_input("Nombre de hermanos (ej: Ana, Luis)", value=_v(perfil, 9, ""), key="input_hermanos")
            mascota = st.text_input("Nombre de su Mascota", value=_v(perfil, 10, ""), key="input_mascota")
            color_guardado = (_v(perfil, 11, "") or "#3498db").strip().lower()
            if not color_guardado.startswith("#"):
                color_guardado = "#" + color_guardado
            idx_color = next((i for i, (_, h) in enumerate(OPCIONES_COLOR_FAVORITO) if h.lower() == color_guardado), 0)
            color_fav = st.selectbox(
                "Color Favorito",
                options=[hex_val for _, hex_val in OPCIONES_COLOR_FAVORITO],
                format_func=lambda x: next((n for n, h in OPCIONES_COLOR_FAVORITO if h == x), x),
                index=idx_color,
                key="input_color",
            )
            animal = st.text_input("Animal Favorito", value=_v(perfil, 12, ""), key="input_animal")
        st.write("---")
        st.subheader("Intereses para Lectura")
        col3, col4 = st.columns(2)
        with col3:
            deporte = st.text_input("Deporte o Juego Favorito", value=_v(perfil, 13, ""), key="input_deporte")
        with col4:
            transporte = st.text_input("Transporte Favorito (Ej: Tren, Avión)", value=_v(perfil, 14, ""), key="input_transporte")
        st.write("---")
        st.subheader("👩‍🏫 Docente o grupo escolar")
        st.caption(
            "Opcional: nombre de la docente o del grupo (p. ej. Profe Ana · 1º A). "
            "En **Zona docentes** se asocia la **cédula** y el acceso; aquí solo se guarda el nombre para enlazar alumnos con ese grupo."
        )
        _doc_def = obtener_nombre_docente(estudiante_id_actual) if estudiante_id_actual else ""
        nombre_docente = st.text_input(
            "Nombre de la docente o del grupo (p. ej. Profe Ana · 1º A)",
            value=_doc_def,
            key="input_nombre_docente",
            placeholder="Ej: Sra. Martínez",
        )
        st.write("---")
        st.subheader("🎓 Tutor LeeConmigo (acompañamiento en la app)")
        st.caption(
            "Opcional: nombre de quien acompaña el avance en **Zona Tutores**. "
            "La **cédula**, la contraseña y el **correo** del tutor se configuran en esa zona, no en el registro del niño."
        )
        _tut_def = obtener_nombre_tutor(estudiante_id_actual) if estudiante_id_actual else ""
        nombre_tutor = st.text_input(
            "Nombre del tutor en LeeConmigo",
            value=_tut_def,
            key="input_nombre_tutor",
            placeholder="Ej: Profe Luis (puede coincidir con docente de aula)",
        )
        st.write("---")
        st.subheader("🔐 Clave del representante")
        clave_album_val = _v(perfil, 19, "")
        clave_album = st.text_input(
            "Clave del representante (PIN o contraseña)",
            value="",
            type="password",
            key="input_clave_album",
            placeholder="Dejar en blanco para no cambiar" if estudiante_id_actual else "Opcional",
        )
        # Clave del niño: se elige con matriz de emojis (fuera del form, ver abajo)
        submit_button = st.form_submit_button("💾 GUARDAR PERFIL" if estudiante_id_actual else "💾 CREAR PERFIL")

    # Familiares fuera del form principal: Streamlit no permite formularios anidados ni st.button dentro del form.
    if estudiante_id_actual:
        st.write("---")
        st.subheader("👨‍👩‍👧 Datos de familiares")
        st.caption("Agrega abuelos, tíos, primos, etc. para personalizar las lecciones con nombres de su familia.")
        familiares = listar_familiares(estudiante_id_actual)
        for (fid, tipo, nombre_f, _orden) in familiares:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{tipo}:** {nombre_f}")
            with c2:
                if st.button("🗑️ Quitar", key=f"del_fam_{fid}"):
                    eliminar_familiar(fid)
                    st.rerun()
        with st.expander("➕ Agregar familiar"):
            _kid = estudiante_id_actual
            tipo_f = st.selectbox("Parentesco", TIPOS_FAMILIAR, key=f"fam_tipo_{_kid}")
            nombre_f = st.text_input("Nombre", key=f"fam_nombre_{_kid}", placeholder="Ej: Margarita")
            if st.button("Agregar", key=f"fam_agregar_{_kid}"):
                if nombre_f and nombre_f.strip():
                    agregar_familiar(estudiante_id_actual, tipo_f, nombre_f.strip())
                    st.rerun()
                else:
                    st.warning("Escribe el nombre del familiar.")

    if submit_button:
        # Clave del niño: desde la matriz de emojis (session state)
        lista_final = st.session_state.get("config_emoji_clave") or []
        while len(lista_final) < 3:
            lista_final.append(EMOJIS_CLAVE[0])
        clave_estudiante = "|".join(lista_final[:3])

        if not nombre or not mama or not papa:
            st.error("❌ Los campos 'Nombre', 'Mamá' y 'Papá' son obligatorios.")
        else:
            datos_estudiante = (
                padre_id,
                nombre,
                segundo_nombre or "",
                (apellidos or "").strip(),
                edad,
                genero,
                ciudad or "",
                mama,
                papa,
                hermanos or "",
                mascota or "",
                color_fav,
                animal or "",
                deporte or "",
                transporte or "",
                (clave_album or "").strip() or (clave_album_val if estudiante_id_actual and perfil else None),
                clave_estudiante,
                (nombre_docente or "").strip(),
                (nombre_tutor or "").strip(),
            )
            gal_nino = _listar_avatares_nino()

            def _aplicar_avatar_salon(id_est, pk):
                if not id_est or not gal_nino:
                    return
                p = st.session_state.get(pk)
                if not p or not isinstance(p, str):
                    return
                permitidas = {_normalizar_ruta_abs(a["path"]) for a in gal_nino}
                pn = _normalizar_ruta_abs(p.strip())
                if pn and pn in permitidas:
                    actualizar_avatar_estudiante(id_est, p.strip())

            if estudiante_id_actual:
                actualizar_estudiante(estudiante_id_actual, datos_estudiante)
                msg_ok = f"✅ Perfil de {nombre} actualizado."
                st.session_state.nombre_nino = nombre
                st.session_state.color_favorito = color_fav
                _aplicar_avatar_salon(
                    estudiante_id_actual,
                    f"config_avatar_nino_path_{estudiante_id_actual}",
                )
                if gal_nino:
                    msg_ok += " 📷 Avatar del Salón actualizado."
                st.success(msg_ok)
            else:
                if existe_estudiante_con_nombre(padre_id, nombre):
                    st.error("❌ Ya existe un perfil con ese nombre en este salón. Edita el perfil existente o usa otro nombre.")
                else:
                    nuevo_id = crear_estudiante(datos_estudiante)
                    if nuevo_id:
                        _aplicar_avatar_salon(nuevo_id, "config_avatar_nino_path_new")
                        st.session_state.estudiante_id = nuevo_id
                        st.session_state.nombre_nino = nombre
                        st.session_state.color_favorito = color_fav
                        st.session_state.config_estudiante_id = nuevo_id  # para mostrar Datos de familiares
                        msg_creado = f"✅ ¡Perfil de {nombre} creado y activado!"
                        if gal_nino:
                            msg_creado += " 📷 Avatar del Salón guardado."
                        st.success(msg_creado)
                        st.balloons()
                        st.rerun()  # recargar para mostrar la sección de familiares
                    else:
                        st.error("❌ Error al guardar en la base de datos.")

    # Reiniciar avance de lecciones (solo al editar un niño existente)
    if estudiante_id_actual:
        st.write("---")
        st.subheader("Avance de lecciones")
        if st.button("🔄 Reiniciar avance de lecciones", key="btn_reiniciar_avance"):
            reiniciar_avance_estudiante(estudiante_id_actual)
            prefix = f"est_{estudiante_id_actual}_"
            for k in list(st.session_state.keys()):
                if isinstance(k, str) and k.startswith(prefix):
                    st.session_state.pop(k, None)
            st.success("Avance reiniciado. El niño volverá a empezar desde la primera letra.")
            st.rerun()

    if st.button("⬅️ Volver"):
        st.session_state.pop("config_estudiante_id", None)
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
