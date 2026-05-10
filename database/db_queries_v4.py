"""
Consultas para la versión 4.0 (misma lógica que db_queries_v3).
"""
from database.db_queries import ejecutar_query


PALABRAS_ESTANDAR_POR_ACTIVIDAD = 6
UMBRAL_PORCENTAJE = 0.75
MIN_ACIERTOS_POR_75 = int((UMBRAL_PORCENTAJE * PALABRAS_ESTANDAR_POR_ACTIVIDAD) + 0.00001)


def _porcentaje_palabras(aciertos):
    ac = int(aciertos or 0)
    if PALABRAS_ESTANDAR_POR_ACTIVIDAD <= 0:
        return 0.0
    ac_clamped = min(ac, PALABRAS_ESTANDAR_POR_ACTIVIDAD)
    return float(ac_clamped) / float(PALABRAS_ESTANDAR_POR_ACTIVIDAD)


def obtener_stats_categoria_tipo(estudiante_id, categoria, tipo_silaba):
    if not estudiante_id or not categoria or not tipo_silaba:
        return (0, 0)
    cats = [categoria]
    if (categoria or "").strip() == "Partes del cuerpo":
        cats.append("Partes del cuerpo humano")
    ac_total = er_total = 0
    for cat in cats:
        res = ejecutar_query(
            "SELECT aciertos, errores FROM progreso_lecciones WHERE estudiante_id = ? AND fonema = ? AND tipo_silaba = ?",
            (estudiante_id, cat, tipo_silaba),
            fetch=True,
        )
        if res:
            ac_total += int(res[0][0] or 0)
            er_total += int(res[0][1] or 0)
    return (ac_total, er_total)


def obtener_stats_categoria_armar_palabra(estudiante_id, categoria):
    return obtener_stats_categoria_tipo(estudiante_id, categoria, "ArmarPalabra")


def obtener_stats_categoria_escucha_toca(estudiante_id, categoria):
    return obtener_stats_categoria_tipo(estudiante_id, categoria, "EscuchaToca")


def porcentaje_exito(aciertos, errores):
    total = int(aciertos or 0) + int(errores or 0)
    if total <= 0:
        return 0.0
    return float(aciertos or 0) / float(total)


def categoria_stats_ambas_actividades(estudiante_id, categoria):
    ac_armar, er_armar = obtener_stats_categoria_armar_palabra(estudiante_id, categoria)
    ac_et, er_et = obtener_stats_categoria_escucha_toca(estudiante_id, categoria)

    pct_armar = _porcentaje_palabras(ac_armar)
    pct_et = _porcentaje_palabras(ac_et)

    logrado_armar = (ac_armar >= MIN_ACIERTOS_POR_75) and (pct_armar >= UMBRAL_PORCENTAJE)
    logrado_et = (ac_et >= MIN_ACIERTOS_POR_75) and (pct_et >= UMBRAL_PORCENTAJE)

    ok = logrado_armar and logrado_et
    return ok, {
        "ArmarPalabra": {"ac": ac_armar, "er": er_armar, "pct": pct_armar, "logrado": logrado_armar},
        "EscuchaToca": {"ac": ac_et, "er": er_et, "pct": pct_et, "logrado": logrado_et},
    }


def categoria_ok_75_por_ambas_actividades(estudiante_id, categoria):
    return categoria_stats_ambas_actividades(estudiante_id, categoria)


def stats_actividad_leccion_vocal(estudiante_id, vocal):
    v = (vocal or "").strip().upper()
    if not v:
        return {}

    def _pack(tipo_silaba):
        ac, er = obtener_stats_categoria_tipo(estudiante_id, v, tipo_silaba)
        pct = _porcentaje_palabras(ac)
        logrado = (ac >= MIN_ACIERTOS_POR_75) and (pct >= UMBRAL_PORCENTAJE)
        return {"ac": ac, "er": er, "pct": pct, "logrado": logrado}

    return {
        "CompletarPalabras": _pack("VocalCompleta"),
        "EscuchaToca": _pack("VocalFin"),
        "ReconoceInicio": _pack("VocalInicio"),
    }
