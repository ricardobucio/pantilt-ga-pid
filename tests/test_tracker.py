import numpy as np, cv2
from pantilt import config as C
from pantilt.tracker import LiveTracker

def test_tracker_follows_synthetic_ball():
    cfg = C.load()
    cfg["hsv"] = {"h_min": 35, "h_max": 85, "s_min": 80, "s_max": 255, "v_min": 60, "v_max": 255, "min_area": 150}  # independiente de user.json
    tk = LiveTracker(cfg, cfg["manual_gains"], "test")
    import time
    for i in range(60):
        fr = np.zeros((720, 1280, 3), np.uint8)
        cv2.circle(fr, (640 + 150, 360 + 50), 25, (0, 255, 0), -1)   # verde (HSV H≈60)
        v, full, mask, info = tk.step(fr); time.sleep(0.005)
    assert v.shape[:2] == (360, 480)
    assert tk.plant.pan.theta > 0 and tk.plant.tilt.theta > 0      # se movió hacia el objetivo
