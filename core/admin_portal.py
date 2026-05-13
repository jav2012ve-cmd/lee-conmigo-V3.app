"""PIN de acceso a la zona de administradores (credenciales docente/tutor)."""

from __future__ import annotations

import os


def resolver_pin_administrador() -> str:
    """
    Orden: variable de entorno LEE_CONMIGO_ADMIN_PIN, luego Streamlit Secrets
    `admin_portal_pin` o `LEE_CONMIGO_ADMIN_PIN`.
    Cadena vacía = no hay PIN configurado (la zona admin no permitirá entrar).
    """
    v = (os.environ.get("LEE_CONMIGO_ADMIN_PIN") or "").strip()
    if v:
        return v
    try:
        import streamlit as st

        s = st.secrets.get("admin_portal_pin", None)
        if s is None:
            s = st.secrets.get("LEE_CONMIGO_ADMIN_PIN", None)
        return (str(s) if s is not None else "").strip()
    except Exception:
        return ""
