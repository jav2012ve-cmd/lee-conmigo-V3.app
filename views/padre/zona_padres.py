"""
Zona de padres: acceso con PIN. Solo editar información de representados y ver resumen de desempeño.
"""
from datetime import datetime
import streamlit as st
from components.colores import nombre_de_color
from database.db_queries import (
    obtener_pin_padre,
    obtener_estudiantes_por_padre,
    obtener_perfil_completo_nino,
    obtener_resumen_avance,
    obtener_ultimo_ingreso,
)

LABEL_TIPO = {
    "VocalInicio": "Empieza con vocal",
    "VocalFin": "Termina con vocal",
    "VocalCompleta": "Completar vocales",
    "Directa": "Sílaba directa",
    "ArmarPalabra": "Armar palabra (álbum)",
}

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def _formatear_fecha_ultimo_ingreso(ts):
    """Convierte timestamp de la DB a texto legible (ej. 2 de marzo de 2025, 14:30)."""
    if not ts:
        return None
    s = str(ts).strip()
    try:
        if "T" in s:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        elif len(s) >= 19 and s[10] == " ":
            d = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        else:
            d = datetime.strptime(s[:10], "%Y-%m-%d")
        if d.hour == 0 and d.minute == 0:
            return f"{d.day} de {MESES[d.month - 1]} de {d.year}"
        return f"{d.day} de {MESES[d.month - 1]} de {d.year}, a las {d.hour:02d}:{d.minute:02d}"
    except Exception:
        return s


def _resumen_actividades(filas_avance):
    """Devuelve texto corto: qué actividades ha practicado (vocales, sílabas, álbum)."""
    if not filas_avance:
        return "aún no ha registrado actividades."
    vocales = sorted(set(f[0] for f in filas_avance if f[1] in ("VocalInicio", "VocalFin", "VocalCompleta")))
    tiene_directa = any(f[1] == "Directa" for f in filas_avance)
    tiene_album = any(f[1] == "ArmarPalabra" for f in filas_avance)
    partes = []
    if vocales:
        partes.append(f"vocales ({', '.join(vocales)})")
    if tiene_directa:
        partes.append("sílabas directas")
    if tiene_album:
        partes.append("armar palabras del álbum")
    if not partes:
        return "actividades registradas (ver detalle más abajo)."
    return ", ".join(partes) + "."


def render_zona_padres():
    padre_id = st.session_state.get("padre_id") or 1
    id_elegido = st.session_state.get("zona_padres_estudiante_id")
    acceso_ok = st.session_state.get("zona_padres_acceso_ok", False)

    estudiantes = obtener_estudiantes_por_padre(padre_id) or []

    def _nombre_completo(datos):
        p = (datos[1] or "").strip()
        s = (datos[2] or "").strip() if len(datos) > 2 else ""
        a = (datos[3] or "").strip() if len(datos) > 3 else ""
        return (" ".join(filter(None, [p, s, a]))).strip() or p

    # Una sola entrada por persona: mismo (primer_nombre, segundo_nombre, apellidos) → quedarse con id más reciente (sin triplicados en el menú)
    grupos = {}
    for datos in estudiantes:
        p = (datos[1] or "").strip()
        s = (datos[2] or "").strip() if len(datos) > 2 else ""
        a = (datos[3] or "").strip() if len(datos) > 3 else ""
        key = (p, s, a)
        id_est = datos[0]
        if key not in grupos or id_est > grupos[key][0]:
            grupos[key] = (id_est, _nombre_completo(datos))
    lista_con_display = sorted(grupos.values(), key=lambda x: (x[1].lower(), x[0]))

    if not lista_con_display:
        st.title("👨‍👩‍👧 Zona de padres")
        st.info("Aún no hay estudiantes registrados. Usa **Registro** (desde el Salón) para dar de alta a un niño.")
        if st.button("⬅️ Volver al Salón"):
            st.session_state.pagina_activa = "salon_entrada"
            st.session_state.pop("zona_padres_estudiante_id", None)
            st.session_state.zona_padres_acceso_ok = False
            st.rerun()
        return

    # Paso 1: seleccionar al estudiante que representas (nombre completo con apellidos)
    if id_elegido is None:
        st.title("👨‍👩‍👧 Zona de padres")
        st.caption("Selecciona al estudiante que representas (nombre y apellidos completos).")
        opciones = ["— Elige —"] + [d for _, d in lista_con_display]
        mapa_display_a_id = {d: id_ for id_, d in lista_con_display}
        sel = st.selectbox("Estudiante que represento (nombre y apellidos):", opciones, key="zona_selector_est")
        if st.button("✏️ Editar / actualizar perfil del estudiante", type="primary", key="zona_btn_continuar"):
            if sel and sel != "— Elige —":
                st.session_state.zona_padres_estudiante_id = mapa_display_a_id.get(sel)
                st.session_state.zona_padres_estudiante_display = sel
                st.rerun()
            else:
                st.warning("Elige un estudiante para continuar.")
        st.write("---")
        if st.button("⬅️ Volver al Salón", key="zona_volver_selector"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    # Paso 2: cargar PIN (estudiante ya elegido)
    nombre_est_display = next((d for id_, d in lista_con_display if id_ == id_elegido), "")
    if not acceso_ok:
        st.title("👨‍👩‍👧 Zona de padres")
        st.caption(f"Representas a **{nombre_est_display}**. Introduce tu PIN o contraseña de tutor para acceder.")
        # Contraseña y Entrar en la misma fila; sin sugerencias de contraseña fuerte del navegador
        col_pin, col_entrar = st.columns(2)
        with col_pin:
            pin_ingresado = st.text_input(
                "PIN o contraseña",
                type="password",
                key="zona_padres_pin",
                placeholder="Ej: 1234",
                autocomplete="off",
            )
        with col_entrar:
            st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)  # alinear con el campo
            if st.button("Entrar", type="primary", key="zona_padres_entrar", use_container_width=True):
                pin_correcto = obtener_pin_padre(padre_id)
                if not pin_correcto:
                    st.error("No hay PIN configurado para este tutor. Usa Registro o Configuración para establecerlo.")
                elif (pin_ingresado or "").strip() == pin_correcto:
                    st.session_state.zona_padres_acceso_ok = True
                    st.rerun()
                else:
                    st.error("PIN o contraseña incorrectos. Vuelve a intentarlo.")
        # Botones del mismo tamaño
        col_cambiar, col_volver = st.columns(2)
        with col_cambiar:
            if st.button("↩️ Cambiar de estudiante", key="zona_cambiar_est", use_container_width=True):
                st.session_state.pop("zona_padres_estudiante_id", None)
                st.rerun()
        with col_volver:
            if st.button("⬅️ Volver al Salón", key="zona_padres_volver_pin", use_container_width=True):
                st.session_state.pop("zona_padres_estudiante_id", None)
                st.session_state.pagina_activa = "salon_entrada"
                st.rerun()
        return

    # Paso 3: ya entró; mostrar resumen e información del representado elegido
    nombre_elegido = nombre_est_display

    st.title("👨‍👩‍👧 Zona de padres")
    st.caption("Edita la información de tu representado y revisa su resumen de desempeño.")

    perfil = obtener_perfil_completo_nino(id_elegido)
    filas_avance = obtener_resumen_avance(id_elegido)

    # Botones de acción (incluye Gestión del Álbum desde Zona de padres)
    st.caption(f"Representando a **{nombre_elegido}**.")
    col_editar, col_album, col_cambiar, col_salir = st.columns(4)
    with col_editar:
        if st.button("✏️ Editar información", key="zona_btn_editar", use_container_width=True):
            st.session_state.pagina_activa = "config_salon"
            st.session_state.config_selector_nino = nombre_elegido
            st.session_state.zona_padres_acceso_ok = False
            st.session_state.pop("zona_padres_estudiante_id", None)
            st.rerun()
    with col_album:
        if st.button("📸 Gestionar Álbum", key="zona_btn_album", use_container_width=True):
            st.session_state.pagina_activa = "album_mgmt"
            st.rerun()
    with col_cambiar:
        if st.button("↩️ Cambiar de estudiante", key="zona_btn_cambiar_est", use_container_width=True):
            st.session_state.pop("zona_padres_estudiante_id", None)
            st.session_state.zona_padres_acceso_ok = False
            st.rerun()
    with col_salir:
        if st.button("🔒 Salir de Zona de padres", key="zona_btn_salir", use_container_width=True):
            st.session_state.pop("zona_padres_estudiante_id", None)
            st.session_state.zona_padres_acceso_ok = False
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()

    st.write("---")

    # Pestañas: Informe (resumen e indicaciones) y Perfil (solo lectura)
    tab_informe, tab_perfil = st.tabs(["📊 Informe de avance", "📋 Perfil del estudiante"])

    def _v(row, idx, default=""):
        if row is None or idx >= len(row):
            return default
        v = row[idx]
        return v if v is not None else default

    # Ranking en el grupo (mismo padre)
    estudiantes_grupo = obtener_estudiantes_por_padre(padre_id) or []
    lista_ids = [e[0] for e in estudiantes_grupo]
    total_aciertos = sum(f[2] for f in filas_avance) if filas_avance else 0
    total_errores = sum(f[3] for f in filas_avance) if filas_avance else 0
    total_actividades = total_aciertos + total_errores
    eficiencia = (total_aciertos / total_actividades) if total_actividades else 0.0
    ranking_lecciones = []
    ranking_eficiencia = []
    for eid in lista_ids:
        r = obtener_resumen_avance(eid) or []
        a = sum(x[2] for x in r)
        b = sum(x[3] for x in r)
        tot = a + b
        eff = (a / tot) if tot else 0.0
        ranking_lecciones.append((eid, tot))
        ranking_eficiencia.append((eid, eff))
    ranking_lecciones.sort(key=lambda x: -x[1])
    ranking_eficiencia.sort(key=lambda x: -x[1])
    lugar_lecciones = next((i + 1 for i, (eid, _) in enumerate(ranking_lecciones) if eid == id_elegido), 1)
    lugar_eficiencia = next((i + 1 for i, (eid, _) in enumerate(ranking_eficiencia) if eid == id_elegido), 1)
    n_grupo = len(lista_ids)

    with tab_informe:
        # 1. Resumen de la última sesión (párrafo sencillo con fecha de último ingreso y actividades)
        st.subheader("📌 Resumen de la última sesión")
        ultimo_ts = obtener_ultimo_ingreso(id_elegido)
        fecha_ingreso = _formatear_fecha_ultimo_ingreso(ultimo_ts)
        actividades_texto = _resumen_actividades(filas_avance)
        if fecha_ingreso:
            st.markdown(
                f"**{nombre_elegido}** ingresó por última vez el **{fecha_ingreso}**. "
                f"En sus sesiones ha practicado: {actividades_texto}"
            )
        else:
            st.markdown(
                f"**{nombre_elegido}** ha practicado: {actividades_texto} "
                f"*(Cuando entre al juego, aquí se mostrará la fecha de su último ingreso.)*"
            )

        st.write("---")
        # 2. Consolidado de avances (párrafo + comparativa con el grupo)
        st.subheader("📈 Consolidado de avances")
        if filas_avance:
            st.markdown(
                f"Sus avances hasta el momento son: **{total_aciertos} aciertos** y **{total_errores} errores** en total. "
                f"En relación con el grupo, su representado ocupa el **lugar {lugar_lecciones} de {n_grupo}** por cantidad de lecciones estudiadas "
                f"y el **lugar {lugar_eficiencia} de {n_grupo}** en términos de eficiencia."
            )
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total aciertos", total_aciertos)
            with col2:
                st.metric("Total errores", total_errores)
        else:
            st.markdown(
                "Sus avances hasta el momento no tienen registros. Cuando practique lecciones, aquí aparecerá el consolidado y su posición en el grupo."
            )
            st.caption("Sin registros aún.")

        st.write("---")
        # 3. Indicaciones generales y sugerencias
        st.subheader("💡 Indicaciones generales y sugerencias")
        st.markdown("""
        - **Practicar poco a poco**: 10–15 minutos al día suelen ser más efectivos que sesiones largas.
        - **Celebrar los aciertos**: Reforzar lo que hace bien anima a seguir practicando.
        - **No corregir en exceso**: Si se equivoca, puede volver a intentar; el sistema ya registra aciertos y errores.
        - **Usar el álbum**: Las palabras con fotos familiares (mamá, papá, mascota) ayudan a mantener la motivación.
        - **Revisar este informe** con calma para ver en qué letras o actividades conviene insistir.
        """)

        st.write("---")
        # 4. Tablas con el detalle
        st.subheader("📋 Detalle por letra y actividad")
        if not filas_avance:
            st.info("No hay detalle aún. El niño debe practicar para que aparezca aquí.")
        else:
            tabla = [["Letra / vocal", "Actividad", "Aciertos", "Errores"]]
            for f in filas_avance:
                tabla.append([f[0], LABEL_TIPO.get(f[1], f[1]), str(f[2]), str(f[3])])
            st.table(tabla)

    with tab_perfil:
        st.subheader("📋 Información cargada (solo lectura)")
        if perfil:
            st.markdown(
                f"""
                | Campo | Valor |
                |-------|-------|
                | Nombre | {_v(perfil, 2, "—")} {_v(perfil, 3, "")} |
                | Apellidos | {_v(perfil, 21, "—")} |
                | Edad | {_v(perfil, 4, "—")} |
                | Género | {_v(perfil, 5, "—")} |
                | Ciudad | {_v(perfil, 6, "—")} |
                | Mamá | {_v(perfil, 7, "—")} |
                | Papá | {_v(perfil, 8, "—")} |
                | Hermanos | {_v(perfil, 9, "—")} |
                | Mascota | {_v(perfil, 10, "—")} |
                | Color favorito | {nombre_de_color(_v(perfil, 11, ""))} |
                | Animal favorito | {_v(perfil, 12, "—")} |
                | Deporte / juego | {_v(perfil, 13, "—")} |
                | Transporte favorito | {_v(perfil, 14, "—")} |
                """
            )
            st.caption("Para modificar estos datos, pulsa **Editar información** arriba.")
        else:
            st.info("No se pudo cargar el perfil.")

    st.write("---")
    if st.button("⬅️ Volver al Salón", key="zona_volver_final"):
        st.session_state.pop("zona_padres_estudiante_id", None)
        st.session_state.zona_padres_acceso_ok = False
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
