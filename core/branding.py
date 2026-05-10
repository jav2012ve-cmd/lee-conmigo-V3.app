"""Rutas de marca (logo) compartidas por Salón y cabeceras de página."""

from __future__ import annotations

import os


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def ruta_logo_app() -> str | None:
    """
    Logo principal de la app.
    Prioridad: assets/genericos/fondos/LogoLeeCommigo.png, luego assets/lee_conmigo_ia.*
    """
    root = _project_root()
    preferido = os.path.join(root, "assets", "genericos", "fondos", "LogoLeeCommigo.png")
    if os.path.isfile(preferido):
        return preferido
    d = os.path.join(root, "assets")
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = os.path.join(d, f"lee_conmigo_ia{ext}")
        if os.path.isfile(p):
            return p
    return None
