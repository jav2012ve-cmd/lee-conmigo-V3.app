import hashlib
import os

from core.album_categories import texto_para_tts


def _gtts_class():
    """Import diferido: evita ModuleNotFoundError al arrancar si gTTS no está instalado (p. ej. Cloud)."""
    try:
        from gtts import gTTS as _GTTS

        return _GTTS
    except ImportError:
        return None


class SpeechEngine:
    def __init__(self, cache_dir="assets/audio_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def generar_audio(self, texto):
        """
        Genera un archivo MP3 para el texto dado.
        Usa un hash MD5 para no repetir descargas de la misma palabra.
        Aplica texto_para_tts() para acentos correctos (colibrí, mamá, brócoli…).
        """
        if not texto:
            return None

        texto_norm = texto_para_tts(texto)
        if not texto_norm:
            return None

        # Hash UTF-8 para distinguir mamá / mama (cachés distintas tras normalizar)
        filename = hashlib.md5(texto_norm.upper().encode("utf-8")).hexdigest() + ".mp3"
        filepath = os.path.join(self.cache_dir, filename)

        # Si ya existe, no lo descargues de nuevo (ahorro de datos y tiempo)
        if os.path.exists(filepath):
            return filepath

        gTTS = _gtts_class()
        if gTTS is None:
            print(
                "gTTS no instalado: pip install gTTS (o añade gTTS al requirements.txt en Streamlit Cloud)."
            )
            return None

        try:
            # minúsculas: en español conserva tildes (í, á…); mejora pronunciación gTTS
            tts = gTTS(text=texto_norm.lower(), lang="es", slow=False)
            tts.save(filepath)
            return filepath
        except Exception as e:
            print(f"Error generando audio: {e}")
            return None