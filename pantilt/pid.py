"""PID por eje: dt real, saturación, anti-windup por clamping, derivada sobre medición filtrada."""
import numpy as np

class PID:
    def __init__(self, kp, ki, kd, out_limit, d_alpha=0.3):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.lim, self.alpha = out_limit, d_alpha
        self.reset()
    def reset(self):
        self.i = 0.0; self.prev_meas = None; self.d = 0.0; self.u = 0.0
    def update(self, error, dt, meas=None):
        """error = setpoint - medición. meas = medición (para derivada). Si None, meas = -error."""
        meas = -error if meas is None else meas
        if self.prev_meas is None:
            self.prev_meas = meas
        d_raw = -(meas - self.prev_meas) / max(dt, 1e-4)      # derivada sobre medición
        self.d = self.alpha * d_raw + (1 - self.alpha) * self.d  # filtro paso-bajas (EMA)
        self.prev_meas = meas
        i_new = self.i + self.ki * error * dt
        u = self.kp * error + i_new + self.kd * self.d
        u_sat = float(np.clip(u, -self.lim, self.lim))
        # clamping: solo integra si no satura o si integrar reduce la saturación
        if u == u_sat or np.sign(error) != np.sign(u):
            self.i = float(np.clip(i_new, -self.lim, self.lim))
        self.u = u_sat
        return u_sat

class PanTiltController:
    """Dos PID + comportamiento con objetivo perdido (mantener y luego regresar al centro)."""
    def __init__(self, gains, pc):
        g = list(gains)
        self.x = PID(g[0], g[1], g[2], pc["out_limit_deg"], pc["d_filter_alpha"])
        self.y = PID(g[3], g[4], g[5], pc["out_limit_deg"], pc["d_filter_alpha"])
        self.hold, self.ret = pc["lost_hold_s"], pc["lost_return_rate_dps"]
        self.lost_t = 0.0; self.u = [0.0, 0.0]
    def reset(self):
        self.x.reset(); self.y.reset(); self.lost_t = 0.0; self.u = [0.0, 0.0]
    def step(self, err, dt):
        """err = (ex, ey) en píxeles o None si no hay detección. Devuelve (pan, tilt) en grados."""
        if err is None:
            self.lost_t += dt
            if self.lost_t > self.hold:  # regresar al centro con rampa
                for k in range(2):
                    s = self.ret * dt
                    self.u[k] -= float(np.clip(self.u[k], -s, s))
                self.x.reset(); self.y.reset()
                self.x.i, self.y.i = self.u[0], self.u[1]  # arranque sin salto
            return tuple(self.u)
        self.lost_t = 0.0
        self.u = [self.x.update(err[0], dt), self.y.update(err[1], dt)]
        return tuple(self.u)
