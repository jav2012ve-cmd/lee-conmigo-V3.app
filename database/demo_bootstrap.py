"""
Estado inicial de la base DEMO: un padre de demostración y un solo estudiante (Ignacio José Salas).

La app de producto sigue usando lee_conmigo.db; main_DEMO fija LEE_CONMIGO_DB_PATH a lee_conmigo_demo.db.
"""

import os
import sqlite3

DEMO_PADRE_EMAIL = "demo@leeconmigo.local"
DEMO_PADRE_PIN = "1234"
# Misma secuencia que la primera fila de EMOJIS_CLAVE en salon_entrada / config_salon (escapes = UTF-8 fiable).
DEMO_CLAVE_ESTUDIANTE = "\U0001f431|\U0001f436|\U0001f31f"


def _is_demo_database_path() -> bool:
    from database.db_config import DB_PATH

    return os.path.basename(DB_PATH).lower() == "lee_conmigo_demo.db"


def reset_demo_database() -> None:
    """Elimina padres y estudiantes y deja un único perfil de demo (cascada limpia tablas hijas)."""
    from database.db_config import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute("DELETE FROM estudiantes")
    c.execute("DELETE FROM config_padres")
    try:
        c.execute("DELETE FROM sqlite_sequence WHERE name IN ('estudiantes', 'config_padres')")
    except sqlite3.OperationalError:
        pass
    c.execute(
        """INSERT INTO config_padres (id, email_padre, pin_seguridad, suscripcion_activa, notificaciones)
           VALUES (1, ?, ?, 1, 1)""",
        (DEMO_PADRE_EMAIL, DEMO_PADRE_PIN),
    )
    c.execute(
        """INSERT INTO estudiantes (
            padre_id, primer_nombre, segundo_nombre, apellidos, edad, genero, ciudad,
            nombre_mama, nombre_papa, nombre_hermanos, nombre_mascota,
            color_favorito, animal_favorito, deporte_favorito, transporte_favorito,
            clave_album, clave_estudiante, ciclo_actual, puntos_estrella, nombre_docente, nombre_tutor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            1,
            "Ignacio",
            "José",
            "Salas",
            6,
            "Masculino",
            "",
            "María",
            "Pedro",
            "",
            "",
            "#4CAF50",
            "perro",
            "",
            "",
            None,
            DEMO_CLAVE_ESTUDIANTE,
            "Ciclo 1",
            0,
            "Docente demo",
            "Tutor demo",
        ),
    )
    conn.commit()
    conn.close()


def ensure_demo_database() -> None:
    """
    Solo actúa si la BD activa es lee_conmigo_demo.db.

    - Si no hay estudiantes: aplica reset_demo_database() (primera ejecución o archivo nuevo).
    - Si LEE_CONMIGO_DEMO_RESET está en 1/true/yes: fuerza reset y quita la variable del entorno.
    """
    if not _is_demo_database_path():
        return

    from database.db_config import DB_PATH

    force = (os.environ.get("LEE_CONMIGO_DEMO_RESET") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM estudiantes")
        n = int(c.fetchone()[0])
    except sqlite3.OperationalError:
        n = 0
    finally:
        conn.close()

    if force:
        reset_demo_database()
        os.environ.pop("LEE_CONMIGO_DEMO_RESET", None)
        return

    if n == 0:
        reset_demo_database()


if __name__ == "__main__":
    import sys

    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    os.environ["LEE_CONMIGO_DB_PATH"] = os.path.join(_root, "database", "lee_conmigo_demo.db")
    from database.db_config import DB_PATH, init_db

    init_db()
    reset_demo_database()
    print("Base DEMO reiniciada:", DB_PATH)
