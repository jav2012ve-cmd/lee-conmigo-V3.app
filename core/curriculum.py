class Curriculum:
    # Sílabas para lecciones de vocales (matriz 3×3 como consonantes: 5 celdas con sílabas)
    SILABAS_POR_VOCAL = {
        "A": ["A", "La", "Ma", "Na", "Pa"],
        "E": ["E", "Le", "Me", "Ne", "Pe"],
        "I": ["I", "Li", "Mi", "Ni", "Pi"],
        "O": ["O", "Lo", "Mo", "No", "Po"],
        "U": ["U", "Lu", "Mu", "Nu", "Pu"],
    }

    # Frases para "Escucha y toca" cuando no hay plantillas de consonante (p. ej. vocales)
    FRASES_MAGICAS_VOCAL = {
        "A": [
            "Amo a {mama}",
            "{nombre} aprende con alegría",
            "La mamá ama a {nombre}",
        ],
        "E": [
            "El elefante es enorme",
            "{nombre} es excelente",
            "Mamá tiene energía",
        ],
        "I": [
            "El indio vive aquí",
            "{nombre} es increíble",
            "Mi mamá me mima",
        ],
        "O": [
            "El oso come miel",
            "{nombre} es oro puro",
            "Yo amo a {mama}",
        ],
        "U": [
            "La luna es una joya",
            "{nombre} es único",
            "Mamá me da un beso",
        ],
    }

    # Sílabas directas por consonante (para encabezado y lecciones tipo "M")
    SILABAS_POR_CONSONANTE = {
        "M": ["Ma", "Me", "Mi", "Mo", "Mu"],
        "P": ["Pa", "Pe", "Pi", "Po", "Pu"],
        "L": ["La", "Le", "Li", "Lo", "Lu"],
        "S": ["Sa", "Se", "Si", "So", "Su"],
        "N": ["Na", "Ne", "Ni", "No", "Nu"],
        "T": ["Ta", "Te", "Ti", "To", "Tu"],
        "D": ["Da", "De", "Di", "Do", "Du"],
        "R": ["Ra", "Re", "Ri", "Ro", "Ru"],
        "C": ["Ca", "Ce", "Ci", "Co", "Cu"],
    }

    # Plantillas de frases mágicas por letra. {nombre} = nombre del niño; {mama} = "Mamá Norkis" o "mamá"
    FRASES_MAGICAS = {
        "M": [
            "{nombre} ama a mamá",
            "Mi mamá me ama mucho",
            "Amo a mi {mama}",
        ],
    }

    # Definición de la progresión según la Regla de Oro #3
    CICLOS = {
        "Ciclo 1": {
            "nombre": "El Despertar",
            "temas_album": ["Familia"],
            "letras": ["A", "E", "I", "O", "U", "M", "P", "L"],
            "siguiente": "Ciclo 2A"
        },
        "Ciclo 2A": {
            "nombre": "Explosión",
            "temas_album": ["Juguetes", "Comida"],
            "letras": ["S", "N", "T"],
            "siguiente": "Ciclo 2B"
        },
        "Ciclo 2B": {
            "nombre": "Refinamiento",
            "temas_album": ["Cuerpo", "Casa"],
            "letras": ["D", "R", "C"],
            "siguiente": None
        }
    }

    UMBRAL_AVANCE = 0.80  # 80% de aciertos requerido

    @staticmethod
    def obtener_letras_por_ciclo(ciclo_nombre):
        """Devuelve la lista de fonemas a trabajar en un ciclo dado."""
        return Curriculum.CICLOS.get(ciclo_nombre, {}).get("letras", [])

    @staticmethod
    def obtener_temas_album(ciclo_nombre):
        """Devuelve las categorías de fotos que el padre debe subir en este ciclo."""
        return Curriculum.CICLOS.get(ciclo_nombre, {}).get("temas_album", [])

    @staticmethod
    def calcular_maestria(aciertos, errores):
        """Calcula si el estudiante domina un fonema."""
        total = aciertos + errores
        if total == 0:
            return 0.0
        return aciertos / total

    @staticmethod
    def puede_avanzar_de_ciclo(progreso_lecciones):
        """
        Analiza si el 80% de las letras del ciclo actual 
        tienen una maestría superior al UMBRAL_AVANCE.
        """
        if not progreso_lecciones:
            return False
        
        letras_completadas = [l for l in progreso_lecciones if l['completado']]
        total_letras_ciclo = len(progreso_lecciones)
        
        porcentaje_ciclo = len(letras_completadas) / total_letras_ciclo
        return porcentaje_ciclo >= Curriculum.UMBRAL_AVANCE