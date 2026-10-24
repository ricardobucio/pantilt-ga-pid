"""Uso: python cli.py {sim|ga|compare|live|calibrate|camtest} [opciones]"""
import argparse, json, os, glob
import numpy as np
from pantilt import config as C
from pantilt.sim import make_scenarios, evaluate
from pantilt.fitness import fitness
from pantilt.ga import run_ga
from pantilt.results import new_run, save_ga, compare, index_append, RES

def latest_best():
    fs = sorted(glob.glob(os.path.join(RES, "*_ga", "best_gains.json")))
    if not fs: raise SystemExit("No hay corridas del AG todavía: python cli.py ga")
    return json.load(open(fs[-1]))["best_gains"], fs[-1]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd")
    ap.add_argument("--gens", type=int); ap.add_argument("--pop", type=int); ap.add_argument("--seed", type=int)
    ap.add_argument("--gains", help="6 valores separados por coma"); ap.add_argument("--duration", type=float)
    a = ap.parse_args(); cfg = C.load()
    if a.gens: cfg["ga"]["generations"] = a.gens
    if a.pop: cfg["ga"]["pop_size"] = a.pop
    if a.seed is not None: cfg["ga"]["seed"] = a.seed
    gains = [float(x) for x in a.gains.split(",")] if a.gains else None
    if a.cmd == "sim":
        g = gains or cfg["manual_gains"]; scen = make_scenarios(cfg["sim"]); m = evaluate(g, cfg, scen)
        base = evaluate(cfg["manual_gains"], cfg, scen)
        for s, mm in zip(scen, m): print(s[0], {k: round(v, 3) for k, v in mm.items()})
        print("J =", round(fitness(m, base, cfg["fitness_weights"]), 4))
    elif a.cmd == "ga":
        d = new_run("ga")
        res = run_ga(cfg, progress=lambda h, b: print(f"gen {h['gen']:3d}  mejor J={h['best']:.4f}  media={h['mean']:.4f}"))
        save_ga(d, res)
        tab = compare(cfg, cfg["manual_gains"], res["best_gains"], d)
        rm = np.mean([r["rmse_px"] for r in tab if r["ctrl"] == "AG"])
        index_append({"run": os.path.basename(d), "kind": "ga", "gains": json.dumps([round(x, 5) for x in res["best_gains"]]),
                      "fitness": round(res["best_fitness"], 5), "rmse_px": round(rm, 3), "notes": f"gens={len(res['history'])}"})
        print("Mejores ganancias:", [round(x, 5) for x in res["best_gains"]], "J =", round(res["best_fitness"], 4))
        print("Guardado en", d)
    elif a.cmd == "compare":
        g, src = (gains, "cli") if gains else latest_best(); d = new_run("compare")
        for r in compare(cfg, cfg["manual_gains"], g, d): print(r["scenario"], r["ctrl"], "RMSE", round(r["rmse_px"], 2), "IAE", round(r["iae"], 1))
        print("Guardado en", d)
    elif a.cmd in ("live", "camtest"):
        from pantilt.live import run_live
        label = "custom" if gains else "manual"
        g = gains or cfg["manual_gains"]
        d, s = run_live(cfg, g, label, duration=a.duration or (3 if a.cmd == "camtest" else None), headless=a.cmd == "camtest")
        print(s, "\nGuardado en", d)
    elif a.cmd == "live-best":
        from pantilt.live import run_live
        g, src = latest_best(); d, s = run_live(cfg, g, "AG", duration=a.duration); print(s, "\nGuardado en", d)
    elif a.cmd == "calibrate":
        from pantilt.live import calibrate; calibrate(cfg)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
