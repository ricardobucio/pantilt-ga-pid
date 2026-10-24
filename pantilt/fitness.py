"""Función objetivo (minimizar). Cada métrica se normaliza por la del PID manual en el MISMO escenario.
J = media_escenarios( sum_i w_i * m_i / m_i_base ). El PID manual obtiene J = 1 por definición."""
import numpy as np
KEYS = ["itae", "iae", "settling", "oscillation", "du", "lost"]

def fitness(cand_metrics, base_metrics, weights):
    J = []
    for c, b in zip(cand_metrics, base_metrics):
        s = 0.0
        for k in KEYS:
            # piso para métricas casi cero en la base (p.ej. lost=0): evita divisiones explosivas
            floor = {"lost": 0.01, "oscillation": 1.0, "settling": 0.1}.get(k, 1e-6)
            s += weights[k] * min(c[k] / max(b[k], floor), 50.0)
        J.append(s)
    return float(np.mean(J)) / sum(weights[k] for k in KEYS)
