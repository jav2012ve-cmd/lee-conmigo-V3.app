import json
import os
import re
import unicodedata
from pathlib import Path

from gtts import gTTS


ROOT = Path(__file__).resolve().parents[1]
SFX_DIR = ROOT / "assets" / "sfx"
CATALOG_PATH = SFX_DIR / "_catalogo_tarjetas_sonido.json"
SOUNDS_MAP_PATH = SFX_DIR / "_sonidos_caracteristicos.json"
REPORT_PATH = SFX_DIR / "_reporte_sonidos_caracteristicos.json"


def slugify(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def run():
    if not CATALOG_PATH.is_file():
        raise FileNotFoundError(f"No existe catálogo: {CATALOG_PATH}")
    if not SOUNDS_MAP_PATH.is_file():
        raise FileNotFoundError(f"No existe mapeo: {SOUNDS_MAP_PATH}")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    sounds_map = json.loads(SOUNDS_MAP_PATH.read_text(encoding="utf-8"))

    updated = []
    skipped = 0
    errors = []

    for item in catalog:
        palabra = (item.get("palabra") or "").strip()
        if not palabra:
            continue
        palabra_slug = slugify(palabra)
        sound_text = sounds_map.get(palabra_slug)
        if not sound_text:
            skipped += 1
            continue

        categorias = item.get("categorias") or []
        categoria_slug = slugify(categorias[0]) if categorias else ""
        target_dir = SFX_DIR / categoria_slug if categoria_slug else SFX_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{palabra_slug}.mp3"

        try:
            tts = gTTS(text=sound_text, lang="es", slow=False)
            tts.save(str(target_file))
            updated.append(
                {
                    "palabra": palabra,
                    "palabra_slug": palabra_slug,
                    "categoria": categorias[0] if categorias else "",
                    "audio_texto": sound_text,
                    "archivo": str(target_file),
                }
            )
        except Exception as exc:
            errors.append({"palabra": palabra, "archivo": str(target_file), "error": str(exc)})

    report = {
        "total_catalogo": len(catalog),
        "total_sonidos_configurados": len(sounds_map),
        "actualizados": len(updated),
        "omitidos_sin_mapeo": skipped,
        "errores": errors,
        "detalles_actualizados": updated,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Actualizados: {len(updated)}")
    print(f"Omitidos sin mapeo: {skipped}")
    print(f"Errores: {len(errors)}")
    print(f"Reporte: {REPORT_PATH}")


if __name__ == "__main__":
    run()
