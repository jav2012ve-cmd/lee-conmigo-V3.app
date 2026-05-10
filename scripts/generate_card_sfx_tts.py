import importlib.util
import json
import os
import re
import unicodedata
from pathlib import Path

from gtts import gTTS


ROOT = Path(__file__).resolve().parents[1]
ALBUM_CATEGORIES_PATH = ROOT / "core" / "album_categories.py"
GENERICOS_DIR = ROOT / "assets" / "genericos"
SFX_DIR = ROOT / "assets" / "sfx"
MANIFEST_PATH = SFX_DIR / "_catalogo_tarjetas_sonido.json"
REPORT_PATH = SFX_DIR / "_reporte_sonidos_tts.json"

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def load_album_module():
    spec = importlib.util.spec_from_file_location("album_categories", str(ALBUM_CATEGORIES_PATH))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def slugify(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_")


def build_manifest(album_module):
    items = []
    if not GENERICOS_DIR.is_dir():
        return items

    for name in sorted(os.listdir(GENERICOS_DIR)):
        p = GENERICOS_DIR / name
        if not p.is_file() or p.suffix.lower() not in SUPPORTED_IMAGE_EXTS:
            continue

        raw = p.stem.replace("_", " ").replace("-", " ").strip().upper()
        if not raw:
            continue

        display = album_module.nombre_para_album_y_tts(raw) or raw
        categorias = [
            c
            for c in album_module.CATEGORIAS_ALBUM
            if album_module.generico_pertenece_a_categoria(raw, c)
        ]
        if not categorias:
            continue

        items.append(
            {
                "archivo_imagen": name,
                "palabra": display,
                "categorias": categorias,
            }
        )
    return items


def generate_audio_files(items):
    SFX_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped_existing = 0
    errors = []
    total_targets = 0

    for item in items:
        palabra = (item.get("palabra") or "").strip()
        categoria = (item.get("categorias") or [None])[0]
        if not palabra:
            continue
        cat_slug = slugify(categoria or "")
        word_slug = slugify(palabra)
        if not word_slug:
            continue
        total_targets += 1

        target_dir = SFX_DIR / cat_slug if cat_slug else SFX_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{word_slug}.mp3"
        if target_file.exists() and target_file.stat().st_size > 0:
            skipped_existing += 1
            continue

        try:
            tts = gTTS(text=palabra, lang="es", slow=False)
            tts.save(str(target_file))
            created += 1
        except Exception as exc:
            errors.append(
                {
                    "palabra": palabra,
                    "categoria": categoria,
                    "destino": str(target_file),
                    "error": str(exc),
                }
            )

    return {
        "total_objetivos": total_targets,
        "creados": created,
        "omitidos_existentes": skipped_existing,
        "errores": errors,
    }


def main():
    album_module = load_album_module()

    items = build_manifest(album_module)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    result = generate_audio_files(items)
    result["tarjetas_catalogadas"] = len(items)
    result["manifest_path"] = str(MANIFEST_PATH)
    result["sfx_root"] = str(SFX_DIR)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Tarjetas catalogadas: {len(items)}")
    print(f"Objetivos audio: {result['total_objetivos']}")
    print(f"Audios creados: {result['creados']}")
    print(f"Audios existentes: {result['omitidos_existentes']}")
    print(f"Errores: {len(result['errores'])}")
    print(f"Manifiesto: {MANIFEST_PATH}")
    print(f"Reporte: {REPORT_PATH}")


if __name__ == "__main__":
    main()
