"""Modo en vivo por CLI (ventanas OpenCV, hilo principal). Teclas: q salir y guardar, c recentrar, h máscara, s guardar HSV."""
import cv2, numpy as np
from . import config as C
from .vision import detect
from .tracker import LiveTracker, open_camera

def calibrate(cfg):
    cap = open_camera(cfg["camera"]); hsv = dict(cfg["hsv"]); W = "calibracion HSV"
    cv2.namedWindow(W)
    for k, mx in [("h_min", 179), ("h_max", 179), ("s_min", 255), ("s_max", 255), ("v_min", 255), ("v_max", 255), ("min_area", 5000)]:
        cv2.createTrackbar(k, W, int(hsv[k]), mx, lambda v: None)
    try:
        while True:
            ok, fr = cap.read()
            if not ok: print("No se pudo leer la cámara (¿permiso de cámara?)"); break
            for k in hsv: hsv[k] = cv2.getTrackbarPos(k, W)
            det, mask = detect(fr, hsv)
            if det: cv2.circle(fr, (int(det[0]), int(det[1])), 12, (0, 0, 255), 2)
            cv2.imshow(W, np.hstack([cv2.resize(fr, (640, 360)), cv2.cvtColor(cv2.resize(mask, (640, 360)), cv2.COLOR_GRAY2BGR)]))
            k = cv2.waitKey(1) & 0xFF
            if k == ord("s"): C.save_user("hsv", hsv); print("HSV guardado:", hsv)
            if k == ord("q"): break
    finally:
        cap.release(); cv2.destroyAllWindows()

def run_live(cfg, gains, label="manual", duration=None, headless=False):
    cap = open_camera(cfg["camera"])
    ok, fr = cap.read()
    if not ok:
        cap.release()
        raise RuntimeError("No se pudo abrir la cámara. Revisa Ajustes > Privacidad > Cámara para tu Terminal/Cursor.")
    tk = LiveTracker(cfg, gains, label); show_mask = False
    try:
        while True:
            ok, fr = cap.read()
            if not ok: break
            v, full, mask, info = tk.step(fr)
            if not headless:
                ch = v.shape[0]; small = cv2.resize(full, (int(ch * full.shape[1] / full.shape[0]), ch))
                cv2.imshow("pan-tilt virtual (q salir)", np.hstack([v, small]))
                if show_mask: cv2.imshow("mascara", mask)
                k = cv2.waitKey(1) & 0xFF
                if k == ord("q"): break
                if k == ord("c"): tk.reset()
                if k == ord("h"): show_mask = not show_mask
            if duration and info["t"] > duration: break
    finally:
        cap.release(); cv2.destroyAllWindows()
    return tk.save()
