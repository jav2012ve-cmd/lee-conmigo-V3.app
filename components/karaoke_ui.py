import streamlit as st
import time
import os
import base64
import json
import streamlit.components.v1 as components
from core.album_categories import palabra_para_display


def segmentar_palabra(palabra):
    """
    Lógica simplificada de silabeo.
    Aplica forma ortográfica con acentos (palabra_para_display) antes de silabear.
    Si la palabra trae guiones, los usa. Si no, usa silabear_es para español.
    """
    p = (palabra or "").strip()
    if not p:
        return []
    p = palabra_para_display(p) or p
    if "-" in p:
        return p.split("-")
    return silabear_es(p)


def _forman_diptongo(c1, c2):
    """En español: fuerte (A,E,O) + débil (I,U) o débil + fuerte o débil + débil = diptongo."""
    fuertes = "AEOÁÉÍÓÚ"
    debiles = "IU"
    v1 = c1.upper() in fuertes or c1.upper() in debiles
    v2 = c2.upper() in fuertes or c2.upper() in debiles
    if not (v1 and v2):
        return False
    d1 = c1.upper() in debiles
    d2 = c2.upper() in debiles
    return d1 or d2  # al menos una débil forma diptongo con la siguiente


def silabear_es(palabra):
    """
    Silabeo para español. Reglas:
    - Diptongos (ue, ie, ia, etc.) se tratan como un solo núcleo (BLO-QUES, no BLO-QU-ES).
    - Una consonante entre vocales va con la siguiente sílaba (A-MA, no AM-A).
    - Dos consonantes entre vocales: CH, LL, RR o grupos (GR, BR...) van juntas a la siguiente;
      si no, la primera va como coda (car-ta).
    - Al final, consonantes finales van en la última sílaba.
    """
    s = (palabra or "").strip().upper()
    if not s:
        return []
    vocales = "AEIOUÁÉÍÓÚ"
    digrafos = ("CH", "LL", "RR")
    grupos_onset = ("GR", "GL", "BR", "BL", "PR", "PL", "TR", "DR", "CR", "CL", "FR", "FL")

    def es_vocal(c):
        return c in vocales

    def es_consonante(c):
        return c.isalpha() and not es_vocal(c)

    idx_voc = [i for i, c in enumerate(s) if es_vocal(c)]
    if not idx_voc:
        return [s] if s else []

    # Agrupar vocales en núcleos (diptongos/triptongos como una sola unidad)
    nucleos = []
    i0 = idx_voc[0]
    fin_nucleo = i0 + 1
    for k in range(1, len(idx_voc)):
        idx = idx_voc[k]
        if idx == fin_nucleo and _forman_diptongo(s[fin_nucleo - 1], s[idx]):
            fin_nucleo = idx + 1
        else:
            nucleos.append((i0, fin_nucleo))
            i0 = idx
            fin_nucleo = idx + 1
    nucleos.append((i0, fin_nucleo))

    silabas = []
    inicio = 0
    for _n_start, n_end in nucleos:
        fin = n_end
        if fin < len(s) and es_consonante(s[fin]):
            if fin + 1 >= len(s):
                fin += 1
            elif fin + 1 < len(s) and es_vocal(s[fin + 1]):
                pass
            elif fin + 2 <= len(s) and s[fin:fin + 2] in digrafos:
                pass
            elif fin + 2 <= len(s) and s[fin:fin + 2] in grupos_onset:
                pass
            else:
                fin += 1
        silabas.append(s[inicio:fin])
        inicio = fin
    return silabas

def _autoplay_audio_bytes(audio_bytes, mime="audio/mpeg"):
    b64 = base64.b64encode(audio_bytes).decode("ascii")
    components.html(
        f"""
        <audio id="lc-audio" autoplay>
          <source src="data:{mime};base64,{b64}" type="{mime}">
        </audio>
        <script>
          const a = document.getElementById("lc-audio");
          try {{
            a.volume = 1.0;
            const p = a.play();
            if (p && p.catch) p.catch(() => {{}});
          }} catch (e) {{}}
        </script>
        <style>
          audio {{ display: none; }}
        </style>
        """,
        height=0,
    )


def render_palabra_karaoke_felicitacion(palabra, unique_id="karaoke_feliz"):
    """
    Muestra la palabra con efecto karaoke (sílabas resaltadas una a una), como en las tarjetas del álbum.
    Usa forma con acentos (palabra_para_display). Usar después del mensaje «¡Muy bien!» en la pantalla de acierto.
    """
    p = (palabra or "").strip()
    if not p:
        return
    p = palabra_para_display(p) or p
    silabas = segmentar_palabra(p)
    if not silabas:
        silabas = [palabra.strip()]
    silabas_escaped = [
        s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        for s in silabas
    ]
    spans_html = "".join(
        f'<span class="lc-silaba-feliz" data-i="{i}">{silabas_escaped[i]}</span>'
        for i in range(len(silabas_escaped))
    )
    silabas_js = json.dumps(silabas)
    uid_safe = (unique_id or "k").replace("-", "_")[:32]
    components.html(
        f"""
        <style>
          .feliz-karaoke-panel {{ display: flex; flex-wrap: wrap; gap: 6px 12px; justify-content: center; padding: 16px; min-height: 60px; align-items: center; }}
          .lc-silaba-feliz {{ font-size: 2rem; font-weight: 800; color: #333; padding: 10px 14px; border-radius: 10px; transition: all 0.25s ease; }}
          .lc-silaba-feliz.karaoke-on {{ background: linear-gradient(135deg, #fff59d 0%, #ffeb3b 100%); color: #1a1a2e; transform: scale(1.12); box-shadow: 0 2px 12px rgba(255,235,59,0.6); }}
        </style>
        <div id="panel-{uid_safe}" class="feliz-karaoke-panel">
          {spans_html}
        </div>
        <script>
          (function() {{
            var panel = document.getElementById("panel-{uid_safe}");
            if (!panel) return;
            var spans = panel.querySelectorAll(".lc-silaba-feliz");
            var idx = 0;
            function quitarHighlight() {{ for (var i = 0; i < spans.length; i++) spans[i].classList.remove("karaoke-on"); }}
            function siguiente() {{
              quitarHighlight();
              if (idx < spans.length) {{ spans[idx].classList.add("karaoke-on"); idx++; }}
            }}
            siguiente();
            var interval = setInterval(function() {{
              if (idx >= spans.length) {{ clearInterval(interval); return; }}
              siguiente();
            }}, 450);
          }})();
        </script>
        """,
        height=100,
    )


def render_frase_karaoke(frase, audio_path=None, unique_id="frase_k"):
    """
    Muestra una frase con efecto karaoke (palabra por palabra resaltada).
    Si se pasa audio_path, se reproduce ese audio; si no, se usa TTS del navegador.
    """
    frase = (frase or "").strip()
    if not frase:
        return
    palabras = [p.strip() for p in frase.split() if p.strip()]
    if not palabras:
        return
    palabras_escaped = [
        p.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        for p in palabras
    ]
    palabras_js = json.dumps(palabras)
    spans_html = "".join(
        f'<span class="lc-palabra-frase" data-i="{i}">{palabras_escaped[i]}</span>'
        for i in range(len(palabras_escaped))
    )
    uid_safe = (unique_id or "f").replace("-", "_")[:32]
    # Autoplay: si hay audio_path, inyectar reproductor base64
    audio_html = ""
    if audio_path and os.path.exists(audio_path):
        try:
            with open(audio_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            audio_html = f"""
            <audio id="lc-frase-audio-{uid_safe}" autoplay>
              <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
            </audio>
            <script>
              (function() {{
                var a = document.getElementById("lc-frase-audio-{uid_safe}");
                if (a) {{ a.volume = 1.0; try {{ a.play(); }} catch(e) {{}} }}
              }})();
            </script>
            """
        except Exception:
            pass
    # Si no hay audio pregenerado, usar TTS del navegador
    if not audio_html:
        frase_js = json.dumps(frase)
        audio_html = f"""
        <script>
          try {{
            var text = {frase_js};
            window.speechSynthesis.cancel();
            var u = new SpeechSynthesisUtterance(text);
            u.lang = "es-ES";
            var voices = window.speechSynthesis.getVoices();
            var esFemale = voices.find(function(v) {{ return v.lang.indexOf("es") === 0 && /mujer|female|woman|helena|sabina|natalia|google español/i.test(v.name); }});
            var esAny = voices.find(function(v) {{ return v.lang.indexOf("es") === 0; }});
            if (esFemale) u.voice = esFemale; else if (esAny) u.voice = esAny;
            window.speechSynthesis.speak(u);
          }} catch (e) {{}}
        </script>
        """
    components.html(
        f"""
        <style>
          .frase-karaoke-panel {{ display: flex; flex-wrap: wrap; gap: 6px 12px; justify-content: center; padding: 16px; min-height: 50px; align-items: center; }}
          .lc-palabra-frase {{ font-size: 1.35rem; font-weight: 700; color: #333; padding: 8px 12px; border-radius: 10px; transition: all 0.25s ease; }}
          .lc-palabra-frase.karaoke-on {{ background: linear-gradient(135deg, #fff59d 0%, #ffeb3b 100%); color: #1a1a2e; transform: scale(1.08); box-shadow: 0 2px 10px rgba(255,235,59,0.5); }}
          audio {{ display: none; }}
        </style>
        {audio_html}
        <div id="panel-frase-{uid_safe}" class="frase-karaoke-panel">
          {spans_html}
        </div>
        <script>
          (function() {{
            var panel = document.getElementById("panel-frase-{uid_safe}");
            if (!panel) return;
            var spans = panel.querySelectorAll(".lc-palabra-frase");
            var idx = 0;
            function quitarHighlight() {{ for (var i = 0; i < spans.length; i++) spans[i].classList.remove("karaoke-on"); }}
            function siguiente() {{
              quitarHighlight();
              if (idx < spans.length) {{ spans[idx].classList.add("karaoke-on"); idx++; }}
            }}
            siguiente();
            var interval = setInterval(function() {{
              if (idx >= spans.length) {{ clearInterval(interval); return; }}
              siguiente();
            }}, 500);
          }})();
        </script>
        """,
        height=80,
    )


# Posiciones 1-based en matriz 3x3 para las 5 sílabas: (1,1), (1,3), (2,2), (3,1), (3,3)
SILABAS_MATRIZ_3X3_POSICIONES = [(1, 1), (1, 3), (2, 2), (3, 1), (3, 3)]


def render_silabas_matriz_9x9(silabas_list, color_hex="#4A90E2", unique_id="matriz9", altura_minima=260):
    """
    Muestra una matriz 3x3 con las 5 sílabas en (1,1), (1,3), (2,2), (3,1), (3,3).
    La matriz usa la misma altura que el bloque de la letra (aprovecha el espacio).
    Cada sílaba es clickeable: al tocar se resalta y se reproduce por TTS.
    """
    if not silabas_list or len(silabas_list) < 5:
        return
    posiciones = SILABAS_MATRIZ_3X3_POSICIONES[:5]
    silabas = (silabas_list + ["", "", "", "", ""])[:5]
    uid_safe = (unique_id or "m").replace("-", "_")[:24]
    # Construir 9 celdas (3x3); las que están en posiciones tienen la sílaba
    celdas = []
    for row in range(3):
        for col in range(3):
            idx = next((i for i, (r, c) in enumerate(posiciones) if (row, col) == (r - 1, c - 1)), None)
            if idx is not None and idx < len(silabas):
                sil = silabas[idx].replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                celdas.append(f'<div class="lc-celda lc-celda-sil" data-silaba="{sil}" data-idx="{idx}">{sil}</div>')
            else:
                celdas.append('<div class="lc-celda"></div>')
    celdas_html = "\n".join(celdas)
    silabas_js = json.dumps(silabas)
    h = max(260, int(altura_minima))
    components.html(
        f"""
        <style>
          .lc-matriz-3-wrapper {{ min-height: {h}px; display: flex; align-items: stretch; justify-content: center; }}
          .lc-matriz-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);
            gap: 6px; width: 100%; max-width: 280px; height: {h}px; margin: 0 auto; }}
          .lc-celda {{ min-width: 0; min-height: 0; display: flex; align-items: center; justify-content: center;
            background: #f0f0f0; border-radius: 10px; font-size: 1rem; }}
          .lc-celda-sil {{
            font-size: 1.5rem; font-weight: 800; color: white; background: {color_hex};
            cursor: pointer; user-select: none; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
          }}
          .lc-celda-sil:hover {{ transform: scale(1.08); opacity: 0.95; }}
          .lc-celda-sil.karaoke-on {{
            background: linear-gradient(135deg, #fff59d 0%, #ffeb3b 100%);
            color: #1a1a2e; transform: scale(1.12);
            box-shadow: 0 2px 10px rgba(255,235,59,0.6);
          }}
        </style>
        <div class="lc-matriz-3-wrapper">
          <div id="matriz-{uid_safe}" class="lc-matriz-3">
            {celdas_html}
          </div>
        </div>
        <script>
          (function() {{
            var panel = document.getElementById("matriz-{uid_safe}");
            if (!panel) return;
            var silabas = {silabas_js};
            var cells = panel.querySelectorAll(".lc-celda-sil");
            function speak(s) {{
              try {{
                window.speechSynthesis.cancel();
                var u = new SpeechSynthesisUtterance(s);
                u.lang = "es-ES";
                var voices = window.speechSynthesis.getVoices();
                var esF = voices.filter(function(v) {{ return v.lang.indexOf("es") === 0 && /mujer|female|woman|helena|sabina|natalia|google español/i.test(v.name); }})[0];
                var esA = voices.filter(function(v) {{ return v.lang.indexOf("es") === 0; }})[0];
                if (esF) u.voice = esF; else if (esA) u.voice = esA;
                window.speechSynthesis.speak(u);
              }} catch (e) {{}}
            }}
            function quitar() {{ for (var i = 0; i < cells.length; i++) cells[i].classList.remove("karaoke-on"); }}
            for (var i = 0; i < cells.length; i++) {{
              (function(idx) {{
                cells[idx].addEventListener("click", function() {{
                  quitar();
                  cells[idx].classList.add("karaoke-on");
                  speak(silabas[idx]);
                  setTimeout(quitar, 700);
                }});
              }})(i);
            }}
          }})();
        </script>
        """,
        height=h + 10,
    )


def render_silabas_karaoke(silabas_list, color_hex="#4A90E2", unique_id="silabas"):
    """
    Muestra las sílabas (Ma, Me, Mi, Mo, Mu, etc.) como botones clickeables.
    Al hacer clic en una sílaba: se resalta con efecto karaoke y se reproduce por TTS.
    El efecto se ve sobre la misma fila de sílabas.
    """
    if not silabas_list:
        return
    silabas_escaped = [
        s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        for s in silabas_list
    ]
    uid_safe = (unique_id or "s").replace("-", "_")[:24]
    # Un span clickeable por sílaba; al hacer clic se habla y se resalta
    items_js = json.dumps(silabas_list)
    spans_html = "".join(
        f'<span class="lc-silaba-btn" data-silaba="{silabas_escaped[i]}" data-i="{i}">'
        f'{silabas_escaped[i]}</span>'
        for i in range(len(silabas_escaped))
    )
    color_js = json.dumps(color_hex or "#4A90E2")
    components.html(
        f"""
        <style>
          .lc-silabas-row {{ display: flex; flex-wrap: wrap; gap: 10px 14px; justify-content: center; padding: 12px 8px; align-items: center; }}
          .lc-silaba-btn {{
            font-size: 1.8rem; font-weight: 800; color: white;
            background: {color_hex};
            padding: 0.6rem 1.2rem; border-radius: 14px;
            cursor: pointer; user-select: none;
            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
          }}
          .lc-silaba-btn:hover {{ transform: scale(1.05); opacity: 0.95; }}
          .lc-silaba-btn.karaoke-on {{
            background: linear-gradient(135deg, #fff59d 0%, #ffeb3b 100%);
            color: #1a1a2e; transform: scale(1.12);
            box-shadow: 0 2px 12px rgba(255,235,59,0.6);
          }}
        </style>
        <div id="panel-silabas-{uid_safe}" class="lc-silabas-row">
          {spans_html}
        </div>
        <script>
          (function() {{
            var panel = document.getElementById("panel-silabas-{uid_safe}");
            if (!panel) return;
            var items = {items_js};
            var spans = panel.querySelectorAll(".lc-silaba-btn");
            function speak(silaba) {{
              try {{
                window.speechSynthesis.cancel();
                var u = new SpeechSynthesisUtterance(silaba);
                u.lang = "es-ES";
                var voices = window.speechSynthesis.getVoices();
                var esFemale = voices.filter(function(v) {{ return v.lang.indexOf("es") === 0 && /mujer|female|woman|helena|sabina|natalia|google español/i.test(v.name); }})[0];
                var esAny = voices.filter(function(v) {{ return v.lang.indexOf("es") === 0; }})[0];
                if (esFemale) u.voice = esFemale; else if (esAny) u.voice = esAny;
                window.speechSynthesis.speak(u);
              }} catch (e) {{}}
            }}
            function quitarHighlight() {{ for (var i = 0; i < spans.length; i++) spans[i].classList.remove("karaoke-on"); }}
            for (var i = 0; i < spans.length; i++) {{
              (function(idx) {{
                spans[idx].addEventListener("click", function() {{
                  quitarHighlight();
                  spans[idx].classList.add("karaoke-on");
                  speak(items[idx]);
                  setTimeout(function() {{ quitarHighlight(); }}, 800);
                }});
              }})(i);
            }}
            if (window.speechSynthesis.getVoices().length === 0) {{
              window.speechSynthesis.onvoiceschanged = function() {{ }};
            }}
          }})();
        </script>
        """,
        height=70,
    )


def _speak_browser_tts(texto):
    """Reproduce el texto con la síntesis del navegador usando voz femenina en español cuando exista."""
    texto_js = json.dumps(texto or "")
    components.html(
        f"""
        <script>
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
        </script>
        """,
        height=0,
    )


def render_karaoke(palabra_segmentada, audio_path=None, texto_original=None):
    """
    Muestra la palabra y permite resaltar sílaba por sílaba.
    """
    st.write("---")
    cols = st.columns(len(palabra_segmentada))
    
    # Estado para controlar qué sílaba está activa
    if 'silaba_activa' not in st.session_state:
        st.session_state.silaba_activa = -1

    # Renderizar las sílabas
    for i, silaba in enumerate(palabra_segmentada):
        with cols[i]:
            estilo = "syllable-highlight" if st.session_state.silaba_activa == i else "syllable-normal"
            st.markdown(f'<div class="{estilo}">{silaba}</div>', unsafe_allow_html=True)

    # Reproducir audio al hacer clic, sin mostrar reproductor
    if st.button("🔊 Escuchar"):
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            _autoplay_audio_bytes(audio_bytes, mime="audio/mpeg")
        else:
            texto_tts = texto_original or "".join(palabra_segmentada)
            _speak_browser_tts(texto_tts)

def render_selector_silaba(silabas_opciones, silaba_correcta, titulo="¿Con qué sílaba empieza?"):
    """
    Componente de evaluación: Ignacio debe elegir la sílaba correcta.
    """
    st.subheader(titulo)
    cols = st.columns(len(silabas_opciones))
    
    for i, opcion in enumerate(silabas_opciones):
        if cols[i].button(opcion, key=f"btn_{opcion}"):
            if opcion == silaba_correcta:
                st.balloons()
                return True
            else:
                st.error("¡Casi! Intenta otra vez")
                return False
    return None