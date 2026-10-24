"""AG de codificación real: torneo k, cruza BLX-alpha, mutación gaussiana con sigma decreciente, elitismo."""
import numpy as np
from .sim import make_scenarios, evaluate
from .fitness import fitness

def run_ga(cfg, progress=None):
    g = cfg["ga"]; rng = np.random.default_rng(g["seed"])
    lo, hi = np.array(g["bounds"]).T; span = hi - lo
    scen = make_scenarios(cfg["sim"])
    base = evaluate(cfg["manual_gains"], cfg, scen)
    f = lambda x: fitness(evaluate(x, cfg, scen), base, cfg["fitness_weights"])
    pop = lo + rng.random((g["pop_size"], 6)) * span
    pop[0] = np.clip(cfg["manual_gains"], lo, hi)        # siembra con el manual
    fit = np.array([f(x) for x in pop])
    hist, best, stall, sigma = [], fit.min(), 0, g["sigma0"]
    for gen in range(g["generations"]):
        order = np.argsort(fit)
        new = [pop[i].copy() for i in order[:g["elitism"]]]
        def tour():
            idx = rng.choice(len(pop), g["tournament_k"], replace=False)
            return pop[idx[np.argmin(fit[idx])]]
        while len(new) < g["pop_size"]:
            p1, p2 = tour(), tour()
            a = g["blx_alpha"]; mn, mx = np.minimum(p1, p2), np.maximum(p1, p2); d = mx - mn
            child = rng.uniform(mn - a * d, mx + a * d)
            mask = rng.random(6) < g["mut_p"]
            child = child + mask * rng.normal(0, sigma, 6) * span
            new.append(np.clip(child, lo, hi))
        pop = np.array(new)
        fit = np.array([fit[order[i]] if i < g["elitism"] else f(pop[i]) for i in range(len(pop))])
        sigma *= g["sigma_decay"]
        b = fit.min()
        hist.append({"gen": gen, "best": float(b), "mean": float(fit.mean()),
                     "std": float(fit.std()), "sigma": float(sigma)})
        if progress: progress(hist[-1], pop[np.argmin(fit)])
        stall = 0 if b < best - 1e-6 else stall + 1
        best = min(best, b)
        if stall >= g["stagnation"]:
            break
    i = int(np.argmin(fit))
    return {"best_gains": pop[i].tolist(), "best_fitness": float(fit[i]), "history": hist,
            "baseline_metrics": base, "best_metrics": evaluate(pop[i], cfg, scen),
            "scenarios": [s[0] for s in scen]}
