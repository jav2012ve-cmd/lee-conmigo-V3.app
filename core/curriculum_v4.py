class CurriculumV4:
    """
    Diseño académico 4.0 (misma progresión que V3):
    - Progresión por ciclos: Álbum (categorías) → desbloquea bloque de lecciones → al superar bloque, +1 categoría.
    """

    CATEGORIAS_INICIALES = ["Familia", "Juguetes", "En la cocina"]

    CATEGORIAS_DESBLOQUEO = [
        "Partes del cuerpo",
        "En la escuela",
        "Medios de transporte",
        "Colores",
        "Números",
        "Figuras geométricas",
        "Animales del mar",
        "Animales del bosque",
        "Animales voladores",
        "Profesiones",
        "En la construcción",
        "Oficios",
        "Deportes",
        "Insectos",
        "En el espacio",
        "En las Olimpiadas",
        "Alimentos",
        "En el zoológico",
        "Dinosaurios",
        "Instrumentos musicales",
        "En el baño",
        "Zodiaco",
        "Sistema Solar",
    ]

    CICLOS = [
        {"id": "C1", "bloque": ["A-E-I", "I-O-U", "A-E-I-O-U"]},
        {"id": "C2", "bloque": ["M", "P", "L"]},
        {"id": "C3", "bloque": ["S", "N", "T"]},
        {"id": "C4", "bloque": ["D", "C", "R"]},
        {"id": "C5", "bloque": ["B", "F", "V"]},
        {"id": "C6", "bloque": ["G", "J", "Q"]},
        {"id": "C7", "bloque": ["H", "K", "Y"]},
        {"id": "C8", "bloque": ["Ñ", "Z", "X"]},
        {"id": "C9", "bloque": ["W", "INTEGRACION"]},
        {"id": "C10", "bloque": ["AN", "EN", "IN", "ON", "UN"]},
        {"id": "C11", "bloque": ["AR", "ER", "IR", "OR", "UR"]},
        {"id": "C12", "bloque": ["QUE", "QUI", "INTEGRACION"]},
        {"id": "C13", "bloque": ["RRA", "RRE", "RRI", "RRO", "RRU"]},
    ]

    @staticmethod
    def categorias_habilitadas_para_ciclo_idx(idx: int):
        idx = max(0, int(idx or 0))
        extra = CurriculumV4.CATEGORIAS_DESBLOQUEO[: max(0, idx)]
        return list(CurriculumV4.CATEGORIAS_INICIALES) + list(extra)

    @staticmethod
    def obtener_ciclo_idx_por_id(ciclo_id: str) -> int:
        cid = (ciclo_id or "").strip().upper()
        for i, c in enumerate(CurriculumV4.CICLOS):
            if (c.get("id") or "").strip().upper() == cid:
                return i
        return 0

    @staticmethod
    def obtener_bloque_por_ciclo_id(ciclo_id: str):
        idx = CurriculumV4.obtener_ciclo_idx_por_id(ciclo_id)
        return CurriculumV4.CICLOS[idx].get("bloque", [])
