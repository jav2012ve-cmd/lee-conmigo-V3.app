"""Títulos de página con logo Lee Conmigo (marca unificada)."""

from __future__ import annotations

import base64
import html
import os
import re
from collections.abc import Callable

import streamlit as st

from core.branding import ruta_logo_app


def _color_hex_seguro(color_fav: str) -> str:
    """Solo `#RGB` o `#RRGGBB` para usar en CSS inline."""
    c = (color_fav or "").strip()
    if re.fullmatch(r"#[\da-fA-F]{3}", c) or re.fullmatch(r"#[\da-fA-F]{6}", c):
        return c
    return "#4A90E2"


def _fondo_banner_suave(hex6: str) -> str:
    """`#RRGGBB` + canal alpha ~12 % para fondo tipo hub."""
    b = _color_hex_seguro(hex6)
    return f"{b}20" if len(b) == 7 else b


def render_encabezado_logo_titulo_acciones(
    titulo: str,
    *,
    color_fav: str,
    logo_height: int = 192,
    slot_acciones: Callable[[], None],
    column_weights: tuple[float, float, float] = (0.95, 1.45, 1.05),
    subtitulo: str | None = None,
    caption_bajo_titulo: str | None = None,
    html_adicional_centro: str | None = None,
) -> None:
    """
    Una fila × 3 columnas al estilo del hub: [logo en recuadro] | [título] | [acciones].
    `slot_acciones` debe dibujar los `st.button` u otros widgets en la tercera columna.
    Texto opcional bajo el `h1` en la celda central: `subtitulo` (énfasis) y `caption_bajo_titulo` (texto secundario).
    `html_adicional_centro`: fragmento HTML de confianza (p. ej. párrafos con datos ya escapados) tras esos bloques.
    """
    col_fav = _color_hex_seguro(color_fav)
    fondo = _fondo_banner_suave(col_fav)
    tit = html.escape((titulo or "").strip())
    extra = ""
    if subtitulo and subtitulo.strip():
        s = html.escape(subtitulo.strip())
        extra += (
            f'<p style="margin:0.45rem 0 0 0;font-size:1rem;font-weight:600;color:#2d3a4a;'
            f'line-height:1.25;">{s}</p>'
        )
    if caption_bajo_titulo and caption_bajo_titulo.strip():
        c = html.escape(caption_bajo_titulo.strip())
        extra += (
            f'<p style="margin:0.3rem 0 0 0;font-size:0.88rem;color:#555;font-weight:400;'
            f'line-height:1.35;">{c}</p>'
        )
    bloque_adicional = html_adicional_centro or ""
    _lg = logo_markup_html(height_px=int(logo_height), margin_right=0)
    c_logo, c_tit, c_act = st.columns(list(column_weights), gap="medium")
    with c_logo:
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:center;'
            f"padding:10px 8px;border-radius:18px;border:3px solid {col_fav};"
            f'background-color:{fondo};min-height:64px;">{_lg}</div>',
            unsafe_allow_html=True,
        )
    with c_tit:
        st.markdown(
            f'<div style="display:flex;flex-direction:column;align-items:flex-start;'
            f'justify-content:center;min-height:64px;">'
            f'<h1 style="margin:0;color:{col_fav};font-size:clamp(1.1rem,2.5vw,1.9rem);'
            f'font-weight:700;line-height:1.15;">{tit}</h1>{extra}{bloque_adicional}</div>',
            unsafe_allow_html=True,
        )
    with c_act:
        slot_acciones()
    st.markdown("<div style='margin-bottom:0.35rem;'></div>", unsafe_allow_html=True)


def logo_markup_html(*, height_px: int = 88, margin_right: int = 0) -> str:
    """`<img>` en base64 para incrustar en `st.markdown(..., unsafe_allow_html=True)`."""
    p = ruta_logo_app()
    if not p or not os.path.isfile(p):
        return ""
    ext = os.path.splitext(p)[1].lower()
    if ext in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"
    else:
        mime = "image/png"
    try:
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    except OSError:
        return ""
    mr = f"margin-right:{int(margin_right)}px;" if margin_right else ""
    return (
        f'<img src="data:{mime};base64,{b64}" alt="" '
        f'style="height:{int(height_px)}px;width:auto;object-fit:contain;{mr}'
        f'vertical-align:middle;flex-shrink:0;display:block;" />'
    )


def render_titulo_pagina(
    titulo: str,
    *,
    subtitle: str | None = None,
    align: str = "left",
    logo_height: int = 88,
    h1_rem: float = 1.75,
) -> None:
    """Título principal: logo arriba (grande) y texto debajo; sin emoji en el texto (pasar título ya limpio)."""
    tit = html.escape((titulo or "").strip())
    is_left = (align or "left").lower() == "left"
    items = "flex-start" if is_left else "center"
    text_align = "left" if is_left else "center"
    lg = logo_markup_html(height_px=logo_height, margin_right=0)
    row = (
        f'<div style="display:flex;flex-direction:column;align-items:{items};'
        f'justify-content:flex-start;gap:0.4rem;margin:0.1rem 0 0.75rem 0;">'
        f'<div style="line-height:0;">{lg}</div>'
        f'<h1 style="margin:0;font-size:{h1_rem}rem;font-weight:700;line-height:1.2;border:none;padding:0;'
        f'text-align:{text_align};width:100%;">{tit}</h1></div>'
    )
    st.markdown(row, unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def render_titulo_sidebar(titulo: str) -> None:
    """Cabecera del sidebar: logo arriba (compacto pero legible) + título."""
    render_titulo_pagina(titulo, logo_height=56, h1_rem=1.12, align="center")
