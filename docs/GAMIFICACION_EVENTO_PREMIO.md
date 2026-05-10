# Gamificación "El Camino del Lector" — Tabla Evento → Premio

Especificación de producto: cada evento en la app dispara premios concretos (Puntos Estrella, Insignias, Recompensas de progreso). Esta tabla es la referencia para implementación.

---

## Leyenda

| Símbolo | Significado |
|--------|-------------|
| ⚡ | Puntos Estrella (moneda acumulable) |
| 🏅 | Insignia (se guarda en Álbum de Trofeos) |
| 🎁 | Recompensa de progreso (desbloqueo estético) |
| 🔊 | Sonido / feedback auditivo |
| ✨ | Animación / feedback visual |

---

## Nivel 1 — Recompensa inmediata (durante la actividad)

| # | Evento | Condición | Premio | Notas UI |
|---|--------|-----------|--------|----------|
| 1.1 | Acierto en "Armar la Palabra" | Niño acierta una palabra (pulsa Listo y es correcto) | ⚡ +1 | 🔊 Sonido positivo corto. ✨ Animación: estrella vuela al contador. |
| 1.2 | Acierto en "Escucha y Toca" | Niño elige la imagen correcta | ⚡ +1 | 🔊 Sonido positivo corto. ✨ Animación: estrella vuela al contador. |
| 1.3 | Completar actividad (6 ítems) | Termina las 6 palabras o 6 imágenes de la actividad | — | ✨ Pantalla de resumen con personaje celebrando. |
| 1.4 | Completar actividad sin errores (Perfecto) | Misma actividad de 6 ítems con 0 errores en esa sesión | ⚡ +5 | Se suma al premio por completar; mostrar "¡Perfecto!" en resumen. |

---

## Nivel 2 — Recompensa de hito (superación en Mi Ruta)

| # | Evento | Condición | Premio | Notas UI |
|---|--------|-----------|--------|----------|
| 2.1 | Superar "Armar la Palabra" de una categoría | Primera vez que aciertos ≥ 75% (mín. 5/6) en esa categoría para ArmarPalabra | 🏅 Insignia "Constructor de Palabras" (bronce / plata / oro según puntuación) | Nivel: bronce 75–89%, plata 90–99%, oro 100%. |
| 2.2 | Superar "Escucha y Toca" de una categoría | Primera vez que aciertos ≥ 75% (mín. 5/6) en esa categoría para EscuchaToca | 🏅 Insignia "Oído de Lince" (bronce / plata / oro) | Misma regla de niveles que 2.1. |
| 2.3 | Completar una categoría | Ambas actividades (ArmarPalabra y EscuchaToca) pasan a "Logrado" para esa categoría | 🏅 Insignia "Maestro de [Nombre Categoría]" (ej. Maestro de Juguetes) + ⚡ +20 | ✨ Categoría en Mi Ruta brilla y check dorado. |
| 2.4 | Superar una lección individual | Niño completa/supera una letra o bloque de lección (según criterio de dominio en lecciones_nino) | 🏅 Insignia de la letra (ej. "La M brillante") + ⚡ +10 | Definir criterio: ej. X aciertos en esa letra o "lección completada". |

---

## Nivel 3 — Recompensa de ciclo (gran premio)

### Fase 1 — Álbum del ciclo completo

| # | Evento | Condición | Premio | Notas UI |
|---|--------|-----------|--------|----------|
| 3.1 | Completar TODO el álbum del ciclo | Todas las categorías habilitadas del ciclo con ambas actividades en "Logrado" | 🏅 Insignia "Coleccionista Experto C[X]" (ej. C1) + 🎁 1 accesorio nuevo para avatar (sombrero, gafas, etc.) | ✨ Mensaje en hub con confeti: "¡Álbum del Ciclo [C1] Completado!". Se habilita botón "Mis Lecciones". |

### Fase 2 — Lecciones del ciclo completadas

| # | Evento | Condición | Premio | Notas UI |
|---|--------|-----------|--------|----------|
| 3.2 | Completar TODAS las lecciones del ciclo | Las 3 letras/bloques del ciclo marcados como superados | 🏅 Trofeo del Ciclo [C1] (en "Estantería de Trofeos") + ⚡ +100 + 🎁 Nueva categoría del álbum desbloqueada + 🎁 Nuevo fondo de pantalla (ej. espacial, selva) | ✨ Pantalla de celebración final; personaje avanza en mapa hacia el siguiente ciclo. Pop-up: nueva categoría y lecciones disponibles. |

---

## Resumen de tipos de premio por evento

| Tipo | Eventos que lo otorgan |
|------|-------------------------|
| ⚡ Puntos Estrella | 1.1, 1.2 (+1); 1.4 (+5); 2.3 (+20); 2.4 (+10); 3.2 (+100) |
| 🏅 Insignias | 2.1 Constructor de Palabras; 2.2 Oído de Lince; 2.3 Maestro de [Categoría]; 2.4 Letra; 3.1 Coleccionista Experto C[X]; 3.2 Trofeo C[X] |
| 🎁 Recompensas | 3.1 Accesorio avatar; 3.2 Nueva categoría + Fondo de pantalla |
| 🔊✨ Feedback | 1.1, 1.2 sonido + animación; 1.3 resumen; 2.3 brillo en Mi Ruta; 3.1 confeti; 3.2 mapa + pop-up |

---

## Criterios técnicos a definir en implementación

- **Estudiante:** todos los premios se asocian a `estudiante_id`.
- **Idempotencia:** insignias y trofeos se conceden una sola vez por estudiante/categoría/ciclo (evitar duplicados al recargar).
- **Niveles bronce/plata/oro:** umbrales exactos (ej. 75–89%, 90–99%, 100%) y si aplican a 2.1 y 2.2 solo.
- **"Perfecto" (1.4):** contar errores solo en la sesión actual de 6 ítems (Armar la palabra o Escucha y Toca), no histórico.
- **Superación de lección (2.4):** criterio en `lecciones_nino` (ej. N aciertos en esa letra, o flag "lección_completada" por letra).

---

*Documento de especificación. Versión 1.0 — El Camino del Lector.*
