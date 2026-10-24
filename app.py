"""UI local: streamlit run app.py  (la cámara se muestra con st.image; nunca cv2.imshow aquí)."""
import os, json, glob, time
import cv2, numpy as np, pandas as pd, streamlit as st
from pantilt import config as C
from pantilt.ga import run_ga
from pantilt.results import new_run, save_ga, compare, index_append, RES
from pantilt.vision import detect
from pantilt.tracker import LiveTracker, open_camera
from pantilt import ui

st.set_page_config(page_title="Pan-tilt AG + PID", layout="wide", initial_sidebar_state="collapsed")
cfg = C.load()
PAGES = ["Inicio", "Calibrar color", "Seguimiento en vivo", "Algoritmo genético", "Comparar", "Resultados"]
ui.inject_css()
if st.session_state.get("page") not in PAGES: st.session_state["page"] = "Inicio"
def _go(p): st.session_state["page"] = p
def _go_ga(): _go("Algoritmo genético")
def _go_live(): _go("Seguimiento en vivo")
ui.top_nav(PAGES, st.session_state["page"], _go)
page = st.session_state["page"]
ss = st.session_state
NAMES = ["Kp_x", "Ki_x", "Kd_x", "Kp_y", "Ki_y", "Kd_y"]

def gains_input(key, default):
    cols = st.columns(6)
    return [c.number_input(n, value=float(v), format="%.5f", key=f"{key}{n}") for c, n, v in zip(cols, NAMES, default)]

def best_runs():
    return sorted(glob.glob(os.path.join(RES, "*_ga", "best_gains.json")), reverse=True)

def rgb(bgr):
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

def cam_controls(prefix):
    c1, c2, c3 = st.columns([1, 1, 1])
    idx = c1.number_input("Índice de cámara", 0, 9, int(cfg["camera"]["index"]), key=prefix + "idx")
    if c2.button("▶ Iniciar", key=prefix + "start", type="primary"): ss[prefix + "run"] = True
    if c3.button("■ Detener", key=prefix + "stop"): ss[prefix + "run"] = False
    return int(idx), ss.get(prefix + "run", False)

if page == "Inicio":
    ui.render_home(RES, _go_ga, _go_live)

elif page == "Algoritmo genético":
    ui.page_title("Algoritmo genético", "Optimiza las 6 ganancias del PID en escenarios simulados idénticos y sembrados. J del manual = 1.0; menor es mejor.")
    g = cfg["ga"]; c1, c2, c3 = st.columns(3)
    g["pop_size"] = c1.number_input("Población", 4, 200, g["pop_size"])
    g["generations"] = c2.number_input("Generaciones máx.", 1, 500, g["generations"])
    g["seed"] = c3.number_input("Semilla", 0, 10**6, g["seed"])
    st.caption(f"Pesos de la función objetivo: {cfg['fitness_weights']}")
    if st.button("Ejecutar AG", type="primary"):
        chart = st.empty(); txt = st.empty(); hist = []
        def prog(h, b):
            hist.append(h); chart.line_chart(pd.DataFrame(hist).set_index("gen")[["best", "mean"]])
            txt.write(f"Generación {h['gen']}: mejor J = {h['best']:.4f} · ganancias {[round(x, 4) for x in b]}")
        res = run_ga(cfg, prog); d = new_run("ga"); save_ga(d, res)
        tab = compare(cfg, cfg["manual_gains"], res["best_gains"], d)
        rm = sum(r["rmse_px"] for r in tab if r["ctrl"] == "AG") / len(res["scenarios"])
        index_append({"run": os.path.basename(d), "kind": "ga", "gains": json.dumps([round(x, 5) for x in res["best_gains"]]),
                      "fitness": round(res["best_fitness"], 5), "rmse_px": round(rm, 3), "notes": f"gens={len(res['history'])}"})
        st.success(f"Listo. J = {res['best_fitness']:.4f} (manual = 1.0). Guardado en {d}")
        st.dataframe(pd.DataFrame(tab)); st.image(sorted(glob.glob(os.path.join(d, "compare_*.png"))))

elif page == "Comparar":
    ui.page_title("Comparar", "PID manual vs optimizado en los mismos escenarios sembrados.")
    runs = best_runs()
    if not runs: st.info("Primero ejecuta el AG."); st.stop()
    sel = st.selectbox("Corrida del AG", runs)
    gb = gains_input("b", json.load(open(sel))["best_gains"]); ga_ = gains_input("a", cfg["manual_gains"])
    if st.button("Comparar"):
        d = new_run("compare"); tab = pd.DataFrame(compare(cfg, ga_, gb, d))
        st.dataframe(tab); st.dataframe(tab.groupby("ctrl").mean(numeric_only=True))
        st.image(sorted(glob.glob(os.path.join(d, "compare_*.png")))); st.caption(f"Guardado en {d}")

elif page == "Calibrar color":
    ui.page_title("Calibrar color", "Ajusta los rangos HSV hasta que en la máscara solo la pelota se vea blanca, y guarda.")
    h = cfg["hsv"]; c1, c2, c3, c4 = st.columns(4)
    hr = c1.slider("H (tono)", 0, 179, (int(h["h_min"]), int(h["h_max"])))
    sr = c2.slider("S (saturación)", 0, 255, (int(h["s_min"]), int(h["s_max"])))
    vr = c3.slider("V (brillo)", 0, 255, (int(h["v_min"]), int(h["v_max"])))
    ma = c4.number_input("Área mínima (px)", 0, 100000, int(h["min_area"]))
    hsv = {"h_min": hr[0], "h_max": hr[1], "s_min": sr[0], "s_max": sr[1], "v_min": vr[0], "v_max": vr[1], "min_area": ma}
    if st.button("💾 Guardar"):
        C.save_user("hsv", hsv); st.success(f"Guardado en config/user.json: {hsv}")
    idx, running = cam_controls("cal")
    st.caption("Mueve los sliders con la vista detenida o en marcha (cada cambio reinicia la vista).")
    col1, col2 = st.columns(2); im1, im2 = col1.empty(), col2.empty(); info = st.empty()
    if running:
        cap = open_camera(cfg["camera"], idx)
        try:
            if not cap.isOpened():
                st.error("No se pudo abrir la cámara (¿permiso de cámara para Terminal/Cursor?)."); ss["calrun"] = False
            while ss.get("calrun"):
                ok, fr = cap.read()
                if not ok:
                    st.error("No se pudo leer un cuadro de la cámara."); ss["calrun"] = False; break
                det, mask = detect(fr, hsv)
                if det: cv2.circle(fr, (int(det[0]), int(det[1])), 14, (0, 0, 255), 3)
                im1.image(rgb(cv2.resize(fr, (640, 360))), caption="cámara")
                im2.image(cv2.resize(mask, (640, 360)), caption="máscara")
                info.write(f"Detección: área {det[2]:.0f} px en ({det[0]:.0f}, {det[1]:.0f})" if det else "Sin detección")
                time.sleep(0.01)
        finally:
            cap.release()   # también corre al presionar Detener (Streamlit interrumpe el script)

elif page == "Seguimiento en vivo":
    ui.page_title("Seguimiento en vivo", "La ventana recortada (cámara virtual) se mueve con servos simulados para centrar la pelota.")
    runs = best_runs()
    opts = ["manual"] + (["mejor AG"] if runs else []) + ["personalizadas"]
    which = st.radio("Ganancias", opts, horizontal=True)
    if which == "manual": gains, label = cfg["manual_gains"], "manual"
    elif which == "mejor AG":
        sel = st.selectbox("Corrida del AG", runs); gains, label = json.load(open(sel))["best_gains"], "AG"
    else: gains, label = gains_input("c", cfg["manual_gains"]), "custom"
    st.caption("Ganancias: " + ", ".join(f"{n}={g:.4g}" for n, g in zip(NAMES, gains)))
    dur = st.number_input("Duración (s, 0 = hasta Detener)", 0, 600, 20)
    idx, running = cam_controls("live")
    col1, col2 = st.columns([3, 2]); view_ph, full_ph = col1.empty(), col2.empty()
    chart_ph, stat_ph = st.empty(), st.empty()
    if ss.get("last_live"):
        d, s = ss["last_live"]; st.success(f"Última corrida guardada en {d}: {s}")
        if os.path.exists(os.path.join(d, "error.png")): st.image(os.path.join(d, "error.png"))
    if running:
        cap = open_camera(cfg["camera"], idx); tk = LiveTracker(cfg, gains, label); n = 0
        try:
            if not cap.isOpened():
                st.error("No se pudo abrir la cámara (¿permiso de cámara para Terminal/Cursor?)."); ss["liverun"] = False
            while ss.get("liverun"):
                ok, fr = cap.read()
                if not ok:
                    st.error("No se pudo leer un cuadro de la cámara."); break
                v, full, mask, info = tk.step(fr); n += 1
                view_ph.image(rgb(v), caption="vista recortada (cámara virtual)")
                full_ph.image(rgb(cv2.resize(full, (480, 270))), caption="cuadro completo")
                if n % 5 == 0:
                    tr = np.array(tk.rows[-300:])
                    chart_ph.line_chart(pd.DataFrame({"ex (px)": tr[:, 6], "ey (px)": tr[:, 7]}, index=tr[:, 0]))
                    stat_ph.write(f"t = {info['t']:.1f} s · fps {info['fps']:.1f}")
                if dur and info["t"] >= dur: break
        finally:
            cap.release()
            res = tk.save()            # guarda aunque se presione Detener
            ss["liverun"] = False
            if res[0]: ss["last_live"] = res
        st.rerun()

else:
    ui.page_title("Resultados", "Historial de corridas guardadas en results/.")
    p = os.path.join(RES, "index.csv")
    if os.path.exists(p): st.dataframe(pd.read_csv(p))
    dirs = sorted([d for d in glob.glob(os.path.join(RES, "*")) if os.path.isdir(d)], reverse=True)
    if dirs:
        d = st.selectbox("Corrida", dirs)
        for f in sorted(glob.glob(os.path.join(d, "*.png"))): st.image(f, caption=os.path.basename(f))
        for f in sorted(glob.glob(os.path.join(d, "*.json"))): st.json(json.load(open(f)))
