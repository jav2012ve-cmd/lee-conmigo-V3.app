import os
from database.db_queries import obtener_album_nino
from core.album_categories import CATEGORIAS_ALBUM, generico_pertenece_a_categoria, palabra_para_display

# Raíz del proyecto (carpeta que contiene core/, assets/, etc.)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AssetManager:
    # Rutas base para activos genéricos (relativas para compatibilidad)
    PATH_GENERICOS = "assets/genericos/"
    # Nombres de archivo (sin extensión, minúsculas) que no deben listarse como genéricos
    _GENERICOS_EXCLUIDOS_STEM = frozenset({"tambor_2"})
    # Ruta absoluta a fondos del abecedario para que se detecten aunque el proceso arranque desde otra carpeta
    PATH_FONDOS_ABECEDARIO = os.path.join(_BASE_DIR, "assets", "genericos", "fondos")
    _cache_genericos = None
    _cache_genericos_size = None
    @staticmethod
    def obtener_fondos_abecedario():
        """
        Lista los fondos disponibles para el abecedario (assets/genericos/fondos/).
        Devuelve lista de {nombre, ruta} con nombre legible (nombre del archivo sin extensión).
        """
        fondos = []
        try:
            ruta_fondos = AssetManager.PATH_FONDOS_ABECEDARIO
            os.makedirs(ruta_fondos, exist_ok=True)
            if not os.path.isdir(ruta_fondos):
                return []
            for name in sorted(os.listdir(ruta_fondos)):
                lower = name.lower()
                if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                    nombre = os.path.splitext(name)[0].replace("_", " ").replace("-", " ").strip()
                    if nombre:
                        nombre_display = nombre.title()
                        if nombre_display.upper().startswith("FONDO "):
                            nombre_display = nombre_display[6:].strip()
                        fondos.append({"nombre": nombre_display, "ruta": os.path.join(ruta_fondos, name)})
        except Exception:
            fondos = []
        return fondos

    @staticmethod
    def _listar_genericos():
        if AssetManager._cache_genericos is not None:
            return AssetManager._cache_genericos

        archivos = []
        try:
            for name in os.listdir(AssetManager.PATH_GENERICOS):
                lower = name.lower()
                if not lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                    continue
                stem, _ = os.path.splitext(lower)
                if stem in AssetManager._GENERICOS_EXCLUIDOS_STEM:
                    continue
                archivos.append(os.path.join(AssetManager.PATH_GENERICOS, name))
        except Exception:
            archivos = []

        AssetManager._cache_genericos = archivos
        return archivos

    @staticmethod
    def obtener_genericos_por_categoria(categoria):
        """
        Devuelve lista de dicts {palabra, ruta_img} de assets/genericos
        cuya primera palabra está en el léxico de esa categoría (puede repetirse en otras categorías).
        """
        if not categoria or categoria not in CATEGORIAS_ALBUM:
            return []
        out = []
        for ruta in AssetManager._listar_genericos():
            palabra = AssetManager._palabra_desde_ruta(ruta)
            if generico_pertenece_a_categoria(palabra, categoria):
                display = palabra_para_display(palabra or os.path.basename(ruta))
                out.append({"palabra": display or palabra or os.path.basename(ruta), "ruta_img": ruta})
        return out

    @staticmethod
    def _palabra_desde_ruta(ruta_img: str) -> str:
        base = os.path.basename(ruta_img)
        base = os.path.splitext(base)[0]
        base = base.replace("_", " ").replace("-", " ")
        return base.strip().upper() if base else ""

    @staticmethod
    def obtener_genericos_por_letra():
        """
        Devuelve dict letra -> lista de {palabra, ruta_img} para abecedario.
        La letra es la primera del nombre (primera palabra del archivo).
        Excluye archivos que no empiecen por una letra (ej. Fondo.png si se considera no-alfabético).
        """
        letras = {}
        for ruta in AssetManager._listar_genericos():
            palabra = AssetManager._palabra_desde_ruta(ruta)
            if not palabra:
                continue
            primera_palabra = (palabra.split() or [""])[0]
            if not primera_palabra or not primera_palabra[0].isalpha():
                continue
            letra = primera_palabra[0].upper()
            display = palabra_para_display(palabra)
            item = {"palabra": display or palabra, "ruta_img": ruta}
            letras.setdefault(letra, []).append(item)
        return letras

    @staticmethod
    def letras_con_imagenes_en_genericos():
        """Conjunto de letras para las que hay al menos una imagen en genericos (para abecedario)."""
        return set(AssetManager.obtener_genericos_por_letra().keys())

    @staticmethod
    def obtener_tamano_promedio_genericos():
        """
        Devuelve un tamaño típico (w, h) de las imágenes en assets/genericos.
        Usa un promedio recortado (10%) para evitar outliers.
        """
        if AssetManager._cache_genericos_size is not None:
            return AssetManager._cache_genericos_size

        try:
            from PIL import Image
        except Exception:
            AssetManager._cache_genericos_size = (235, 249)
            return AssetManager._cache_genericos_size

        sizes = []
        for p in AssetManager._listar_genericos():
            try:
                with Image.open(p) as im:
                    w, h = im.size
                    if w and h:
                        sizes.append((int(w), int(h)))
            except Exception:
                continue

        if not sizes:
            AssetManager._cache_genericos_size = (235, 249)
            return AssetManager._cache_genericos_size

        ws = sorted([w for w, _h in sizes])
        hs = sorted([h for _w, h in sizes])
        k = max(1, int(0.1 * len(ws)))
        ws2 = ws[k:-k] if len(ws) > 2 * k else ws
        hs2 = hs[k:-k] if len(hs) > 2 * k else hs

        avg_w = sum(ws2) / len(ws2)
        avg_h = sum(hs2) / len(hs2)
        AssetManager._cache_genericos_size = (int(round(avg_w)), int(round(avg_h)))
        return AssetManager._cache_genericos_size
    
    @staticmethod
    def obtener_recurso_lectura(estudiante_id, fonema):
        """
        Busca un activo (imagen/palabra) que empiece con el fonema dado.
        Prioriza el álbum personal del niño.
        """
        # 1. Intentar buscar en el álbum personal de la DB
        album = obtener_album_nino(estudiante_id)

        # album debería devolver una lista de tuplas: (palabra_clave, categoria, img_path)
        # Nos protegemos por si la consulta falla y devuelve None o datos inesperados.
        if album:
            for registro in album:
                if not isinstance(registro, (tuple, list)) or len(registro) < 3:
                    continue
                palabra, categoria, img_path = registro
                if isinstance(palabra, str) and palabra.startswith(fonema.upper()):
                    return {
                        "palabra": palabra,
                        "ruta_img": img_path,
                        "origen": "personal"
                    }
        
        # 2. Si no hay nada en el álbum, buscar en la biblioteca genérica
        # Aquí simulamos una búsqueda en la carpeta assets/genericos/
        # En una versión real, esto leería un archivo JSON o una carpeta.
        biblioteca_generica = {
            "A": {"palabra": "AVIÓN", "ruta": "assets/genericos/avion.jpg"},
            "E": {"palabra": "ESTRELLA", "ruta": "assets/genericos/estrella.jpg"},
            "M": {"palabra": "MESA", "ruta": "assets/genericos/mesa.jpg"},
            "P": {"palabra": "PATO", "ruta": "assets/genericos/pato.jpg"},
            "L": {"palabra": "LÁPIZ", "ruta": "assets/genericos/lapiz.jpg"}
        }
        
        recurso = biblioteca_generica.get(fonema.upper())
        if recurso:
            return {
                "palabra": recurso["palabra"],
                "ruta_img": recurso["ruta"],
                "origen": "generico"
            }
        
        return None

    @staticmethod
    def obtener_recursos_lectura(estudiante_id, fonema, total=4):
        """
        Devuelve varios recursos para el mismo fonema (ideal para vocales).
        Prioriza el álbum personal y rellena con biblioteca genérica.
        """
        fonema_u = (fonema or "").upper()
        recursos = []
        vistos = set()

        # 1) Álbum personal
        album = obtener_album_nino(estudiante_id) or []
        for registro in album:
            if not isinstance(registro, (tuple, list)) or len(registro) < 3:
                continue
            palabra, _categoria, img_path = registro
            if not isinstance(palabra, str) or not palabra.startswith(fonema_u):
                continue
            key = str(img_path)
            if key in vistos:
                continue
            vistos.add(key)
            recursos.append({"palabra": palabra, "ruta_img": img_path, "origen": "personal"})
            if len(recursos) >= total:
                return recursos

        # 2) Biblioteca genérica (por nombre de archivo que comience por la letra)
        for ruta in AssetManager._listar_genericos():
            palabra = AssetManager._palabra_desde_ruta(ruta)
            if not palabra.startswith(fonema_u):
                continue
            if ruta in vistos:
                continue
            vistos.add(ruta)
            recursos.append({"palabra": palabra or fonema_u, "ruta_img": ruta, "origen": "generico"})
            if len(recursos) >= total:
                return recursos

        # 3) Fallback mínimo: biblioteca_generica (asegura que vocales no queden vacías)
        # Nota: aquí solo hay 1 ejemplo por letra; sirve para evitar pantalla en blanco.
        if len(recursos) < total:
            biblioteca_generica = {
                "A": {"palabra": "AVIÓN", "ruta": "assets/genericos/avion.jpg"},
                "E": {"palabra": "ESTRELLA", "ruta": "assets/genericos/estrella.jpg"},
                "I": {"palabra": "IGLÚ", "ruta": "assets/genericos/iglu.jpg"},
                "O": {"palabra": "OSO", "ruta": "assets/genericos/oso.jpg"},
                "U": {"palabra": "UVA", "ruta": "assets/genericos/uva.jpg"},
                "M": {"palabra": "MESA", "ruta": "assets/genericos/mesa.jpg"},
                "P": {"palabra": "PATO", "ruta": "assets/genericos/pato.jpg"},
                "L": {"palabra": "LÁPIZ", "ruta": "assets/genericos/lapiz.jpg"},
            }
            rec = biblioteca_generica.get(fonema_u)
            if rec:
                ruta = rec.get("ruta") or ""
                if ruta and ruta not in vistos:
                    vistos.add(ruta)
                    recursos.append({"palabra": rec.get("palabra") or fonema_u, "ruta_img": ruta, "origen": "generico"})

        return recursos

    _NORM_VOCAL = str.maketrans("ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜ", "AEIOUAEIOUAEIOUAEIOU")

    @staticmethod
    def _ultima_letra_normalizada(palabra: str) -> str:
        """Última letra en mayúscula sin acento, para comparar vocales."""
        if not palabra or not isinstance(palabra, str):
            return ""
        return palabra.strip().upper()[-1:].translate(AssetManager._NORM_VOCAL)

    @staticmethod
    def obtener_recursos_que_terminan_en(estudiante_id, vocal, total=4):
        """
        Devuelve recursos cuya palabra termina en la vocal dada (para actividad "terminan con A").
        Prioriza álbum personal y rellena con biblioteca genérica.
        """
        vocal_u = (vocal or "").upper().translate(AssetManager._NORM_VOCAL)
        if vocal_u not in "AEIOU":
            return []
        recursos = []
        vistos = set()

        # 1) Álbum personal
        album = obtener_album_nino(estudiante_id) or []
        for registro in album:
            if not isinstance(registro, (tuple, list)) or len(registro) < 3:
                continue
            palabra, _categoria, img_path = registro
            if not isinstance(palabra, str):
                continue
            if AssetManager._ultima_letra_normalizada(palabra) != vocal_u:
                continue
            key = str(img_path)
            if key in vistos:
                continue
            vistos.add(key)
            recursos.append({"palabra": palabra, "ruta_img": img_path, "origen": "personal"})
            if len(recursos) >= total:
                return recursos

        # 2) Biblioteca genérica (palabra derivada del nombre de archivo termina en vocal)
        for ruta in AssetManager._listar_genericos():
            palabra = AssetManager._palabra_desde_ruta(ruta)
            if not palabra or AssetManager._ultima_letra_normalizada(palabra) != vocal_u:
                continue
            if ruta in vistos:
                continue
            vistos.add(ruta)
            recursos.append({"palabra": palabra or vocal_u, "ruta_img": ruta, "origen": "generico"})
            if len(recursos) >= total:
                return recursos

        return recursos

    @staticmethod
    def verificar_existencia_carpetas(user_id):
        """Asegura que el niño tenga su carpeta local de fotos creada."""
        path_usuario = f"assets/usuarios/{user_id}/fotos_familia"
        if not os.path.exists(path_usuario):
            os.makedirs(path_usuario)
        return path_usuario