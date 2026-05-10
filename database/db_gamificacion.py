"""
Gamificación: puntos estrella y insignias.
Tablas: estudiantes.puntos_estrella, estudiante_insignias.
"""
from database.db_queries import ejecutar_query


def get_stars(estudiante_id):
    """Devuelve los puntos estrella del estudiante (0 si no existe)."""
    if not estudiante_id:
        return 0
    res = ejecutar_query(
        "SELECT puntos_estrella FROM estudiantes WHERE id = ?",
        (estudiante_id,),
        fetch=True,
    )
    if not res:
        return 0
    val = res[0][0]
    return int(val) if val is not None else 0


def add_stars(estudiante_id, cantidad):
    """Suma puntos estrella al estudiante. Devuelve el total actualizado."""
    if not estudiante_id or cantidad <= 0:
        return get_stars(estudiante_id)
    ejecutar_query(
        "UPDATE estudiantes SET puntos_estrella = COALESCE(puntos_estrella, 0) + ? WHERE id = ?",
        (cantidad, estudiante_id),
    )
    return get_stars(estudiante_id)


def has_badge(estudiante_id, tipo, ref=""):
    """True si el estudiante ya tiene la insignia (tipo, ref)."""
    if not estudiante_id or not tipo:
        return False
    res = ejecutar_query(
        "SELECT 1 FROM estudiante_insignias WHERE estudiante_id = ? AND tipo = ? AND ref = ?",
        (estudiante_id, tipo, ref or ""),
        fetch=True,
    )
    return bool(res)


def grant_badge(estudiante_id, tipo, nivel=None, ref=""):
    """
    Otorga una insignia si no la tiene (idempotente).
    ref: categoría, ciclo_id o letra según el tipo.
    Devuelve True si se otorgó, False si ya la tenía.
    """
    if not estudiante_id or not tipo:
        return False
    if has_badge(estudiante_id, tipo, ref or ""):
        return False
    try:
        ejecutar_query(
            "INSERT INTO estudiante_insignias (estudiante_id, tipo, nivel, ref) VALUES (?, ?, ?, ?)",
            (estudiante_id, tipo, nivel or "", ref or ""),
        )
        return True
    except Exception:
        return False


def get_badges(estudiante_id):
    """Lista de (tipo, nivel, ref, fecha) del estudiante."""
    if not estudiante_id:
        return []
    res = ejecutar_query(
        "SELECT tipo, nivel, ref, fecha FROM estudiante_insignias WHERE estudiante_id = ? ORDER BY fecha",
        (estudiante_id,),
        fetch=True,
    )
    return [(row[0], row[1] or "", row[2] or "", row[3]) for row in (res or [])]
