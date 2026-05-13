"""
Zona docentes: consulta del desempeño del grupo asociado al nombre de docente
guardado en cada perfil de estudiante (campo nombre_docente). Acceso con contraseña
(cédula registrada en Configuración del salón; cambio obligatorio en el primer acceso).
"""

from database.db_queries import obtener_estudiantes_por_docente
from views.rol_portal_zona import render_zona_con_acceso_rol


def render_zona_docente():
    render_zona_con_acceso_rol(
        rol="docente",
        titulo_pagina="Zona docentes",
        caption_md=(
            "Accede con el **mismo nombre de docente o grupo** que figura en el perfil de cada niño "
            "y la **contraseña** que el tutor registró (**cédula** la primera vez). "
            "Los datos se cargan en **Configuración del salón** (perfil del niño)."
        ),
        label_nombre="Nombre de la docente o del grupo",
        placeholder_nombre="Ej: Profe Ana · 1º A",
        label_listado="Grupo:",
        mensaje_sin_credencial=(
            "Aún no se ha registrado la **cédula** de esta docente o grupo. "
            "El tutor debe abrir **Configuración del salón** → mismo nombre en el campo de docente "
            "→ **Cédula de la docente** y guardar el perfil."
        ),
        mensaje_sin_alumnos=(
            "No hay perfiles con ese nombre de docente/grupo. Revisa la escritura o pide al tutor "
            "que lo actualice en la configuración del niño."
        ),
        obtener_alumnos=obtener_estudiantes_por_docente,
    )
