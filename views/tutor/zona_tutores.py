"""
Zona Tutores: maestros/tutores que acompañan en LeeConmigo (campo nombre_tutor del perfil).
Acceso con contraseña (cédula en Configuración del salón; cambio en el primer acceso).
"""

from database.db_queries import obtener_estudiantes_por_tutor
from views.rol_portal_zona import render_zona_con_acceso_rol


def render_zona_tutores():
    render_zona_con_acceso_rol(
        rol="tutor",
        titulo_pagina="Zona Tutores",
        caption_md=(
            "Accede con el **mismo nombre de tutor LeeConmigo** que figura en el perfil del niño "
            "y la **contraseña** que el tutor registró (**cédula** la primera vez). "
            "No tiene que coincidir con la docente de aula."
        ),
        label_nombre="Nombre del tutor en LeeConmigo",
        placeholder_nombre="Ej: Profe Luis",
        label_listado="Tutor:",
        mensaje_sin_credencial=(
            "Aún no se ha registrado la **cédula** de este tutor LeeConmigo. "
            "El tutor debe abrir **Configuración del salón** → nombre en **Tutor LeeConmigo** "
            "→ **Cédula del tutor** y guardar el perfil."
        ),
        mensaje_sin_alumnos=(
            "No hay perfiles con ese nombre de tutor. Revisa la escritura o pide a la familia "
            "que lo registre en el perfil del niño (Zona de padres → Configuración)."
        ),
        obtener_alumnos=obtener_estudiantes_por_tutor,
    )
