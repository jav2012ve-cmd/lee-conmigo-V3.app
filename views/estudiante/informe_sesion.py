"""
Pantalla de informe de avance al finalizar la sesión del estudiante.
Muestra el resumen y permite enviar por correo al tutor.
"""
import html

import streamlit as st

from components.page_title import logo_markup_html
from datetime import datetime
from database.db_queries import (
    obtener_perfil_completo_nino,
    obtener_resumen_avance,
    obtener_email_padre,
)
from core.informe_avance import generar_informe_html, enviar_informe_email

LABEL_TIPO = {
    "VocalInicio": "Empieza con vocal",
    "VocalFin": "Termina con vocal",
    "VocalCompleta": "Completar vocales",
    "Directa": "Sílaba directa",
    "ArmarPalabra": "Armar palabra (álbum)",
}


def render_informe_sesion():
    estudiante_id = st.session_state.get("estudiante_id")
    nombre_nino = st.session_state.get("nombre_nino", "Estudiante")
    ciclo = st.session_state.get("ciclo_actual", "Ciclo 1")

    if not estudiante_id:
        st.warning("No hay estudiante en sesión.")
        if st.button("Volver al Salón"):
            st.session_state.pagina_activa = "salon_entrada"
            st.rerun()
        return

    info = obtener_perfil_completo_nino(estudiante_id)
    padre_id = info[1] if info and len(info) > 1 else None
    email_padre = obtener_email_padre(padre_id) if padre_id else None
    filas = obtener_resumen_avance(estudiante_id)
    fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    _lg = logo_markup_html(height_px=88, margin_right=0)
    _nn = html.escape((nombre_nino or "").strip() or "Estudiante")
    _ci = html.escape((ciclo or "").strip() or "Ciclo 1")
    _fe = html.escape(fecha_str)
    st.markdown(
        f"""
        <div style="text-align: center; padding: 20px; border-radius: 16px; background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border: 2px solid #2e7d32;">
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;margin-bottom:8px;">
              {_lg}
              <h1 style="color: #2e7d32; margin: 0;">Informe de avance</h1>
            </div>
            <p style="font-size: 1.2rem; color: #333;">{_nn} · {_ci}</p>
            <p style="color: #666;">{_fe}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    if not filas:
        st.info("Aún no hay registros de avance en lecciones. ¡Sigue practicando!")
    else:
        st.subheader("Resumen por letra y actividad")
        tabla = [["Letra / vocal", "Actividad", "Aciertos", "Errores"]]
        for f in filas:
            tabla.append([f[0], LABEL_TIPO.get(f[1], f[1]), str(f[2]), str(f[3])])
        st.table(tabla)
        total_aciertos = sum(f[2] for f in filas)
        total_errores = sum(f[3] for f in filas)
        st.markdown(f"**Total aciertos:** {total_aciertos} · **Total errores:** {total_errores}")

    html_informe = generar_informe_html(nombre_nino, ciclo, filas, fecha_str)

    st.write("---")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="📥 Descargar informe (HTML)",
            data=html_informe,
            file_name=f"informe_avance_{nombre_nino}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            key="btn_descargar_informe",
        )

    with col2:
        if email_padre:
            if st.button("📧 Enviar informe por correo al tutor", key="btn_enviar_informe"):
                ok, err = enviar_informe_email(email_padre, nombre_nino, html_informe)
                if ok:
                    st.success(f"Informe enviado a {email_padre}")
                else:
                    st.error(f"No se pudo enviar: {err}")
        else:
            st.caption("Configura el email del tutor en Configuración para enviar el informe por correo.")

    st.write("---")
    if st.button("🏠 Volver al Salón", type="primary", key="btn_volver_informe"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()
