"""
Punto de apoyo para PDFs con fuente Unicode (DejaVu Sans).
La clase PDF extiende FPDF, descarga y registra DejaVuSans.ttf / DejaVuSans-Bold.ttf
y redirige Arial/Helvetica hacia DejaVu para símbolos como Σ, ∫, ∞.
"""
from __future__ import annotations

import io
import os
import shutil
import tarfile
import urllib.error
import urllib.request

from fpdf import FPDF

_ROOT = os.path.abspath(os.path.dirname(__file__))
_FONTS_DIR = os.path.join(_ROOT, "assets", "fonts")
_DEJAVU_SANS = os.path.join(_FONTS_DIR, "DejaVuSans.ttf")
_DEJAVU_SANS_BOLD = os.path.join(_FONTS_DIR, "DejaVuSans-Bold.ttf")

# Paquete oficial (release 2.37): contiene ttf/DejaVuSans.ttf y ttf/DejaVuSans-Bold.ttf
_DEJAVU_TTF_RELEASE_TBZ2 = (
    "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/"
    "version_2_37/dejavu-fonts-ttf-2.37.tar.bz2"
)
_TAR_MEMBER_SANS = "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf"
_TAR_MEMBER_BOLD = "dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf"

FAMILY_DEJAVU = "DejaVu"


def _font_ok(path: str) -> bool:
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 1000
    except OSError:
        return False


def _copiar_fuente_si_existe(origen: str, destino: str) -> bool:
    if not _font_ok(origen):
        return False
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy2(origen, destino)
        return _font_ok(destino)
    except OSError:
        return False


def _intentar_fuentes_sistema() -> bool:
    """Windows / Linux: copia DejaVu desde el sistema si ya está instalada."""
    candidatos = [
        (
            os.path.join(os.environ.get("WINDIR", ""), "Fonts", "DejaVuSans.ttf"),
            os.path.join(os.environ.get("WINDIR", ""), "Fonts", "DejaVuSans-Bold.ttf"),
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
    ]
    for sans_src, bold_src in candidatos:
        if _copiar_fuente_si_existe(sans_src, _DEJAVU_SANS) and _copiar_fuente_si_existe(bold_src, _DEJAVU_SANS_BOLD):
            return True
    return False


def _descargar_y_extraer_dejavu_ttf() -> None:
    os.makedirs(_FONTS_DIR, exist_ok=True)
    req = urllib.request.Request(
        _DEJAVU_TTF_RELEASE_TBZ2,
        headers={"User-Agent": "LeeConmigoV4/1.0 (DejaVu fonts)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise RuntimeError(
            "No se pudo descargar el paquete de fuentes DejaVu (tar.bz2). "
            "Comprueba la conexión o coloca manualmente DejaVuSans.ttf y "
            f"DejaVuSans-Bold.ttf en {_FONTS_DIR}. Detalle: {e}"
        ) from e

    tmp_sans = _DEJAVU_SANS + ".part"
    tmp_bold = _DEJAVU_SANS_BOLD + ".part"
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:bz2") as tf:
            f_sans = tf.extractfile(_TAR_MEMBER_SANS)
            f_bold = tf.extractfile(_TAR_MEMBER_BOLD)
            if not f_sans or not f_bold:
                raise RuntimeError("El archivo descargado no contiene las fuentes DejaVu esperadas.")
            with open(tmp_sans, "wb") as out:
                out.write(f_sans.read())
            with open(tmp_bold, "wb") as out:
                out.write(f_bold.read())
        os.replace(tmp_sans, _DEJAVU_SANS)
        os.replace(tmp_bold, _DEJAVU_SANS_BOLD)
    except (tarfile.TarError, OSError, KeyError, RuntimeError) as e:
        for p in (tmp_sans, tmp_bold):
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass
        raise RuntimeError(
            "No se pudieron extraer DejaVuSans.ttf / DejaVuSans-Bold.ttf del paquete descargado."
        ) from e


def ensure_dejavu_fonts() -> tuple[str, str]:
    """
    Garantiza DejaVu Sans (regular y negrita) en assets/fonts/:
    1) Si ya existen, las reutiliza.
    2) Intenta copiar desde fuentes del sistema (Windows / Linux).
    3) Descarga el paquete oficial de la release 2.37 y extrae los .ttf.
    """
    if _font_ok(_DEJAVU_SANS) and _font_ok(_DEJAVU_SANS_BOLD):
        return _DEJAVU_SANS, _DEJAVU_SANS_BOLD

    if _intentar_fuentes_sistema() and _font_ok(_DEJAVU_SANS) and _font_ok(_DEJAVU_SANS_BOLD):
        return _DEJAVU_SANS, _DEJAVU_SANS_BOLD

    _descargar_y_extraer_dejavu_ttf()

    if not (_font_ok(_DEJAVU_SANS) and _font_ok(_DEJAVU_SANS_BOLD)):
        raise RuntimeError(
            f"No se encontraron fuentes válidas en {_FONTS_DIR}. "
            "Copia allí DejaVuSans.ttf y DejaVuSans-Bold.ttf (p. ej. desde la release de DejaVu)."
        )
    return _DEJAVU_SANS, _DEJAVU_SANS_BOLD


class PDF(FPDF):
    """
    FPDF con familia 'DejaVu' registrada (sustituye Arial/Helvetica para Unicode matemático).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        regular, bold = ensure_dejavu_fonts()
        self.add_font(FAMILY_DEJAVU, "", regular)
        self.add_font(FAMILY_DEJAVU, "B", bold)

    def set_font(self, family=None, style="", size=0) -> None:  # noqa: A003 — API de FPDF
        if family is not None and str(family).strip().lower() in ("arial", "helvetica"):
            family = FAMILY_DEJAVU
        super().set_font(family, style, size)
