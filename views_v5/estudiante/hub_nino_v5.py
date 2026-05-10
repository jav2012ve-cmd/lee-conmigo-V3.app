import html
import os

import streamlit as st

from components.page_title import logo_markup_html
from components.styles import apply_fondo_pagina_principal_hub

from components.cards import get_image_base64
from core.curriculum_v4 import CurriculumV4
from core import gamificacion

import database.db_queries as db_queries
from database.db_queries import vocal_fase_avance
from database.db_queries_v4 import categoria_stats_ambas_actividades, stats_actividad_leccion_vocal

# Raíz del proyecto (hub: views_v3/estudiante/ → subir 3 niveles)
_PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEMO_LECCIONES_ACTIVAS = ["M", "P"]


def _resolver_ruta_archivo(path):
    """Convierte rutas relativas o guardadas desde otra cwd en ruta absoluta existente."""
    if not path or not isinstance(path, str):
        return None
    p = path.strip()
    if os.path.isfile(p):
        return os.path.normpath(p)
    rel = os.path.join(_PROJ_ROOT, p.replace("/", os.sep).lstrip("\\/"))
    if os.path.isfile(rel):
        return os.path.normpath(rel)
    return None


def _foto_hub_estudiante(id_est, nombre, avatar_path):
    """
    Misma lógica que el Salón: avatar en BD (ruta resuelta) o foto del álbum
    cuya palabra coincida con el nombre del niño (ej. IGNACIO).
    """
    r = _resolver_ruta_archivo(avatar_path)
    if r:
        return r
    album = db_queries.obtener_album_nino(id_est) or []
    nombre_upper = (nombre or "").strip().upper()
    for palabra, _cat, img_path in album:
        if (palabra or "").strip().upper() != nombre_upper:
            continue
        r = _resolver_ruta_archivo(img_path)
        if r:
            return r
    return None


def render_hub_nino_v5():
    """
    Hub V3: por ahora reusa el estilo general, pero deja el gancho
    para el nuevo gating académico (álbum primero → luego lecciones).
    """
    apply_fondo_pagina_principal_hub()
    id_est = st.session_state.get("estudiante_id")
    if id_est:
        db_queries.actualizar_ultimo_ingreso(id_est)
        # Sincronizar ciclo con trofeos en BD (p. ej. C1 completado → mostrar C2)
        st.session_state.v5_ciclo_id = gamificacion.ciclo_v4_activo(id_est)

    info = db_queries.obtener_perfil_completo_nino(id_est)
    nombre = info[2] if info and len(info) > 2 else "Explorador"
    color_fav = info[11] if info and len(info) > 11 else "#4CAF50"

    st.session_state.nombre_nino = nombre
    st.session_state.color_favorito = color_fav

    # Resumen del ciclo V3 + gating por 75% en categorías (antes del saludo para poder otorgar 3.1)
    ciclo_id = st.session_state.get("v5_ciclo_id", "C1")
    ciclo_al_inicio = ciclo_id

    def _recalcular_album_ciclo(cid):
        try:
            i = next(ii for ii, c in enumerate(CurriculumV4.CICLOS) if c["id"] == cid)
        except StopIteration:
            i = 0
        c_list = CurriculumV4.categorias_habilitadas_para_ciclo_idx(i)
        ec = []
        comp = 0
        for cat in c_list:
            ok, stats = categoria_stats_ambas_actividades(id_est, cat)
            if ok:
                comp += 1
            ec.append({"cat": cat, "ok": ok, "stats": stats})
        a_ok = (len(c_list) > 0) and (comp == len(c_list))
        return c_list, ec, a_ok

    cats, estado_cats, album_ok = _recalcular_album_ciclo(ciclo_id)
    st.session_state.v5_bloque_lecciones_habilitado = bool(album_ok)

    ciclo_tuvo_trofeo = False
    if album_ok and id_est:
        gamificacion.check_and_grant_album_ciclo_complete(id_est, ciclo_id)
        ciclo_tuvo_trofeo = gamificacion.check_and_grant_lessons_ciclo_complete(id_est, ciclo_id)
        # Tras otorgar trofeo de lecciones, avanzar ciclo en la misma visita (p. ej. C1 → C2)
        st.session_state.v5_ciclo_id = gamificacion.ciclo_v4_activo(id_est)
        ciclo_id = st.session_state.get("v5_ciclo_id", "C1")
        if ciclo_id != ciclo_al_inicio:
            cats, estado_cats, album_ok = _recalcular_album_ciclo(ciclo_id)
            st.session_state.v5_bloque_lecciones_habilitado = bool(album_ok)

    estrellas = gamificacion.get_stars(id_est)
    if ciclo_tuvo_trofeo:
        st.success("🏆 ¡Has completado las lecciones del ciclo! ¡Trofeo ganado!")

    # Cintillo: 1 fila × 4 celdas (bienvenida | foto | estrellas | acciones)
    _box = (
        f"border:2px solid {color_fav};border-radius:16px;padding:14px 16px;"
        f"background:linear-gradient(180deg,{color_fav}22 0%,#fff 70%);min-height:200px;"
    )
    c_welcome, c_photo, c_stars, c_actions = st.columns([1.35, 1, 0.95, 1.2], gap="medium")
    avatar_db = db_queries.obtener_avatar_estudiante(id_est) if id_est else None
    foto_resuelta = _foto_hub_estudiante(id_est, nombre, avatar_db) if id_est else None

    with c_welcome:
        _lg = logo_markup_html(height_px=160, margin_right=0)
        _nom_raw = (nombre or "Explorador").strip() or "Explorador"
        _nom_raw = _nom_raw.lstrip("¡").rstrip("!").strip() or "Explorador"
        _nom = html.escape(_nom_raw)
        st.markdown(
            f"""
            <div style="{_box}">
              <div style="display:grid;grid-template-columns:auto 1fr;gap:0.65rem 0.85rem;align-items:center;">
                <div style="display:flex;align-items:center;justify-content:center;min-width:0;">
                  {_lg}
                </div>
                <div style="text-align:left;min-width:11rem;max-width:100%;">
                  <p style="font-size:1.35rem;font-weight:800;color:{color_fav};margin:0 0 0.25rem 0;line-height:1.2;white-space:normal;overflow-wrap:break-word;">
                    ¡Hola, {_nom}!
                  </p>
                  <p style="font-size:0.88rem;color:#444;margin:0;line-height:1.3;">
                    V5: camino guiado por ciclos (Álbum → Lecciones).
                  </p>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_photo:
        if foto_resuelta and os.path.isfile(foto_resuelta):
            img_b64 = get_image_base64(foto_resuelta)
            ext = foto_resuelta.lower().rsplit(".", 1)[-1] if "." in foto_resuelta else "png"
            if ext in ("jpg", "jpeg"):
                mime = "image/jpeg"
            elif ext == "webp":
                mime = "image/webp"
            else:
                mime = "image/png"
            if img_b64:
                st.markdown(
                    f"""
                    <div style="{_box}display:flex;align-items:center;justify-content:center;">
                      <img src="data:{mime};base64,{img_b64}" alt=""
                           style="width:112px;height:112px;border-radius:50%;object-fit:cover;border:3px solid {color_fav};" />
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="{_box}display:flex;align-items:center;justify-content:center;">
                      <div style="width:112px;height:112px;border-radius:50%;background:#e8e8e8;
                           display:flex;align-items:center;justify-content:center;font-size:2.8rem;border:3px solid #ddd;">👤</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"""
                <div style="{_box}display:flex;align-items:center;justify-content:center;">
                  <div style="width:112px;height:112px;border-radius:50%;background:#e8e8e8;
                       display:flex;align-items:center;justify-content:center;font-size:2.8rem;border:3px solid #ddd;">
                    👤
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c_stars:
        st.markdown(
            f"""
            <div style="{_box}text-align:center;">
              <div style="font-size:2rem;line-height:1;">⭐</div>
              <div style="font-size:1.65rem;font-weight:800;color:#333;margin-top:6px;">{estrellas}</div>
              <div style="font-size:0.88rem;color:#666;">estrellas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_actions:
        # Los dos botones van dentro de la misma casilla (borde del contenedor)
        # border=True: los dos botones quedan dentro del mismo marco (cuarta casilla)
        with st.container(border=True):
            btn_album = st.button(
                "Ir al álbum",
                use_container_width=True,
                key="v5_ir_album",
                disabled=False,
                help=(
                    "Puedes entrar a tu álbum cuando quieras, aunque ya hayas completado el ciclo."
                    if album_ok
                    else "Completa todas las categorías del ciclo (75% en cada actividad)."
                ),
            )
            btn_lecciones = st.button(
                "Ir a mis lecciones",
                use_container_width=True,
                key="v5_ir_lecciones",
                disabled=not bool(album_ok),
                help=(
                    "Completa antes el álbum del ciclo (75% por categoría)."
                    if not album_ok
                    else "Lecciones del ciclo actual desbloqueadas."
                ),
            )
            btn_abecedario = st.button(
                "Abecedario (9×3)",
                use_container_width=True,
                key="v5_ir_abecedario_matriz",
                help="Matriz 9 filas × 3 columnas: karaoke y sonido extra (abecedario/ o SFX de álbum donde aplique).",
            )
        if btn_album:
            st.session_state.pagina_activa = "album_nino"
            st.rerun()
        if btn_lecciones:
            if ciclo_id == "C1" and "v5_leccion_bloque_idx" not in st.session_state:
                st.session_state["v5_leccion_bloque_idx"] = 0
            st.session_state.pagina_activa = "lecciones_nino"
            st.rerun()
        if btn_abecedario:
            st.session_state.pagina_activa = "abecedario_matriz"
            st.rerun()
    st.write("")

    bloque = [s.upper() for s in DEMO_LECCIONES_ACTIVAS]
    if album_ok:
        st.success(f"✅ **Álbum del ciclo completado**. Ya puedes pasar a lecciones: **{', '.join(bloque)}**.")
    else:
        faltan = [e["cat"] for e in estado_cats if not e["ok"]]
        prox = faltan[0] if faltan else (cats[0] if cats else "Álbum")
        st.info(
            f"Ruta del ciclo **{ciclo_id}**: completa el **Álbum** (75% de éxito por categoría) para liberar lecciones: **{', '.join(bloque)}**.\n\n"
            f"Te falta: **{prox}**."
        )

    # Botón específico: aparece en la categoría/actividad que falta
    # (en vez de un botón genérico arriba).

    with st.expander("📍 Mi Ruta (ver detalle)"):
        st.markdown(f"**Ciclo actual:** `{ciclo_id}`")
        st.markdown("**Álbum (categorías habilitadas):**")

        # Primera categoría que aún no está superada y cuál actividad falta.
        primera_pendiente = None
        for e in estado_cats:
            if not e["ok"]:
                ar = e["stats"]["ArmarPalabra"]
                et = e["stats"]["EscuchaToca"]
                if not ar["logrado"]:
                    primera_pendiente = (e["cat"], "ArmarPalabra")
                elif not et["logrado"]:
                    primera_pendiente = (e["cat"], "EscuchaToca")
                else:
                    primera_pendiente = (e["cat"], None)
                break
        for e in estado_cats:
            status = "✅" if e["ok"] else "🔄"
            ar = e["stats"]["ArmarPalabra"]
            et = e["stats"]["EscuchaToca"]
            ar_word = "Logrado" if ar["logrado"] else "En progreso"
            et_word = "Logrado" if et["logrado"] else "En progreso"
            ar_pct = int(round(ar["pct"] * 100))
            et_pct = int(round(et["pct"] * 100))
            st.write(
                f"{status} **{e['cat']}** — ArmarPalabra: {ar_pct}% ({ar_word}) · "
                f"EscuchaToca: {et_pct}% ({et_word})"
            )

            # Botón solo para la actividad que falta en la primera categoría pendiente
            if primera_pendiente and e["cat"] == primera_pendiente[0] and primera_pendiente[1]:
                actividad = primera_pendiente[1]
                if actividad == "ArmarPalabra":
                    label_btn = f"Vamos allí (ArmarPalabra: {e['cat']})"
                    if st.button(label_btn, type="primary", use_container_width=True, key=f"v5_btn_go_armar_{e['cat']}"):
                        st.session_state.v5_album_categoria_activa = e["cat"]
                        st.session_state.pagina_activa = "album_nino"
                        st.rerun()
                elif actividad == "EscuchaToca":
                    label_btn = f"Vamos allí (Escucha y Toca: {e['cat']})"
                    if st.button(label_btn, type="primary", use_container_width=True, key=f"v5_btn_go_et_{e['cat']}"):
                        # Ir directo a la actividad "Escucha y Toca"
                        st.session_state.album_actividad_categoria = e["cat"]
                        st.session_state.album_escucha_toca_activo = True
                        st.session_state.album_escucha_toca_idx = 0
                        st.session_state.pagina_activa = "album_silabas"
                        st.rerun()
        st.markdown("**Lecciones del ciclo:**")
        st.caption(
            "✅ Superada · 🔄 En progreso — **mismo criterio que el álbum**: "
            "75% sobre 6 ítems por actividad (Completar palabras y Escucha y toca en vocales; "
            "«Reconoce inicio» solo si usas el flujo clásico con esa fase)."
        )

        def _fmt_actividad(d):
            pct = int(round(float(d.get("pct", 0) or 0) * 100))
            w = "Logrado" if d.get("logrado") else "En progreso"
            return f"{pct}% ({w})"

        for item in bloque:
            letras_v = gamificacion.parse_bloque_vocales_c1(item)
            if letras_v and id_est:
                sub_ok = [vocal_fase_avance(id_est, L) == "completo" for L in letras_v]
                header_ok = all(sub_ok)
                icon_h = "✅" if header_ok else "🔄"
                st.markdown(f"{icon_h} **{item}**")
                for L in letras_v:
                    stt = stats_actividad_leccion_vocal(id_est, L)
                    ic = "✅" if vocal_fase_avance(id_est, L) == "completo" else "🔄"
                    c_comp = stt["CompletarPalabras"]
                    c_et = stt["EscuchaToca"]
                    c_ini = stt["ReconoceInicio"]
                    partes = [
                        f"Completar palabras: {_fmt_actividad(c_comp)}",
                        f"Escucha y toca: {_fmt_actividad(c_et)}",
                    ]
                    if (c_ini.get("ac", 0) + c_ini.get("er", 0)) > 0 or c_ini.get("logrado"):
                        partes.append(f"Reconoce inicio: {_fmt_actividad(c_ini)}")
                    st.write(
                        f"&nbsp;&nbsp;&nbsp;{ic} **{L}** — " + " · ".join(partes),
                        unsafe_allow_html=True,
                    )
            elif id_est:
                ok_item = gamificacion.bloque_leccion_ciclo_superada(id_est, ciclo_id, item)
                icon = "✅" if ok_item else "🔄"
                ac_d, er_d, pct_d = gamificacion.obtener_stats_directa(id_est, str(item).strip().upper())
                ok_directa = gamificacion._is_aciertos_75_y_pct(ac_d, er_d, pct_d)
                pct_i = int(round(pct_d * 100)) if (ac_d + er_d) > 0 else 0
                w = "Logrado" if ok_directa else "En progreso"
                st.write(
                    f"{icon} **{item}** — Lección (progreso directo): {pct_i}% ({w}) "
                    f"(aciertos {ac_d}, errores {er_d})"
                )
            else:
                st.write(f"🔄 **{item}**")

    with st.expander("🏅 Mis insignias"):
        badges = gamificacion.get_badges(id_est)
        if badges:
            for tipo, nivel, ref, _ in badges:
                ref_txt = f" — {ref}" if ref else ""
                nivel_txt = f" ({nivel})" if nivel else ""
                st.caption(f"• {tipo}{nivel_txt}{ref_txt}")
        else:
            st.caption("Aún no tienes insignias. ¡Completa actividades y categorías para ganarlas!")

    st.write("---")
    if st.button("🏠 Volver al Salón", use_container_width=True, key="v5_volver_salon"):
        st.session_state.pagina_activa = "salon_entrada"
        st.rerun()

