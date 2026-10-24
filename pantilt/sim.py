"""Simulación offline: trayectorias sintéticas sembradas, ruido, latencia y pérdidas de detección."""
from collections import deque
import numpy as np
from .plant import VirtualPlant
from .pid import PanTiltController

def make_scenarios(sc):
    """Lista de escenarios deterministas (misma lista para todos los candidatos)."""
    T, dt = sc["duration"], sc["dt"]
    n = int(T / dt)
    t = np.arange(n) * dt
    out = []
    # 1) escalones
    x = np.where(t < 0.5, 0, np.where(t < 4.0, 150, -120)).astype(float)
    y = np.where(t < 0.5, 0, np.where(t < 4.0, 60, -50)).astype(float)
    out.append(("escalones", x, y))
    # 2) senoidal
    out.append(("senoidal", 180 * np.sin(2 * np.pi * 0.3 * t), 60 * np.sin(2 * np.pi * 0.45 * t)))
    # 3) caminatas aleatorias sembradas
    for k in range(sc["n_random_walk"]):
        r = np.random.default_rng(sc["seed"] + k)
        v = np.zeros(2); p = np.zeros(2); xs, ys = [], []
        for _ in range(n):
            v = 0.95 * v + r.normal(0, 25, 2)
            p = np.clip(p + v * dt, [-300, -150], [300, 150])
            xs.append(p[0]); ys.append(p[1])
        out.append((f"caminata{k}", np.array(xs), np.array(ys)))
    return out

def run_episode(gains, cfg, scenario, seed=0):
    sc, cam = cfg["sim"], cfg["camera"]
    name, tx, ty = scenario
    rng = np.random.default_rng(sc["seed"] * 1000 + seed)
    plant = VirtualPlant(cfg["plant"]); ctrl = PanTiltController(gains, cfg["pid"])
    lat = deque([None] * sc["latency_frames"])
    hw, hh = cam["crop_w"] / 2, cam["crop_h"] / 2
    rows = []; t = 0.0
    for i in range(len(tx)):
        dt = sc["dt"] + rng.uniform(-sc["dt_jitter"], sc["dt_jitter"])
        t += dt
        ox, oy = plant.offset_px()
        ex, ey = tx[i] - ox, ty[i] - oy                 # error real (px)
        visible = abs(ex) < hw and abs(ey) < hh
        meas = None
        if visible and rng.random() >= sc["dropout_p"]:
            meas = (ex + rng.normal(0, sc["noise_px"]), ey + rng.normal(0, sc["noise_px"]))
        lat.append(meas); meas_d = lat.popleft()          # latencia de detección
        u = ctrl.step(meas_d, dt)
        plant.command(u[0], u[1], dt)
        rows.append((t, dt, tx[i], ty[i], ox, oy, ex, ey, u[0], u[1], meas_d is not None))
    return np.array(rows, dtype=float)

COLS = ["t", "dt", "tx", "ty", "view_x", "view_y", "ex", "ey", "u_pan", "u_tilt", "detected"]

def metrics(tr, band):
    t, dt, ex, ey, ux, uy, det = tr[:, 0], tr[:, 1], tr[:, 6], tr[:, 7], tr[:, 8], tr[:, 9], tr[:, 10]
    e = np.abs(ex) + np.abs(ey)
    def zc(s):  # cruces por cero con histéresis de 3 px
        sg = np.sign(np.where(np.abs(s) > 3, s, 0)); sg = sg[sg != 0]
        return int(np.sum(sg[1:] != sg[:-1]))
    return {
        "iae": float(np.sum(e * dt)),
        "itae": float(np.sum(t * e * dt)),
        "settling": float(np.sum(dt[e > band])),           # tiempo fuera de banda (s)
        "oscillation": float(zc(ex) + zc(ey)),
        "du": float(np.sum(np.abs(np.diff(ux))) + np.sum(np.abs(np.diff(uy)))),
        "lost": float(1 - det.mean()),
        "rmse_px": float(np.sqrt(np.mean(ex ** 2 + ey ** 2))),
    }

def evaluate(gains, cfg, scenarios=None):
    scenarios = scenarios or make_scenarios(cfg["sim"])
    res = []
    for k, s in enumerate(scenarios):
        m = metrics(run_episode(gains, cfg, s, seed=k), cfg["sim"]["settle_band_px"])
        if not np.all(np.isfinite(list(m.values()))):
            m = {kk: 1e6 for kk in m}
        res.append(m)
    return res
