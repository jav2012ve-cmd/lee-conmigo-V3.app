"""
Utilidades para informes PDF con historial de chat (FPDF) y texto de respuestas IA.

- formatear_para_pdf: normaliza LaTeX / símbolos antes de escribir en el PDF.
- multi_cell_seguro: multi_cell con tolerancia a Latin-1 (fallback unidecode).
- generar_pdf_historial_chat: PDF con estilos USER / ASSISTANT.
"""
from __future__ import annotations

import re
from io import BytesIO
from typing import Any, Iterable, Sequence

from fpdf import FPDF

from app import PDF

try:
    from unidecode import unidecode
except ImportError:  # pragma: no cover - dependencia obligatoria en runtime
    unidecode = None  # type: ignore[misc, assignment]


_SUPER_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _digitos_a_superindice(s: str) -> str:
    if not s:
        return s
    return str(s).translate(_SUPER_DIGITS)


def _exponentes_a_superindice_o_circunflejo(texto: str) -> str:
    """Convierte ^n, ^{n} y ^<dígitos> a superíndice Unicode."""

    def repl_digitos(m: re.Match) -> str:
        return _digitos_a_superindice(m.group(1))

    out = re.sub(r"\^\{(\d+)\}", repl_digitos, texto)
    # ^ seguido de uno o más dígitos (0-9): superíndice, p. ej. x^2 -> x², x^10 -> x¹⁰
    out = re.sub(r"\^(\d+)", repl_digitos, out)
    return out


def formatear_para_pdf(texto: str) -> str:
    """
    Filtro de texto antes de escribir en el PDF (respuestas IA, mensajes, etc.).
    - \\int_ y \\int -> ∫; palabra INTEGRAL -> ∫
    - ^infinito / ^infty -> ^∞; \\infty -> ∞
    - \\pm -> ±; \\rightarrow / \\Rightarrow -> flechas
    - Exponentes ^n / ^{n} y variantes con ^{\\wedge} -> superíndices Unicode
    - Al final se eliminan las barras invertidas (\\) restantes para no mostrar “código”.
    """
    if texto is None:
        return ""
    out = str(texto)

    # Integrales: \\int_ antes que \\int
    out = re.sub(r"\\int_", "∫", out, flags=re.IGNORECASE)
    out = re.sub(r"\\int\b", "∫", out, flags=re.IGNORECASE)
    out = re.sub(r"\bINTEGRAL\b", "∫", out, flags=re.IGNORECASE)

    out = out.replace("\\pm", "±")
    out = out.replace("\\rightarrow", "→")
    out = out.replace("\\Rightarrow", "⇒")

    # Infinito (español o estilo LaTeX informal)
    out = re.sub(r"(?i)\^infinito", "^∞", out)
    out = re.sub(r"(?i)\^infty", "^∞", out)
    out = re.sub(r"\\infty\b", "∞", out)

    # Variantes frecuentes de “potencia” mal escapadas por modelos
    out = out.replace("^{\\wedge}", "^")
    out = out.replace("^{\wedge}", "^")
    out = re.sub(r"\^\{\s*\\\s*wedge\s*\}", "^", out, flags=re.IGNORECASE)
    out = re.sub(r"\^\{\s*\^\s*\}", "^", out)
    out = re.sub(r"\\\^", "^", out)
    out = re.sub(r"\{\s*\^\s*\}", "^", out)

    out = _exponentes_a_superindice_o_circunflejo(out)

    # Quitar restos de LaTeX/markdown para que el estudiante no vea barras invertidas
    out = out.replace("\\", "")

    # Normaliza espacios finales por línea
    out = "\n".join(line.rstrip() for line in out.splitlines())
    return out.rstrip()


def _ascii_fallback(texto: str) -> str:
    if unidecode is None:
        return texto.encode("latin-1", errors="replace").decode("latin-1")
    return unidecode(texto)


def multi_cell_seguro(
    pdf: FPDF,
    w: float,
    h: float,
    texto: str,
    *,
    es_ia: bool = True,
    **kwargs: Any,
) -> None:
    """
    Escribe en el PDF; si es_ia, aplica formatear_para_pdf antes de multi_cell
    (respuestas de la IA). Si falla la codificación o la escritura, reintenta con
    unidecode (equivalente ASCII aproximado).
    """
    raw = texto or ""
    contenido = formatear_para_pdf(raw) if es_ia else raw
    try:
        pdf.multi_cell(w, h, contenido, **kwargs)
    except Exception:
        pdf.multi_cell(w, h, _ascii_fallback(contenido), **kwargs)


def _normalizar_rol(role: str) -> str:
    r = (role or "").strip().upper()
    if r in ("USER", "USUARIO", "HUMAN"):
        return "USER"
    if r in ("ASSISTANT", "AI", "BOT", "SYSTEM"):
        return "ASSISTANT"
    return "ASSISTANT"


def _iter_mensajes(historial: Iterable[Any]) -> Sequence[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in historial or []:
        if isinstance(m, dict):
            role = str(m.get("role") or m.get("remitente") or "")
            content = str(m.get("content") or m.get("texto") or m.get("message") or "")
        elif isinstance(m, (list, tuple)) and len(m) >= 2:
            role, content = str(m[0]), str(m[1])
        else:
            continue
        out.append((_normalizar_rol(role), content))
    return out


def _pdf_output_bytes(pdf: FPDF) -> bytes:
    try:
        data = pdf.output(dest="S")
    except Exception:
        raise
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        try:
            return data.encode("latin-1")
        except UnicodeEncodeError:
            return _ascii_fallback(data).encode("latin-1", errors="replace")
    return bytes(data)


def generar_pdf_historial_chat(
    historial: Iterable[Any],
    titulo: str = "Conversación",
) -> bytes:
    """
    Genera un PDF del historial. Cada ítem: dict con role/content o tupla (role, content).
    USER: negrita, azul oscuro. ASSISTANT: sangría, fuente normal; línea tenue entre pares.
    """
    rows = list(_iter_mensajes(historial))
    margen = 14.0
    sangria_asst = 8.0
    ancho_pag = 210.0
    ancho_user = ancho_pag - 2 * margen
    ancho_asst = ancho_pag - margen - (margen + sangria_asst)
    h_linea = 5.5

    def construir(forzar_ascii_cuerpo: bool) -> PDF:
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()
        pdf.set_margins(left=margen, top=margen, right=margen)

        titulo_pdf = (titulo or "Conversación")[:200]
        if forzar_ascii_cuerpo:
            titulo_pdf = _ascii_fallback(titulo_pdf)

        try:
            pdf.set_title(titulo_pdf[:120])
        except Exception:
            try:
                pdf.set_title(_ascii_fallback(titulo_pdf[:120]))
            except Exception:
                pass

        pdf.set_font("DejaVu", "B", 14)
        pdf.set_text_color(30, 30, 30)
        try:
            pdf.cell(0, 10, titulo_pdf, ln=1)
        except Exception:
            pdf.cell(0, 10, _ascii_fallback(titulo_pdf), ln=1)
        pdf.ln(3)

        for _, (rol, cuerpo) in enumerate(rows):
            if rol == "USER":
                pdf.set_font("DejaVu", "B", 11)
                pdf.set_text_color(15, 40, 90)
                pdf.set_x(margen)
                txt_user = _ascii_fallback(cuerpo) if forzar_ascii_cuerpo else cuerpo
                multi_cell_seguro(pdf, ancho_user, h_linea, txt_user, es_ia=False, align="L")
            else:
                pdf.set_font("DejaVu", "", 10)
                pdf.set_text_color(35, 35, 35)
                pdf.set_x(margen + sangria_asst)
                txt_asst = cuerpo
                if forzar_ascii_cuerpo:
                    txt_asst = _ascii_fallback(formatear_para_pdf(cuerpo))
                multi_cell_seguro(pdf, ancho_asst, h_linea, txt_asst, es_ia=not forzar_ascii_cuerpo, align="L")

            if rol == "ASSISTANT":
                y = pdf.get_y() + 1.5
                pdf.set_draw_color(218, 220, 228)
                pdf.set_line_width(0.25)
                try:
                    pdf.line(margen, y, ancho_pag - margen, y)
                except Exception:
                    pass
                pdf.set_y(y + 3.0)

        return pdf

    try:
        pdf = construir(False)
        return _pdf_output_bytes(pdf)
    except Exception:
        pdf2 = construir(True)
        return _pdf_output_bytes(pdf2)


def generar_pdf_historial_chat_buffer(
    historial: Iterable[Any],
    titulo: str = "Conversación",
) -> BytesIO:
    """Igual que generar_pdf_historial_chat pero devuelve BytesIO (p. ej. st.download_button)."""
    buf = BytesIO(generar_pdf_historial_chat(historial, titulo=titulo))
    buf.seek(0)
    return buf
