"""
Categorías fijas del álbum. Se usan en la gestión (padres) y en la vista del niño.
Palabras clave para asignar imágenes de assets/genericos a cada categoría (por la primera palabra del nombre de archivo).
La misma palabra puede figurar en varias categorías; el álbum lista genéricos por categoría con generico_pertenece_a_categoria.
"""

import os
import unicodedata

CATEGORIAS_ALBUM = [
    "Familia",
    "Colores",
    "Figuras geométricas",
    "Animales del mar",
    "Animales del bosque",
    "Juguetes",
    "Medios de transporte",
    "Números",
    "Animales voladores",
    "Sonidos especiales A",
    "Sonidos especiales B",
    "Partes del cuerpo",
    "En la cocina",
    "En el baño",
    "En la escuela",
    "Profesiones",
    "En la construcción",
    "Oficios",
    "Deportes",
    "Insectos",
    "En el espacio",
    "Sistema Solar",
    "Zodiaco",
    "En las Olimpiadas",
    "Alimentos",
    "En el zoológico",
    "Dinosaurios",
    "Instrumentos musicales",
]

# Portadas de la cuadrícula del álbum (vista clásica): carpeta assets/album_categorias/
# Nombre por defecto: slug de la categoría + .jpg (p. ej. familia.jpg, en_el_bano.jpg).
PORTADA_ALBUM_OVERRIDE = {
    "Colores": "colores_2.jpg",
    "Sonidos especiales A": "sonidos_especiales_A-M.jpg",
    "Sonidos especiales B": "sonidos_especiales_N-Z.jpg",
    "Zodiaco": "zodiaco.jpg",
}

# Álbum: categorías con audio adicional en assets/sfx/<categoria_slug>/Sonido_*.mp3
CATEGORIAS_SONIDOS_ESPECIALES = frozenset({"Sonidos especiales A", "Sonidos especiales B"})
CATEGORIAS_CON_SFX_TARJETA = frozenset(set(CATEGORIAS_SONIDOS_ESPECIALES) | {"Instrumentos musicales"})


def _slug_archivo_portada_album(categoria: str) -> str:
    """Genera nombre de archivo tipo familia.jpg, figuras_geometricas.jpg."""
    t = unicodedata.normalize("NFKD", (categoria or "").strip())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    buf = []
    for ch in t:
        if ch.isalnum():
            buf.append(ch)
        elif ch.isspace() or ch in "_-":
            buf.append("_")
    s = "".join(buf)
    while "__" in s:
        s = s.replace("__", "_")
    s = s.strip("_")
    return f"{s}.jpg" if s else ""


def nombre_archivo_portada_album(categoria: str) -> str:
    """Nombre de archivo en assets/album_categorias/ (sin ruta)."""
    if categoria in PORTADA_ALBUM_OVERRIDE:
        return PORTADA_ALBUM_OVERRIDE[categoria]
    return _slug_archivo_portada_album(categoria)


def ruta_portada_album_categoria(categoria: str, base_dir: str) -> str | None:
    """Ruta absoluta a la imagen de portada si existe (.jpg/.jpeg/.png/.webp)."""
    if not categoria or not base_dir:
        return None
    name = nombre_archivo_portada_album(categoria)
    if not name:
        return None
    candidates = [name]
    stem, ext = os.path.splitext(name)
    if ext:
        for alt in (".jpeg", ".png", ".webp"):
            if alt != ext:
                candidates.append(stem + alt)
    else:
        for alt in (".jpg", ".jpeg", ".png", ".webp"):
            candidates.append(name + alt)
    gen_dir = os.path.join(os.path.dirname(os.path.normpath(base_dir)), "genericos")
    # Zodiaco: priorizar assets/genericos/zodiaco.jpg (portada oficial), no una copia antigua en album_categorias
    search_dirs = [gen_dir, base_dir] if (categoria or "").strip() == "Zodiaco" else [base_dir]
    for d in search_dirs:
        for fn in candidates:
            p = os.path.join(d, fn)
            if os.path.isfile(p):
                return p
    return None


# Léxico por categoría (primera palabra del nombre de archivo, normalizada a minúsculas sin puntuación).
# Una misma palabra puede repetirse en varias categorías.
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
        "colores", "rosa", "rubi",
    },
    "Figuras geométricas": {
        "circulo", "cuadrado", "triangulo", "rectangulo", "ovalo",
        "rombo", "hexagono", "pentagono", "octogono", "decagono",
        "esfera", "cilindro", "cubo", "trapecio", "diamante", "cruz", "alb",
        "semicirculo",
    },
    "Animales del mar": {
        "pescado", "ballena", "tortuga", "ostra", "delfin", "tiburon", "pulpo",
        "medusa", "cangrejo", "pez", "orca", "manati", "pargo", "morrocoy",
        "foca", "isla",
    },
    "Animales del bosque": {
        "oso", "lobo", "zorro", "ardilla", "venado", "ciervo", "jabali", "mapache",
        "tejon", "erizo", "lince", "comadreja", "corzo", "gamo", "nutria", "turon",
        "jabalina", "conejo", "leon", "tigre", "puma", "rinoceronte", "hipopotamo",
        "hipopoytamo", "elefante", "elefanta",
        "araguaney", "campo", "fogata", "gato", "halcon", "hoja", "iguana", "invierno",
        "koala", "lagartija", "lagarto", "lechuza", "leopardo", "lombriz", "mono",
        "nieve", "oveja", "pino", "raiz", "rio",
        "saman", "sapo", "selva", "vaca", "yegua", "zebra", "ñu", "ñandu",
    },
    "Juguetes": {
        "pelota", "bloques", "carrito", "carritos", "muneca", "casa", "castillo",
        "robot", "tambor", "trompo", "patineta", "bate", "futbol", "osito", "unicornio",
        "varita", "set", "cometa", "pala", "bikini", "globo",
        "dardo", "ula", "yoyo",
    },
    "Medios de transporte": {
        "avion", "barco", "bicicleta", "camion", "carro", "cohete", "tren", "taxi",
        "autobus", "submarino", "helicoptero", "monopatin", "moto",
        "avioneta", "kayak", "lancha", "metro", "tranvia", "transbordador", "tractor",
        "velero", "yate", "cuatrimoto", "ambulancia", "teleferico", "canoa", "motociclista",
        "auto",
    },
    "Números": {
        "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
        "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieciseis",
        "diecisiete", "dieciocho", "diecinueve", "veinte", "veinticinco", "veintisiete",
        "veintitres", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta",
        "ochenta", "noventa", "cien", "suma",
    },
    "Animales voladores": {
        "colibri", "urraca", "mariposa", "mariposas", "pajaro", "aguila", "buitre", "ovni",
        "loro", "guacamaya", "buho", "garza", "perico", "turpial", "zamuro",
        "nandu", "andu",
        "cocuyos", "coquito", "halcon", "lechuza", "nido", "zancudo",
        "ñandu",
    },
    "Sonidos especiales A": {
        "ambulancia", "aplausos", "auto", "avion", "barco", "buho", "canario", "cerdo",
        "chivo", "delfin", "gallina", "gallo", "gato", "gorila", "grillo", "lancha",
        "leon", "licuadora",
    },
    "Sonidos especiales B": {
        "lluvia", "lobo", "loro", "metro", "mono", "moto", "oveja", "pato", "perro",
        "policia", "reloj", "rio", "sapo", "telefono", "tigre", "tren", "trueno", "vaca",
    },
    "Partes del cuerpo": {
        "pie", "pies", "mano", "manos", "cabeza", "ojo", "nariz", "boca", "oreja",
        "pelo", "unas", "uñas", "uas", "pua", "maniqui", "brazo",
        "dientes", "diente", "pierna",
        "pulmones", "pulmon", "corazon", "higado", "rinon", "rinones", "riñones",
        "dedo", "esqueleto", "lengua",
        "estomago",
        "intestinos", "cerebro", "vesicula", "bazo", "pancreas", "sangre", "musculo",
        "tendon", "cuello", "espalda", "hombro", "rodilla", "tobillo", "codo",
    },
    "En la cocina": {
        "cuchara", "olla", "cocina", "sal", "ajo", "cebolla", "tomate", "berenjena",
        "brocoli", "calabaza", "pimenton", "pimiento", "espinaca", "coliflor", "auyama",
        "cambur", "aguacate", "cerezas", "coco", "durazno", "fresas", "patilla", "pera",
        "pina", "platamo", "uvas", "uva", "zanahoria", "tapa", "sopa", "espaguiti",
        "aji_rojo", "aji_verde", "aji", "kiwi", "lechuga", "limon", "mango", "manzana",
        "melocoton", "melon", "maiz", "masa", "naranja",
        "copa", "cafe", "ducha", "hielo", "huevo", "humo", "ketchup", "lenteja", "nata",
        "radio", "refrigerador", "safa", "zumo", "ñoqui",
    },
    "En el baño": {
        "champu",
        "agua", "cepillo", "toalla", "cholas", "jabon", "peine", "crema",
        "banera", "bañera", "ducha", "diente", "dientes",
    },
    "En la escuela": {
        "escuela", "lapiz", "libro", "examen", "escalera", "escoba", "espejo",
        "pizarra", "mesa", "silla", "mochila", "oficina", "lupa", "mapa", "idea",
        "bolso", "colores", "compas", "cuaderno", "cuadernos", "iman", "kilogramo",
        "kinder", "lentes", "libros", "regla", "reloj",
    },
    "Profesiones": {
        "doctor", "doctora", "enfermera", "enfermero", "maestro", "maestra", "policia",
        "bombero", "cocinero", "piloto", "astronauta", "veterinario", "dentista", "abogado",
        "arquitecto", "cientifico", "artista", "cantante", "escritor", "periodista",
        "fotografo", "ingeniero", "juez", "musico", "bibliotecario", "granjero",
        "veterinaria", "enfermeria",
        "abogada", "administrador", "administradora", "aviador", "bombera", "camionero",
        "cocinera", "diseñadora", "disenadora", "florista", "ingeniera", "jardinero",
        "jueza", "medica", "medico", "mesonero", "pastelera", "pastelero", "pediatra",
        "programador", "programadora", "psicologa", "taxista",
        "soldado", "soldada", "repartidor", "modelo", "pilotodecarreras",
        "jinete",
    },
    "En la construcción": {
        "obra", "ladrillo", "cemento", "grua", "excavadora", "andamio", "mezcladora",
        "hormigon", "demolicion", "casco", "martillo", "taladro", "albanil", "albañil",
        "yeso", "tubo", "andamiaje", "perno", "arena", "grava", "mezcla", "soldadura",
        "clavo", "clavos", "tornillo", "tuerca", "serrucho", "destornillador", "tablon",
        "madera", "ladrillos",
        "pala", "pico", "camion", "carretilla", "rodillo", "volquete", "carreta",
        "retroexcavadora", "topadora", "compactadora", "cincel", "piqueta", "nivel",
        "cinta", "cal", "cantera",
        "farol", "fuente", "hacha", "iglu", "regla", "reja", "roca", "rueda", "yunque",
    },
    "Oficios": {
        "carpintero", "electricista", "fontanero", "pintor", "mecanico", "sastre",
        "barbero", "peluquero", "panadero", "carnicero", "zapatero", "herrero",
        "cerrajero", "alfarero", "modista", "costurera", "costurero", "soldador", "cerrajeria",
        "hojalatero", "vidriero",
        "plomero", "peluquera",
        "policias", "bomberos", "soldados", "secretaria", "secretario", "maestros", "maestras",
        "quiosquero", "oftalmologo", "orfebre", "artesano", "escultor", "escultora",
        "lentes", "mimo",
    },
    "Deportes": {
        "deporte", "deportes", "baloncesto", "basquet", "basket", "tenis", "beisbol",
        "voleibol", "natacion", "atletismo", "boxeo", "karate", "yoga", "rugby",
        "hockey", "esqui", "surf", "ciclismo", "golf", "gimnasia", "medalla", "trofeo",
        "nadador", "nadadora", "corredor", "portero", "arbitro", "estadio", "remo",
        "lucha", "esgrima", "patinaje", "skate", "skater", "vela", "buceo", "gimnasio",
        "danza", "dardo", "jinete", "kimono", "nudo", "raqueta", "ula", "vestido", "zapato",
    },
    "Insectos": {
        "hormiga", "hormigas", "abeja", "avispa", "mosca", "mosquito", "cucaracha", "grillo",
        "saltamontes", "escarabajo", "libelula", "libelulas", "gusano", "oruga", "termita", "mantis",
        "chinche", "pulga", "arana", "araña", "ciempies", "luciernaga", "luciernagas", "abejorro",
        "tijereta", "cochinilla", "pulgon", "insecto", "insectos", "mariquita",
        "cocuyos", "coquito", "lagartija", "lombriz", "sapo", "zancudo",
        "xilofago", "xilofagp",
    },
    "En el espacio": {
        "galaxia", "nebulosa", "asteroide", "satelite", "orbita",
        "universo", "espacio", "estacion", "nave", "modulo", "telescopio", "eclipse", "meteoro",
        "constelacion", "cuasar", "gravedad", "cosmos",
        "estrella",
        "astronauta", "astronautas", "cohete", "cohetes", "transbordador", "transbordadores",
        "sonda", "sondas", "meteorito", "meteoritos", "capsula", "capsulas", "alunizaje",
        "ovni", "cometa", "agujeronegro", "vialactea", "via",
        "supernova", "pulsar", "aurora",
        "nube", "nubes", "rayo", "relampago",
    },
    "Sistema Solar": {
        "planeta",
        "mercurio",
        "venus",
        "tierra",
        "marte",
        "jupiter",
        "saturno",
        "urano",
        "neptuno",
        "pluton",
        "luna",
        "sol",
    },
    "Zodiaco": {
        "aries",
        "tauro",
        "geminis",
        "cancer",
        "leo",
        "virgo",
        "libra",
        "escorpio",
        "sagitario",
        "capricornio",
        "acuario",
        "piscis",
    },
    "En las Olimpiadas": {
        "olimpiada", "olimpiadas", "antorcha", "podio", "anillas", "barras", "relevo", "relevos",
        "lanzamiento", "maraton", "salto", "balonmano", "softbol", "equitacion", "nado",
        "pentatlon", "vallas", "judo", "yudo", "halterofilia", "tiro", "arco",
        "badminton", "waterpolo", "paralimpico", "paralimpicos", "mascota", "ceremonia",
        "natacion", "ciclismo", "beisbol", "baloncesto", "tenis", "voleibol", "gimnasia",
        "atletismo", "boxeo", "remo", "triatlon", "esgrima", "taekwondo", "karate", "rugby",
        "hockey", "golf", "futbol", "futbolista", "esqui", "surf", "skate", "patinaje",
        "levantamiento", "medalla", "trofeo",
        "raqueta",
    },
    "Alimentos": {
        "alimento", "alimentos", "comida", "merienda", "pan", "galleta", "cereal",
        "pasta", "arroz", "fideos", "pizza", "hamburguesa", "sandwich", "queso",
        "leche", "yogurt", "mantequilla", "miel", "azucar", "aceite", "embutido",
        "salchicha", "chorizo", "jamon", "lacteos", "helado", "chocolate", "dulce",
        "harina", "snack", "palomitas", "caramelos", "galletas", "salsa", "mermelada",
        "cafe", "dona", "hielo", "huevo", "ketchup", "lenteja", "nabo", "nata", "yuca",
        "zumo", "ñapa", "ñoqui",
    },
    "En el zoológico": {
        "zoo", "zoologico", "jaula", "exhibicion", "cuidador", "safari",
        "vivero", "reptilario", "aviario", "mamiferos", "reptiles", "felinos",
        "habitat", "cercado", "recorrido", "visitante",
        "rinoceronte", "rinocetonte",
        "foca", "iguana", "koala", "lagarto", "leopardo", "mono", "oveja", "selva",
        "vaca", "yegua", "zebra", "ñandu", "ñu",
    },
    "Dinosaurios": {
        "velociraptor", "velociraptores", "caiman", "cocodrilo", "iguana",
        "diplodocus", "tyrannosaurus", "giganotosaurus", "iguanodon",
        "tiranosaurio", "braquiosaurio", "triceratops", "estegosaurio", "pterodactilo",
    },
    "Instrumentos musicales": {
        "violin", "viola", "violonchelo", "violon", "contrabajo", "bajo", "chelo", "cello",
        "guitarra", "guitarraelectrica", "piano", "teclado", "organillo", "organo",
        "flauta", "flautin", "trompeta", "trombon", "trompa", "tuba", "corneta",
        "bateria", "bombo", "redoblante", "tambor", "timbales", "platillo", "cencerro",
        "arpa", "acordeon", "bandoneon", "armonica", "oboe", "fagot", "clarinete",
        "saxofon", "saxo", "ukelele", "ukulele", "charango", "banjo", "mandolina",
        "xilofono", "metalofono", "maracas", "castañuelas", "bongo", "congas",
        "guiro", "pandero", "djembe", "gong", "platillos", "timbal",
        "cuatrovenezolano", "furruco", "bandola", "nota", "notas", "coral",
    },
}


def normalizar_categoria(cat):
    """Para comparar categorías (p. ej. al filtrar)."""
    if not cat:
        return ""
    return (cat or "").strip().lower()


def fila_album_coincide_categoria(categoria_fila, categoria_seleccionada, palabra_clave=None):
    """True si una fila de album_personal pertenece a la categoría elegida en la UI (incluye alias legados)."""
    s = (categoria_fila or "").strip()
    t = (categoria_seleccionada or "").strip()
    if s == t:
        return True
    if t == "Partes del cuerpo" and s == "Partes del cuerpo humano":
        return True
    if s == "Sonidos especiales" and t in CATEGORIAS_SONIDOS_ESPECIALES and palabra_clave:
        palabras_t = GENERICOS_PALABRAS_POR_CATEGORIA.get(t)
        if not palabras_t:
            return False
        primera = _normalizar_primera_palabra(palabra_clave)
        return bool(primera and primera in palabras_t)
    return False


def _normalizar_primera_palabra(texto):
    """Extrae la primera palabra y deja solo letras (para emparejar con nombres de archivo)."""
    if not texto:
        return ""
    primera = (texto.split() or [""])[0].strip().lower()
    return "".join(c for c in primera if c.isalpha() or c in "áéíóúñü")


def _es_estrella_de_mar(palabra_del_archivo):
    """
    True si el nombre indica estrella de mar (animal), p. ej. estrella_de_mar, estrella de mar.
    No aplica a la palabra suelta 'estrella' (astro / constelación).
    """
    if not palabra_del_archivo:
        return False
    t = (palabra_del_archivo or "").lower().replace("_", " ").replace("-", " ")
    parts = [p.strip(".,;") for p in t.split() if p.strip()]
    if "estrella" not in parts:
        return False
    return "mar" in parts


def _es_huevo_de_dinosaurio(palabra_del_archivo):
    """True si el nombre indica huevo de dinosaurio (no el 'huevo' genérico)."""
    if not palabra_del_archivo:
        return False
    t = (palabra_del_archivo or "").lower().replace("_", " ").replace("-", " ")
    parts = [p.strip(".,;") for p in t.split() if p.strip()]
    return "huevo" in parts and "dinosaurio" in parts


def _es_esqueleto_de_dinosaurio(palabra_del_archivo):
    """True si el nombre indica esqueleto de dinosaurio (no el 'esqueleto' genérico)."""
    if not palabra_del_archivo:
        return False
    t = (palabra_del_archivo or "").lower().replace("_", " ").replace("-", " ")
    parts = [p.strip(".,;") for p in t.split() if p.strip()]
    return "esqueleto" in parts and "dinosaurio" in parts


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
    "cancer": "Cáncer",
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
    # Instrumentos (nombre de archivo en una sola palabra)
    "cuatrovenezolano": "cuatro venezolano",
    # Signos del zodiaco (nombres de archivo sin tilde)
    "aries": "Aries",
    "tauro": "Tauro",
    "geminis": "Géminis",
    "leo": "Leo",
    "virgo": "Virgo",
    "libra": "Libra",
    "escorpio": "Escorpio",
    "sagitario": "Sagitario",
    "capricornio": "Capricornio",
    "acuario": "Acuario",
    "piscis": "Piscis",
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


def generico_pertenece_a_categoria(palabra_del_archivo, categoria):
    """
    True si la primera palabra del nombre de archivo está en el léxico de esa categoría.
    Una misma palabra puede estar en varias categorías; el álbum usa esto por categoría.
    """
    if not categoria:
        return False
    es_edm = _es_estrella_de_mar(palabra_del_archivo)
    if es_edm:
        if categoria == "Animales del mar":
            return True
        if categoria == "En el espacio":
            return False
    if categoria == "Dinosaurios":
        if _es_huevo_de_dinosaurio(palabra_del_archivo) or _es_esqueleto_de_dinosaurio(palabra_del_archivo):
            return True
    palabras = GENERICOS_PALABRAS_POR_CATEGORIA.get(categoria)
    if not palabras:
        return False
    primera = _normalizar_primera_palabra(palabra_del_archivo or "")
    return bool(primera and primera in palabras)


def categoria_para_palabra_generica(palabra_del_archivo):
    """
    Primera categoría (orden del diccionario) cuyo léxico contiene la primera palabra del archivo.
    Si la palabra está en varias categorías, solo devuelve una; para listar por categoría usar generico_pertenece_a_categoria.
    """
    if _es_estrella_de_mar(palabra_del_archivo):
        return "Animales del mar"
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
