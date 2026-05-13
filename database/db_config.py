import sqlite3
import os

# Definimos la ruta de forma absoluta respecto a este archivo para evitar errores de ejecución
# Esto asegura que la DB siempre se cree en /database/ sin importar desde dónde corras Streamlit
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_default_db = os.path.join(BASE_DIR, "lee_conmigo.db")
# main_DEMO.py puede fijar LEE_CONMIGO_DB_PATH antes de importar este módulo (lee_conmigo_demo.db)
DB_PATH = os.path.abspath(os.environ.get("LEE_CONMIGO_DB_PATH") or _default_db)

def init_db():
    """
    Inicializa la base de datos asegurando que el directorio exista 
    y todas las tablas necesarias para el método LeeConmigo estén presentes.
    """
    # 1. Asegurar que el directorio 'database' existe
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    # 2. Conexión robusta
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Habilitar claves foráneas para integridad referencial (borrado en cascada)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 3. TABLA: CONFIG_PADRES (Gestión de acceso)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_padres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_padre TEXT UNIQUE NOT NULL,
            pin_seguridad TEXT NOT NULL DEFAULT '1234',
            suscripcion_activa BOOLEAN DEFAULT 1,
            notificaciones BOOLEAN DEFAULT 1
        )
    ''')

    # 4. TABLA: ESTUDIANTES (Perfil enriquecido para Enfoque Comunicativo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            padre_id INTEGER,
            primer_nombre TEXT NOT NULL,
            segundo_nombre TEXT,
            edad INTEGER,
            genero TEXT,
            ciudad TEXT,
            nombre_mama TEXT,
            nombre_papa TEXT,
            nombre_hermanos TEXT,
            nombre_mascota TEXT,
            color_favorito TEXT,
            animal_favorito TEXT,
            deporte_favorito TEXT,
            transporte_favorito TEXT,
            avatar_path TEXT,
            ciclo_actual TEXT DEFAULT 'Ciclo 1',
            progreso_global REAL DEFAULT 0.0,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            clave_album TEXT,
            clave_estudiante TEXT,
            FOREIGN KEY(padre_id) REFERENCES config_padres(id) ON DELETE CASCADE
        )
    ''')
    # Migración: añadir columnas si no existen (DB ya creadas)
    for col, tipo in [
        ("clave_album", "TEXT"),
        ("clave_estudiante", "TEXT"),
        ("apellidos", "TEXT"),
        ("ultimo_ingreso", "TIMESTAMP"),
        ("puntos_estrella", "INTEGER DEFAULT 0"),
        ("nombre_docente", "TEXT"),
        ("nombre_tutor", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE estudiantes ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass  # columna ya existe

    # Tabla gamificación: insignias (idempotente por estudiante + tipo + ref)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiante_insignias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            nivel TEXT,
            ref TEXT NOT NULL DEFAULT '',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(estudiante_id, tipo, ref),
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
        )
    ''')

    # 5. TABLA: ALBUM_PERSONAL (Activos significativos para el niño)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS album_personal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER,
            palabra_clave TEXT NOT NULL, 
            categoria TEXT,     
            img_path TEXT,      
            audio_path TEXT,    
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
        )
    ''')

    # 5b. TABLA: FAMILIARES (familiares del niño para personalizar lecciones)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS familiares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            orden INTEGER DEFAULT 0,
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
        )
    ''')

    # 6. TABLA: PROGRESO_LECCIONES (Métrica del método silábico)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progreso_lecciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER,
            fonema TEXT NOT NULL,        
            tipo_silaba TEXT,
            aciertos INTEGER DEFAULT 0,
            errores INTEGER DEFAULT 0,
            completado BOOLEAN DEFAULT 0,
            ultima_sesion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
        )
    ''')

    # 7. TABLA: ABECEDARIO_ESTUDIANTE (2 imágenes elegidas por letra para "Mi abecedario")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS abecedario_estudiante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER NOT NULL,
            letra TEXT NOT NULL,
            palabra TEXT NOT NULL,
            img_path TEXT NOT NULL,
            orden INTEGER NOT NULL,
            UNIQUE(estudiante_id, letra, orden),
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
        )
    ''')

    # 8. TABLA: PDF_JOBS (generación de PDFs en segundo plano)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            params_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            pdf_blob BLOB,
            error_msg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
        )
    ''')

    # Fase del flujo guiado (principal → armar → escucha) por consonante y estudiante
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leccion_consonante_fase (
            estudiante_id INTEGER NOT NULL,
            letra TEXT NOT NULL,
            fase TEXT NOT NULL DEFAULT 'principal',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (estudiante_id, letra),
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
        )
    ''')

    # Credenciales Zona docentes / Zona tutores (nombre en perfil + contraseña; inicial = cédula)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acceso_docente_tutor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT NOT NULL CHECK(rol IN ('docente', 'tutor')),
            nombre_norm TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            must_change_password INTEGER NOT NULL DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(rol, nombre_norm)
        )
    ''')

    conn.commit()
    conn.close()
    # Evitar emojis para compatibilidad con codificación Windows (cp1252)
    print(f"Base de datos inicializada en: {DB_PATH}")

if __name__ == "__main__":
    init_db()