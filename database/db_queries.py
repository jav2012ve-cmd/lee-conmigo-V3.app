import sqlite3
import os
import unicodedata

from database.db_config import DB_PATH
from core.password_utils import (
    hash_password,
    nombre_docente_tutor_norm,
    normalizar_cedula_o_clave_numerica,
    verify_password,
)


def normalizar_clave_emoji_nino(s):
    """
    Clave tipo '🐱|🐶|🌟': NFC y sin U+FE0F por segmento (misma idea que el Salón al validar).
    Devuelve None si no hay 3 segmentos no vacíos tras '|'.
    """
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None

    def _norm_seg(t):
        t = (t or "").strip()
        t = unicodedata.normalize("NFC", t)
        return "".join(c for c in t if c != "\uFE0F")

    partes = [_norm_seg(x) for x in s.split("|")[:3]]
    if len(partes) < 3 or any(not p for p in partes):
        return None
    return "|".join(partes)

def ejecutar_query(query, params=(), fetch=False):
    """Ejecutor universal que gestiona la conexión de forma segura (Tu versión robusta)."""
    try:
        # Aseguramos que la carpeta exista
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"❌ Error en DB: {e}")
        return None

# --- SECCIÓN PADRES ---
def registrar_padre(email, pin):
    query_ins = "INSERT OR IGNORE INTO config_padres (email_padre, pin_seguridad) VALUES (?, ?)"
    ejecutar_query(query_ins, (email, pin))
    query_sel = "SELECT id FROM config_padres WHERE email_padre = ?"
    res = ejecutar_query(query_sel, (email,), fetch=True)
    return res[0][0] if res else None

def login_padre(email, pin):
    query = "SELECT id FROM config_padres WHERE email_padre = ? AND pin_seguridad = ?"
    res = ejecutar_query(query, (email, pin), fetch=True)
    return res[0][0] if res else None

def obtener_pin_padre(padre_id):
    """Devuelve el PIN del padre para verificación (p. ej. acceso al álbum)."""
    if not padre_id:
        return None
    res = ejecutar_query("SELECT pin_seguridad FROM config_padres WHERE id = ?", (padre_id,), fetch=True)
    return (res[0][0] or "").strip() if res else None

# --- SECCIÓN ESTUDIANTES ---
def crear_estudiante(datos_tupla):
    """Inserción: perfil + apellidos + claves + nombre_docente + nombre_tutor (LeeConmigo)."""
    padre_id = datos_tupla[0]
    check_padre = ejecutar_query("SELECT id FROM config_padres WHERE id = ?", (padre_id,), fetch=True)
    
    if not check_padre:
        print(f"⚠️ Padre {padre_id} no existe. Creando perfil de rescate...")
        ejecutar_query("INSERT OR IGNORE INTO config_padres (id, email_padre, pin_seguridad) VALUES (?, ?, ?)", 
                       (padre_id, f"padre_{padre_id}@test.com", "1234"))

    query = '''
        INSERT INTO estudiantes (
            padre_id, primer_nombre, segundo_nombre, apellidos, edad, genero, ciudad,
            nombre_mama, nombre_papa, nombre_hermanos, nombre_mascota,
            color_favorito, animal_favorito, deporte_favorito, transporte_favorito,
            clave_album, clave_estudiante, nombre_docente, nombre_tutor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    return ejecutar_query(query, datos_tupla)

def actualizar_estudiante(estudiante_id, datos_tupla):
    """Actualización incluyendo apellidos, claves, docente de aula y tutor LeeConmigo."""
    query = '''
        UPDATE estudiantes SET
            padre_id = ?, primer_nombre = ?, segundo_nombre = ?, apellidos = ?, edad = ?, 
            genero = ?, ciudad = ?, nombre_mama = ?, nombre_papa = ?, 
            nombre_hermanos = ?, nombre_mascota = ?, color_favorito = ?, 
            animal_favorito = ?, deporte_favorito = ?, transporte_favorito = ?,
            clave_album = ?, clave_estudiante = ?, nombre_docente = ?, nombre_tutor = ?
        WHERE id = ?
    '''
    params = datos_tupla + (estudiante_id,)
    return ejecutar_query(query, params)


def actualizar_avatar_estudiante(estudiante_id, avatar_path):
    """Actualiza solo la ruta de la foto del estudiante (p. ej. para la pantalla de bienvenida)."""
    if not estudiante_id:
        return
    ejecutar_query(
        "UPDATE estudiantes SET avatar_path = ? WHERE id = ?",
        (avatar_path or None, estudiante_id),
    )


def obtener_avatar_estudiante(estudiante_id):
    """Devuelve la ruta (avatar_path) de la foto del estudiante o None."""
    if not estudiante_id:
        return None
    res = ejecutar_query(
        "SELECT avatar_path FROM estudiantes WHERE id = ?",
        (estudiante_id,),
        fetch=True,
    )
    if not res or not res[0][0]:
        return None
    return (res[0][0] or "").strip() or None


def actualizar_ultimo_ingreso(estudiante_id):
    """Registra la fecha/hora del último ingreso del estudiante al hub."""
    if not estudiante_id:
        return
    try:
        ejecutar_query(
            "UPDATE estudiantes SET ultimo_ingreso = CURRENT_TIMESTAMP WHERE id = ?",
            (estudiante_id,),
        )
    except Exception:
        pass


def obtener_ultimo_ingreso(estudiante_id):
    """Devuelve la fecha del último ingreso del estudiante (str o None)."""
    if not estudiante_id:
        return None
    res = ejecutar_query(
        "SELECT ultimo_ingreso FROM estudiantes WHERE id = ?",
        (estudiante_id,),
        fetch=True,
    )
    if not res or not res[0][0]:
        return None
    return res[0][0]


def obtener_claves_estudiante(estudiante_id):
    """Devuelve (clave_album, clave_estudiante) para el estudiante. clave_estudiante es string de 3 emojis (ej. '🐱|🌟|❤️')."""
    if not estudiante_id:
        return None, None
    res = ejecutar_query(
        "SELECT clave_album, clave_estudiante FROM estudiantes WHERE id = ?",
        (estudiante_id,),
        fetch=True,
    )
    if not res:
        return None, None
    a, b = res[0][0], res[0][1]
    a_out = (a or "").strip() or None
    b_raw = (b or "").strip() or None
    b_out = normalizar_clave_emoji_nino(b_raw) if b_raw else None
    if b_out is None and b_raw:
        b_out = b_raw
    return a_out, b_out

def _fetch_estudiantes_con_apellidos(padre_id):
    """Intenta SELECT con apellidos; si falla (columna no existe), devuelve filas con apellidos vacío."""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, primer_nombre, segundo_nombre, COALESCE(apellidos,''), avatar_path, edad, ciclo_actual FROM estudiantes WHERE padre_id = ? ORDER BY id",
                (padre_id,),
            )
            return cursor.fetchall()
    except sqlite3.OperationalError:
        rows = ejecutar_query(
            "SELECT id, primer_nombre, segundo_nombre, avatar_path, edad, ciclo_actual FROM estudiantes WHERE padre_id = ? ORDER BY id",
            (padre_id,),
            fetch=True,
        )
        if not rows:
            return rows
        return [(r[0], r[1], r[2], "", r[3], r[4], r[5]) for r in rows]


def obtener_estudiantes_por_padre(padre_id):
    """
    Retorna (id, primer_nombre, segundo_nombre, apellidos, avatar_path, edad, ciclo_actual)
    para mostrar nombre completo con apellidos en listas para padres.
    """
    return _fetch_estudiantes_con_apellidos(padre_id) or []


def obtener_nombre_docente(estudiante_id):
    """Nombre del grupo / docente asignado al perfil (texto libre), o cadena vacía."""
    if not estudiante_id:
        return ""
    try:
        res = ejecutar_query(
            "SELECT COALESCE(nombre_docente, '') FROM estudiantes WHERE id = ?",
            (estudiante_id,),
            fetch=True,
        )
        return (res[0][0] or "").strip() if res else ""
    except Exception:
        return ""


def obtener_estudiantes_por_docente(nombre_docente):
    """
    Estudiantes cuyo campo nombre_docente coincide (sin distinguir mayúsculas).
    Retorna lista de dicts: id, primer_nombre, segundo_nombre, apellidos, padre_id,
    ultimo_ingreso, puntos_estrella, ciclo_actual.
    """
    nd = (nombre_docente or "").strip()
    if not nd:
        return []
    try:
        rows = ejecutar_query(
            """
            SELECT id, primer_nombre, segundo_nombre, COALESCE(apellidos, ''), padre_id,
                   ultimo_ingreso, COALESCE(puntos_estrella, 0), COALESCE(ciclo_actual, '')
            FROM estudiantes
            WHERE TRIM(COALESCE(nombre_docente, '')) != ''
              AND LOWER(TRIM(nombre_docente)) = LOWER(TRIM(?))
            ORDER BY primer_nombre, id
            """,
            (nd,),
            fetch=True,
        )
    except Exception:
        return []
    out = []
    for r in rows or []:
        out.append(
            {
                "id": r[0],
                "primer_nombre": r[1] or "",
                "segundo_nombre": r[2] or "",
                "apellidos": r[3] or "",
                "padre_id": r[4],
                "ultimo_ingreso": r[5],
                "puntos_estrella": int(r[6] or 0),
                "ciclo_actual": r[7] or "",
            }
        )
    return out


def obtener_nombre_tutor(estudiante_id):
    """Tutor LeeConmigo asignado al perfil (texto libre), o cadena vacía."""
    if not estudiante_id:
        return ""
    try:
        res = ejecutar_query(
            "SELECT COALESCE(nombre_tutor, '') FROM estudiantes WHERE id = ?",
            (estudiante_id,),
            fetch=True,
        )
        return (res[0][0] or "").strip() if res else ""
    except Exception:
        return ""


def obtener_estudiantes_por_tutor(nombre_tutor):
    """
    Estudiantes cuyo campo nombre_tutor coincide (sin distinguir mayúsculas).
    Misma forma que por docente: listado para la Zona Tutores.
    """
    nt = (nombre_tutor or "").strip()
    if not nt:
        return []
    try:
        rows = ejecutar_query(
            """
            SELECT id, primer_nombre, segundo_nombre, COALESCE(apellidos, ''), padre_id,
                   ultimo_ingreso, COALESCE(puntos_estrella, 0), COALESCE(ciclo_actual, '')
            FROM estudiantes
            WHERE TRIM(COALESCE(nombre_tutor, '')) != ''
              AND LOWER(TRIM(nombre_tutor)) = LOWER(TRIM(?))
            ORDER BY primer_nombre, id
            """,
            (nt,),
            fetch=True,
        )
    except Exception:
        return []
    out = []
    for r in rows or []:
        out.append(
            {
                "id": r[0],
                "primer_nombre": r[1] or "",
                "segundo_nombre": r[2] or "",
                "apellidos": r[3] or "",
                "padre_id": r[4],
                "ultimo_ingreso": r[5],
                "puntos_estrella": int(r[6] or 0),
                "ciclo_actual": r[7] or "",
            }
        )
    return out


# --- Credenciales Zona docentes / Zona tutores (cédula inicial, cambio en primer acceso) ---


def credencial_docente_tutor_existe(rol: str, nombre_display: str) -> bool:
    nn = nombre_docente_tutor_norm(nombre_display)
    if not nn or rol not in ("docente", "tutor"):
        return False
    res = ejecutar_query(
        "SELECT 1 FROM acceso_docente_tutor WHERE rol = ? AND nombre_norm = ? LIMIT 1",
        (rol, nn),
        fetch=True,
    )
    return bool(res)


def obtener_credencial_docente_tutor(rol: str, nombre_display: str):
    """Devuelve dict password_hash, must_change_password o None."""
    nn = nombre_docente_tutor_norm(nombre_display)
    if not nn or rol not in ("docente", "tutor"):
        return None
    res = ejecutar_query(
        """
        SELECT password_hash, COALESCE(must_change_password, 1)
        FROM acceso_docente_tutor WHERE rol = ? AND nombre_norm = ?
        """,
        (rol, nn),
        fetch=True,
    )
    if not res or not res[0] or not res[0][0]:
        return None
    return {"password_hash": res[0][0], "must_change_password": bool(int(res[0][1] or 1))}


def upsert_credencial_cedula_docente_tutor(rol: str, nombre_display: str, cedula_solo_digitos: str):
    """Registra o actualiza contraseña desde la cédula (obliga a cambiarla en el siguiente acceso)."""
    nn = nombre_docente_tutor_norm(nombre_display)
    if not nn or rol not in ("docente", "tutor"):
        return None
    digits = normalizar_cedula_o_clave_numerica(cedula_solo_digitos)
    if len(digits) < 5:
        return None
    h = hash_password(digits)
    return ejecutar_query(
        """
        INSERT INTO acceso_docente_tutor (rol, nombre_norm, password_hash, must_change_password)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(rol, nombre_norm) DO UPDATE SET
            password_hash = excluded.password_hash,
            must_change_password = 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        (rol, nn, h),
    )


def actualizar_password_docente_tutor(rol: str, nombre_display: str, nueva_clave: str):
    """Nueva contraseña elegida por docente/tutor; quita la obligación de cambio."""
    nn = nombre_docente_tutor_norm(nombre_display)
    if not nn or rol not in ("docente", "tutor"):
        return None
    if not (nueva_clave or "").strip() or len((nueva_clave or "").strip()) < 6:
        return None
    h = hash_password((nueva_clave or "").strip())
    return ejecutar_query(
        """
        UPDATE acceso_docente_tutor
        SET password_hash = ?, must_change_password = 0, updated_at = CURRENT_TIMESTAMP
        WHERE rol = ? AND nombre_norm = ?
        """,
        (h, rol, nn),
    )


def verificar_password_docente_tutor(rol: str, nombre_display: str, clave_ingresada: str) -> bool:
    """True si la clave coincide (cédula normalizada o contraseña actual)."""
    row = obtener_credencial_docente_tutor(rol, nombre_display)
    if not row:
        return False
    plain = (clave_ingresada or "").strip()
    digits = normalizar_cedula_o_clave_numerica(plain)
    if verify_password(plain, row["password_hash"]):
        return True
    if digits and verify_password(digits, row["password_hash"]):
        return True
    return False


def eliminar_estudiantes_duplicados(padre_id):
    """
    Elimina registros duplicados por (primer_nombre, segundo_nombre, apellidos),
    dejando solo el de mayor id por cada grupo. Retorna el número de filas eliminadas.
    """
    rows = ejecutar_query(
        "SELECT id, primer_nombre, segundo_nombre, COALESCE(apellidos, '') FROM estudiantes WHERE padre_id = ?",
        (padre_id,),
        fetch=True,
    )
    if not rows:
        return 0
    # Agrupar por (primer_nombre, segundo_nombre, apellidos); quedarse con max(id)
    grupos = {}
    for id_est, p, s, a in rows:
        key = ((p or "").strip(), (s or "").strip(), (a or "").strip())
        if key not in grupos or id_est > grupos[key]:
            grupos[key] = id_est
    ids_a_mantener = set(grupos.values())
    ids_a_borrar = [r[0] for r in rows if r[0] not in ids_a_mantener]
    if not ids_a_borrar:
        return 0
    placeholders = ",".join("?" * len(ids_a_borrar))
    ejecutar_query(
        f"DELETE FROM estudiantes WHERE id IN ({placeholders}) AND padre_id = ?",
        tuple(ids_a_borrar) + (padre_id,),
    )
    return len(ids_a_borrar)


def existe_estudiante_con_nombre(padre_id, primer_nombre, excluir_id=None):
    """True si ya existe un estudiante con ese nombre para este padre (evitar duplicados)."""
    if not padre_id or not (primer_nombre or "").strip():
        return False
    nombre = (primer_nombre or "").strip()
    if excluir_id:
        res = ejecutar_query(
            "SELECT id FROM estudiantes WHERE padre_id = ? AND primer_nombre = ? AND id != ?",
            (padre_id, nombre, excluir_id),
            fetch=True,
        )
    else:
        res = ejecutar_query(
            "SELECT id FROM estudiantes WHERE padre_id = ? AND primer_nombre = ?",
            (padre_id, nombre),
            fetch=True,
        )
    return bool(res)

def obtener_perfil_completo_nino(estudiante_id):
    if not estudiante_id: return None
    query = "SELECT * FROM estudiantes WHERE id = ?"
    res = ejecutar_query(query, (estudiante_id,), fetch=True)
    return res[0] if res else None

# --- SECCIÓN FAMILIARES ---
def listar_familiares(estudiante_id):
    """Lista (id, tipo, nombre, orden) de familiares del estudiante."""
    if not estudiante_id:
        return []
    query = "SELECT id, tipo, nombre, orden FROM familiares WHERE estudiante_id = ? ORDER BY orden, id"
    res = ejecutar_query(query, (estudiante_id,), fetch=True)
    return res or []

def agregar_familiar(estudiante_id, tipo, nombre):
    """Inserta un familiar (ej. Abuela, Tío) para el estudiante."""
    if not estudiante_id or not tipo or not nombre:
        return None
    res = ejecutar_query("SELECT COALESCE(MAX(orden),0)+1 FROM familiares WHERE estudiante_id = ?", (estudiante_id,), fetch=True)
    orden = res[0][0] if res and res[0] else 1
    query = "INSERT INTO familiares (estudiante_id, tipo, nombre, orden) VALUES (?, ?, ?, ?)"
    return ejecutar_query(query, (estudiante_id, tipo.strip(), nombre.strip(), orden))

def actualizar_familiar(familiar_id, tipo, nombre):
    if not familiar_id:
        return None
    query = "UPDATE familiares SET tipo = ?, nombre = ? WHERE id = ?"
    return ejecutar_query(query, (tipo.strip(), nombre.strip(), familiar_id))

def eliminar_familiar(familiar_id):
    if not familiar_id:
        return None
    return ejecutar_query("DELETE FROM familiares WHERE id = ?", (familiar_id,))

# --- SECCIÓN ÁLBUM ---
def guardar_en_album(estudiante_id, palabra, categoria, img_path):
    query = "INSERT INTO album_personal (estudiante_id, palabra_clave, categoria, img_path) VALUES (?, ?, ?, ?)"
    return ejecutar_query(query, (estudiante_id, palabra.upper(), categoria, img_path))

def guardar_en_album_reemplazando(estudiante_id, palabra, categoria, img_path):
    """
    Reemplaza la imagen de una palabra/categoría para evitar duplicados.
    Útil en familia cuando alternamos foto real y avatar de respaldo.
    """
    palabra_u = (palabra or "").strip().upper()
    categoria_u = (categoria or "").strip()
    if not estudiante_id or not palabra_u or not categoria_u or not img_path:
        return None
    ejecutar_query(
        "DELETE FROM album_personal WHERE estudiante_id = ? AND palabra_clave = ? AND categoria = ?",
        (estudiante_id, palabra_u, categoria_u),
    )
    return guardar_en_album(estudiante_id, palabra_u, categoria_u, img_path)

def obtener_album_nino(estudiante_id):
    """Mantiene la funcionalidad crítica para views.padre.album_mgmt"""
    query = "SELECT palabra_clave, categoria, img_path FROM album_personal WHERE estudiante_id = ?"
    return ejecutar_query(query, (estudiante_id,), fetch=True)


# --- ABECEDARIO ESTUDIANTE (Mi abecedario: 2 imágenes por letra) ---
def guardar_abecedario_letra(estudiante_id, letra, opciones_elegidas):
    """
    Guarda las 2 imágenes elegidas para una letra.
    opciones_elegidas: lista de 2 dicts {palabra, ruta_img} (o path en 'ruta_img').
    """
    if not estudiante_id or not letra or not opciones_elegidas or len(opciones_elegidas) != 2:
        return False
    letra_u = (letra or "").strip().upper()[:1]
    ejecutar_query("DELETE FROM abecedario_estudiante WHERE estudiante_id = ? AND letra = ?", (estudiante_id, letra_u))
    for orden, item in enumerate(opciones_elegidas[:2], start=1):
        palabra = (item.get("palabra") or "").strip() or "?"
        img_path = (item.get("ruta_img") or item.get("img_path") or "").strip()
        if img_path:
            ejecutar_query(
                "INSERT INTO abecedario_estudiante (estudiante_id, letra, palabra, img_path, orden) VALUES (?, ?, ?, ?, ?)",
                (estudiante_id, letra_u, palabra, img_path, orden),
            )
    return True


def obtener_abecedario_estudiante(estudiante_id):
    """
    Devuelve dict letra -> [ {palabra, ruta_img}, {palabra, ruta_img} ] con las 2 imágenes guardadas por letra.
    """
    if not estudiante_id:
        return {}
    res = ejecutar_query(
        "SELECT letra, palabra, img_path, orden FROM abecedario_estudiante WHERE estudiante_id = ? ORDER BY letra, orden",
        (estudiante_id,),
        fetch=True,
    )
    out = {}
    for row in res or []:
        letra = (row[0] or "").strip().upper()
        palabra = row[1] or ""
        img_path = row[2] or ""
        if letra and img_path:
            out.setdefault(letra, []).append({"palabra": palabra, "ruta_img": img_path})
    return out


# --- SECCIÓN PROGRESO ---
def actualizar_progreso_silabico(estudiante_id, fonema, tipo_silaba, es_acierto):
    """Mantiene tu lógica completa de conteo de aciertos y errores."""
    check_query = "SELECT id FROM progreso_lecciones WHERE estudiante_id = ? AND fonema = ? AND tipo_silaba = ?"
    res = ejecutar_query(check_query, (estudiante_id, fonema, tipo_silaba), fetch=True)
    campo = "aciertos" if es_acierto else "errores"
    if res:
        ejecutar_query(f"UPDATE progreso_lecciones SET {campo} = {campo} + 1 WHERE id = ?", (res[0][0],))
    else:
        ac, err = (1, 0) if es_acierto else (0, 1)
        ejecutar_query("INSERT INTO progreso_lecciones (estudiante_id, fonema, tipo_silaba, aciertos, errores) VALUES (?, ?, ?, ?, ?)", 
                       (estudiante_id, fonema, tipo_silaba, ac, err))


# Mismo criterio numérico que `categoria_stats_ambas_actividades` (db_queries_v3): 6 ítems, ≥75 %.
_LECCION_PALABRAS_OBJ = 6
_LECCION_UMBRAL_PCT = 0.75
_LECCION_MIN_ACIERTOS = int((_LECCION_UMBRAL_PCT * _LECCION_PALABRAS_OBJ) + 0.00001)


def _logrado_tipo_conteo_palabras(aciertos):
    """True si alcanza 'Logrado' igual que ArmarPalabra / EscuchaToca en el álbum (sobre 6 palabras)."""
    ac = int(aciertos or 0)
    ac_clamped = min(ac, _LECCION_PALABRAS_OBJ)
    pct = float(ac_clamped) / float(_LECCION_PALABRAS_OBJ)
    return (ac >= _LECCION_MIN_ACIERTOS) and (pct >= _LECCION_UMBRAL_PCT)


def vocal_fase_avance(estudiante_id, vocal):
    """
    Devuelve el avance de la lección de vocal para no repetir fases.
    - "empieza": debe hacer la parte "palabras que empiezan con X"
    - "termina": ya completó empieza, debe hacer "palabras que terminan con X"
    - "completo": ya completó ambas fases para esta vocal

    V3 (presenta → completa → termina) puede omitir "empieza"; en ese caso
    consideramos completo cuando hay 'Logrado' en VocalCompleta y en VocalFin
    (mismo criterio numérico que ArmarPalabra / EscuchaToca en el álbum).
    """
    if not estudiante_id or not vocal:
        return "empieza"
    v = (vocal or "").upper()
    q_inicio = "SELECT aciertos FROM progreso_lecciones WHERE estudiante_id = ? AND fonema = ? AND tipo_silaba = 'VocalInicio'"
    q_fin = "SELECT aciertos FROM progreso_lecciones WHERE estudiante_id = ? AND fonema = ? AND tipo_silaba = 'VocalFin'"
    q_comp = "SELECT aciertos FROM progreso_lecciones WHERE estudiante_id = ? AND fonema = ? AND tipo_silaba = 'VocalCompleta'"
    res_inicio = ejecutar_query(q_inicio, (estudiante_id, v), fetch=True)
    res_fin = ejecutar_query(q_fin, (estudiante_id, v), fetch=True)
    res_comp = ejecutar_query(q_comp, (estudiante_id, v), fetch=True)
    aciertos_inicio = int(res_inicio[0][0] if res_inicio else 0)
    aciertos_fin = int(res_fin[0][0] if res_fin else 0)
    aciertos_comp = int(res_comp[0][0] if res_comp else 0)
    li = _logrado_tipo_conteo_palabras(aciertos_inicio)
    lf = _logrado_tipo_conteo_palabras(aciertos_fin)
    lc = _logrado_tipo_conteo_palabras(aciertos_comp)
    # Clásico: reconoce inicio + escucha (termina)
    if li and lf:
        return "completo"
    # V3: completar palabras + escucha (termina)
    if lc and lf:
        return "completo"
    # Siguiente fase: escucha con palabras que terminan
    if li and not lf:
        return "termina"
    if lc and not lf:
        return "termina"
    return "empieza"


def reiniciar_avance_estudiante(estudiante_id):
    """Borra todo el progreso de lecciones del estudiante para que vuelva a empezar desde la primera letra."""
    if not estudiante_id:
        return False
    ejecutar_query("DELETE FROM progreso_lecciones WHERE estudiante_id = ?", (estudiante_id,))
    return True


def obtener_email_padre(padre_id):
    """Email del tutor para envío de informes."""
    if not padre_id:
        return None
    res = ejecutar_query("SELECT email_padre FROM config_padres WHERE id = ?", (padre_id,), fetch=True)
    return (res[0][0] or "").strip() or None if res else None


def actualizar_email_padre(padre_id, email):
    """Actualiza el correo del tutor (para recibir informes)."""
    if not padre_id:
        return False
    email = (email or "").strip()
    if not email:
        return False
    try:
        ejecutar_query("UPDATE config_padres SET email_padre = ? WHERE id = ?", (email, padre_id))
        return True
    except Exception:
        return False


def obtener_resumen_avance(estudiante_id):
    """
    Devuelve resumen para el informe: lista de (fonema, tipo_silaba, aciertos, errores).
    tipo_silaba: VocalInicio, VocalFin, Directa.
    """
    if not estudiante_id:
        return []
    res = ejecutar_query(
        "SELECT fonema, tipo_silaba, aciertos, errores FROM progreso_lecciones WHERE estudiante_id = ? ORDER BY fonema, tipo_silaba",
        (estudiante_id,),
        fetch=True,
    )
    return res or []


# --- PDF JOBS (generación en segundo plano) ---
def pdf_job_crear(estudiante_id, tipo, params_json):
    """Crea un trabajo de PDF pendiente. tipo: 'leccion' | 'abecedario'. Devuelve job_id o None."""
    if not estudiante_id or not tipo or params_json is None:
        return None
    return ejecutar_query(
        "INSERT INTO pdf_jobs (estudiante_id, tipo, params_json, status) VALUES (?, ?, ?, 'pending')",
        (estudiante_id, tipo, params_json),
    )


def pdf_job_obtener(job_id):
    """
    Devuelve un trabajo por id como dict: id, estudiante_id, tipo, params_json, status, pdf_blob, error_msg, created_at.
    Si no existe, devuelve None.
    """
    if not job_id:
        return None
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, estudiante_id, tipo, params_json, status, pdf_blob, error_msg, created_at FROM pdf_jobs WHERE id = ?",
                (job_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "estudiante_id": row[1],
                "tipo": row[2],
                "params_json": row[3],
                "status": row[4],
                "pdf_blob": row[5],
                "error_msg": row[6],
                "created_at": row[7],
            }
    except sqlite3.Error as e:
        print(f"❌ Error en DB pdf_job_obtener: {e}")
        return None


def pdf_job_marcar_ready(job_id, pdf_bytes):
    """Marca el trabajo como listo y guarda el PDF."""
    if not job_id:
        return False
    return ejecutar_query(
        "UPDATE pdf_jobs SET status = 'ready', pdf_blob = ?, error_msg = NULL WHERE id = ?",
        (pdf_bytes, job_id),
    ) is not None


def pdf_job_marcar_failed(job_id, error_msg):
    """Marca el trabajo como fallido."""
    if not job_id:
        return False
    return ejecutar_query(
        "UPDATE pdf_jobs SET status = 'failed', error_msg = ? WHERE id = ?",
        (str(error_msg)[:500], job_id),
    ) is not None


# --- Fase UI lección consonante (persiste entre sesiones / reinicios de Streamlit) ---
_FASES_CONSONANTE_VALIDAS = frozenset(
    (
        "principal",
        "actividad_armar_1",
        "actividad_armar_2",
        "escucha_palabras",
        "escucha_frases",
    )
)


def obtener_fase_leccion_consonante(estudiante_id, letra):
    """Devuelve la fase guardada o None si no hay fila (primera vez)."""
    if not estudiante_id or not letra:
        return None
    letra_n = (letra or "").strip().upper()[:8]
    if not letra_n:
        return None
    res = ejecutar_query(
        "SELECT fase FROM leccion_consonante_fase WHERE estudiante_id = ? AND letra = ?",
        (estudiante_id, letra_n),
        fetch=True,
    )
    if not res:
        return None
    f = (res[0][0] or "").strip()
    return f if f in _FASES_CONSONANTE_VALIDAS else None


def guardar_fase_leccion_consonante(estudiante_id, letra, fase):
    """UPSERT de la fase del flujo guiado para una consonante."""
    if not estudiante_id or not letra:
        return False
    letra_n = (letra or "").strip().upper()[:8]
    if not letra_n:
        return False
    fase_n = (fase or "").strip()
    if fase_n not in _FASES_CONSONANTE_VALIDAS:
        fase_n = "principal"
    return (
        ejecutar_query(
            """
            INSERT INTO leccion_consonante_fase (estudiante_id, letra, fase, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(estudiante_id, letra) DO UPDATE SET
                fase = excluded.fase,
                updated_at = CURRENT_TIMESTAMP
            """,
            (estudiante_id, letra_n, fase_n),
        )
        is not None
    )