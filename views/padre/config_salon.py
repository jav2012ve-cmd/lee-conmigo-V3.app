import streamlit as st
import os
from components.colores import OPCIONES_COLOR_FAVORITO
from database.db_queries import (
    crear_estudiante,
    actualizar_estudiante,
    actualizar_avatar_estudiante,
    obtener_album_nino,
    obtener_perfil_completo_nino,
    listar_familiares,
    agregar_familiar,
    eliminar_familiar,
    reiniciar_avance_estudiante,
    obtener_email_padre,
    actualizar_email_padre,
    existe_estudiante_con_nombre,
)
def _foto_perfil_estudiante(id_est, nombre, avatar_path):
    """Solo usa avatar_path o una foto del álbum cuya palabra clave sea el nombre del niño. No usa otras fotos (ej. familiares)."""
    if avatar_path and os.path.isfile(avatar_path):
        return avatar_path
    album = obtener_album_nino(id_est) or []
    nombre_upper = (nombre or "").strip().upper()
    for palabra, _cat, img_path in album:
        if img_path and os.path.isfile(img_path) and (palabra or "").strip().upper() == nombre_upper:
            return img_path
    return None

TIPOS_FAMILIAR = ["Abuela", "Abuelo", "Tía", "Tío", "Primo", "Prima", "Hermano", "Hermana", "Otro"]

# 9 emojis para la clave del estudiante (elegir 3 en orden); matriz 3x3
EMOJIS_CLAVE = ["🐱", "🐶", "🌟", "❤️", "🌈", "🎈", "🦋", "⚽", "🍎"]

def render_config_salon():
    st.title("⚙️ Configuración del perfil del niño")
    st.caption("Inscribe un nuevo estudiante. Para ver o editar datos con PIN, usa **Zona de padres** desde el Salón.")
    padre_id = st.session_state.get("padre_id") or 1
    # Si acabamos de crear un perfil (o tenemos un id en sesión), mostramos el formulario con Datos de familiares
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
        st.session_state.config_emoji_clave = [e for e in clave_guardada.split("|") if e in EMOJIS_CLAVE][:3]
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
    # Matriz 3x3 de emojis: botones más grandes y emojis bien visibles
    st.markdown(
        """
        <style>
        main .stButton > button { font-size: 3.5rem !important; min-height: 5rem !important; border-radius: 14px !important; padding: 0.5rem !important; line-height: 1 !important; }
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
                    if st.button(EMOJIS_CLAVE[idx], key=f"emoji_grid_{perfil_emoji_key}_{idx}", use_container_width=True):
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
        st.subheader("📷 Foto en la pantalla de bienvenida")
        st.caption(
            "Esta foto es la que verá el niño en el Salón al elegir su perfil (¡Soy [nombre]!). "
            "Puedes subir una imagen aquí **o** en **Gestión del Álbum** añadir una foto cuya **palabra clave** sea exactamente el nombre del niño (ej. José, Camila)."
        )
        # Mostrar foto actual al editar
        if estudiante_id_actual and perfil:
            ruta_actual = _foto_perfil_estudiante(estudiante_id_actual, _v(perfil, 2, ""), _v(perfil, 15, ""))
            if ruta_actual and os.path.isfile(ruta_actual):
                st.image(ruta_actual, caption="Foto actual en el Salón", width=120)
            else:
                st.caption("_Aún no hay foto. Sube una aquí o añade en el Álbum una foto con palabra clave = nombre del niño._")
        foto_salon = st.file_uploader(
            "Subir foto para el Salón (opcional)",
            type=["jpg", "jpeg", "png"],
            key="foto_salon_upload",
        )
        if foto_salon:
            st.session_state._avatar_file_bytes = foto_salon.getvalue()
            st.session_state._avatar_file_name = foto_salon.name
        st.write("---")
        st.subheader("Intereses para Lectura")
        col3, col4 = st.columns(2)
        with col3:
            deporte = st.text_input("Deporte o Juego Favorito", value=_v(perfil, 13, ""), key="input_deporte")
        with col4:
            transporte = st.text_input("Transporte Favorito (Ej: Tren, Avión)", value=_v(perfil, 14, ""), key="input_transporte")
        st.write("---")
        st.subheader("📧 Correo del tutor")
        st.caption("Para recibir por correo el informe de avance al finalizar cada sesión del niño.")
        email_actual = obtener_email_padre(padre_id) or ""
        email_tutor = st.text_input("Correo electrónico del tutor", value=email_actual, key="input_email_tutor", placeholder="ejemplo@correo.com")
        st.write("---")
        st.subheader("🔐 Clave para edición del álbum")
        clave_album_val = _v(perfil, 19, "")
        clave_album = st.text_input("Clave para edición del álbum (PIN o contraseña)", value="", type="password", key="input_clave_album", placeholder="Dejar en blanco para no cambiar" if estudiante_id_actual else "Opcional")
        # Datos de familiares (dentro del formulario de edición)
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
                with st.form("form_familiar"):
                    tipo_f = st.selectbox("Parentesco", TIPOS_FAMILIAR, key="fam_tipo")
                    nombre_f = st.text_input("Nombre", key="fam_nombre", placeholder="Ej: Margarita")
                    if st.form_submit_button("Agregar"):
                        if nombre_f and nombre_f.strip():
                            agregar_familiar(estudiante_id_actual, tipo_f, nombre_f.strip())
                            st.rerun()
                        else:
                            st.warning("Escribe el nombre del familiar.")
        # Clave del niño: se elige con matriz de emojis (fuera del form, ver abajo)
        submit_button = st.form_submit_button("💾 GUARDAR PERFIL" if estudiante_id_actual else "💾 CREAR PERFIL")

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
            )
            id_para_avatar = estudiante_id_actual
            if estudiante_id_actual:
                actualizar_estudiante(estudiante_id_actual, datos_estudiante)
                st.success(f"✅ Perfil de {nombre} actualizado.")
                st.session_state.nombre_nino = nombre
                st.session_state.color_favorito = color_fav
            else:
                if existe_estudiante_con_nombre(padre_id, nombre):
                    st.error("❌ Ya existe un perfil con ese nombre en este salón. Edita el perfil existente o usa otro nombre.")
                else:
                    nuevo_id = crear_estudiante(datos_estudiante)
                    if nuevo_id:
                        id_para_avatar = nuevo_id
                        st.session_state.estudiante_id = nuevo_id
                        st.session_state.nombre_nino = nombre
                        st.session_state.color_favorito = color_fav
                        st.session_state.config_estudiante_id = nuevo_id  # para mostrar Datos de familiares
                        st.success(f"✅ ¡Perfil de {nombre} creado y activado!")
                        st.balloons()
                        st.rerun()  # recargar para mostrar la sección de familiares
                    else:
                        st.error("❌ Error al guardar en la base de datos.")
                        id_para_avatar = None
            # Guardar foto del salón si se subió una (guardada en session state al elegir el archivo)
            avatar_bytes = st.session_state.get("_avatar_file_bytes")
            avatar_name = st.session_state.get("_avatar_file_name", "")
            if id_para_avatar and avatar_bytes:
                avatares_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "avatares")
                os.makedirs(avatares_dir, exist_ok=True)
                ext = (os.path.splitext(avatar_name)[1] or ".png").lower()
                if ext not in (".jpg", ".jpeg", ".png"):
                    ext = ".png"
                ruta_avatar = os.path.join(avatares_dir, f"est_{id_para_avatar}{ext}")
                with open(ruta_avatar, "wb") as f:
                    f.write(avatar_bytes)
                actualizar_avatar_estudiante(id_para_avatar, ruta_avatar)
                st.success("📷 Foto del salón actualizada.")
                st.session_state.pop("_avatar_file_bytes", None)
                st.session_state.pop("_avatar_file_name", None)
            # Registrar o actualizar correo del tutor (al crear o editar el perfil)
            if email_tutor and "@" in email_tutor:
                actualizar_email_padre(padre_id, email_tutor.strip())

    # Reiniciar avance de lecciones (solo al editar un niño existente)
    if estudiante_id_actual:
        st.write("---")
        st.subheader("📚 Avance de lecciones")
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
