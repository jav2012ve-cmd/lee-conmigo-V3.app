import os
import html
import base64
import json
import re
import functools
import unicodedata
import streamlit as st
import streamlit.components.v1 as components
from components.karaoke_ui import segmentar_palabra
from core.album_categories import CATEGORIAS_CON_SFX_TARJETA, palabra_para_display

# Categoría ficticia: activa búsqueda de SFX en assets/sfx/abecedario/ (matriz abecedario).
ABECEDARIO_MATRIZ_SFX_CATEGORIA = "__MATRIZ_ABECEDARIO__"


def _letra_prefijo_abecedario(letra_abecedario: str | None, nombre_display: str) -> str:
    """Primera grafema para «L de …» (p. ej. Ñ en la matriz)."""
    z = (letra_abecedario or "").strip()
    if z:
        return z[0].upper()
    nd = (nombre_display or "").strip()
    return nd[0].upper() if nd else "?"


def _capitalizar_ejemplo_abecedario(s: str) -> str:
    """«Ambulancia», «Bajo»… a partir de la forma ya normalizada para pantalla."""
    t = (s or "").strip()
    if not t:
        return ""
    return t[0].upper() + t[1:].lower()


@functools.lru_cache(maxsize=256)
def _get_image_base64_cached(path: str):
    """Lee imagen y devuelve base64; cache solo lecturas correctas (no cachear fallos)."""
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def get_image_base64(path):
    """Convierte imagen local a base64 para que Streamlit la renderice en HTML."""
    if not path or not isinstance(path, str):
        return None
    p = os.path.normpath(path.strip())
    if not os.path.isfile(p):
        return None
    try:
        return _get_image_base64_cached(p)
    except OSError:
        return None


def mime_type_for_image_path(path: str) -> str:
    """MIME para data-URL; JPEG no debe enviarse como image/png (varios navegadores no lo muestran bien)."""
    if not path:
        return "image/png"
    lower = path.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    return "image/png"


@functools.lru_cache(maxsize=256)
def _get_audio_base64_cached(path: str):
    with open(path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode()


def get_audio_base64(path):
    if not path or not isinstance(path, str):
        return None
    p = os.path.normpath(path.strip())
    if not os.path.isfile(p):
        return None
    try:
        return _get_audio_base64_cached(p)
    except OSError:
        return None


def mime_type_for_audio_path(path: str) -> str:
    if not path:
        return "audio/mpeg"
    lower = path.lower()
    if lower.endswith(".wav"):
        return "audio/wav"
    if lower.endswith(".ogg"):
        return "audio/ogg"
    return "audio/mpeg"


def _normalizar_slug(texto):
    t = unicodedata.normalize("NFKD", (texto or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


# slug de la tarjeta (tras _normalizar_slug) -> stem del archivo Sonido_<stem>.mp3
_SFX_STEM_OVERRIDE_POR_PALABRA_SLUG = {
    "auto_de_carreras": "auto",
}

# casos especiales por texto crudo de la tarjeta (antes de normalizar)
_SFX_STEM_OVERRIDE_POR_PALABRA_RAW = {
    "tambor_2": "tambor_2",
    "tambor2": "tambor_2",
    "tambor}": "tambor_2",
}


def _resolver_sfx_abecedario_matriz(palabra):
    """
    Sonidos extra para la matriz Abecedario: primero `assets/sfx/abecedario/`,
    luego las mismas rutas que el álbum (Instrumentos musicales, Sonidos especiales A/B).
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sfx"))
    if not os.path.isdir(base_dir):
        return None
    abec_dir = os.path.join(base_dir, "abecedario")
    palabra_raw = (palabra or "").strip().lower()
    palabra_slug = _normalizar_slug(palabra)
    if not palabra_slug:
        return None
    sfx_stem = _SFX_STEM_OVERRIDE_POR_PALABRA_RAW.get(palabra_raw)
    if not sfx_stem:
        sfx_stem = _SFX_STEM_OVERRIDE_POR_PALABRA_SLUG.get(palabra_slug, palabra_slug)
    extensiones = (".mp3", ".wav", ".ogg")
    candidatos = []
    if os.path.isdir(abec_dir):
        candidatos.extend(
            [os.path.join(abec_dir, f"Sonido_{sfx_stem}{ext}") for ext in extensiones]
        )
        candidatos.extend(
            [os.path.join(abec_dir, f"Sonido_{sfx_stem.capitalize()}{ext}") for ext in extensiones]
        )
        candidatos.extend([os.path.join(abec_dir, f"{sfx_stem}{ext}") for ext in extensiones])
    candidatos.extend([os.path.join(base_dir, f"{sfx_stem}{ext}") for ext in extensiones])
    for path in candidatos:
        if os.path.isfile(path):
            return path
    # Mismas convenciones que tarjetas del álbum (p. ej. xilófono en Instrumentos musicales).
    for cat in sorted(CATEGORIAS_CON_SFX_TARJETA):
        alt = _resolver_sfx_tarjeta_album(cat, palabra)
        if alt:
            return alt
    return None


def _resolver_sfx_tarjeta_album(categoria, palabra):
    """
    Resolución SFX de álbum sin pasar por la categoría sentinela del abecedario
    (evita recursión con _resolver_sfx_tarjeta).
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sfx"))
    if not os.path.isdir(base_dir):
        return None
    if (categoria or "").strip() not in CATEGORIAS_CON_SFX_TARJETA:
        return None
    palabra_raw = (palabra or "").strip().lower()
    palabra_slug = _normalizar_slug(palabra)
    if not palabra_slug:
        return None
    sfx_stem = _SFX_STEM_OVERRIDE_POR_PALABRA_RAW.get(palabra_raw)
    if not sfx_stem:
        sfx_stem = _SFX_STEM_OVERRIDE_POR_PALABRA_SLUG.get(palabra_slug, palabra_slug)
    categoria_slug = _normalizar_slug(categoria)
    extensiones = (".mp3", ".wav", ".ogg")
    candidatos = []
    if categoria_slug:
        candidatos.extend(
            [os.path.join(base_dir, categoria_slug, f"Sonido_{sfx_stem}{ext}") for ext in extensiones]
        )
        candidatos.extend(
            [os.path.join(base_dir, categoria_slug, f"Sonido_{sfx_stem.capitalize()}{ext}") for ext in extensiones]
        )
        candidatos.extend([os.path.join(base_dir, categoria_slug, f"{sfx_stem}{ext}") for ext in extensiones])
    candidatos.extend([os.path.join(base_dir, f"{sfx_stem}{ext}") for ext in extensiones])
    for path in candidatos:
        if os.path.isfile(path):
            return path
    return None


def _resolver_sfx_tarjeta(categoria, palabra):
    """
    Busca audio opcional para la tarjeta en assets/sfx.
    Convención recomendada:
    - assets/sfx/<categoria_slug>/<palabra_slug>.mp3
    - assets/sfx/<palabra_slug>.mp3
    Soporta .mp3, .wav y .ogg.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sfx"))
    if not os.path.isdir(base_dir):
        return None
    if (categoria or "").strip() == ABECEDARIO_MATRIZ_SFX_CATEGORIA:
        return _resolver_sfx_abecedario_matriz(palabra)
    if (categoria or "").strip() not in CATEGORIAS_CON_SFX_TARJETA:
        return None
    return _resolver_sfx_tarjeta_album(categoria, palabra)


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
    if size == "xlarge":
        min_h = "220px"
    elif size == "large":
        min_h = "180px"
    elif size == "compact":
        min_h = "115px"
    elif size == "abecedario_wide":
        min_h = "172px"
    else:
        min_h = "175px"
    st.markdown(
        f"""
        <div style="border: 3px dashed #ccc; border-radius: 14px; background: #f8f9fa; min-height: {min_h}; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <span style="color: #999; font-size: 0.9rem;">Espacio para imagen</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_album_card_karaoke(
    img_path,
    palabra,
    unique_id=None,
    size="normal",
    show_label_below=True,
    categoria=None,
    sonidos_tarjeta_habilitados=True,
    *,
    prefijo_letra_de_abecedario: bool = False,
    letra_abecedario: str | None = None,
):
    """
    Tarjeta del álbum. Al hacer clic: la imagen desaparece y en su lugar se muestra
    la palabra en sílabas, destacando sílaba por sílaba (efecto karaoke) mientras suena el nombre.
    show_label_below: si True (Familia), además se muestra cintillo fijo debajo cuando no hay karaoke.
    En abecedario (`prefijo_letra_de_abecedario`): el karaoke y el TTS empiezan con «A de Ambulancia»,
    luego las sílabas de la palabra; `letra_abecedario` fuerza la L de «L de …» (p. ej. M con palabra «Papá»).
    """
    img_b64 = get_image_base64(img_path) if img_path else None
    if not img_b64:
        st.warning(f"No se encontró la imagen: {palabra}")
        return
    uid = (unique_id if unique_id is not None else id(img_path))
    uid_safe = re.sub(r"\W", "_", str(uid))[:32] or "card"
    nombre_display = palabra_para_display((palabra or "").strip()) or (palabra or "").strip() or "Imagen"
    nd_stripped = (nombre_display or "").strip()
    if prefijo_letra_de_abecedario and len(nd_stripped) >= 2:
        L = _letra_prefijo_abecedario(letra_abecedario, nombre_display)
        ejemplo = _capitalizar_ejemplo_abecedario(nombre_display)
        core = segmentar_palabra(nombre_display)
        if not core:
            core = [nombre_display]
        silabas = [L, " de ", ejemplo] + core
        tts_text = f"{L} de {ejemplo}. {nombre_display}"
    else:
        silabas = segmentar_palabra(nombre_display)
        if not silabas:
            silabas = [nombre_display]
        tts_text = nombre_display
    texto_js = json.dumps(tts_text)
    silabas_js = json.dumps(silabas)
    silabas_escaped = [s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;") for s in silabas]
    spans_html = "".join(f'<span class="lc-silaba" data-i="{i}">{silabas_escaped[i]}</span>' for i in range(len(silabas_escaped)))
    sfx_b64 = ""
    sfx_mime = "audio/mpeg"
    show_sfx_button = False
    if sonidos_tarjeta_habilitados:
        sfx_path = _resolver_sfx_tarjeta(categoria, nombre_display)
        if sfx_path:
            sfx_b64 = get_audio_base64(sfx_path) or ""
            sfx_mime = mime_type_for_audio_path(sfx_path)
            show_sfx_button = bool(sfx_b64)

    if show_label_below:
        if size == "xlarge":
            height_px, img_style = 420, "max-height: 260px; object-fit: contain;"
        elif size == "large":
            height_px, img_style = 380, "max-height: 200px; object-fit: contain;"
        elif size == "compact":
            height_px, img_style = 240, "max-height: 105px; object-fit: contain;"
        elif size == "abecedario_wide":
            height_px, img_style = 360, "max-height: 200px; object-fit: contain;"
        else:
            height_px, img_style = 280, "max-height: 140px; object-fit: contain;"
    else:
        # Sin cintillo: categorías no Familia (normal ~25% más grande que antes)
        if size == "xlarge":
            height_px, img_style = 320, "max-height: 280px; object-fit: contain;"
        elif size == "large":
            height_px, img_style = 260, "max-height: 240px; object-fit: contain;"
        elif size == "compact":
            height_px, img_style = 210, "max-height: 115px; object-fit: contain;"
        elif size == "abecedario_wide":
            # Altura acotada al contenido real para no dejar banda en blanco entre filas de la matriz.
            height_px, img_style = 258, "max-height: 172px; object-fit: contain;"
        else:
            height_px, img_style = 250, "max-height: 225px; object-fit: contain;"
    ext = os.path.splitext(img_path or "")[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

    cintillo_fijo = ""
    if show_label_below:
        palabra_safe = nombre_display.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        if size == "xlarge":
            cintillo_class = "album-karaoke-cintillo album-karaoke-cintillo-xlarge"
        elif size == "compact":
            cintillo_class = "album-karaoke-cintillo album-karaoke-cintillo-compact"
        elif size == "abecedario_wide":
            cintillo_class = "album-karaoke-cintillo album-karaoke-cintillo-wide"
        else:
            cintillo_class = "album-karaoke-cintillo"
        cintillo_fijo = f'<div id="lc-cintillo-{uid_safe}" class="{cintillo_class}">{palabra_safe}</div>'

    extra_size_css = ""
    if size == "compact":
        extra_size_css = """
          .album-karaoke-card { padding: 6px !important; min-height: 72px !important; }
          .lc-silaba { font-size: 1.12rem !important; padding: 3px 6px !important; }
          .album-karaoke-cintillo-compact { font-size: 0.88rem !important; margin-top: 4px !important; }
          .album-karaoke-karaoke-panel { min-height: 88px !important; padding: 8px 4px !important; }
          .album-sfx-btn { width: 30px !important; height: 30px !important; font-size: 0.9rem !important; top: 4px !important; right: 4px !important; }
        """
    elif size == "abecedario_wide":
        extra_size_css = """
          .album-karaoke-card { padding: 5px !important; min-height: 0 !important; }
          .lc-silaba { font-size: 1.45rem !important; padding: 5px 8px !important; }
          .album-karaoke-cintillo-wide { font-size: 1.05rem !important; margin-top: 8px !important; }
          .album-karaoke-karaoke-panel { min-height: 82px !important; padding: 8px 6px !important; }
          .album-sfx-btn { width: 40px !important; height: 40px !important; font-size: 1.05rem !important; top: 6px !important; right: 6px !important; }
        """

    iframe_width = 620 if size == "abecedario_wide" else None

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
          {extra_size_css}
          .album-sfx-btn {{
            position: absolute;
            top: 12px;
            right: 12px;
            border: none;
            border-radius: 999px;
            width: 40px;
            height: 40px;
            font-size: 1.1rem;
            background: rgba(255, 255, 255, 0.92);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            cursor: pointer;
          }}
          .album-sfx-btn:hover {{ transform: scale(1.06); }}
        </style>
        <div class="album-karaoke-card">
          {"<button class='album-sfx-btn' title='Sonido de tarjeta' onclick='lcPlaySfx_" + uid_safe + "()'>🔊</button>" if show_sfx_button else ""}
          <img id="lc-img-{uid_safe}" src="data:{mime};base64,{img_b64}" alt="" onclick="lcKaraokePlay_{uid_safe}()" />
          {"<audio id='lc-sfx-" + uid_safe + "' preload='auto'><source src='data:" + sfx_mime + ";base64," + sfx_b64 + "' type='" + sfx_mime + "'></audio>" if show_sfx_button else ""}
          <div id="lc-panel-{uid_safe}" class="album-karaoke-karaoke-panel">
            {spans_html}
          </div>
          {cintillo_fijo}
        </div>
        <script>
          function lcStopAllAlbumMediaExcept(except) {{
            try {{ window.speechSynthesis.cancel(); }} catch (e0) {{}}
            function pauseDoc(doc) {{
              if (!doc || !doc.querySelectorAll) return;
              var xs = doc.querySelectorAll("audio");
              for (var i = 0; i < xs.length; i++) {{
                var a = xs[i];
                if (except && a === except) continue;
                try {{ a.pause(); a.currentTime = 0; }} catch (e1) {{}}
              }}
            }}
            function scanFrame(win) {{
              if (!win || !win.document) return;
              try {{
                pauseDoc(win.document);
                var fs = win.document.querySelectorAll("iframe");
                for (var k = 0; k < fs.length; k++) {{
                  try {{
                    var cw = fs[k].contentWindow;
                    if (cw) scanFrame(cw);
                  }} catch (e2) {{}}
                }}
              }} catch (e3) {{}}
            }}
            var topw = window;
            try {{
              while (topw.parent && topw.parent !== topw) topw = topw.parent;
            }} catch (e4) {{}}
            try {{ scanFrame(topw); }} catch (e5) {{}}
          }}

          var lcSfxTimer_{uid_safe} = null;
          function lcStopSfxAfterMax_{uid_safe}(audioEl) {{
            try {{
              if (!audioEl) return;
              if (lcSfxTimer_{uid_safe}) {{
                clearTimeout(lcSfxTimer_{uid_safe});
              }}
              lcSfxTimer_{uid_safe} = setTimeout(function() {{
                try {{
                  audioEl.pause();
                  audioEl.currentTime = 0;
                }} catch (e) {{}}
              }}, 25000); // Máximo 25 segundos por reproducción
            }} catch (e) {{}}
          }}

          function lcPlaySfx_{uid_safe}() {{
            try {{
              const audio = document.getElementById("lc-sfx-{uid_safe}");
              if (!audio) return;
              lcStopAllAlbumMediaExcept(null);
              audio.volume = 1.0;
              audio.currentTime = 0;
              const p = audio.play();
              if (p && p.catch) p.catch(function() {{}});
              lcStopSfxAfterMax_{uid_safe}(audio);
            }} catch (e) {{}}
          }}

          function lcKaraokePlay_{uid_safe}() {{
            var img = document.getElementById("lc-img-{uid_safe}");
            var panel = document.getElementById("lc-panel-{uid_safe}");
            var silabas = {silabas_js};
            if (!img || !panel || !silabas || !silabas.length) return;
            lcStopAllAlbumMediaExcept(null);
            // Intento de desbloqueo del audio dentro del gesto del usuario (click).
            try {{
              var sfxEl = document.getElementById("lc-sfx-{uid_safe}");
              if (sfxEl) {{
                sfxEl.loop = true;
                sfxEl.muted = true;
                sfxEl.volume = 0.0;
                sfxEl.currentTime = 0;
                var unlockPromise = sfxEl.play();
                if (unlockPromise && unlockPromise.then) {{
                  unlockPromise.then(function() {{
                    // Queda reproduciendo en silencio para evitar bloqueo al final del karaoke.
                  }}).catch(function() {{
                    try {{
                      sfxEl.loop = false;
                      sfxEl.muted = false;
                      sfxEl.volume = 1.0;
                    }} catch (e) {{}}
                  }});
                }}
              }}
            }} catch (e) {{}}
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
              if (idx >= spans.length) {{
                clearInterval(interval);
                setTimeout(function() {{
                  panel.classList.remove("show");
                  img.style.display = "block";
                  quitarHighlight();
                  // Secuencia solicitada: primero Karaoke, luego sonido característico.
                  try {{
                    var sfxEnd = document.getElementById("lc-sfx-{uid_safe}");
                    if (sfxEnd) {{
                      lcStopAllAlbumMediaExcept(null);
                      sfxEnd.loop = false;
                      sfxEnd.muted = false;
                      sfxEnd.volume = 1.0;
                      sfxEnd.currentTime = 0;
                      var pEnd = sfxEnd.play();
                      if (pEnd && pEnd.catch) pEnd.catch(function() {{}});
                      lcStopSfxAfterMax_{uid_safe}(sfxEnd);
                    }} else {{
                      lcPlaySfx_{uid_safe}();
                    }}
                  }} catch (e) {{
                    lcPlaySfx_{uid_safe}();
                  }}
                }}, 600);
                return;
              }}
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
        height=int(height_px),
        **({"width": int(iframe_width)} if iframe_width else {}),
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


def render_selector_avatar(img_path, nombre, seleccionado=False, salon_entrar_id=None):
    """Tarjeta para el Salón: foto circular + nombre. Si salon_entrar_id está definido, la tarjeta es un enlace (?salon_entrar=) que la app procesa como entrada."""
    img_b64 = None
    mime = "image/png"
    if img_path and isinstance(img_path, str):
        img_b64 = get_image_base64(img_path)
        mime = mime_type_for_image_path(img_path)
    src = f"data:{mime};base64,{img_b64}" if img_b64 else _PLACEHOLDER_AVATAR_SVG
    opacity = "1.0" if seleccionado else "0.7"
    border = "4px solid #4A90E2" if seleccionado else "1px solid #DDD"
    nombre_esc = html.escape((nombre or "").strip())
    sid = int(salon_entrar_id) if salon_entrar_id is not None else None

    inner = f"""
            <img src="{src}" alt="{nombre_esc}"
                 style="width: 120px; height: 120px; border-radius: 50%; border: {border}; object-fit: cover; display: inline-block;">
            <p style="font-weight: bold; margin-top: 8px; font-size: 0.95rem; line-height: 1.25; word-break: break-word; color: #333; max-width: 168px; margin-left: auto; margin-right: auto;">{nombre_esc}</p>
    """
    if sid is not None:
        st.markdown(
            f"""
            <a class="lc-salon-avatar-wrap" href="?salon_entrar={sid}" target="_self" role="link"
               title="Entrar — {nombre_esc}"
               style="text-align: center; opacity: {opacity}; text-decoration: none; color: inherit; display: block; cursor: pointer;">
                {inner}
            </a>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="lc-salon-avatar-wrap" style="text-align: center; opacity: {opacity};">
                {inner}
            </div>
            """,
            unsafe_allow_html=True,
        )