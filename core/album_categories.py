"""
Categorías fijas del álbum. Se usan en la gestión (padres) y en la vista del niño.
Palabras clave para asignar imágenes de assets/genericos a cada categoría (por la primera palabra del nombre de archivo).
"""

import unicodedata

CATEGORIAS_ALBUM = [
    "Familia",
    "Colores",
    "Figuras geométricas",
    "Animales del mar",
    "Juguetes",
    "Medios de transporte",
    "Números",
    "Animales voladores",
    "Partes del cuerpo humano",
    "En la cocina",
    "En la escuela",
]

# Primera palabra del nombre de archivo (minúscula) -> categoría. Usado para rellenar álbum con genericos.
GENERICOS_PALABRAS_POR_CATEGORIA = {
    "Familia": {
        "abuela", "abuelo", "mama", "papá", "papa", "tia", "tio", "prima", "primo",
        "hermano", "hermana", "camila", "albert", "margarita", "jose", "samanta",
        "johana", "olegario", "abril", "sanchez", "alberto", "yo", "nene", "norkis",
        "ignacio",
    },
    "Colores": {
        "amarillo", "azul", "blanco", "rojo", "verde", "violeta", "rosado", "dorado",
        "colornaranja", "color", "colo", "gris", "marron", "negro",
    },
    "Figuras geométricas": {
        "circulo", "cuadrado", "triangulo", "rectangulo", "estrella", "ovalo", "sol",
        "rombo", "corazon", "hexagono", "pentagono", "octogono", "decagono",
        "esfera", "cilindro", "cubo", "trapecio", "diamante", "cruz", "alb",
        "semicirculo",
    },
    "Animales del mar": {
        "pescado", "ballena", "tortuga", "ostra", "delfin", "tiburon", "pulpo",
        "medusa", "cangrejo", "pez", "orca", "manati", "pargo", "morrocoy",
    },
    "Juguetes": {
        "pelota", "bloques", "carrito", "carritos", "muneca", "casa", "castillo",
        "robot", "tambor", "trompo", "patineta", "bate", "futbol", "osito", "unicornio",
        "varita", "set", "cometa", "pala", "bikini", "globo",
    },
    "Medios de transporte": {
        "avion", "barco", "bicicleta", "camion", "carro", "cohete", "tren", "taxi",
        "autobus", "submarino", "helicoptero", "monopatin", "moto",
    },
    "Números": {
        "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
        "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieciseis",
        "diecisiete", "dieciocho", "diecinueve", "veinte", "veinticinco", "veintisiete",
        "veintitres", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta",
        "ochenta", "noventa", "cien", "suma",
    },
    "Animales voladores": {
        "colibri", "urraca", "mariposa", "pajaro", "aguila", "buitre", "ovni",
        "loro", "guacamaya", "buho", "garza", "perico", "turpial", "zamuro",
        "nandu", "andu",
    },
    "Partes del cuerpo humano": {
        "pie", "pies", "mano", "manos", "cabeza", "ojo", "nariz", "boca", "oreja",
        "pelo", "unas", "uñas", "uas", "pua", "champu", "maniqui", "brazo",
        "dientes", "pierna",
    },
    "En la cocina": {
        "cuchara", "olla", "cocina", "sal", "ajo", "cebolla", "tomate", "berenjena",
        "brocoli", "calabaza", "pimenton", "pimiento", "espinaca", "coliflor", "auyama",
        "cambur", "aguacate", "cerezas", "coco", "durazno", "fresas", "patilla", "pera",
        "pina", "platamo", "uvas", "uva", "zanahoria", "tapa", "sopa", "espaguiti",
        "aji_rojo", "aji_verde", "aji", "kiwi", "lechuga", "limon", "mango", "manzana",
        "melocoton", "melon", "maiz", "masa", "naranja",
    },
    "En la escuela": {
        "escuela", "lapiz", "libro", "examen", "escalera", "escoba", "espejo",
        "pizarra", "mesa", "silla", "mochila", "oficina", "lupa", "mapa", "idea",
    },
}


def normalizar_categoria(cat):
    """Para comparar categorías (p. ej. al filtrar)."""
    if not cat:
        return ""
    return (cat or "").strip().lower()


def _normalizar_primera_palabra(texto):
    """Extrae la primera palabra y deja solo letras (para emparejar con nombres de archivo)."""
    if not texto:
        return ""
    primera = (texto.split() or [""])[0].strip().lower()
    return "".join(c for c in primera if c.isalpha() or c in "áéíóúñü")


# Esdrújulas y palabras con tilde obligatoria (léxico escolar + genéricos de la app).
# Formas sin tilde (p. ej. nombres de archivo) -> forma correcta para UI y TTS.
# PALABRAS_DISPLAY_ES_BASE tiene prioridad al fusionar (evita pisar casos ya definidos).
_PALABRAS_ESDRUJULAS_Y_ACENTO = {
    # App / archivos frecuentes
    "manati": "manatí",
    "maniqui": "maniquí",
    "champu": "champú",
    # Números (acento en la sílaba fuerte)
    "dieciseis": "dieciséis",
    "veintitres": "veintitrés",
    # Esdrújulas y palabras con tilde muy frecuentes
    "musica": "música",
    "musicas": "músicas",
    "publico": "público",
    "publica": "pública",
    "publicos": "públicos",
    "publicas": "públicas",
    "ultimo": "último",
    "ultima": "última",
    "ultimos": "últimos",
    "ultimas": "últimas",
    "pagina": "página",
    "paginas": "páginas",
    "telefono": "teléfono",
    "telefonos": "teléfonos",
    "rapido": "rápido",
    "rapida": "rápida",
    "rapidos": "rápidos",
    "rapidas": "rápidas",
    "facil": "fácil",
    "faciles": "fáciles",
    "dificil": "difícil",
    "dificiles": "difíciles",
    "lagrima": "lágrima",
    "lagrimas": "lágrimas",
    "cancer": "cáncer",
    "carcel": "cárcel",
    "codigo": "código",
    "codigos": "códigos",
    "epoca": "época",
    "epocas": "épocas",
    "ejercito": "ejército",
    "heroe": "héroe",
    "heroes": "héroes",
    "heroina": "heroína",
    "idolo": "ídolo",
    "idolos": "ídolos",
    "indice": "índice",
    "indices": "índices",
    "intimo": "íntimo",
    "intima": "íntima",
    "limite": "límite",
    "limites": "límites",
    "maquina": "máquina",
    "maquinas": "máquinas",
    "martir": "mártir",
    "mascara": "máscara",
    "mascaras": "máscaras",
    "medico": "médico",
    "medica": "médica",
    "medicos": "médicos",
    "medicas": "médicas",
    "musculo": "músculo",
    "numeros": "números",
    "optico": "óptico",
    "optica": "óptica",
    "opticos": "ópticos",
    "opticas": "ópticas",
    "organo": "órgano",
    "organos": "órganos",
    "ovalo": "óvalo",
    "parrafo": "párrafo",
    "parrafos": "párrafos",
    "pendulo": "péndulo",
    "perdida": "pérdida",
    "perdidas": "pérdidas",
    "petalo": "pétalo",
    "petalos": "pétalos",
    "practica": "práctica",
    "practicas": "prácticas",
    "proximo": "próximo",
    "proxima": "próxima",
    "proximos": "próximos",
    "proximas": "próximas",
    "quimico": "químico",
    "quimica": "química",
    "quimicos": "químicos",
    "quimicas": "químicas",
    "record": "récord",
    "records": "récords",
    "regimen": "régimen",
    "regimenes": "regímenes",
    "ritmico": "rítmico",
    "ritmica": "rítmica",
    "sabado": "sábado",
    "sabados": "sábados",
    "sabana": "sábana",
    "sabanas": "sábanas",
    "septimo": "séptimo",
    "septima": "séptima",
    "silaba": "sílaba",
    "silabas": "sílabas",
    "simbolo": "símbolo",
    "simbolos": "símbolos",
    "subito": "súbito",
    "subita": "súbita",
    "tactica": "táctica",
    "tacticas": "tácticas",
    "teorico": "teórico",
    "teorica": "teórica",
    "termino": "término",
    "terminos": "términos",
    "timido": "tímido",
    "timida": "tímida",
    "titulo": "título",
    "titulos": "títulos",
    "toxico": "tóxico",
    "toxica": "tóxica",
    "trafico": "tráfico",
    "tragico": "trágico",
    "tragica": "trágica",
    "transito": "tránsito",
    "tripode": "trípode",
    "tunel": "túnel",
    "tuneles": "túneles",
    "ulcera": "úlcera",
    "ulceras": "úlceras",
    "unico": "único",
    "unica": "única",
    "unicos": "únicos",
    "unicas": "únicas",
    "utero": "útero",
    "uteros": "úteros",
    "util": "útil",
    "utiles": "útiles",
    "video": "vídeo",
    "videos": "vídeos",
    "anatomia": "anatomía",
    "biologia": "biología",
    "ecologia": "ecología",
    "geografia": "geografía",
    "matematica": "matemática",
    "matematicas": "matemáticas",
    "gramatica": "gramática",
    "dramatico": "dramático",
    "dramatica": "dramática",
    "atomico": "atómico",
    "atomica": "atómica",
    "economico": "económico",
    "economica": "económica",
    "electronico": "electrónico",
    "electronica": "electrónica",
    "plastico": "plástico",
    "plastica": "plástica",
    "magico": "mágico",
    "magica": "mágica",
    "metalico": "metálico",
    "metalica": "metálica",
    "numerico": "numérico",
    "numerica": "numérica",
    "guia": "guía",
    "guias": "guías",
    "marron": "marrón",
    "futbol": "fútbol",
    "bikini": "bikini",
    "patin": "patín",
    "patineta": "patineta",
    "monopatin": "monopatín",
    "helicoptero": "helicóptero",
    "autobus": "autobús",
    "camion": "camión",
    "mochila": "mochila",
    "pizarra": "pizarra",
    "lamina": "lámina",
    "laminas": "láminas",
    "regla": "regla",
    "cuaderno": "cuaderno",
    "diccionario": "diccionario",
    "biblioteca": "biblioteca",
    "periodico": "periódico",
    "periodica": "periódica",
    "caracter": "carácter",
    "caracteres": "caracteres",
    "algebra": "álgebra",
    "area": "área",
    "areas": "áreas",
    "atomo": "átomo",
    "atomos": "átomos",
    "bacteria": "bacteria",
    "bacterias": "bacterias",
    "quimica": "química",
    "fisica": "física",
    "fisico": "físico",
    "quimico": "químico",
    "grafico": "gráfico",
    "grafica": "gráfica",
    "graficos": "gráficos",
    "graficas": "gráficas",
    "especimen": "espécimen",
    "especimenes": "especímenes",
    "hipotesis": "hipótesis",
    "analisis": "análisis",
    "crisis": "crisis",
    "tesis": "tesis",
    "dosis": "dosis",
    "apice": "ápice",
    "volumen": "volumen",
    "album": "álbum",
    "albumes": "álbumes",
    "angel": "ángel",
    "angeles": "ángeles",
    "hormigon": "hormigón",
    "melon": "melón",
    "jabon": "jabón",
    "ladron": "ladrón",
    "ladrones": "ladrones",
}

# Palabras que en archivos/DB pueden venir sin acento o sin ñ; karaoke y prioridad sobre el léxico amplio.
PALABRAS_DISPLAY_ES_BASE = {
    "muneca": "muñeca",
    "munecas": "muñecas",
    "melon": "melón",
    "arbol": "árbol",
    "lapiz": "lápiz",
    "mama": "mamá",
    "papa": "papá",
    "aji": "ají",
    "aji_rojo": "ají rojo",
    "aji_verde": "ají verde",
    "numero": "número",
    "dia": "día",
    "corazon": "corazón",
    "tambor": "tambor",
    "circulo": "círculo",
    "triangulo": "triángulo",
    "rectangulo": "rectángulo",
    "pentagono": "pentágono",
    "hexagono": "hexágono",
    "octogono": "octógono",
    "decagono": "decágono",
    "semicirculo": "semicírculo",
    "examen": "examen",
    "escalera": "escalera",
    "escuela": "escuela",
    "espejo": "espejo",
    "cebolla": "cebolla",
    "limon": "limón",
    "naranja": "naranja",
    "pimiento": "pimiento",
    "pimenton": "pimentón",
    "brocoli": "brócoli",
    "coliflor": "coliflor",
    "espinaca": "espinaca",
    "berenjena": "berenjena",
    "calabaza": "calabaza",
    "zanahoria": "zanahoria",
    "aguacate": "aguacate",
    "manzana": "manzana",
    "pera": "pera",
    "cerezas": "cerezas",
    "durazno": "durazno",
    "fresas": "fresas",
    "melocoton": "melocotón",
    "pina": "piña",
    "uva": "uva",
    "uvas": "uvas",
    "coco": "coco",
    "kiwi": "kiwi",
    "mango": "mango",
    "lechuga": "lechuga",
    "tomate": "tomate",
    "sopa": "sopa",
    "olla": "olla",
    "cuchara": "cuchara",
    "cocina": "cocina",
    "mesa": "mesa",
    "silla": "silla",
    "libro": "libro",
    "lupa": "lupa",
    "mapa": "mapa",
    "idea": "idea",
    "cabeza": "cabeza",
    "nariz": "nariz",
    "boca": "boca",
    "oreja": "oreja",
    "ojo": "ojo",
    "pie": "pie",
    "pies": "pies",
    "mano": "mano",
    "manos": "manos",
    "pierna": "pierna",
    "brazo": "brazo",
    "dientes": "dientes",
    "pelo": "pelo",
    "uñas": "uñas",
    "unas": "uñas",
    # Animales / naturaleza (archivos suelen ir sin tilde)
    "colibri": "colibrí",
    "delfin": "delfín",
    "tiburon": "tiburón",
    "pajaro": "pájaro",
    "aguila": "águila",
    "buitre": "buitre",
    "buho": "búho",
    "nandu": "ñandú",
    "andu": "ñandú",
    # Transporte / otros
    "avion": "avión",
    "helicoptero": "helicóptero",
    "autobus": "autobús",
    "monopatin": "monopatín",
    # Familia (variantes sin tilde)
    "tia": "tía",
    "tio": "tío",
}

PALABRAS_DISPLAY_ES = {**_PALABRAS_ESDRUJULAS_Y_ACENTO, **PALABRAS_DISPLAY_ES_BASE}


def texto_para_tts(texto):
    """
    Normaliza ortografía para síntesis de voz (gTTS): tildes y ñ según PALABRAS_DISPLAY_ES.
    Las palabras suelen llegar sin acento (p. ej. nombres de archivo: colibri, mama).
    """
    if texto is None:
        return ""
    t = unicodedata.normalize("NFC", str(texto).strip())
    if not t:
        return ""
    t_lower = t.lower()
    if t_lower in PALABRAS_DISPLAY_ES:
        return PALABRAS_DISPLAY_ES[t_lower]
    if " " in t:
        return " ".join(palabra_para_display(w) for w in t.split())
    return palabra_para_display(t)


def palabra_para_display(palabra):
    """Devuelve la forma correcta para mostrar (p. ej. muñeca en lugar de muneca)."""
    if not palabra or not (palabra or "").strip():
        return (palabra or "").strip()
    raw = unicodedata.normalize("NFC", (palabra or "").strip())
    k = raw.lower()
    return PALABRAS_DISPLAY_ES.get(k, raw)


def categoria_para_palabra_generica(palabra_del_archivo):
    """Dada la palabra derivada del nombre de archivo (ej. 'ABUELA' o 'ABUELA MARGARITA'), devuelve la categoría o None."""
    primera = _normalizar_primera_palabra(palabra_del_archivo or "")
    if not primera:
        return None
    for cat, palabras in GENERICOS_PALABRAS_POR_CATEGORIA.items():
        if primera in palabras:
            return cat
    return None


def nombre_para_album_y_tts(palabra):
    """
    Nombre a mostrar y reproducir en el álbum (karaoke, TTS, armar sílabas).
    P. ej. "COLOR NARANJA" / "COLORNARANJA" -> "NARANJA" (solo el color, no "color naranja").
    """
    if not palabra or not (palabra or "").strip():
        return (palabra or "").strip()
    p = (palabra or "").strip().upper()
    sin_espacios = p.replace(" ", "")
    if sin_espacios == "COLORNARANJA" or (p.startswith("COLOR") and "NARANJA" in p):
        return "NARANJA"
    raw = (palabra or "").strip()
    return palabra_para_display(raw) or raw
