import streamlit as st
import os

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
    obtener_email_padre,
    actualizar_email_padre,
    existe_estudiante_con_nombre,
    credencial_docente_tutor_existe,
    upsert_credencial_cedula_docente_tutor,
)
from core.password_utils import normalizar_cedula_o_clave_numerica

_PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_AVATARES_NINO_DIR = os.path.join(_PROJ_ROOT, "assets", "avatars_nino")


def _listar_avatares_nino():
    avatares = []
    try:
        os.makedirs(_AVATARES_NINO_DIR, exist_ok=True)
        if not os.path.isdir(_AVATARES_NINO_DIR):
            return []
        for name in sorted(os.listdir(_AVATARES_NINO_DIR)):
            lower = name.lower()
            if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                label = os.path.splitext(name)[0].replace("_", " ").replace("-", " ").strip()
                path_abs = os.path.join(_AVATARES_NINO_DIR, name)
                if os.path.isfile(path_abs):
                    avatares.append({"label": label.title() or name, "path": path_abs})
    except Exception:
        return []
    return avatares


def _index_avatar_en_galeria_nino(ruta_resuelta, lista):
    if not ruta_resuelta or not lista:
        return 0
    try:
        ra = os.path.normpath(os.path.abspath(ruta_resuelta))
    except Exception:
        return 0
    for i, av in enumerate(lista):
        try:
            ap = os.path.normpath(os.path.abspath(av["path"]))
            if ap == ra:
                return i
        except Exception:
            continue
    return 0


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

    st.subheader("Clave del niño (3 emojis)")
    st.caption("Elige 3 emojis en orden. Se irán llenando los espacios de arriba al hacer clic en la matriz.")
    # Tres espacios que se van llenando
    slot1 = lista_emoji[0] if len(lista_emoji) > 0 else "—"
    slot2 = lista_emoji[1] if len(lista_emoji) > 1 else "—"
    slot3 = lista_emoji[2] if len(lista_emoji) > 2 else "—"
    # Cajitas grises: más grandes, emoji centrado y bien proporcionado
    st.markdown(
        f"""
        <style>
        #config-clave-slots .slot-emoji {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 4.5rem; height: 4.5rem; font-size: 3rem; line-height: 1;
            border: 3px solid #ccc; border-radius: 14px; margin: 0 8px;
            background: #f8f9fa; vertical-align: middle;
        }}
        </style>
        <div id="config-clave-slots" style="text-align: center; margin: 20px 0; letter-spacing: 0.5rem;">
            <span class="slot-emoji">{slot1}</span>
            <span class="slot-emoji">{slot2}</span>
            <span class="slot-emoji">{slot3}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Matriz 3x3: solo estos botones usan type="primary" para poder darles emoji grande sin un <style> global que luego las pise.
    _mc = (st.session_state.get("color_favorito") or "#4A90E2").strip()
    if not _mc.startswith("#"):
        _mc = "#" + _mc
    st.markdown(
        f"""
        <style>
        section[data-testid="stMain"] button[kind="primary"],
        section[data-testid="stMain"] button[kind="primary"] * {{
            font-size: clamp(2.85rem, 9vmin, 3.55rem) !important;
            line-height: 1 !important;
        }}
        section[data-testid="stMain"] button[kind="primary"] {{
            min-height: 3.95rem !important;
            max-height: 3.95rem !important;
            height: 3.95rem !important;
            padding: 0.05rem 0.35rem !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
            background-color: {_mc} !important;
            color: #fff !important;
            border-radius: 20px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
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
    if lista_emoji:
        if st.button("🗑️ Quitar último emoji", key=f"emoji_quitar_{perfil_emoji_key}"):
            st.session_state.config_emoji_clave = lista_emoji[:-1]
            st.rerun()
    st.write("---")

    with st.form("form_registro_nino", clear_on_submit=False):
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
        st.subheader("📷 Avatar en la pantalla de bienvenida")
        st.caption(
            "El dibujo que elijas es el que verá el niño en el **Salón** al tocar su foto para entrar (junto al nombre). "
            "Las imágenes vienen de la carpeta del proyecto **assets/avatars_nino**. "
            "Ese avatar tiene **prioridad** sobre una foto del álbum con palabra clave = nombre del niño."
        )
        avatares_nino = _listar_avatares_nino()
        sel_key = f"config_avatar_nino_sel_{estudiante_id_actual or 'new'}"
        if avatares_nino:
            if sel_key not in st.session_state:
                ruta_vis = None
                if estudiante_id_actual and perfil:
                    ruta_vis = _foto_perfil_estudiante(
                        estudiante_id_actual, _v(perfil, 2, ""), _v(perfil, 15, "")
                    )
                st.session_state[sel_key] = _index_avatar_en_galeria_nino(ruta_vis, avatares_nino)
            if estudiante_id_actual and perfil:
                ruta_prev = _foto_perfil_estudiante(
                    estudiante_id_actual, _v(perfil, 2, ""), _v(perfil, 15, "")
                )
                if ruta_prev and os.path.isfile(ruta_prev):
                    st.image(ruta_prev, caption="Vista previa (Salón / álbum)", width=120)
            else:
                st.caption("_Tras guardar el perfil, el avatar elegido aparecerá en el Salón._")
            st.caption(f"**{len(avatares_nino)}** personajes disponibles. Elige uno y guarda el perfil.")
            ncols = 6
            for row0 in range(0, len(avatares_nino), ncols):
                row_items = avatares_nino[row0 : row0 + ncols]
                gcols = st.columns(ncols)
                for j, av in enumerate(row_items):
                    with gcols[j]:
                        st.image(av["path"], use_container_width=True)
                        cap = av["label"][:22] + ("…" if len(av["label"]) > 22 else "")
                        st.caption(cap)
            st.selectbox(
                "Selecciona el avatar del niño",
                range(len(avatares_nino)),
                format_func=lambda i: avatares_nino[i]["label"],
                key=sel_key,
            )
        else:
            st.warning(
                "Aún no hay dibujos en **assets/avatars_nino**. "
                "Añade archivos .png o .jpg en esa carpeta del proyecto para poder elegir avatar."
            )
            if estudiante_id_actual and perfil:
                ruta_prev = _foto_perfil_estudiante(
                    estudiante_id_actual, _v(perfil, 2, ""), _v(perfil, 15, "")
                )
                if ruta_prev and os.path.isfile(ruta_prev):
                    st.image(ruta_prev, caption="Foto actual (álbum o avatar previo)", width=120)
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
            "Opcional pero recomendado: la docente podrá ver en **Zona docentes** el listado y el avance "
            "de todos los niños que compartan exactamente este nombre (sin distinguir mayúsculas)."
        )
        _doc_def = obtener_nombre_docente(estudiante_id_actual) if estudiante_id_actual else ""
        nombre_docente = st.text_input(
            "Nombre de la docente o del grupo (p. ej. Profe Ana · 1º A)",
            value=_doc_def,
            key="input_nombre_docente",
            placeholder="Ej: Sra. Martínez",
        )
        cedula_docente = st.text_input(
            "Cédula de la docente (contraseña inicial en Zona docentes)",
            value="",
            type="password",
            key="input_cedula_docente",
            placeholder="Solo números; obligatoria la primera vez si hay nombre arriba",
            help="Quien configura el perfil debe conocer la cédula. La docente usará ese número para entrar la primera vez y luego podrá cambiar la contraseña.",
        )
        st.write("---")
        st.subheader("🎓 Tutor LeeConmigo (acompañamiento en la app)")
        st.caption(
            "Persona que seguirá el avance del niño **dentro de LeeConmigo** (Zona Tutores). "
            "Puede ser **la misma** que la docente de aula o **otra** (ej. maestra de apoyo, coordinación)."
        )
        _tut_def = obtener_nombre_tutor(estudiante_id_actual) if estudiante_id_actual else ""
        nombre_tutor = st.text_input(
            "Nombre del tutor en LeeConmigo",
            value=_tut_def,
            key="input_nombre_tutor",
            placeholder="Ej: Profe Luis (puede coincidir con docente de aula)",
        )
        cedula_tutor = st.text_input(
            "Cédula del tutor LeeConmigo (contraseña inicial en Zona Tutores)",
            value="",
            type="password",
            key="input_cedula_tutor",
            placeholder="Solo números; obligatoria la primera vez si hay nombre arriba",
            help="El tutor LeeConmigo usará ese número para entrar la primera vez y luego podrá cambiar la contraseña.",
        )
        st.write("---")
        st.subheader("📧 Correo del tutor")
        st.caption("Para recibir por correo el informe de avance al finalizar cada sesión del niño.")
        email_actual = obtener_email_padre(padre_id) or ""
        email_tutor = st.text_input("Correo electrónico del tutor", value=email_actual, key="input_email_tutor", placeholder="ejemplo@correo.com")
        st.write("---")
        st.subheader("🔐 Clave para edición del álbum")
        clave_album_val = _v(perfil, 19, "")
        clave_album = st.text_input("Clave para edición del álbum (PIN o contraseña)", value="", type="password", key="input_clave_album", placeholder="Dejar en blanco para no cambiar" if estudiante_id_actual else "Opcional")
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
            nd = (nombre_docente or "").strip()
            nt = (nombre_tutor or "").strip()
            ced_doc_digits = normalizar_cedula_o_clave_numerica(cedula_docente or "")
            ced_tut_digits = normalizar_cedula_o_clave_numerica(cedula_tutor or "")
            err_ced = None
            if nd:
                if not ced_doc_digits and not credencial_docente_tutor_existe("docente", nd):
                    err_ced = (
                        "Si indicaste **nombre de docente o grupo**, debes registrar la **cédula** "
                        "(contraseña inicial en Zona docentes)."
                    )
                elif ced_doc_digits and len(ced_doc_digits) < 5:
                    err_ced = "La cédula de la docente debe tener al menos 5 dígitos."
            if nt and not err_ced:
                if not ced_tut_digits and not credencial_docente_tutor_existe("tutor", nt):
                    err_ced = (
                        "Si indicaste **nombre del tutor LeeConmigo**, debes registrar la **cédula** "
                        "(contraseña inicial en Zona Tutores)."
                    )
                elif ced_tut_digits and len(ced_tut_digits) < 5:
                    err_ced = "La cédula del tutor debe tener al menos 5 dígitos."
            if err_ced:
                st.error(f"❌ {err_ced}")
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

                def _aplicar_avatar_salon(id_est, sk):
                    if not id_est or not gal_nino:
                        return
                    idx = int(st.session_state.get(sk, 0))
                    idx = max(0, min(idx, len(gal_nino) - 1))
                    actualizar_avatar_estudiante(id_est, gal_nino[idx]["path"])

                def _guardar_credenciales_doc_tut():
                    if ced_doc_digits and nd:
                        upsert_credencial_cedula_docente_tutor("docente", nd, ced_doc_digits)
                    if ced_tut_digits and nt:
                        upsert_credencial_cedula_docente_tutor("tutor", nt, ced_tut_digits)

                if estudiante_id_actual:
                    actualizar_estudiante(estudiante_id_actual, datos_estudiante)
                    _guardar_credenciales_doc_tut()
                    msg_ok = f"✅ Perfil de {nombre} actualizado."
                    st.session_state.nombre_nino = nombre
                    st.session_state.color_favorito = color_fav
                    _aplicar_avatar_salon(
                        estudiante_id_actual,
                        f"config_avatar_nino_sel_{estudiante_id_actual}",
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
                            _guardar_credenciales_doc_tut()
                            _aplicar_avatar_salon(nuevo_id, "config_avatar_nino_sel_new")
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
                # Registrar o actualizar correo del tutor (al crear o editar el perfil)
                if email_tutor and "@" in email_tutor:
                    actualizar_email_padre(padre_id, email_tutor.strip())

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
