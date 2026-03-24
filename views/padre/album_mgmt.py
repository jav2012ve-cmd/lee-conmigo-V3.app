import streamlit as st
import os
from database.db_queries import (
    guardar_en_album,
    obtener_album_nino,
    obtener_estudiantes_por_padre,
    obtener_pin_padre,
    obtener_claves_estudiante,
)
from core.album_categories import CATEGORIAS_ALBUM

def render_album_mgmt():
    st.title("📸 Gestión del Álbum Familiar")
    st.write("Sube las fotos que el niño usará para aprender. ¡Recuerda que el vínculo emocional es la clave!")

    padre_id = st.session_state.get("padre_id") or 1
    estudiantes = obtener_estudiantes_por_padre(padre_id) or []

    if not estudiantes:
        st.warning("⚠️ No hay perfiles de estudiante. Crea uno en la Configuración del Salón.")
        if st.button("Ir a Configuración"):
            st.session_state.pagina_activa = "config_salon"
            st.rerun()
        return

    def _nombre_completo(e):
        p = (e[1] or "").strip()
        s = (e[2] or "").strip() if len(e) > 2 else ""
        a = (e[3] or "").strip() if len(e) > 3 else ""
        return (" ".join(filter(None, [p, s, a]))).strip() or p

    # Opciones por nombre completo (único con " (id X)" si hay repetidos)
    opciones = ["— Elige un estudiante —"]
    mapa_display_a_id = {}
    for e in estudiantes:
        id_est = e[0]
        nombre_completo = _nombre_completo(e)
        display = nombre_completo
        if display in mapa_display_a_id:
            display = f"{nombre_completo} (id {id_est})"
        opciones.append(display)
        mapa_display_a_id[display] = id_est

    if "album_estudiante_id" not in st.session_state:
        st.session_state.album_estudiante_id = None
    if "album_acceso_confirmado_ids" not in st.session_state:
        st.session_state.album_acceso_confirmado_ids = []

    idx_sel = st.selectbox(
        "**Selecciona el estudiante** cuyo álbum quieres gestionar",
        range(len(opciones)),
        format_func=lambda i: opciones[i],
    )
    estudiante_seleccionado_id = mapa_display_a_id.get(opciones[idx_sel]) if idx_sel > 0 else None
    estudiante_seleccionado_nombre = opciones[idx_sel] if idx_sel > 0 else None

    # Al cambiar de estudiante, usamos el elegido (no confirmado aún si es otro)
    if estudiante_seleccionado_id != st.session_state.album_estudiante_id:
        st.session_state.album_estudiante_id = estudiante_seleccionado_id
        st.session_state.album_estudiante_nombre = estudiante_seleccionado_nombre

    if not estudiante_seleccionado_id:
        st.info("Elige un estudiante de la lista para continuar.")
        if st.button("⬅️ Volver al Salón"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    # Paso 2: confirmación o clave de acceso (clave del álbum del niño, o PIN del padre)
    acceso_ok = estudiante_seleccionado_id in (st.session_state.album_acceso_confirmado_ids or [])

    if not acceso_ok:
        clave_album_est, _ = obtener_claves_estudiante(estudiante_seleccionado_id)
        pin_padre = obtener_pin_padre(padre_id)
        nombre_nino = estudiante_seleccionado_nombre or "el niño"

        if clave_album_est:
            st.subheader("🔐 Clave de acceso al álbum")
            st.caption(f"Para gestionar el álbum de **{nombre_nino}**, introduce la clave definida en su perfil.")
            clave_ingresada = st.text_input("Clave del álbum", type="password", key="album_clave_input", placeholder="Clave del perfil del niño")
            if st.button("Confirmar acceso"):
                if (clave_ingresada or "").strip() == clave_album_est:
                    if estudiante_seleccionado_id not in st.session_state.album_acceso_confirmado_ids:
                        st.session_state.album_acceso_confirmado_ids = list(
                            st.session_state.album_acceso_confirmado_ids or []
                        ) + [estudiante_seleccionado_id]
                    st.success("Acceso confirmado.")
                    st.rerun()
                else:
                    st.error("Clave incorrecta. Vuelve a intentarlo.")
        elif pin_padre:
            st.subheader("🔐 Clave de acceso")
            st.caption(f"Para gestionar el álbum de **{nombre_nino}**, introduce tu PIN de tutor.")
            pin_ingresado = st.text_input("PIN", type="password", key="album_pin_input", placeholder="Ej: 1234")
            if st.button("Confirmar acceso"):
                if (pin_ingresado or "").strip() == pin_padre:
                    if estudiante_seleccionado_id not in st.session_state.album_acceso_confirmado_ids:
                        st.session_state.album_acceso_confirmado_ids = list(
                            st.session_state.album_acceso_confirmado_ids or []
                        ) + [estudiante_seleccionado_id]
                    st.success("Acceso confirmado.")
                    st.rerun()
                else:
                    st.error("PIN incorrecto. Vuelve a intentarlo.")
        else:
            st.subheader("Confirmación")
            st.caption(f"Confirma que eres el tutor de **{nombre_nino}** para gestionar su álbum.")
            if st.button("Sí, soy el tutor. Acceder al álbum"):
                if estudiante_seleccionado_id not in (st.session_state.album_acceso_confirmado_ids or []):
                    st.session_state.album_acceso_confirmado_ids = list(
                        st.session_state.album_acceso_confirmado_ids or []
                    ) + [estudiante_seleccionado_id]
                st.rerun()
        if st.button("⬅️ Volver al Salón"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    # Paso 3: gestión del álbum (estudiante ya seleccionado y acceso confirmado)
    id_est = st.session_state.album_estudiante_id
    nombre_nino = st.session_state.get("album_estudiante_nombre") or "el niño"

    with st.expander("➕ Añadir nueva foto al álbum", expanded=True):
        with st.form("upload_foto_form"):
            col1, col2 = st.columns(2)
            with col1:
                palabra = st.text_input("Palabra Clave (ej: MAMÁ, DADO, REX)").strip().upper()
            with col2:
                categoria = st.selectbox("Categoría", CATEGORIAS_ALBUM)

            uploaded_file = st.file_uploader("Elige una foto", type=["png", "jpg", "jpeg"])

            submit = st.form_submit_button("💾 Guardar en el Álbum")

            if submit:
                if uploaded_file and palabra:
                    try:
                        user_path = os.path.join("assets", "uploads", str(id_est))
                        os.makedirs(user_path, exist_ok=True)
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        file_name = f"{categoria}_{palabra.replace(' ', '_')}{file_extension}"
                        file_path = os.path.join(user_path, file_name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        exito = guardar_en_album(id_est, palabra, categoria, file_path)
                        if exito:
                            st.success(f"✅ ¡'{palabra}' ha sido añadida con éxito!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Error al registrar en la base de datos.")
                    except Exception as e:
                        st.error(f"❌ Error al guardar el archivo: {e}")
                else:
                    st.warning("⚠️ Por favor, escribe una palabra y selecciona una foto.")

    st.divider()

    st.subheader(f"🖼️ Fotos actuales en el álbum de {nombre_nino}")
    fotos = obtener_album_nino(id_est)

    if fotos:
        for cat in CATEGORIAS_ALBUM:
            fotos_cat = [f for f in fotos if (f[1] or "").strip() == cat]
            if not fotos_cat:
                continue
            st.markdown(f"**{cat}**")
            cols = st.columns(4)
            for i, (palabra_db, cat_db, path_db) in enumerate(fotos_cat):
                with cols[i % 4]:
                    if os.path.exists(path_db):
                        st.image(path_db, caption=f"{palabra_db}", use_container_width=True)
                    else:
                        st.error(f"Archivo no encontrado: {palabra_db}")
            st.write("")
    else:
        st.info("El álbum está vacío. ¡Empieza subiendo la primera foto!")

    if st.button("⬅️ Volver al Salón"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
