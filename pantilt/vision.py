"""Detección por color HSV y recorte (pan-tilt virtual)."""
import cv2, numpy as np

def detect(bgr, hsv_cfg):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lo = np.array([hsv_cfg["h_min"], hsv_cfg["s_min"], hsv_cfg["v_min"]])
    hi = np.array([hsv_cfg["h_max"], hsv_cfg["s_max"], hsv_cfg["v_max"]])
    mask = cv2.inRange(hsv, lo, hi)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, mask
    c = max(cnts, key=cv2.contourArea)
    a = cv2.contourArea(c)
    if a < hsv_cfg["min_area"]:
        return None, mask
    m = cv2.moments(c)
    return (m["m10"] / m["m00"], m["m01"] / m["m00"], a), mask

def crop(frame, cx, cy, w, h):
    H, W = frame.shape[:2]
    x0 = int(np.clip(cx - w / 2, 0, W - w)); y0 = int(np.clip(cy - h / 2, 0, H - h))
    return frame[y0:y0 + h, x0:x0 + w], x0, y0
