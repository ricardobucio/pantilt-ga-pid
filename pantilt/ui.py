"""Estilos y página de inicio (inspirada en un sitio limpio tipo landing)."""
import os, glob, json, html
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button, input, label { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; height: 0; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 5rem; }
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"], [data-testid="stExpandSidebarButton"] { display: none !important; }
/* barra de navegación superior */
.st-key-ptnav { position: sticky; top: 0; z-index: 999; background: #fff; border-bottom: 1px solid #ececf1; padding: .35rem 0; margin-bottom: 2.5rem; }
.st-key-ptnav [data-testid="stHorizontalBlock"] { align-items: center; gap: .2rem; }
.st-key-ptnav .pt-brand { font-weight: 700; font-size: 1.05rem; color: #0b0b0f; white-space: nowrap; }
.st-key-ptnav .pt-brand span { color: #4338ca; }
.st-key-ptnav .stButton button { background: transparent !important; border: none !important; box-shadow: none !important;
  color: #3f3f46 !important; font-weight: 500; padding: .35rem .6rem; border-radius: 10px; width: 100%; white-space: nowrap; }
.st-key-ptnav .stButton button:hover { color: #0b0b0f !important; background: #f4f4f6 !important; }
.st-key-ptnav .stButton button[kind="primary"] { color: #4338ca !important; background: #eef0ff !important; font-weight: 600; }
.st-key-ptnav .stButton button p { font-size: .9rem; white-space: nowrap; overflow: visible; text-overflow: clip; }
.st-key-ptnav .stButton button { padding: .35rem .3rem !important; }
/* acento morado en sliders */
div[data-baseweb="slider"] div[role="slider"] { background-color: #4338ca !important; border-color: #4338ca !important; }
h1, h2, h3 { letter-spacing: -0.02em; font-weight: 700 !important; }
.stButton button, .stDownloadButton button { border-radius: 999px; padding: .5rem 1.3rem; font-weight: 600; border: 1px solid #e5e5ea; }
.stButton button[kind="primary"] { background: #4338ca; border-color: #4338ca; color: #fff; }
.stButton button[kind="primary"]:hover { background: #4a3bd9; border-color: #4a3bd9; }
[data-testid="stImage"] img { border-radius: 14px; }
[data-testid="stDataFrame"], [data-testid="stExpander"] { border-radius: 14px; overflow: hidden; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px !important; }
.pt-nav { display:flex; justify-content:space-between; align-items:center; margin-bottom: 3.5rem; }
.pt-logo { font-weight:700; font-size:1.05rem; } .pt-logo span { color:#4338ca; }
.pt-pills { display:flex; gap:.4rem; } .pt-pill { background:#f3f3f6; border-radius:999px; padding:.3rem .8rem; font-size:.82rem; color:#444; }
.pt-hero { text-align:center; margin: 1rem auto 1.6rem; max-width: 860px; }
.pt-hero h1 { font-size: clamp(2.6rem, 6vw, 4rem); line-height:1.05; font-weight:800 !important; color:#000; letter-spacing:-.045em; margin:0 0 1.2rem; }
.pt-hero p { font-size:1.2rem; color:#18181b; line-height:1.55; margin:0 auto; max-width: 720px; }
.pt-hero p.gray { color:#71717a; margin-top:.2rem; }
.st-key-ptcta .stButton button { background:#4338ca !important; border-color:#4338ca !important; color:#fff !important; padding:.7rem 1.6rem; font-size:1rem; }
.st-key-ptcta .stButton button:hover { background:#3730a3 !important; }
.st-key-ptcta2 .stButton button { background:#fff !important; color:#18181b !important; border:1px solid #e4e4e7 !important; padding:.7rem 1.6rem; }
.pt-section { display:grid; grid-template-columns: 1fr 1.15fr; gap: 3.5rem; align-items:center; margin: 6.5rem 0; }
.pt-section.rev .pt-text { order: 2; }
.pt-text h2 { font-size: 2rem; margin: 0 0 .9rem; color:#0b0b0f; }
.pt-text p, .pt-text li { color:#55555f; font-size:1.02rem; line-height:1.65; }
.pt-text b { color:#111; }
.pt-card { border-radius: 26px; padding: 2.4rem; }
.g-green { background: linear-gradient(135deg,#b8f5a3 0%,#f4f08a 55%,#ffe27a 100%); }
.g-pink { background: linear-gradient(135deg,#ffb3c7 0%,#ff7a88 55%,#ff9a6a 100%); }
.g-blue { background: linear-gradient(135deg,#a9d4ff 0%,#7aa8ff 50%,#9b8cff 100%); }
.g-violet { background: linear-gradient(135deg,#e2d6ff 0%,#c3b4ff 50%,#ffc7ef 100%); }
.pt-inner { background:#fff; border-radius:18px; padding:1.4rem 1.5rem; box-shadow: 0 10px 30px rgba(0,0,0,.08); }
.pt-inner h4 { margin:0 0 .6rem; font-size:.95rem; color:#111; }
.pt-inner .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.86rem; color:#333; }
.pt-row { display:flex; justify-content:space-between; padding:.45rem 0; border-bottom:1px solid #f0f0f3; font-size:.92rem; }
.pt-row:last-child { border-bottom:none; } .pt-row span:last-child { color:#4338ca; font-weight:600; }
.pt-steps { display:flex; flex-direction:column; gap:.5rem; }
.pt-step { display:flex; gap:.75rem; align-items:flex-start; font-size:.9rem; color:#333; }
.pt-step .n { flex:0 0 26px; height:26px; border-radius:999px; background:#4338ca; color:#fff; font-weight:700; font-size:.8rem; display:flex; align-items:center; justify-content:center; }
.pt-big { font-size:2.6rem; font-weight:800; color:#0b0b0f; letter-spacing:-.03em; }
.pt-muted { color:#8a8a94; font-size:.85rem; }
.pt-page-title { font-size:2.2rem; font-weight:800; letter-spacing:-.03em; margin:.2rem 0 .3rem; }
.pt-page-sub { color:#6b6b76; font-size:1.05rem; margin-bottom:1.8rem; }
@media (max-width: 820px) { .pt-section { grid-template-columns: 1fr; gap: 1.6rem; } .pt-section.rev .pt-text { order: 0; } }
</style>
"""

def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)

def page_title(title, subtitle=""):
    st.markdown(f'<div class="pt-page-title">{title}</div><div class="pt-page-sub">{subtitle}</div>', unsafe_allow_html=True)

def _section(text_html, card_html, grad, rev=False):
    st.markdown(f'<div class="pt-section {"rev" if rev else ""}"><div class="pt-text">{text_html}</div>'
                f'<div class="pt-card {grad}">{card_html}</div></div>', unsafe_allow_html=True)

def best_ga(res_dir):
    """Corrida del AG con menor J entre las guardadas (datos reales de results/)."""
    best = None
    for f in glob.glob(os.path.join(res_dir, "*_ga", "best_gains.json")):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        if best is None or r["best_fitness"] < best[1]["best_fitness"]:
            best = (os.path.dirname(f), r)
    return best

GA_SVG = """
<svg viewBox="0 0 520 200" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="Inter,system-ui,sans-serif">
 <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#4338ca"/></marker></defs>
 <g font-size="12" font-weight="600" fill="#111" text-anchor="middle">
  <rect x="10" y="20" width="110" height="44" rx="22" fill="#efeaff"/><text x="65" y="47">Población</text>
  <rect x="140" y="20" width="110" height="44" rx="22" fill="#efeaff"/><text x="195" y="47">Evaluar (J)</text>
  <rect x="270" y="20" width="110" height="44" rx="22" fill="#efeaff"/><text x="325" y="47">Torneo</text>
  <rect x="400" y="20" width="110" height="44" rx="22" fill="#efeaff"/><text x="455" y="47">Cruza</text>
  <rect x="400" y="130" width="110" height="44" rx="22" fill="#efeaff"/><text x="455" y="157">Mutación</text>
  <rect x="270" y="130" width="110" height="44" rx="22" fill="#efeaff"/><text x="325" y="157">Elitismo</text>
  <rect x="140" y="130" width="110" height="44" rx="22" fill="#4338ca"/><text x="195" y="157" fill="#fff">Nueva generación</text>
 </g>
 <g stroke="#4338ca" stroke-width="2" fill="none" marker-end="url(#a)">
  <path d="M120 42 H136"/><path d="M250 42 H266"/><path d="M380 42 H396"/><path d="M455 64 V126"/>
  <path d="M400 152 H384"/><path d="M270 152 H254"/><path d="M140 152 C 60 152, 60 100, 65 68"/>
 </g>
 <text x="60" y="110" font-size="11" fill="#8a8a94" text-anchor="middle">repetir</text>
</svg>"""

def top_nav(pages, current, go):
    """Barra superior: marca a la izquierda y enlaces (botones) centrados; la página activa se resalta."""
    with st.container(key="ptnav"):
        cols = st.columns([1.6] + [0.6 + 0.07 * len(p) for p in pages] + [0.2], gap="small")
        cols[0].markdown('<div class="pt-brand">pan-tilt <span>AG</span> · PID</div>', unsafe_allow_html=True)
        for c, p in zip(cols[1:], pages):
            c.button(p, key=f"nav_{p}", type="primary" if p == current else "secondary",
                     on_click=go, args=(p,), use_container_width=True)

def render_home(res_dir, go_ga, go_live=None):
    st.markdown('<div class="pt-hero"><h1>Una cámara que mantiene<br>la pelota en el centro</h1>'
                '<p>Una computadora ve una pelota de color y mueve la cámara para que quede siempre al centro de la imagen.</p>'
                '<p class="gray">Por ahora la cámara de la Mac hace de pan-tilt virtual; después la moverán dos servos reales con un ESP32.</p>'
                '</div>', unsafe_allow_html=True)
    _, c1, c2, _ = st.columns([1.2, 1, 1, 1.2])
    with c1.container(key="ptcta"):
        st.button("Optimizar con el AG  →", type="primary", use_container_width=True, on_click=go_ga, key="cta")
    if go_live:
        with c2.container(key="ptcta2"):
            st.button("Seguimiento en vivo", use_container_width=True, on_click=go_live, key="cta_live")

    _section("<h2>El problema</h2><p>Para mover la cámara usamos un <b>controlador PID</b>. En cada instante mide el "
             "<b>error</b>: cuántos píxeles está la pelota fuera del centro. Con eso calcula cuánto girar sumando tres partes:</p>"
             "<ul><li><b>P (proporcional):</b> corrige según el error actual.</li>"
             "<li><b>I (integral):</b> corrige según el error acumulado en el tiempo.</li>"
             "<li><b>D (derivativo):</b> corrige según qué tan rápido cambia el error.</li></ul>"
             "<p>Cada parte tiene un número (ganancia) y hay dos ejes, horizontal y vertical: <b>6 números</b>. "
             "Si son muy bajos, la cámara llega tarde; si son muy altos, se pasa y tiembla. Ajustarlos a mano es lento y depende de la intuición.</p>",
             '<div class="pt-inner"><h4>Las 6 ganancias</h4><div class="mono">'
             '<div class="pt-row"><span>Eje X (pan)</span><span>Kp · Ki · Kd</span></div>'
             '<div class="pt-row"><span>Eje Y (tilt)</span><span>Kp · Ki · Kd</span></div>'
             '<div class="pt-row"><span>giro = Kp·e + Ki·∫e + Kd·de/dt</span><span>por eje</span></div></div></div>', "g-green")

    _section("<h2>¿Qué es un algoritmo genético?</h2><p>Es un método de búsqueda inspirado en la evolución:</p>"
             '<div class="pt-steps">'
             + "".join(f'<div class="pt-step"><div class="n">{i}</div><div>{t}</div></div>' for i, t in enumerate([
                 "<b>Población:</b> se crean muchos juegos de 6 ganancias (candidatos).",
                 "<b>Evaluación:</b> cada candidato controla la cámara en los <i>mismos</i> escenarios simulados y recibe una calificación J.",
                 "<b>Selección por torneo:</b> se toman 3 al azar y gana el de mejor J; así se eligen los padres.",
                 "<b>Cruza:</b> se mezclan los números de dos padres para crear un hijo.",
                 "<b>Mutación:</b> se cambian algunos números un poco al azar para explorar.",
                 "<b>Elitismo:</b> los 2 mejores pasan intactos a la siguiente generación.",
                 "<b>Repetir</b> por varias generaciones hasta que deja de mejorar."], 1)) + "</div>",
             f'<div class="pt-inner">{GA_SVG}</div>', "g-pink", rev=True)

    _section("<h2>¿Por qué usarlo aquí?</h2><p>El sistema tiene retrasos, límites de velocidad, ruido en la detección y "
             "momentos en que la pelota se pierde. Con todo eso no hay una fórmula sencilla para las mejores ganancias. "
             "El algoritmo genético no necesita esa fórmula: solo prueba, compara y se queda con lo que funciona mejor. "
             "Además, como todos los candidatos se prueban en los mismos escenarios con la misma semilla, la comparación es justa y repetible.</p>",
             '<div class="pt-inner"><h4>Escenarios de prueba (idénticos para todos)</h4>'
             '<div class="pt-row"><span>Escalones</span><span>saltos bruscos</span></div>'
             '<div class="pt-row"><span>Senoidal</span><span>vaivén suave</span></div>'
             '<div class="pt-row"><span>Caminatas aleatorias ×2</span><span>sembradas</span></div>'
             '<div class="pt-row"><span>Ruido, retraso y pérdidas</span><span>incluidos</span></div></div>', "g-blue")

    _section("<h2>Cómo leer los resultados</h2>"
             "<ul><li><b>J (aptitud):</b> el PID manual vale 1.0 y <b>menor es mejor</b>. J = 0.93 significa ≈7 % mejor en conjunto.</li>"
             "<li><b>RMSE / IAE:</b> error en píxeles (típico y acumulado). Menor = la pelota está más centrada.</li>"
             "<li><b>Variación del comando:</b> cuánto se mueven los servos en total. Menor = movimiento más suave y menos desgaste.</li>"
             "<li><b>Oscilaciones:</b> veces que el error cambia de lado. Muchas = la cámara tiembla.</li>"
             "<li><b>Cuadros sin objetivo:</b> fracción del tiempo con la pelota perdida.</li>"
             "<li><b>Gráfica de convergencia:</b> la línea del mejor baja y se estabiliza; la media se acerca al mejor. Bueno = baja y se aplana; malo = no baja de 1.0.</li>"
             "<li><b>Comparación:</b> error contra tiempo, manual vs AG: bueno = curva del AG más cerca de 0 y sin vibrar.</li></ul>"
             "<p class='pt-muted'>Estos son resultados de <b>simulación</b> hasta validarlos en el hardware real.</p>",
             _results_card(res_dir), "g-violet", rev=True)

    b = best_ga(res_dir)
    if b and os.path.exists(os.path.join(b[0], "convergence.png")):
        c = st.columns([1, 3, 1])[1]
        c.image(os.path.join(b[0], "convergence.png"), caption=f"Convergencia real de {os.path.basename(b[0])}: mejor y media de J por generación")

    _section("<h2>Cómo usar la app</h2><p>Sigue este orden desde la barra de arriba.</p>",
             '<div class="pt-inner"><div class="pt-steps">' + "".join(
                 f'<div class="pt-step"><div class="n">{i}</div><div><b>{a}</b> — {b}</div></div>' for i, (a, b) in enumerate([
                     ("Calibrar color", "ajusta los rangos HSV hasta que solo la pelota se vea blanca en la máscara y guarda."),
                     ("Seguimiento en vivo", "prueba el PID manual con la cámara."),
                     ("Algoritmo genético", "optimiza las 6 ganancias en simulación."),
                     ("Comparar", "manual vs optimizado en los mismos escenarios."),
                     ("Resultados", "revisa CSV, gráficas e historial de corridas.")], 1)) + "</div></div>", "g-green")

def _results_card(res_dir):
    b = best_ga(res_dir)
    if not b:
        return '<div class="pt-inner"><h4>Resultados reales</h4><p class="pt-muted">Aún no hay corridas del AG. Ejecuta una en la página "Algoritmo genético".</p></div>'
    d, r = b; g = r["best_gains"]; names = ["Kp_x", "Ki_x", "Kd_x", "Kp_y", "Ki_y", "Kd_y"]
    rows = "".join(f'<div class="pt-row"><span>{n}</span><span>{v:.4f}</span></div>' for n, v in zip(names, g))
    imp = (1 - r["best_fitness"]) * 100
    return (f'<div class="pt-inner"><h4>Mejor corrida guardada</h4><div class="pt-big">J = {r["best_fitness"]:.4f}</div>'
            f'<div class="pt-muted">{imp:+.1f} % vs manual · {len(r["history"])} generaciones · {html.escape(os.path.basename(d))}</div>'
            f'<div class="mono" style="margin-top:.8rem">{rows}</div></div>')
