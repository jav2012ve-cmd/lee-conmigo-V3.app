# LeeConmigo DEMO (comercial)

Esta version DEMO esta pensada para presentaciones comerciales y no reemplaza los flujos completos de V3/V4.

## Ejecutar la DEMO

```bash
streamlit run main_DEMO.py
```

## Alcance funcional de la DEMO

- Registro y acceso de estudiantes desde flujo dedicado DEMO.
- Sin fotos personales: representacion por avatares de galeria.
- Albumes activos:
  - Familia
  - Juguetes
  - En la cocina
  - Instrumentos musicales
- Resto de tapas de album: visibles pero bloqueadas.
- Lecciones activas: M y P.

## Estructura principal

- Entrada DEMO: `main_DEMO.py`
- Estado de sesion DEMO: `core/session_state_demo.py`
- Vistas DEMO: `views_demo/`
- Restricciones de BD DEMO: `database/db_queries_demo.py`

## Checklist rapido para validar antes de una presentacion

1. Abrir DEMO y crear un estudiante.
2. Verificar que no se promueva subida de fotos personales en gestion de album.
3. Confirmar que solo 4 albumes abren y los demas muestran bloqueo.
4. Confirmar que en lecciones solo aparecen M y P.
5. Verificar regreso correcto a Salon, Hub y Zona de padres.

## Nota operativa

Si necesitas una presentacion mas rapida, prepara previamente:

- `assets/avatars_familia/` con variedad de personajes.
- `assets/album_categorias/` con portadas visibles para todas las categorias.
- Al menos 1-2 perfiles de estudiante de ejemplo.
