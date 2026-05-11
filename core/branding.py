"""Rutas de marca (logo) compartidas por Salón y cabeceras de página."""

from __future__ import annotations

import os


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def ruta_logo_app() -> str | None:
    """
    Logo principal de la app: solo bajo assets/genericos/fondos/.
    Prioridad: LogoLeeConmigo.*, luego LogoLeeCommigo.* (typo histórico), mismas bases con distintas extensiones.
    """
    root = _project_root()
    fondos = os.path.join(root, "assets", "genericos", "fondos")
    for base in ("LogoLeeConmigo", "LogoLeeCommigo"):
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = os.path.join(fondos, f"{base}{ext}")
            if os.path.isfile(p):
                return p
    return None
