"""
Genera un PDF del abecedario del estudiante:
- Página 1: portada con título "El abecedario de [nombre sin apellidos]"
- Páginas siguientes: encabezado con nombre del estudiante, máximo 4 letras por hoja.
"""
import os
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def _nombre_sin_apellidos(nombre_completo: str) -> str:
    """Devuelve solo el primer nombre (sin apellidos)."""
    if not nombre_completo or not isinstance(nombre_completo, str):
        return "Explorador"
    return (nombre_completo.strip().split() or ["Explorador"])[0]


def _hex_to_rgb(hex_color: str):
    """Convierte '#RRGGBB' a (r, g, b) en 0-1."""
    hex_color = (hex_color or "#4A90E2").strip().lstrip("#")
    if len(hex_color) == 6:
        return (
            int(hex_color[0:2], 16) / 255,
            int(hex_color[2:4], 16) / 255,
            int(hex_color[4:6], 16) / 255,
        )
    return (0.29, 0.56, 0.89)  # #4A90E2 por defecto


# A4 en puntos
A4_W, A4_H = A4
MARGIN = 50
HEADER_H = 36
LETRAS_POR_HOJA = 4
# Por cada letra: altura de fila (imagen + letra + palabras); con 4 letras hay más espacio por imagen
ALTURA_FILA = (A4_H - MARGIN * 2 - HEADER_H) / LETRAS_POR_HOJA
IMG_H = int(ALTURA_FILA * 0.60)
LETRA_FONT_SIZE = int(ALTURA_FILA * 0.30)
PALABRA_FONT_SIZE = 11
# Anchos: imagen | letra | imagen (centrados en la página)
ANCHO_IMG = (A4_W - MARGIN * 2) * 0.32
ANCHO_LETRA = (A4_W - MARGIN * 2) * 0.18
# Ancho total de cada fila (imagen + letra + imagen) para centrarla
ANCHO_FILA = ANCHO_IMG * 2 + ANCHO_LETRA
X_FILA_INICIO = (A4_W - ANCHO_FILA) / 2


# Tamaño de la foto del estudiante en la portada del PDF
FOTO_PORTADA_W = 140
FOTO_PORTADA_H = 140


def _draw_fondo_pagina(c: canvas.Canvas, fondo_ruta: str, alpha_overlay: float = 0.7):
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


def _draw_portada(c: canvas.Canvas, nombre_portada: str, color_rgb: tuple, foto_ruta: str = "", fondo_ruta: str = "", nombre_para_reconozca: str = ""):
    """Dibuja la página inicial: fondo (opcional), título, foto del estudiante (opcional), LeeConmigo y párrafo introductorio.
    nombre_portada: nombre para título y «creado para X» (p. ej. primer + segundo). nombre_para_reconozca: para «que X se reconozca» (p. ej. solo primer)."""
    c.setPageSize(A4)
    _draw_fondo_pagina(c, fondo_ruta or "", alpha_overlay=0.7)

    # Foto del estudiante (centrada, encima del título)
    y_titulo = A4_H / 2 + 30
    if foto_ruta and os.path.isfile(foto_ruta):
        try:
            img = ImageReader(foto_ruta)
            iw, ih = img.getSize()
            if iw and ih:
                ratio = min(FOTO_PORTADA_W / iw, FOTO_PORTADA_H / ih)
                w, h = iw * ratio, ih * ratio
                x_foto = (A4_W - w) / 2
                y_foto = A4_H / 2 + 80
                c.drawImage(img, x_foto, y_foto, width=w, height=h)
                y_titulo = y_foto - 25
        except Exception:
            pass

    c.setFillColorRGB(*color_rgb)
    c.setFont("Helvetica-Bold", 34)
    texto = f"El abecedario de {nombre_portada}"
    c.drawCentredString(A4_W / 2, y_titulo, texto)

    # Subtítulo LeeConmigo
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 16)
    c.drawCentredString(A4_W / 2, A4_H / 2 - 30, "LeeConmigo")

    # Párrafo introductorio personalizado
    nombre_reconozca = (nombre_para_reconozca or "").strip() or (nombre_portada.strip().split() or ["el niño"])[0]
    c.setFont("Helvetica", 11)
    lineas = [
        f"Este abecedario ha sido creado especialmente para {nombre_portada},",
        "integrando su mundo favorito con tecnología de Inteligencia Artificial.",
        f"Diseñado como un complemento de Lee Conmigo IA, cada página busca que {nombre_reconozca}",
        "se reconozca como el héroe de su propio aprendizaje, facilitando la memorización",
        "a través de la emoción y el juego.",
    ]
    y_texto = A4_H / 2 - 60
    for linea in lineas:
        c.drawCentredString(A4_W / 2, y_texto, linea)
        y_texto -= 14

    # Limitación de responsabilidades (pie de portada)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont("Helvetica", 7)
    lineas_legal = [
        "Los contenidos, ilustraciones y diseños presentados en este abecedario son propiedad intelectual de LeeConmigo IA",
        "y el ecosistema AprendeConNosotros IA. Este material ha sido creado con fines estrictamente educativos y personalizados,",
        "por lo que su distribución comercial, reproducción total o parcial por parte de editoriales o terceros, así como su",
        "alteración sin autorización expresa, queda prohibida. Los desarrolladores no se hacen responsables del uso indebido",
        "del material fuera del entorno pedagógico sugerido, ni de interpretaciones derivadas de los elementos gráficos",
        "generados por Inteligencia Artificial.",
    ]
    y_legal = MARGIN + (len(lineas_legal) * 9)
    for linea in lineas_legal:
        c.drawString(MARGIN, y_legal, linea)
        y_legal -= 9


def _draw_header(c: canvas.Canvas, nombre_estudiante: str, color_rgb: tuple):
    """Dibuja el encabezado con el nombre del estudiante (sobre el fondo ya dibujado)."""
    c.setFillColorRGB(*color_rgb)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN, A4_H - MARGIN - 18, nombre_estudiante)
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(MARGIN, A4_H - MARGIN - 24, A4_W - MARGIN, A4_H - MARGIN - 24)
    c.setStrokeColorRGB(0, 0, 0)


def _load_image(ruta: str, max_w: float, max_h: float):
    """Carga imagen desde ruta; devuelve (ImageReader o None, ancho_final, alto_final)."""
    if not ruta or not os.path.isfile(ruta):
        return None, max_w, max_h
    try:
        img = ImageReader(ruta)
        iw, ih = img.getSize()
        if iw <= 0 or ih <= 0:
            return None, max_w, max_h
        ratio = min(max_w / iw, max_h / ih)
        return img, iw * ratio, ih * ratio
    except Exception:
        return None, max_w, max_h


def _draw_letra_en_fila(
    c: canvas.Canvas,
    y_base: float,
    letra: str,
    par: list,
    color_rgb: tuple,
):
    """Dibuja una fila centrada: imagen 1 | letra | imagen 2, con palabras debajo."""
    x_izq = X_FILA_INICIO
    x_centro = X_FILA_INICIO + ANCHO_IMG + (ANCHO_LETRA / 2)
    x_der = X_FILA_INICIO + ANCHO_IMG + ANCHO_LETRA
    y_img = y_base + ALTURA_FILA - IMG_H - 22
    y_letra = y_base + ALTURA_FILA - IMG_H - 10

    # Imagen izquierda (centrada en su celda)
    ruta1 = (par[0].get("ruta_img") or "").strip() if par and len(par) > 0 else ""
    pal1 = (par[0].get("palabra") or "?").strip() if par and len(par) > 0 else "?"
    img_reader, w1, h1 = _load_image(ruta1, ANCHO_IMG, IMG_H)
    x1_centrado = x_izq + (ANCHO_IMG - w1) / 2
    if img_reader:
        c.drawImage(img_reader, x1_centrado, y_img, width=w1, height=h1)
    else:
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x_izq, y_img, ANCHO_IMG, IMG_H, fill=1, stroke=0)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica-Bold", PALABRA_FONT_SIZE)
    centro_izq = x_izq + ANCHO_IMG / 2
    c.drawCentredString(centro_izq, y_base + 4, (pal1[:18] + "…") if len(pal1) > 18 else pal1)

    # Letra en el centro (entre las dos imágenes)
    c.setFillColorRGB(*color_rgb)
    c.setFont("Helvetica-Bold", LETRA_FONT_SIZE)
    c.drawCentredString(x_centro, y_letra, letra)

    # Imagen derecha (centrada en su celda)
    ruta2 = (par[1].get("ruta_img") or "").strip() if par and len(par) > 1 else ""
    pal2 = (par[1].get("palabra") or "?").strip() if par and len(par) > 1 else "?"
    img_reader2, w2, h2 = _load_image(ruta2, ANCHO_IMG, IMG_H)
    x2_centrado = x_der + (ANCHO_IMG - w2) / 2
    if img_reader2:
        c.drawImage(img_reader2, x2_centrado, y_img, width=w2, height=h2)
    else:
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x_der, y_img, ANCHO_IMG, IMG_H, fill=1, stroke=0)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica-Bold", PALABRA_FONT_SIZE)
    centro_der = x_der + ANCHO_IMG / 2
    c.drawCentredString(centro_der, y_base + 4, (pal2[:18] + "…") if len(pal2) > 18 else pal2)


def generar_pdf_abecedario(
    nombre_estudiante: str,
    letras_disponibles: list,
    abecedario_guardado: dict,
    color_fav: str = "#4A90E2",
    foto_ruta: str = "",
    fondo_ruta: str = "",
    nombre_para_reconozca: str = "",
) -> bytes:
    """
    Genera el PDF del abecedario.
    nombre_estudiante: nombre para portada/título (p. ej. "Ignacio Mateo" sin apellidos).
    nombre_para_reconozca: nombre para "que X se reconozca" (p. ej. "Ignacio"). Si vacío, se usa la primera palabra de nombre_estudiante.
    """
    nombre_solo = (nombre_estudiante or "").strip() or "Explorador"
    color_rgb = _hex_to_rgb(color_fav)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Solo letras que tienen 2 imágenes
    letras_con_contenido = [
        letra for letra in letras_disponibles
        if len(abecedario_guardado.get(letra, [])) == 2
    ]

    # Página 1: Portada (con fondo y/o foto si se pasan)
    _draw_portada(c, nombre_solo, color_rgb, foto_ruta=foto_ruta or "", fondo_ruta=fondo_ruta or "", nombre_para_reconozca=nombre_para_reconozca or "")

    if letras_con_contenido:
        c.showPage()
        contenido_y_base = A4_H - MARGIN - HEADER_H

        for i in range(0, len(letras_con_contenido), LETRAS_POR_HOJA):
            chunk = letras_con_contenido[i : i + LETRAS_POR_HOJA]
            c.setPageSize(A4)
            # Fondo en todas las páginas (no solo la inicial)
            _draw_fondo_pagina(c, fondo_ruta or "", alpha_overlay=0.75)
            _draw_header(c, nombre_solo, color_rgb)

            for j, letra in enumerate(chunk):
                par = abecedario_guardado.get(letra, [])
                y_base = contenido_y_base - (j + 1) * ALTURA_FILA
                _draw_letra_en_fila(c, y_base, letra, par, color_rgb)

            if i + LETRAS_POR_HOJA < len(letras_con_contenido):
                c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
