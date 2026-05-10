"""
Gamificación "El Camino del Lector": premios por eventos.
Ver docs/GAMIFICACION_EVENTO_PREMIO.md.
"""
from database import db_gamificacion as db_gam
from database.db_queries import ejecutar_query, vocal_fase_avance
from database.db_queries_v3 import (
    obtener_stats_categoria_armar_palabra,
    obtener_stats_categoria_escucha_toca,
    categoria_stats_ambas_actividades,
    _porcentaje_palabras,
    porcentaje_exito,
    PALABRAS_ESTANDAR_POR_ACTIVIDAD,
    MIN_ACIERTOS_POR_75,
    UMBRAL_PORCENTAJE,
)


def _nivel_insignia(pct):
    """Bronce 75-89%, plata 90-99%, oro 100%."""
    if pct is None or pct < UMBRAL_PORCENTAJE:
        return "bronce"
    if pct >= 1.0:
        return "oro"
    if pct >= 0.90:
        return "plata"
    return "bronce"


def add_stars(estudiante_id, cantidad):
    """Suma puntos estrella. Devuelve total actualizado."""
    return db_gam.add_stars(estudiante_id, cantidad)


def get_stars(estudiante_id):
    """Puntos estrella actuales."""
    return db_gam.get_stars(estudiante_id)


def on_correct_answer(estudiante_id, categoria, tipo_actividad):
    """
    Evento 1.1 / 1.2: acierto en Armar la Palabra o Escucha y Toca.
    - Suma 1 estrella.
    - Si es la primera vez que alcanza >=75% en esta (categoria, tipo), otorga insignia 2.1 o 2.2.
    - Si con este paso ambas actividades quedan en "Logrado", otorga 2.3 (Maestro categoría) + 20 estrellas.
    """
    if not estudiante_id or not categoria or tipo_actividad not in ("ArmarPalabra", "EscuchaToca"):
        return
    db_gam.add_stars(estudiante_id, 1)

    if tipo_actividad == "ArmarPalabra":
        ac, _ = obtener_stats_categoria_armar_palabra(estudiante_id, categoria)
    else:
        ac, _ = obtener_stats_categoria_escucha_toca(estudiante_id, categoria)
    pct = _porcentaje_palabras(ac)
    if ac >= MIN_ACIERTOS_POR_75 and pct >= UMBRAL_PORCENTAJE:
        badge_tipo = "ConstructorPalabras" if tipo_actividad == "ArmarPalabra" else "OidoLince"
        if db_gam.grant_badge(estudiante_id, badge_tipo, _nivel_insignia(pct), categoria):
            pass  # granted 2.1 or 2.2

    ok, _ = categoria_stats_ambas_actividades(estudiante_id, categoria)
    if ok and db_gam.grant_badge(estudiante_id, "MaestroCategoria", None, categoria):
        db_gam.add_stars(estudiante_id, 20)


def on_activity_complete(estudiante_id, categoria, tipo_actividad, errores_sesion=0):
    """
    Evento 1.3 / 1.4: completar 6 ítems. Si errores_sesion == 0 -> Perfecto, +5 estrellas.
    """
    if not estudiante_id:
        return
    if errores_sesion == 0:
        db_gam.add_stars(estudiante_id, 5)


def check_and_grant_album_ciclo_complete(estudiante_id, ciclo_id):
    """
    Evento 3.1: todas las categorías del ciclo con ambas actividades en "Logrado".
    Idempotente: solo otorga una vez por (estudiante, ciclo).
    """
    if not estudiante_id or not ciclo_id:
        return False
    if db_gam.has_badge(estudiante_id, "ColeccionistaCiclo", ciclo_id):
        return False
    from core.curriculum_v3 import CurriculumV3
    idx = CurriculumV3.obtener_ciclo_idx_por_id(ciclo_id)
    cats = CurriculumV3.categorias_habilitadas_para_ciclo_idx(idx)
    for cat in cats:
        ok, _ = categoria_stats_ambas_actividades(estudiante_id, cat)
        if not ok:
            return False
    return db_gam.grant_badge(estudiante_id, "ColeccionistaCiclo", None, ciclo_id)


def parse_bloque_vocales_c1(bloque_item):
    """
    Si el ítem del curriculum es un bloque de vocales (p. ej. 'A-E-I', 'A-E-I-O-U'),
    devuelve la lista de letras. Si no aplica, devuelve None (consonante u otro).
    """
    s = (bloque_item or "").strip().upper()
    if "-" not in s:
        return None
    parts = [p.strip() for p in s.split("-") if p.strip()]
    if not parts:
        return None
    if all(len(p) == 1 and p in "AEIOU" for p in parts):
        return parts
    return None


def bloque_leccion_ciclo_superada(estudiante_id, ciclo_id, bloque_item):
    """
    True si ese ítem del bloque del ciclo está superado (p. ej. Mi Ruta en hub V3).
    - Bloques tipo 'A-E-I': todas las vocales con vocal_fase_avance == 'completo'.
    - Consonantes: progreso tipo_silaba Directa con umbral 75%.
    """
    _ = ciclo_id  # reservado si el criterio varía por ciclo
    if not estudiante_id or bloque_item is None:
        return False
    letras = parse_bloque_vocales_c1(bloque_item)
    if letras:
        return all(vocal_fase_avance(estudiante_id, L) == "completo" for L in letras)
    fonema = str(bloque_item).strip().upper()
    ac, er, pct = obtener_stats_directa(estudiante_id, fonema)
    return _is_aciertos_75_y_pct(ac, er, pct)


def check_and_grant_lessons_ciclo_complete(estudiante_id, ciclo_id):
    """
    Evento 3.2: todas las lecciones del ciclo superadas.
    - C1 (vocales): ítems 'A-E-I', 'I-O-U', etc. → cada vocal del bloque debe estar
      completa según vocal_fase_avance (incluye flujo V3 con VocalCompleta+VocalFin).
    - Consonantes: progreso Directa por letra (M, P, L…).
    Idempotente.
    """
    if not estudiante_id or not ciclo_id:
        return False
    if db_gam.has_badge(estudiante_id, "TrofeoCiclo", ciclo_id):
        return False

    from core.curriculum_v3 import CurriculumV3

    bloque = CurriculumV3.obtener_bloque_por_ciclo_id(ciclo_id) or []
    if not bloque:
        return False

    for fonema in bloque:
        letras = parse_bloque_vocales_c1(fonema)
        if letras:
            for L in letras:
                if vocal_fase_avance(estudiante_id, L) != "completo":
                    return False
        else:
            ac, er, pct = obtener_stats_directa(estudiante_id, str(fonema).strip().upper())
            if not (_is_aciertos_75_y_pct(ac, er, pct)):
                return False

    # Otorgar trofeo + estrellas (3.2)
    otorgada = db_gam.grant_badge(estudiante_id, "TrofeoCiclo", None, ciclo_id)
    if otorgada:
        db_gam.add_stars(estudiante_id, 100)
    return otorgada


def ciclo_v3_activo(estudiante_id):
    """
    Ciclo V3 que debe mostrarse en la sesión (Hub, Álbum, Lecciones, Salón).

    Regla: el **primer** ciclo en orden (C1…C13) que aún **no** tiene la insignia
    ``TrofeoCiclo`` con ``ref`` = id del ciclo. Así, al completar lecciones de C1
    y otorgarse el trofeo, el siguiente render pasa automáticamente a **C2**.

    Si no hay estudiante o no hay ciclo pendiente, se devuelve C1.
    Si ya tiene trofeo en todos los ciclos, se devuelve el último (C13).
    """
    if not estudiante_id:
        return "C1"
    from core.curriculum_v3 import CurriculumV3

    for c in CurriculumV3.CICLOS:
        cid = (c.get("id") or "").strip()
        if not cid:
            continue
        if not db_gam.has_badge(estudiante_id, "TrofeoCiclo", cid):
            return cid
    return CurriculumV3.CICLOS[-1]["id"]


def ciclo_v4_activo(estudiante_id):
    """Misma regla que ``ciclo_v3_activo`` usando el currículo 4.0 (LeeConmigoV4)."""
    if not estudiante_id:
        return "C1"
    from core.curriculum_v4 import CurriculumV4

    for c in CurriculumV4.CICLOS:
        cid = (c.get("id") or "").strip()
        if not cid:
            continue
        if not db_gam.has_badge(estudiante_id, "TrofeoCiclo", cid):
            return cid
    return CurriculumV4.CICLOS[-1]["id"]


def get_badges(estudiante_id):
    """Lista de insignias del estudiante (tipo, nivel, ref, fecha)."""
    return db_gam.get_badges(estudiante_id)


def obtener_stats_directa(estudiante_id, fonema):
    """
    Para lecciones de consonantes: progreso almacenado como
    progreso_lecciones.fonema = letra (fonema) y tipo_silaba = 'Directa'
    """
    if not estudiante_id or not fonema:
        return (0, 0, 0.0)
    res = ejecutar_query(
        "SELECT aciertos, errores FROM progreso_lecciones WHERE estudiante_id = ? AND fonema = ? AND tipo_silaba = 'Directa'",
        (estudiante_id, fonema),
        fetch=True,
    )
    if not res:
        return (0, 0, 0.0)
    ac = int(res[0][0] or 0)
    er = int(res[0][1] or 0)
    pct = porcentaje_exito(ac, er)
    return (ac, er, pct)


def _is_aciertos_75_y_pct(ac, er, pct):
    """
    Criterio simple para declarar una 'lección superada':
    - al menos MIN_ACIERTOS_POR_75 (por coherencia con el 75% de 6 ítems)
    - eficiencia >= 0.75
    """
    if ac < MIN_ACIERTOS_POR_75:
        return False
    return (pct is not None) and (pct >= UMBRAL_PORCENTAJE)


def check_and_grant_letter_mastery(estudiante_id, fonema):
    """
    Evento 2.4: superación de lección individual.
    Otorga insignia de letra +10 estrellas (idempotente).
    """
    if not estudiante_id or not fonema:
        return False

    ac, er, pct = obtener_stats_directa(estudiante_id, fonema)
    if not _is_aciertos_75_y_pct(ac, er, pct):
        return False

    nivel = _nivel_insignia(pct)
    # Insignia única por letra
    granted = db_gam.grant_badge(estudiante_id, "Letra", nivel, fonema)
    if granted:
        db_gam.add_stars(estudiante_id, 10)
    return granted
