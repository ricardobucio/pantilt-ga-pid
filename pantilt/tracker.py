"""Lógica de seguimiento en vivo sin GUI (la usan la CLI con cv2.imshow y Streamlit con st.image)."""
import os, json, time
import cv2, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .plant import VirtualPlant
from .pid import PanTiltController
from .vision import detect, crop
from .results import new_run, index_append, save_trace

def open_camera(cam, index=None):
    cap = cv2.VideoCapture(cam["index"] if index is None else index, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam["width"]); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam["height"])
    return cap

class LiveTracker:
    def __init__(self, cfg, gains, label="manual"):
        self.cfg, self.gains, self.label = cfg, list(gains), label
        self.plant = VirtualPlant(cfg["plant"]); self.ctrl = PanTiltController(gains, cfg["pid"])
        self.rows, self.t0, self.last, self.fps = [], None, None, 0.0
    def reset(self):
        self.plant.reset(); self.ctrl.reset()
    def step(self, fr):
        """Procesa un cuadro. Devuelve (vista anotada BGR, cuadro completo anotado BGR, máscara, info)."""
        cam = self.cfg["camera"]; H, W = fr.shape[:2]; cw, ch = cam["crop_w"], cam["crop_h"]
        now = time.time()
        if self.t0 is None: self.t0 = self.last = now - 1 / 30
        dt = now - self.last; self.last = now; t = now - self.t0
        self.fps = 0.9 * self.fps + 0.1 / max(dt, 1e-3) if self.fps else 1 / max(dt, 1e-3)
        ox, oy = self.plant.offset_px()
        view, x0, y0 = crop(fr, W / 2 + ox, H / 2 + oy, cw, ch)
        det, mask = detect(view, self.cfg["hsv"])
        err = None if det is None else (det[0] - cw / 2, det[1] - ch / 2)
        u = self.ctrl.step(err, dt); self.plant.command(u[0], u[1], dt)
        nan = np.nan
        self.rows.append((t, dt, nan if det is None else det[0] + x0 - W / 2, nan if det is None else det[1] + y0 - H / 2,
                          ox, oy, nan if err is None else err[0], nan if err is None else err[1], u[0], u[1], det is not None))
        full = fr.copy(); cv2.rectangle(full, (x0, y0), (x0 + cw, y0 + ch), (0, 255, 255), 3)
        v = view.copy(); cv2.drawMarker(v, (cw // 2, ch // 2), (255, 255, 255), cv2.MARKER_CROSS, 30, 2)
        if det:
            cv2.circle(v, (int(det[0]), int(det[1])), 10, (0, 0, 255), 2)
            cv2.line(v, (cw // 2, ch // 2), (int(det[0]), int(det[1])), (0, 0, 255), 1)
        g = self.gains
        txt = [f"{self.label}  fps {self.fps:.1f}", f"err {err[0]:+.0f},{err[1]:+.0f}px" if err else "objetivo perdido",
               f"pan {self.plant.pan.theta:+.1f} tilt {self.plant.tilt.theta:+.1f} deg",
               "Kx " + " ".join(f"{x:.3g}" for x in g[:3]), "Ky " + " ".join(f"{x:.3g}" for x in g[3:])]
        for i, s in enumerate(txt):
            cv2.putText(v, s, (8, 22 + 20 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
        return v, full, mask, {"t": t, "err": err, "fps": self.fps}
    def save(self):
        """Guarda trace.csv, error.png, summary.json y agrega fila a results/index.csv."""
        if not self.rows: return None, None
        tr = np.array(self.rows, dtype=float); d = new_run("live_" + self.label)
        save_trace(os.path.join(d, "trace.csv"), tr)
        e = tr[:, 6:8]; ok = ~np.isnan(e[:, 0])
        s = {"gains": self.gains, "frames": len(tr), "duration_s": float(tr[-1, 0]),
             "fps_mean": float(1 / np.mean(tr[1:, 1])) if len(tr) > 1 else 0.0, "detected_frac": float(ok.mean()),
             "rmse_px": float(np.sqrt(np.mean(np.sum(e[ok] ** 2, 1)))) if ok.any() else None}
        json.dump(s, open(os.path.join(d, "summary.json"), "w"), indent=2)
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(tr[:, 0], tr[:, 6], label="ex (px)"); ax.plot(tr[:, 0], tr[:, 7], label="ey (px)")
        ax.set_xlabel("t (s)"); ax.set_title(f"En vivo {self.label} · RMSE {s['rmse_px']}"); ax.legend(); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(os.path.join(d, "error.png"), dpi=110); plt.close(fig)
        index_append({"run": os.path.basename(d), "kind": "live_" + self.label, "gains": json.dumps([round(x, 5) for x in self.gains]),
                      "fitness": "", "rmse_px": s["rmse_px"], "notes": f"fps={s['fps_mean']:.1f}"})
        return d, s
