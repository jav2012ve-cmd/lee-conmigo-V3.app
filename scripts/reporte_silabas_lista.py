"""
Script de una sola ejecución: genera la lista por consonante (palabras con 2, 3 o más sílabas)
para identificar qué letras requieren más palabras. Ejecutar desde la raíz del proyecto:
  python scripts/reporte_silabas_lista.py
  python scripts/reporte_silabas_lista.py  --output lista_silabas.csv
"""
import os
import sys
import csv

# Raíz del proyecto
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db_config import init_db, DB_PATH
from core.curriculum import Curriculum
from core.asset_manager import AssetManager
from components.karaoke_ui import segmentar_palabra


def main():
    init_db()
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM estudiantes ORDER BY id LIMIT 1").fetchone()
    conn.close()
    estudiante_id = row[0] if row else None
    if not estudiante_id:
        print("No hay estudiantes en la base de datos. La lista usa álbum + biblioteca genérica; puedes crear un estudiante y volver a ejecutar.")
        estudiante_id = 1  # intentar igual para genéricos

    consonantes = list(Curriculum.SILABAS_POR_CONSONANTE.keys())
    filas = []

    for letra in consonantes:
        recursos = AssetManager.obtener_recursos_lectura(estudiante_id, letra, total=9999)
        palabras_unicas = set()
        for r in recursos or []:
            p = (r.get("palabra") or "").strip()
            if p:
                palabras_unicas.add(p.upper())

        cont_2 = cont_3 = cont_4 = 0
        for p in palabras_unicas:
            palabra_original = None
            for r in recursos or []:
                if (r.get("palabra") or "").strip().upper() == p:
                    palabra_original = (r.get("palabra") or "").strip()
                    break
            palabra_original = palabra_original or p
            silabas = segmentar_palabra(palabra_original)
            n = len(silabas)
            if n == 2:
                cont_2 += 1
            elif n == 3:
                cont_3 += 1
            else:
                cont_4 += 1

        total = cont_2 + cont_3 + cont_4
        filas.append({
            "consonante": letra,
            "2_silabas": cont_2,
            "3_silabas": cont_3,
            "4_o_mas": cont_4,
            "total": total,
        })

    # Salida por consola
    print("Consonante\t2 sílabas\t3 sílabas\t4 o más\tTotal")
    print("-" * 50)
    for r in filas:
        print(f"{r['consonante']}\t{r['2_silabas']}\t{r['3_silabas']}\t{r['4_o_mas']}\t{r['total']}")

    # Archivo CSV si se pide
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "lista_reporte_silabas.csv"
        path = os.path.join(ROOT, path) if not os.path.isabs(path) else path
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["consonante", "2_silabas", "3_silabas", "4_o_mas", "total"])
            w.writeheader()
            w.writerows(filas)
        print(f"\nLista guardada en: {path}")

    return filas


if __name__ == "__main__":
    main()
