"""
Opciones de color favorito: nombres en español y valor hex para guardar y usar en la app.
"""

# (Nombre mostrado, valor hex que se guarda)
OPCIONES_COLOR_FAVORITO = [
    ("Azul", "#3498db"),
    ("Azul claro", "#4A90E2"),
    ("Rojo", "#e74c3c"),
    ("Verde", "#2ecc71"),
    ("Amarillo", "#f1c40f"),
    ("Naranja", "#e67e22"),
    ("Rosa", "#e91e63"),
    ("Morado", "#9b59b6"),
    ("Verde azulado", "#1abc9c"),
    ("Azul oscuro", "#2980b9"),
    ("Gris", "#7f8c8d"),
]

# Para mostrar el nombre cuando tenemos el hex guardado (ej. en perfil / zona padres)
HEX_A_NOMBRE = {hex_val.lower(): nombre for nombre, hex_val in OPCIONES_COLOR_FAVORITO}


def nombre_de_color(hex_val):
    """Devuelve el nombre del color si está en la lista; si no, el hex tal cual."""
    if not hex_val or not isinstance(hex_val, str):
        return hex_val or "—"
    h = hex_val.strip().lower()
    if not h.startswith("#"):
        h = "#" + h
    return HEX_A_NOMBRE.get(h, hex_val)
