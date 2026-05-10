"""
Ruta Abecedario: matriz 9 filas × 3 columnas (27 letras del alfabeto español).

Imágenes: assets/genericos/ (misma convención que el álbum).
Sonido extra: assets/sfx/abecedario/ y, si aplica, mismas rutas que el álbum
(Instrumentos musicales, Sonidos especiales A/B) vía components.cards.

Orden alfabético: A–Z con Ñ entre N y O (sin celda Ch separada: 27 = 9×3).
Cada tupla: (letra_mostrar, palabra_ejemplo, pista_sonido_corta)
"""

import os
import re
import unicodedata

# 9 filas × 3 columnas = 27 letras
FILAS_ABECEDARIO_9X3 = [
    [("A", "Ambulancia", "¡Aaa! sirena"), ("B", "Bajo", "Bum-bum grave"), ("C", "Coral", "C en el mar")],
    [("D", "Delfín", "D en el mar"), ("E", "Elefante", "E larga"), ("F", "Flauta", "F suave")],
    [("G", "Gato", "G g-g"), ("H", "Helicóptero", "H… jjj"), ("I", "Iglú", "I corta")],
    [("J", "Jirafa", "J como ge"), ("K", "Kiwi", "K fuerte"), ("L", "León", "L llana")],
    [("M", "Mono", "M con labios"), ("N", "Nube", "N nasal"), ("Ñ", "Niño", "Ñ ñ-ñ")],
    [("O", "Oveja", "Beee"), ("P", "Piano", "Pim-pam"), ("Q", "Queso", "Qu-")],
    [("R", "Reloj", "Tic-tac"), ("S", "Sapo", "Croac"), ("T", "Trompeta", "Tara-tán")],
    [("U", "Uva", "U corta"), ("V", "Violín", "Cuerdas"), ("W", "Waffle", "W doble u")],
    [("X", "Xilófono", "X = ks"), ("Y", "Yoyo", "Y ye"), ("Z", "Zorro", "Z vibrante")],
]

# Alias retrocompatible por si algo importa el nombre antiguo
FILAS_ABECEDARIO_7X4 = FILAS_ABECEDARIO_9X3


def _slug_archivo(texto: str) -> str:
    t = unicodedata.normalize("NFKD", (texto or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def slug_sugerido_generico(palabra: str) -> str:
    """Nombre de archivo sugerido (sin extensión) para `assets/genericos/`."""
    s = _slug_archivo(palabra)
    return s if s else "palabra"


def resolver_ruta_imagen_abecedario(letra: str, palabra: str) -> str | None:
    """
    Busca imagen en assets/genericos: nombre de archivo coherente con la palabra
    (p. ej. ambulancia.jpg, leon.jpg, xilofono.png).
    """
    from core.asset_manager import AssetManager

    palabra_l = (palabra or "").strip().lower()
    slug_p = _slug_archivo(palabra)
    if not slug_p:
        return None

    candidatos_parcial = []
    for ruta in AssetManager._listar_genericos():
        stem = os.path.splitext(os.path.basename(ruta))[0].replace("_", " ").replace("-", " ").strip().lower()
        slug_s = _slug_archivo(stem)
        if slug_s == slug_p:
            return ruta
        if slug_p and slug_s and (slug_p in slug_s or slug_s in slug_p):
            candidatos_parcial.append(ruta)
        elif palabra_l and palabra_l in stem:
            candidatos_parcial.append(ruta)

    if candidatos_parcial:
        return candidatos_parcial[0]

    por_letra = AssetManager.obtener_genericos_por_letra()
    letra_u = (letra or "").strip()
    if letra_u.upper() == "CH":
        for item in por_letra.get("C", []) or []:
            p_item = (item.get("palabra") or "").strip().lower()
            if "chocol" in p_item or _slug_archivo(p_item).startswith("chocol"):
                return item.get("ruta_img")
        if por_letra.get("C"):
            return por_letra["C"][0].get("ruta_img")

    clave = letra_u[:1] if letra_u else ""
    if clave and clave in por_letra and por_letra[clave]:
        return por_letra[clave][0].get("ruta_img")
    return None
