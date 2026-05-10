import os
import sqlite3


def main():
    db_path = os.path.join("database", "lee_conmigo.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, primer_nombre FROM estudiantes WHERE UPPER(primer_nombre)=UPPER(?) LIMIT 1",
        ("Ignacio",),
    )
    row = cur.fetchone()
    if not row:
        raise SystemExit("No se encontró Ignacio en la tabla estudiantes.")

    est_id = row[0]
    print("Ignacio estudiante_id:", est_id)

    vowels = ("A", "E", "I", "O", "U")
    cur.execute(
        """
        SELECT COUNT(*)
        FROM progreso_lecciones
        WHERE estudiante_id=? AND fonema IN ('A','E','I','O','U') AND tipo_silaba LIKE 'Vocal%'
        """,
        (est_id,),
    )
    before = cur.fetchone()[0]
    print("Vocal progress rows before:", before)

    cur.execute(
        """
        DELETE FROM progreso_lecciones
        WHERE estudiante_id=? AND fonema IN ('A','E','I','O','U') AND tipo_silaba LIKE 'Vocal%'
        """,
        (est_id,),
    )
    conn.commit()

    print("Rows deleted (total_changes):", conn.total_changes)

    cur.execute(
        """
        SELECT COUNT(*)
        FROM progreso_lecciones
        WHERE estudiante_id=? AND fonema IN ('A','E','I','O','U') AND tipo_silaba LIKE 'Vocal%'
        """,
        (est_id,),
    )
    after = cur.fetchone()[0]
    print("Vocal progress rows after:", after)

    conn.close()


if __name__ == "__main__":
    main()

