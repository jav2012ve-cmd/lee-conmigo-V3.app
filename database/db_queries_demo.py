"""
Consultas de BD para la DEMO comercial.
No modifica la logica de V3/V4; aplica restricciones solo al flujo DEMO.
"""

from database.db_queries import *  # noqa: F401,F403
from database.db_queries import ejecutar_query


DEMO_ALBUM_CATEGORIAS_PERMITIDAS = frozenset(
    {"Familia", "Juguetes", "En la cocina", "Instrumentos musicales"}
)


def _categoria_album_demo_permitida(categoria):
    return (categoria or "").strip() in DEMO_ALBUM_CATEGORIAS_PERMITIDAS


def guardar_en_album(estudiante_id, palabra, categoria, img_path):
    if not _categoria_album_demo_permitida(categoria):
        return None
    query = "INSERT INTO album_personal (estudiante_id, palabra_clave, categoria, img_path) VALUES (?, ?, ?, ?)"
    return ejecutar_query(query, (estudiante_id, (palabra or "").upper(), categoria, img_path))


def guardar_en_album_reemplazando(estudiante_id, palabra, categoria, img_path):
    palabra_u = (palabra or "").strip().upper()
    categoria_u = (categoria or "").strip()
    if not estudiante_id or not palabra_u or not categoria_u or not img_path:
        return None
    if not _categoria_album_demo_permitida(categoria_u):
        return None
    ejecutar_query(
        "DELETE FROM album_personal WHERE estudiante_id = ? AND palabra_clave = ? AND categoria = ?",
        (estudiante_id, palabra_u, categoria_u),
    )
    return guardar_en_album(estudiante_id, palabra_u, categoria_u, img_path)
