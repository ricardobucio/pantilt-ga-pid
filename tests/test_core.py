import numpy as np
from pantilt import config as C
from pantilt.plant import ServoAxis
from pantilt.pid import PID, PanTiltController
from pantilt.sim import make_scenarios, evaluate
from pantilt.fitness import fitness

cfg = C.load()

def test_servo_limits_and_rate():
    s = ServoAxis(0.05, 0.04, 100, [-20, 20])
    for _ in range(3): s.step(90, 0.01)
    assert s.theta == 0.0               # retardo puro: aún no se mueve
    for _ in range(200): s.step(90, 0.01)
    assert abs(s.theta - 20) < 1e-6     # límite de ángulo

def test_pid_antiwindup():
    p = PID(0.0, 10.0, 0.0, 5.0)
    for _ in range(1000): p.update(100, 0.01)
    assert p.i <= 5.0 and p.u == 5.0

def test_lost_returns_to_center():
    c = PanTiltController([0.05, 0, 0, 0.05, 0, 0], cfg["pid"])
    c.step((200, 100), 0.03)
    for _ in range(200): u = c.step(None, 0.03)
    assert abs(u[0]) < 1e-6 and abs(u[1]) < 1e-6

def test_baseline_fitness_is_one_and_deterministic():
    sc = make_scenarios(cfg["sim"])
    b1 = evaluate(cfg["manual_gains"], cfg, sc); b2 = evaluate(cfg["manual_gains"], cfg, sc)
    assert b1 == b2
    assert abs(fitness(b1, b1, cfg["fitness_weights"]) - 1.0) < 1e-9
