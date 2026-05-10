import html

import streamlit as st

from components.cards import (
    ABECEDARIO_MATRIZ_SFX_CATEGORIA,
    render_album_card_karaoke,
    render_album_card_placeholder,
)
from components.page_title import render_encabezado_logo_titulo_acciones
from core.abecedario_ruta import (
    FILAS_ABECEDARIO_9X3,
    resolver_ruta_imagen_abecedario,
    slug_sugerido_generico,
)


def render_abecedario_matriz(*, titulo_extra: str | None = None):
    """
    Matriz 9×3 (9 filas, 3 columnas): tarjetas estilo álbum con karaoke al tocar
    la imagen y sonido extra (abecedario/ + categorías SFX del álbum donde aplique).
    """
    nombre = st.session_state.get("nombre_nino", "Explorador") or "Explorador"
    color = st.session_state.get("color_favorito", "#4A90E2") or "#4A90E2"
    te = (titulo_extra or "").strip()
    titulo = f"Abecedario — {te}" if te else "Abecedario"
    nombre_esc = html.escape(nombre)
    html_centro = (
        f'<p style="margin:0.45rem 0 0 0;font-size:1.02rem;color:#333;line-height:1.45;font-weight:400;">'
        f'Hola, <b>{nombre_esc}</b>. Cada tarjeta une una letra con una figura conocida '
        f"(muchas con sonidos llamativos: ambulancia, león, tambor…). "
        f"<b>Toca la imagen</b> para el karaoke por sílabas; si hay archivo de sonido, "
        f"se reproduce después (toca el botón de sonido en la tarjeta si está disponible).</p>"
        f'<p style="margin:0.35rem 0 0 0;font-size:0.82rem;color:#666;line-height:1.35;">'
        f"Matriz <b>9 filas × 3 columnas</b> (27 letras, Ñ incluida). "
        f"Imágenes: <code>assets/genericos/</code> · Sonidos: <code>assets/sfx/abecedario/</code> "
        f"y, si existe, los mismos archivos de sonido que en Instrumentos musicales o Sonidos especiales del álbum.</p>"
    )

    def _acciones_abecedario_hdr():
        if st.button("Volver a mi inicio", use_container_width=True, key="abecedario_volver_hub"):
            st.session_state.pagina_activa = "hub_nino"
            st.rerun()
        if st.button(
            "Mi abecedario — elegir mis imágenes por letra",
            use_container_width=True,
            key="abecedario_hdr_mi_abecedario",
        ):
            st.session_state.pop("album_abecedario_ver_estado", None)
            st.session_state.pagina_activa = "album_abecedario"
            st.rerun()

    render_encabezado_logo_titulo_acciones(
        titulo,
        color_fav=color,
        logo_height=192,
        slot_acciones=_acciones_abecedario_hdr,
        html_adicional_centro=html_centro,
    )
    st.write("---")

    for fi, fila in enumerate(FILAS_ABECEDARIO_9X3):
        cols = st.columns(3)
        # Aproximar filas: margen negativo fuerte en letras tras la 1.ª + iframe más bajo en cards.py
        row_tight = "margin-top:-1.45rem;" if fi > 0 else ""
        for ci, (letra, palabra, _pista) in enumerate(fila):
            with cols[ci]:
                st.markdown(
                    f"<div style='text-align:center;font-size:1.55rem;font-weight:800;"
                    f"color:{color};margin-bottom:0;line-height:1;{row_tight}'>{letra}</div>",
                    unsafe_allow_html=True,
                )
                ruta = resolver_ruta_imagen_abecedario(letra, palabra)
                uid = f"abcm_{fi}_{ci}_{letra}"
                if ruta:
                    render_album_card_karaoke(
                        ruta,
                        palabra,
                        unique_id=uid,
                        size="abecedario_wide",
                        show_label_below=False,
                        categoria=ABECEDARIO_MATRIZ_SFX_CATEGORIA,
                        sonidos_tarjeta_habilitados=True,
                        prefijo_letra_de_abecedario=True,
                        letra_abecedario=letra,
                    )
                else:
                    render_album_card_placeholder(unique_id=uid, size="abecedario_wide")
                    st.caption(f"**{palabra}** — sin imagen en genéricos")
                    st.caption(
                        f"Añade en `assets/genericos` un archivo cuyo nombre sugiera "
                        f"«{palabra.lower()}» (p. ej. `{slug_sugerido_generico(palabra)}.jpg`)."
                    )

