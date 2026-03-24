class CurriculumV3:
    """
    Diseño académico V3 (sin implementación todavía):
    - Progresión por ciclos: Álbum (categorías) → desbloquea bloque de lecciones → al superar bloque, +1 categoría.
    - Bloques de lecciones incluyen consonantes y luego sílabas especiales.
    """

    # Categorías del álbum (reusando exactamente las categorías existentes en V2: core/album_categories.py)
    # Inicio con 3 categorías: Familia + 2 adicionales.
    CATEGORIAS_INICIALES = ["Familia", "Juguetes", "En la cocina"]

    # Desbloqueo de 1 categoría por ciclo (orden sugerido).
    CATEGORIAS_DESBLOQUEO = [
        "Partes del cuerpo humano",
        "En la escuela",
        "Medios de transporte",
        "Colores",
        "Números",
        "Figuras geométricas",
        "Animales del mar",
        "Animales voladores",
    ]

    # Ciclos propuestos.
    # C1 inicia con vocales en 3 lecciones:
    # - A-E-I
    # - I-O-U
    # - A-E-I-O-U
    # C2 inicia consonantes.
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
        extra = CurriculumV3.CATEGORIAS_DESBLOQUEO[: max(0, idx)]
        return list(CurriculumV3.CATEGORIAS_INICIALES) + list(extra)

    @staticmethod
    def obtener_ciclo_idx_por_id(ciclo_id: str) -> int:
        cid = (ciclo_id or "").strip().upper()
        for i, c in enumerate(CurriculumV3.CICLOS):
            if (c.get("id") or "").strip().upper() == cid:
                return i
        return 0

    @staticmethod
    def obtener_bloque_por_ciclo_id(ciclo_id: str):
        idx = CurriculumV3.obtener_ciclo_idx_por_id(ciclo_id)
        return CurriculumV3.CICLOS[idx].get("bloque", [])

