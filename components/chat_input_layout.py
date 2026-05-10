"""
Layout de st.chat_input en flujo normal del documento.

Streamlit ancla el chat al pie (bloque [data-testid="stBottom"]) cuando
`st.chat_input()` se llama en el main sin contenedores ancestro. Envolviendo
la llamada en `st.container()` (u otra columna/expander) se usa posición
inline y el campo queda donde lo renderizas (p. ej. justo debajo del título).
"""
from __future__ import annotations

from typing import Any, Literal

import streamlit as st


def chat_input_debajo_del_titulo(
    titulo: str,
    placeholder: str,
    *,
    titulo_es_html: bool = False,
    heading: Literal["h2", "h3", "h4"] = "h3",
    **chat_kwargs: Any,
) -> str | Any | None:
    """
    Muestra el título y, enseguida, el campo de pregunta en el flujo de la página
    (no flotando sobre el contenido).

    Parameters
    ----------
    titulo : str
        Texto o HTML del encabezado (p. ej. "Dime y te digo").
    titulo_es_html : bool
        Si True, se pasa `unsafe_allow_html=True` al markdown del título.
    heading : "h2" | "h3" | "h4"
        Etiqueta HTML si `titulo_es_html` es False (solo el texto del título).
    **chat_kwargs : argumentos extra para `st.chat_input` (key, max_chars, etc.).
    """
    if titulo_es_html:
        st.markdown(titulo, unsafe_allow_html=True)
    else:
        esc = titulo.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f"<{heading}>{esc}</{heading}>", unsafe_allow_html=True)

    with st.container():
        return st.chat_input(placeholder, **chat_kwargs)
