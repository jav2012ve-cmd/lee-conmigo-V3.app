"""
Cola de trabajos para generar PDFs en segundo plano.
Al encolar un trabajo se lanza un hilo que genera el PDF y lo guarda en la DB;
la UI puede consultar el estado y ofrecer la descarga cuando status == 'ready'.
"""
import json
import threading
from database.db_queries import pdf_job_obtener, pdf_job_marcar_ready, pdf_job_marcar_failed

# Generadores (importación diferida para no fallar si ReportLab no está)
def _ejecutar_leccion(job_id):
    from core.leccion_pdf import generar_pdf_leccion
    job = pdf_job_obtener(job_id)
    if not job or job["status"] != "pending":
        return
    try:
        params = json.loads(job["params_json"])
        pdf_bytes = generar_pdf_leccion(
            letra=params.get("letra", ""),
            silabas=params.get("silabas", []),
            nombre_estudiante=params.get("nombre_estudiante", ""),
            fondo_ruta=params.get("fondo_ruta", ""),
            color_hex=params.get("color_hex", "#4A90E2"),
            palabras=params.get("palabras", []),
            frases=params.get("frases", []),
            foto_estudiante=params.get("foto_estudiante", ""),
            foto_mama=params.get("foto_mama", ""),
        )
        pdf_job_marcar_ready(job_id, pdf_bytes)
    except Exception as e:
        pdf_job_marcar_failed(job_id, str(e))


def _ejecutar_abecedario(job_id):
    from core.abecedario_pdf import generar_pdf_abecedario
    job = pdf_job_obtener(job_id)
    if not job or job["status"] != "pending":
        return
    try:
        params = json.loads(job["params_json"])
        pdf_bytes = generar_pdf_abecedario(
            nombre_estudiante=params.get("nombre_portada", ""),
            letras_disponibles=params.get("letras_disponibles", []),
            abecedario_guardado=params.get("abecedario_guardado", {}),
            color_fav=params.get("color_fav", "#4A90E2"),
            foto_ruta=params.get("foto_ruta", ""),
            fondo_ruta=params.get("fondo_ruta", ""),
            nombre_para_reconozca=params.get("nombre_para_reconozca", ""),
        )
        pdf_job_marcar_ready(job_id, pdf_bytes)
    except Exception as e:
        pdf_job_marcar_failed(job_id, str(e))


def ejecutar_job_en_background(job_id):
    """Lanza en un hilo la generación del PDF según el tipo de trabajo."""
    job = pdf_job_obtener(job_id)
    if not job or job["status"] != "pending":
        return
    tipo = (job.get("tipo") or "").strip().lower()
    if tipo == "leccion":
        thread = threading.Thread(target=_ejecutar_leccion, args=(job_id,), daemon=True)
    elif tipo == "abecedario":
        thread = threading.Thread(target=_ejecutar_abecedario, args=(job_id,), daemon=True)
    else:
        pdf_job_marcar_failed(job_id, f"Tipo de trabajo desconocido: {tipo}")
        return
    thread.start()
