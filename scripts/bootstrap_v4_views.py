"""Reemplaza referencias V3 por V4 en views_v4/. Excluye claves v3_* en lecciones_nino_v4 (puente a lecciones V2)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWS = ROOT / "views_v4"
SKIP_GLOBAL = VIEWS / "estudiante" / "lecciones_nino_v4.py"

CHAIN = [
    ("ciclo_v3_activo", "ciclo_v4_activo"),
    ("CurriculumV3", "CurriculumV4"),
    ("curriculum_v3", "curriculum_v4"),
    ("db_queries_v3", "db_queries_v4"),
    ("render_salon_entrada_v3", "render_salon_entrada_v4"),
    ("render_config_salon_v3", "render_config_salon_v4"),
    ("render_zona_padres_v3", "render_zona_padres_v4"),
    ("render_album_mgmt_v3", "render_album_mgmt_v4"),
    ("render_hub_nino_v3", "render_hub_nino_v4"),
    ("render_lecciones_nino_v3", "render_lecciones_nino_v4"),
    ("render_album_nino_v3", "render_album_nino_v4"),
    ("render_album_silabas_nino_v3", "render_album_silabas_nino_v4"),
    ("render_album_abecedario_nino_v3", "render_album_abecedario_nino_v4"),
    ("render_informe_sesion_v3", "render_informe_sesion_v4"),
    ("_mensaje_ruta_v3", "_mensaje_ruta_v4"),
    ("_render_salon_entrada_v3", "_render_salon_entrada_v4"),
    ("Versión V3", "Versión 4.0"),
    ("(V3)", "(4.0)"),
    ("Mi escalera de progreso (V3)", "Mi escalera de progreso (4.0)"),
    ("Panel de Control (V3)", "Panel de Control (4.0)"),
    ("Gestión de álbum (V3)", "Gestión de álbum (4.0)"),
    ("Volver a Mi Ruta (V3)", "Volver a Mi Ruta (4.0)"),
    ("Lecciones V3 del ciclo", "Lecciones 4.0 del ciclo"),
]

for p in VIEWS.rglob("*.py"):
    text = p.read_text(encoding="utf-8")
    orig = text
    for a, b in CHAIN:
        text = text.replace(a, b)
    if p.resolve() == SKIP_GLOBAL.resolve():
        p.write_text(text, encoding="utf-8")
        print("updated (chain only)", p.relative_to(ROOT))
        continue
    text = text.replace("v3_", "v4_")
    text = text.replace("btn_v3_", "btn_v4_")
    if text != orig:
        p.write_text(text, encoding="utf-8")
        print("updated", p.relative_to(ROOT))

print("done")
