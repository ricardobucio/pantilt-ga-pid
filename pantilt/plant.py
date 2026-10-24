"""Planta: interfaz común para el pan-tilt virtual y el real (ESP32 por serial)."""
from collections import deque
import numpy as np

class Plant:
    """Interfaz. command(pan_deg, tilt_deg, dt) -> (pan_real, tilt_real) en grados."""
    def reset(self): ...
    def command(self, pan_deg, tilt_deg, dt): raise NotImplementedError
    def close(self): ...

class ServoAxis:
    """Servo simulado: retardo puro + primer orden (tau) + límite de velocidad + límites de ángulo."""
    def __init__(self, tau, dead_time, max_rate, limits):
        self.tau, self.dead, self.rate, self.lim = tau, dead_time, max_rate, limits
        self.reset()
    def reset(self):
        self.theta = 0.0; self.t = 0.0; self.buf = deque([(0.0, 0.0)])
    def step(self, u, dt):
        u = float(np.clip(u, *self.lim))
        self.t += dt
        self.buf.append((self.t, u))
        # comando vigente = el más reciente con antigüedad >= dead_time
        ud = self.buf[0][1]
        while len(self.buf) > 1 and self.buf[1][0] <= self.t - self.dead:
            self.buf.popleft(); ud = self.buf[0][1]
        if self.buf[0][0] <= self.t - self.dead:
            ud = self.buf[0][1]
        vel = (ud - self.theta) / max(self.tau, 1e-4)
        vel = float(np.clip(vel, -self.rate, self.rate))
        self.theta = float(np.clip(self.theta + vel * dt, *self.lim))
        return self.theta

class VirtualPlant(Plant):
    def __init__(self, pc):
        self.pan = ServoAxis(pc["tau"], pc["dead_time"], pc["max_rate_dps"], pc["pan_limits"])
        self.tilt = ServoAxis(pc["tau"], pc["dead_time"], pc["max_rate_dps"], pc["tilt_limits"])
        self.k = pc["px_per_deg"]
    def reset(self):
        self.pan.reset(); self.tilt.reset()
    def command(self, pan_deg, tilt_deg, dt):
        return self.pan.step(pan_deg, dt), self.tilt.step(tilt_deg, dt)
    def offset_px(self):
        """Desplazamiento del centro del recorte respecto al centro del cuadro completo."""
        return self.pan.theta * self.k, self.tilt.theta * self.k

class SerialPlant(Plant):
    """STUB para el hardware real: ESP32 por USB-serial.
    Protocolo propuesto (texto): 'P<pan_deg>,T<tilt_deg>\\n' con 90° = centro del servo.
    El firmware aplica watchdog de 300 ms (vuelve al centro si no recibe mensajes)."""
    def __init__(self, port="/dev/cu.usbserial-0001", baud=115200):
        import serial  # pyserial
        self.ser = serial.Serial(port, baud, timeout=0)
        self.pan = self.tilt = 0.0
    def command(self, pan_deg, tilt_deg, dt):
        self.ser.write(f"P{90 + pan_deg:.1f},T{90 + tilt_deg:.1f}\n".encode())
        # Sin retroalimentación de posición: se asume el comando (o se lee eco del ESP32).
        self.pan, self.tilt = pan_deg, tilt_deg
        return pan_deg, tilt_deg
    def close(self):
        self.ser.close()
