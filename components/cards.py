import os
import base64
import json
import re
import functools
import streamlit as st
import streamlit.components.v1 as components
from components.karaoke_ui import segmentar_palabra
from core.album_categories import palabra_para_display


@functools.lru_cache(maxsize=256)
def _get_image_base64_cached(path: str):
    """Lee imagen y devuelve base64; cache por ruta para no repetir I/O en cada rerun."""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None


def get_image_base64(path):
    """Convierte imagen local a base64 para que Streamlit la renderice en HTML. Usa cache por ruta."""
    if not path or not isinstance(path, str):
        return None
    return _get_image_base64_cached(path)

def render_polaroid(img_path, palabra, es_acierto=None, mostrar_texto=True, mostrar_top_pct=100):
    """
    Renderiza una tarjeta estilo Polaroid.
    es_acierto: True (verde), False (rojo), None (neutro)
    """
    img_b64 = get_image_base64(img_path)
    
    # Definir color del borde según el feedback
    border_color = "#E0E0E0" # Neutro
    if es_acierto is True: border_color = "#4CAF50" # Verde éxito
    elif es_acierto is False: border_color = "#F44336" # Rojo error

    if img_b64:
        texto_html = f'<div class="polaroid-text">{palabra}</div>' if mostrar_texto else ""
        mostrar_top_pct = max(0, min(100, int(mostrar_top_pct)))
        recorte_inferior = 100 - mostrar_top_pct
        clip_style = f"clip-path: inset(0 0 {recorte_inferior}% 0);" if recorte_inferior > 0 else ""
        st.markdown(f"""
            <div class="polaroid-card" style="border: 5px solid {border_color};">
                <img src="data:image/png;base64,{img_b64}" class="polaroid-img" style="{clip_style}">
                {texto_html}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"No se encontró la imagen para: {palabra}")


def render_polaroid_click_to_play(
    img_path,
    texto_tts,
    audio_path=None,
    es_acierto=None,
    mostrar_top_pct=85,
    width_pct=100,
    max_width_px=None,
    height_px=420,
):
    """
    Polaroid clickeable: al tocar la imagen reproduce audio (sin banner).
    Si no hay audio, usa TTS del navegador como fallback.
    """
    img_b64 = get_image_base64(img_path)

    # Definir color del borde según el feedback
    border_color = "#E0E0E0"  # Neutro
    if es_acierto is True:
        border_color = "#4CAF50"  # Verde éxito
    elif es_acierto is False:
        border_color = "#F44336"  # Rojo error

    if not img_b64:
        st.warning("No se encontró la imagen.")
        return

    audio_b64 = ""
    if audio_path:
        try:
            with open(audio_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("ascii")
        except Exception:
            audio_b64 = ""

    mostrar_top_pct = max(0, min(100, int(mostrar_top_pct)))
    recorte_inferior = 100 - mostrar_top_pct
    clip_style = f"clip-path: inset(0 0 {recorte_inferior}% 0);" if recorte_inferior > 0 else ""

    width_pct = max(10, min(100, int(width_pct)))
    max_width_px_style = ""
    if max_width_px is not None:
        try:
            mw = int(max_width_px)
            if mw > 0:
                max_width_px_style = f"max-width:{mw}px;"
        except Exception:
            max_width_px_style = ""

    texto_js = json.dumps(texto_tts or "")

    components.html(
        f"""
        <style>
          .lc-card {{
            box-sizing: border-box;
            border: 5px solid {border_color};
            border-radius: 12px;
            padding: 10px;
            background: #fff;
            margin: 0 auto;
            max-width: {width_pct}%;
            {max_width_px_style}
          }}
          .lc-img {{
            width: 100%;
            height: auto;
            display: block;
            border-radius: 8px;
          }}
        </style>

        <div class="lc-card">
          <img
            src="data:image/png;base64,{img_b64}"
            class="lc-img"
            style="cursor:pointer; {clip_style}"
            onclick="window.__lcPlay && window.__lcPlay();"
            alt=""
          />
        </div>

        <script>
          window.__lcPlay = function() {{
            try {{
              const b64 = "{audio_b64}";
              if (b64 && b64.length > 0) {{
                const audio = new Audio("data:audio/mpeg;base64," + b64);
                audio.volume = 1.0;
                audio.play();
                return;
              }}
            }} catch (e) {{}}

            // Fallback: TTS del navegador (solo voz femenina)
            try {{
              const text = {texto_js};
              window.speechSynthesis.cancel();
              const u = new SpeechSynthesisUtterance(text);
              u.lang = "es-ES";
              const voices = window.speechSynthesis.getVoices();
              const esFemale = voices.find(v => v.lang.startsWith("es") && /mujer|female|woman|helena|sabina|natalia|google español/i.test(v.name));
              const esAny = voices.find(v => v.lang.startsWith("es"));
              if (esFemale) u.voice = esFemale; else if (esAny) u.voice = esAny;
              window.speechSynthesis.speak(u);
            }} catch (e) {{}}
          }};
        </script>
        """,
        height=int(height_px),
    )


def render_album_card_placeholder(unique_id=None, size="normal"):
    """Espacio vacío en la cuadrícula del álbum para cargar una imagen después."""
    min_h = "220px" if size == "xlarge" else ("180px" if size == "large" else "175px")
    st.markdown(
        f"""
        <div style="border: 3px dashed #ccc; border-radius: 14px; background: #f8f9fa; min-height: {min_h}; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <span style="color: #999; font-size: 0.9rem;">Espacio para imagen</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_album_card_karaoke(img_path, palabra, unique_id=None, size="normal", show_label_below=True):
    """
    Tarjeta del álbum. Al hacer clic: la imagen desaparece y en su lugar se muestra
    la palabra en sílabas, destacando sílaba por sílaba (efecto karaoke) mientras suena el nombre.
    show_label_below: si True (Familia), además se muestra cintillo fijo debajo cuando no hay karaoke.
    """
    img_b64 = get_image_base64(img_path) if img_path else None
    if not img_b64:
        st.warning(f"No se encontró la imagen: {palabra}")
        return
    uid = (unique_id if unique_id is not None else id(img_path))
    uid_safe = re.sub(r"\W", "_", str(uid))[:32] or "card"
    nombre_display = palabra_para_display((palabra or "").strip()) or (palabra or "").strip() or "Imagen"
    texto_js = json.dumps(nombre_display)
    silabas = segmentar_palabra(nombre_display)
    if not silabas:
        silabas = [nombre_display]
    silabas_js = json.dumps(silabas)
    silabas_escaped = [s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;") for s in silabas]
    spans_html = "".join(f'<span class="lc-silaba" data-i="{i}">{silabas_escaped[i]}</span>' for i in range(len(silabas_escaped)))

    if show_label_below:
        if size == "xlarge":
            height_px, img_style = 420, "max-height: 260px; object-fit: contain;"
        elif size == "large":
            height_px, img_style = 380, "max-height: 200px; object-fit: contain;"
        else:
            height_px, img_style = 280, "max-height: 140px; object-fit: contain;"
    else:
        # Sin cintillo: categorías no Familia (normal ~25% más grande que antes)
        if size == "xlarge":
            height_px, img_style = 320, "max-height: 280px; object-fit: contain;"
        elif size == "large":
            height_px, img_style = 260, "max-height: 240px; object-fit: contain;"
        else:
            height_px, img_style = 250, "max-height: 225px; object-fit: contain;"
    ext = os.path.splitext(img_path or "")[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

    cintillo_fijo = ""
    if show_label_below:
        palabra_safe = nombre_display.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        cintillo_class = "album-karaoke-cintillo album-karaoke-cintillo-xlarge" if size == "xlarge" else "album-karaoke-cintillo"
        cintillo_fijo = f'<div id="lc-cintillo-{uid_safe}" class="{cintillo_class}">{palabra_safe}</div>'

    components.html(
        f"""
        <style>
          .album-karaoke-card {{ border: 4px solid #E0E0E0; border-radius: 14px; padding: 10px; background: #fff; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.08); position: relative; min-height: 120px; }}
          .album-karaoke-card img {{ width: 100%; height: auto; display: block; border-radius: 10px; cursor: pointer; {img_style} }}
          .album-karaoke-karaoke-panel {{ display: none; padding: 20px 10px; align-items: center; justify-content: center; min-height: 140px; }}
          .album-karaoke-karaoke-panel.show {{ display: flex !important; flex-wrap: wrap; gap: 4px 10px; justify-content: center; }}
          .lc-silaba {{ font-size: 1.8rem; font-weight: 800; color: #333; padding: 8px 12px; border-radius: 10px; transition: all 0.25s ease; }}
          .lc-silaba.karaoke-on {{ background: linear-gradient(135deg, #fff59d 0%, #ffeb3b 100%); color: #1a1a2e; transform: scale(1.12); box-shadow: 0 2px 12px rgba(255,235,59,0.6); }}
          .album-karaoke-cintillo {{ font-size: 1.2rem; font-weight: 700; color: #1a1a2e; margin-top: 10px; text-align: center; width: 100%; }}
          .album-karaoke-cintillo-xlarge {{ font-size: 1.35rem; margin-top: 12px; text-align: center; width: 100%; }}
        </style>
        <div class="album-karaoke-card">
          <img id="lc-img-{uid_safe}" src="data:{mime};base64,{img_b64}" alt="" onclick="lcKaraokePlay_{uid_safe}()" />
          <div id="lc-panel-{uid_safe}" class="album-karaoke-karaoke-panel">
            {spans_html}
          </div>
          {cintillo_fijo}
        </div>
        <script>
          function lcKaraokePlay_{uid_safe}() {{
            var img = document.getElementById("lc-img-{uid_safe}");
            var panel = document.getElementById("lc-panel-{uid_safe}");
            var silabas = {silabas_js};
            if (!img || !panel || !silabas || !silabas.length) return;
            img.style.display = "none";
            panel.classList.add("show");
            var spans = panel.querySelectorAll(".lc-silaba");
            var idx = 0;
            function quitarHighlight() {{ for (var i = 0; i < spans.length; i++) spans[i].classList.remove("karaoke-on"); }}
            function siguiente() {{
              quitarHighlight();
              if (idx < spans.length) {{ spans[idx].classList.add("karaoke-on"); idx++; }}
            }}
            siguiente();
            var interval = setInterval(function() {{
              if (idx >= spans.length) {{ clearInterval(interval); setTimeout(function() {{ panel.classList.remove("show"); img.style.display = "block"; quitarHighlight(); }}, 600); return; }}
              siguiente();
            }}, 450);
            function setVoiceAndSpeak(u, voices) {{
              var esFemale = voices.filter(function(v) {{ return v.lang.indexOf("es") === 0 && /mujer|female|woman|helena|sabina|natalia|google español/i.test(v.name); }})[0];
              var esAny = voices.filter(function(v) {{ return v.lang.indexOf("es") === 0; }})[0];
              if (esFemale) u.voice = esFemale; else if (esAny) u.voice = esAny;
              window.speechSynthesis.speak(u);
            }}
            function speakFemale() {{
              var text = {texto_js};
              window.speechSynthesis.cancel();
              var u = new SpeechSynthesisUtterance(text);
              u.lang = "es-ES";
              var voices = window.speechSynthesis.getVoices();
              if (voices.length === 0) {{ window.speechSynthesis.onvoiceschanged = function() {{ setVoiceAndSpeak(u, window.speechSynthesis.getVoices()); }}; return; }}
              setVoiceAndSpeak(u, voices);
            }}
            try {{ speakFemale(); }} catch (e) {{}}
          }}
        </script>
        """,
        height=height_px,
    )


# Placeholder SVG (persona) en base64 para cuando no hay foto de estudiante
_PLACEHOLDER_AVATAR_SVG = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        b'<circle cx="50" cy="50" r="48" fill="#E8E8E8" stroke="#ccc"/>'
        b'<circle cx="50" cy="38" r="18" fill="#aaa"/>'
        b'<path d="M22 92 A48 48 0 0 1 78 92" fill="#aaa"/>'
        b'</svg>'
    ).decode()
)


def render_selector_avatar(img_path, nombre, seleccionado=False):
    """Tarjeta simplificada para la pantalla de entrada (Login visual). Muestra foto del estudiante o placeholder."""
    img_b64 = None
    if img_path and isinstance(img_path, str):
        img_b64 = get_image_base64(img_path)
    src = f"data:image/png;base64,{img_b64}" if img_b64 else _PLACEHOLDER_AVATAR_SVG
    opacity = "1.0" if seleccionado else "0.7"
    border = "4px solid #4A90E2" if seleccionado else "1px solid #DDD"

    st.markdown(f"""
        <div style="text-align: center; cursor: pointer; opacity: {opacity};">
            <img src="{src}"
                 style="width: 120px; height: 120px; border-radius: 50%; border: {border}; object-fit: cover;">
            <p style="font-weight: bold; margin-top: 6px; font-size: 1.15rem;">{nombre}</p>
        </div>
    """, unsafe_allow_html=True)