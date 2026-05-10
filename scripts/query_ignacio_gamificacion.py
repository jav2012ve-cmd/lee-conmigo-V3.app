import os
import sqlite3


def main():
    db_path = os.path.join("database", "lee_conmigo.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1) Encontrar Ignacio
    cur.execute(
        "SELECT id, primer_nombre, ciclo_actual FROM estudiantes WHERE UPPER(primer_nombre) LIKE UPPER(?)",
        ("%IGNACIO%",),
    )
    rows = cur.fetchall()
    print("Ignacio rows:", rows)
    if not rows:
        raise SystemExit("No se encontró Ignacio en la tabla estudiantes.")

    est_id = rows[0][0]
    print("Usando estudiante_id:", est_id)

    vowels = ["A", "E", "I", "O", "U"]

    # 2) Progreso de vocales en lecciones (V2)
    sql_vowels = (
        "SELECT fonema, tipo_silaba, aciertos, errores, ultima_sesion "
        "FROM progreso_lecciones "
        "WHERE estudiante_id=? AND fonema IN (?,?,?,?,?) "
        "AND tipo_silaba IN (?,?) "
        "ORDER BY fonema, tipo_silaba, ultima_sesion DESC"
    )
    cur.execute(sql_vowels, (est_id, *vowels, "VocalInicio", "VocalFin"))
    vowel_rows = cur.fetchall()

    print("\nVocalInicio / VocalFin (orden reciente ->):")
    for r in vowel_rows:
        print(r)

    # Resumen: aciertos recientes para inicio y fin por vocal
    summary = {v: {"VocalInicio": None, "VocalFin": None} for v in vowels}
    for fonema, tipo, aciertos, errores, ultima_sesion in vowel_rows:
        if summary[fonema][tipo] is None:
            summary[fonema][tipo] = (aciertos, errores, ultima_sesion)
    print("\nResumen (primer registro más reciente por tipo):")
    for v in vowels:
        print(v, summary[v])

    # 3) Progreso de álbum para ciclo 1 (V3 gating)
    cats_c1 = ["Familia", "Juguetes", "En la cocina"]
    sql_album = (
        "SELECT fonema, tipo_silaba, aciertos, errores, ultima_sesion "
        "FROM progreso_lecciones "
        "WHERE estudiante_id=? AND fonema IN (?,?,?) "
        "AND tipo_silaba IN ('ArmarPalabra','EscuchaToca') "
        "ORDER BY fonema, tipo_silaba, ultima_sesion DESC"
    )
    cur.execute(sql_album, (est_id, *cats_c1))
    album_rows = cur.fetchall()
    print("\nAlbum progress C1 categories (Familia/Juguetes/En la cocina):")
    for r in album_rows:
        print(r)

    # Cálculo de "logrado" según db_queries_v3 (75% en ambas con 6 ítems)
    PALABRAS = 6
    UMBRAL = 0.75
    MIN_ACIERTOS_POR_75 = int((UMBRAL * PALABRAS) + 0.00001)  # coherente con db_queries_v3

    def logrado_ac(ac):
        ac = int(ac or 0)
        pct = min(ac, PALABRAS) / float(PALABRAS)
        return (ac >= MIN_ACIERTOS_POR_75) and (pct >= UMBRAL)

    # resumen por categoría
    print("\nEvaluación gating álbum (según db_queries_v3):")
    for cat in cats_c1:
        # aciertos más recientes por actividad (solo tomamos el top1 por tipo)
        top = {}
        for fonema, tipo, aciertos, errores, ultima_sesion in album_rows:
            if fonema != cat:
                continue
            if tipo not in top:
                top[tipo] = (aciertos, errores, ultima_sesion)

        ac_armar = top.get("ArmarPalabra", (0, 0, None))[0]
        ac_et = top.get("EscuchaToca", (0, 0, None))[0]
        ok_armar = logrado_ac(ac_armar)
        ok_et = logrado_ac(ac_et)
        ok_both = ok_armar and ok_et
        print(
            f"- {cat}: ArmarPalabra aciertos={ac_armar} ok={ok_armar} | "
            f"EscuchaToca aciertos={ac_et} ok={ok_et} => ambos={ok_both}"
        )

    conn.close()


if __name__ == "__main__":
    main()

