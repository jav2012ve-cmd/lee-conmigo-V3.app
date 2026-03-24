"""
Generación del informe de avance y envío por correo al finalizar la sesión del estudiante.
"""
import os
from datetime import datetime

# Etiquetas amigables para tipo_silaba
LABEL_TIPO = {
    "VocalInicio": "Empieza con vocal",
    "VocalFin": "Termina con vocal",
    "Directa": "Sílaba directa",
}


def generar_informe_html(nombre_estudiante, ciclo, filas_resumen, fecha_str=None):
    """
    Genera el HTML del informe de avance.
    filas_resumen: lista de (fonema, tipo_silaba, aciertos, errores).
    """
    if not fecha_str:
        fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    filas_html = ""
    total_aciertos = 0
    total_errores = 0
    for fonema, tipo_silaba, aciertos, errores in filas_resumen:
        tipo_label = LABEL_TIPO.get(tipo_silaba, tipo_silaba)
        filas_html += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{fonema}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{tipo_label}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{aciertos}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{errores}</td>
        </tr>"""
        total_aciertos += aciertos
        total_errores += errores

    if not filas_html:
        filas_html = """
        <tr>
            <td colspan="4" style="padding: 12px; border: 1px solid #ddd; color: #666;">
                Aún no hay registros de esta sesión. ¡Sigue practicando!
            </td>
        </tr>"""

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Informe de avance - LeeConmigo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; color: #333; }}
        .titulo {{ font-size: 1.5rem; color: #2e7d32; margin-bottom: 8px; }}
        .subtitulo {{ color: #666; margin-bottom: 20px; }}
        table {{ border-collapse: collapse; width: 100%; max-width: 500px; }}
        th {{ background: #f5f5f5; padding: 10px; border: 1px solid #ddd; text-align: left; }}
        .total {{ margin-top: 16px; font-weight: bold; }}
        .pie {{ margin-top: 24px; font-size: 0.85rem; color: #888; }}
    </style>
</head>
<body>
    <div class="titulo">📚 Informe de avance - LeeConmigo</div>
    <div class="subtitulo">Estudiante: <strong>{nombre_estudiante}</strong> · Ciclo: <strong>{ciclo}</strong> · {fecha_str}</div>
    <table>
        <thead>
            <tr>
                <th>Letra / vocal</th>
                <th>Actividad</th>
                <th>Aciertos</th>
                <th>Errores</th>
            </tr>
        </thead>
        <tbody>
            {filas_html}
        </tbody>
    </table>
    <div class="total">Total aciertos: {total_aciertos} · Total errores: {total_errores}</div>
    <div class="pie">Generado por LeeConmigo. Sesión finalizada.</div>
</body>
</html>"""
    return html


def enviar_informe_email(destino_email, nombre_estudiante, html_cuerpo):
    """
    Envía el informe por correo. Usa variables de entorno:
    SMTP_HOST, SMTP_PORT (opcional, default 587), SMTP_USER, SMTP_PASSWORD.
    Devuelve (True, None) si se envió bien, (False, mensaje_error) si no.
    """
    host = os.environ.get("SMTP_HOST") or os.environ.get("smtp_host")
    port = int(os.environ.get("SMTP_PORT") or os.environ.get("smtp_port") or "587")
    user = os.environ.get("SMTP_USER") or os.environ.get("smtp_user")
    password = os.environ.get("SMTP_PASSWORD") or os.environ.get("smtp_password")
    if not all([host, user, password]) or not destino_email:
        return False, "Correo no configurado o sin dirección de destino."

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"LeeConmigo - Informe de avance de {nombre_estudiante}"
        msg["From"] = user
        msg["To"] = destino_email
        part = MIMEText(html_cuerpo, "html", "utf-8")
        msg.attach(part)

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [destino_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)
