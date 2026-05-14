"""Galería unificada de avatares: carpeta Familia + avatares de estudiante (assets/avatars_nino)."""

import os
from pathlib import Path

import streamlit as st

_IMG = (".jpg", ".jpeg", ".png", ".webp")


def _proyecto_root():
    cur = Path(__file__).resolve().parent
    for _ in range(10):
        if (cur / "database" / "db_config.py").is_file():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return Path(__file__).resolve().parents[1]


@st.cache_data(show_spinner=False, ttl=180)
def listar_avatares_familia_galeria():
    """
    Imágenes para el álbum Familia y vistas que listan la misma galería:
    - Raíz de assets/avatars_familia
    - Recursivo bajo assets/avatars_nino (p. ej. nino/ y nina/)
    Sin duplicar la misma ruta absoluta.
    """
    out = []
    seen = set()
    root = _proyecto_root()

    def add(path_abs, filename):
        if not path_abs:
            return
        # Evitar os.path.isfile: OneDrive / archivos bajo demanda pueden fallar aquí.
        if not os.path.lexists(path_abs):
            return
        try:
            norm = os.path.normpath(os.path.abspath(path_abs))
        except OSError:
            return
        if norm in seen:
            return
        seen.add(norm)
        label = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").strip()
        out.append({"label": label.title() or filename, "path": norm})

    fam = os.path.join(str(root), "assets", "avatars_familia")
    try:
        if os.path.isdir(fam):
            for name in sorted(os.listdir(fam)):
                if name.startswith("."):
                    continue
                if not name.lower().endswith(_IMG):
                    continue
                add(os.path.join(fam, name), name)
    except OSError:
        pass

    nino = os.path.join(str(root), "assets", "avatars_nino")
    try:
        if os.path.isdir(nino):
            for wroot, _dirs, files in os.walk(nino):
                for name in sorted(files):
                    if name.startswith("."):
                        continue
                    if not name.lower().endswith(_IMG):
                        continue
                    add(os.path.join(wroot, name), name)
    except OSError:
        pass

    return out
