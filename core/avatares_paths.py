"""Galería unificada de avatares: carpeta Familia + avatares de estudiante (assets/avatars_nino)."""

import os

_IMG = (".jpg", ".jpeg", ".png", ".webp")


def _proyecto_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


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
        if not path_abs or not os.path.isfile(path_abs):
            return
        try:
            norm = os.path.normpath(os.path.abspath(path_abs))
        except Exception:
            return
        if norm in seen:
            return
        seen.add(norm)
        label = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").strip()
        out.append({"label": label.title() or filename, "path": norm})

    fam = os.path.join(root, "assets", "avatars_familia")
    try:
        if os.path.isdir(fam):
            for name in sorted(os.listdir(fam)):
                if name.startswith("."):
                    continue
                if not name.lower().endswith(_IMG):
                    continue
                add(os.path.join(fam, name), name)
    except Exception:
        pass

    nino = os.path.join(root, "assets", "avatars_nino")
    try:
        if os.path.isdir(nino):
            for wroot, _dirs, files in os.walk(nino):
                for name in sorted(files):
                    if name.startswith("."):
                        continue
                    if not name.lower().endswith(_IMG):
                        continue
                    add(os.path.join(wroot, name), name)
    except Exception:
        pass

    return out
