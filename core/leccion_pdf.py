"""
Genera un PDF de una hoja de lección (letra + sílabas + palabras con imágenes + frases con fotos)
para que el estudiante vaya creando su propio libro de lecturas.
"""
import os
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

A4_W, A4_H = A4
MARGIN = 40


def _hex_to_rgb(hex_color: str):
    """Convierte '#RRGGBB' a (r, g, b) en 0-1."""
    hex_color = (hex_color or "#4A90E2").strip().lstrip("#")
    if len(hex_color) == 6:
        return (
            int(hex_color[0:2], 16) / 255,
            int(hex_color[2:4], 16) / 255,
            int(hex_color[4:6], 16) / 255,
        )
    return (0.29, 0.56, 0.89)


def _draw_fondo_pagina(c: canvas.Canvas, fondo_ruta: str, alpha_overlay: float = 0.75):
    """Dibuja el fondo en toda la página y una capa clara para legibilidad."""
    if not fondo_ruta or not os.path.isfile(fondo_ruta):
        return
    try:
        img = ImageReader(fondo_ruta)
        iw, ih = img.getSize()
        if iw and ih:
            c.drawImage(img, 0, 0, width=A4_W, height=A4_H)
    except Exception:
        return
    c.setFillColorRGB(1, 1, 1)
    c.setFillAlpha(alpha_overlay)
    c.rect(0, 0, A4_W, A4_H, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setFillColorRGB(0, 0, 0)


def _draw_image_fit(c: canvas.Canvas, ruta: str, x: float, y: float, w: float, h: float):
    """Dibuja una imagen escalada para caber en (w, h), centrada en (x, y) es el centro del rectángulo."""
    if not ruta or not os.path.isfile(ruta):
        return
    try:
        img = ImageReader(ruta)
        iw, ih = img.getSize()
        if iw <= 0 or ih <= 0:
            return
        ratio = min(w / iw, h / ih)
        nw, nh = iw * ratio, ih * ratio
        c.drawImage(img, x - nw / 2, y - nh / 2, width=nw, height=nh)
    except Exception:
        pass


# Posiciones 1-based en matriz 3x3: (1,1), (1,3), (2,2), (3,1), (3,3)
_POS_SILABAS_3X3 = [(1, 1), (1, 3), (2, 2), (3, 1), (3, 3)]


def _draw_matriz_3x3_silabas(c: canvas.Canvas, silabas: list, x0: float, y0: float, lado: float, color_rgb: tuple):
    """Dibuja una matriz 3x3 con las 5 sílabas en (1,1), (1,3), (2,2), (3,1), (3,3)."""
    if not silabas or len(silabas) < 5:
        return
    celda = lado / 3
    gap = 4
    for row in range(3):
        for col in range(3):
            x = x0 + col * celda + gap / 2
            y = y0 + (2 - row) * celda + gap / 2
            w = celda - gap
            h = celda - gap
            idx = next((i for i, (r, c) in enumerate(_POS_SILABAS_3X3[:5]) if (row, col) == (r - 1, c - 1)), None)
            if idx is not None and idx < len(silabas):
                c.setFillColorRGB(*color_rgb)
                c.roundRect(x, y, w, h, 5, fill=1, stroke=0)
                c.setFillColorRGB(1, 1, 1)
                c.setFont("Helvetica-Bold", max(12, int(celda * 0.5)))
                c.drawCentredString(x + w / 2, y + h / 2 - 4, silabas[idx])
            else:
                c.setFillColorRGB(0.94, 0.94, 0.94)
                c.roundRect(x, y, w, h, 4, fill=1, stroke=0)


def generar_pdf_leccion(
    letra: str,
    silabas: list,
    nombre_estudiante: str = "",
    fondo_ruta: str = "",
    color_hex: str = "#4A90E2",
    palabras: list = None,
    frases: list = None,
    foto_estudiante: str = "",
    foto_mama: str = "",
) -> bytes:
    """
    Genera el PDF de la lección.
    palabras: lista de dicts {"palabra": str, "ruta_img": str} (con imagen cada una).
    frases: lista de cadenas.
    foto_estudiante, foto_mama: rutas a imágenes para la sección de frases.
    """
    letra = (letra or "M").strip().upper()
    silabas = list(silabas or [])
    palabras = list(palabras or [])
    frases = list(frases or [])
    nombre = (nombre_estudiante or "").strip() or "Mi libro"
    color_rgb = _hex_to_rgb(color_hex)
    # Normalizar palabras: puede ser list de str o list de dict
    palabras_data = []
    for p in palabras[:9]:
        if isinstance(p, dict):
            palabras_data.append({"palabra": (p.get("palabra") or "").strip(), "ruta_img": (p.get("ruta_img") or "").strip()})
        else:
            palabras_data.append({"palabra": (str(p).strip() or ""), "ruta_img": ""})

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    _draw_fondo_pagina(c, fondo_ruta or "", alpha_overlay=0.75)

    y = A4_H - MARGIN
    # Sin cintillo superior; bloque letra Mm y matriz 25% más pequeños para dar espacio a las frases
    alto_bloque = 135
    lado_matriz = alto_bloque * 0.85
    x_letra = MARGIN + 10
    y_letra_base = y - alto_bloque * 0.35
    c.setFont("Helvetica-Bold", 51)
    c.setFillColorRGB(0.78, 0.16, 0.16)
    c.drawString(x_letra, y_letra_base, f"{letra} {letra.lower()}")
    x_matriz = A4_W - MARGIN - lado_matriz - 10
    y_matriz_base = y - lado_matriz - 10
    _draw_matriz_3x3_silabas(c, silabas, x_matriz, y_matriz_base, lado_matriz, color_rgb)
    y -= alto_bloque + 18

    PIE_Y = MARGIN + 50

    # Sección "Leo con mis papás..." — imágenes con su nombre debajo (cada una trae su nombre, sin cintillo extra)
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(MARGIN, y, "Leo con mis papás...")
    y -= 26
    cols_pal = 3
    ancho_col = (A4_W - 2 * MARGIN) / cols_pal
    img_pal_h = 90
    img_pal_w = 105
    espaciado_fila = img_pal_h + 36
    if palabras_data:
        for i, item in enumerate(palabras_data[:9]):
            fila, col = i // cols_pal, i % cols_pal
            x_c = MARGIN + col * ancho_col + ancho_col / 2
            y_img = y - fila * espaciado_fila - img_pal_h / 2 - 6
            if item.get("ruta_img") and os.path.isfile(item["ruta_img"]):
                _draw_image_fit(c, item["ruta_img"], x_c, y_img, img_pal_w, img_pal_h)
            palabra_txt = (item.get("palabra") or "").strip().upper()
            if palabra_txt:
                c.setFont("Helvetica-Bold", 12)
                c.setFillColorRGB(0.15, 0.15, 0.15)
                c.drawCentredString(x_c, y_img - img_pal_h / 2 - 10, palabra_txt[:20])
        num_filas = max(1, (len(palabras_data) + cols_pal - 1) // cols_pal)
        y -= num_filas * espaciado_fila + 16
    else:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(MARGIN + 8, y, "(Agrega palabras que empiecen con esta letra en tu álbum)")
        y -= 20

    # Sección "Frases mágicas" — cintillo de fotos familiares (Mamá | frases 1x3 | Ignacio)
    if y < PIE_Y + 80:
        y = PIE_Y + 80
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, y, "Frases mágicas")
    y -= 22

    # Fila: [Mamá + cintillo] [Frase1 | Frase2 | Frase3] [Ignacio + cintillo]
    foto_sz = 42
    y_fila = y - foto_sz / 2 - 10
    x_mama = MARGIN + foto_sz / 2 + 8
    x_est = A4_W - MARGIN - foto_sz / 2 - 8
    if foto_mama and os.path.isfile(foto_mama):
        _draw_image_fit(c, foto_mama, x_mama, y_fila, foto_sz, foto_sz)
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawCentredString(x_mama, y_fila - foto_sz / 2 - 6, "Mamá")
    if foto_estudiante and os.path.isfile(foto_estudiante):
        _draw_image_fit(c, foto_estudiante, x_est, y_fila, foto_sz, foto_sz)
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawCentredString(x_est, y_fila - foto_sz / 2 - 6, "Ignacio")

    # Frases en matriz 1x3 entre las dos fotos
    espacio_entre = 12
    ancho_total_frases = A4_W - 2 * MARGIN - foto_sz - 40 - foto_sz - 40
    ancho_frase = (ancho_total_frases - 2 * espacio_entre) / 3
    alto_btn = 32
    y_btn = y_fila - alto_btn / 2 - 2
    x_ini_frases = MARGIN + foto_sz + 36
    frases_3 = (frases or [])[:3]
    if frases_3:
        for idx, f in enumerate(frases_3):
            x_btn = x_ini_frases + idx * (ancho_frase + espacio_entre)
            c.setFillColorRGB(*color_rgb)
            c.roundRect(x_btn, y_btn, ancho_frase, alto_btn, 6, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica", 10)
            linea = (str(f).strip() or "")[:38]
            c.drawCentredString(x_btn + ancho_frase / 2, y_btn + alto_btn / 2 - 3, linea)
    else:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(x_ini_frases, y_btn - 6, "(Frases para practicar con tu familia)")

    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 9)
    c.drawCentredString(A4_W / 2, MARGIN + 14, f"Mi libro de lecturas — {nombre}")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
