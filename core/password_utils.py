"""Hash y verificación de contraseñas (docentes / tutores LeeConmigo)."""

from __future__ import annotations

import hashlib
import re
import secrets


def normalizar_cedula_o_clave_numerica(s: str) -> str:
    """Deja solo dígitos (cédulas con puntos o espacios se normalizan)."""
    if not s or not isinstance(s, str):
        return ""
    return re.sub(r"\D", "", s.strip())


def nombre_docente_tutor_norm(s: str) -> str:
    """Clave estable para coincidir con Zona docentes / Tutores (sin distinguir mayúsculas)."""
    return (s or "").strip().lower()


def hash_password(plain: str) -> str:
    """Devuelve cadena 'salt$hexdigest' (PBKDF2-SHA256)."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        (plain or "").encode("utf-8"),
        salt.encode("ascii"),
        120_000,
    )
    return f"{salt}${dk.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, hexd = stored.split("$", 1)
    try:
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            (plain or "").encode("utf-8"),
            salt.encode("ascii"),
            120_000,
        )
    except Exception:
        return False
    return secrets.compare_digest(dk.hex(), hexd)
