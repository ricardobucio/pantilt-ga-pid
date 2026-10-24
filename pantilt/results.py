"""Guardado de resultados: results/<timestamp>_<tipo>/ + results/index.csv"""
import os, json, csv, datetime
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .config import ROOT
from .sim import COLS, make_scenarios, run_episode, metrics
RES = os.path.join(ROOT, "results")

def new_run(kind):
    d = os.path.join(RES, datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + kind)
    os.makedirs(d, exist_ok=True); return d

def index_append(row):
    p = os.path.join(RES, "index.csv"); new = not os.path.exists(p)
    with open(p, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run", "kind", "gains", "fitness", "rmse_px", "notes"])
        if new: w.writeheader()
        w.writerow(row)

def save_trace(path, tr):
    np.savetxt(path, tr, delimiter=",", header=",".join(COLS), comments="", fmt="%.5f")

def save_ga(d, res):
    with open(os.path.join(d, "best_gains.json"), "w") as f:
        json.dump(res, f, indent=2)
    with open(os.path.join(d, "convergence.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res["history"][0])); w.writeheader(); w.writerows(res["history"])
    h = res["history"]; fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([r["gen"] for r in h], [r["best"] for r in h], label="mejor")
    ax.plot([r["gen"] for r in h], [r["mean"] for r in h], label="media")
    ax.axhline(1.0, ls="--", c="gray", label="PID manual (J=1)")
    ax.set_xlabel("generación"); ax.set_ylabel("J (menor es mejor)"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(d, "convergence.png"), dpi=120); plt.close(fig)

def compare(cfg, gains_a, gains_b, d, labels=("manual", "AG")):
    """Corre ambos juegos de ganancias en los MISMOS escenarios sembrados; guarda CSV, PNG y tabla."""
    scen = make_scenarios(cfg["sim"]); table = []
    for k, s in enumerate(scen):
        fig, axs = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
        for lab, g in zip(labels, (gains_a, gains_b)):
            tr = run_episode(g, cfg, s, seed=k)
            save_trace(os.path.join(d, f"{s[0]}_{lab}.csv"), tr)
            m = metrics(tr, cfg["sim"]["settle_band_px"]); m.update(scenario=s[0], ctrl=lab); table.append(m)
            axs[0].plot(tr[:, 0], tr[:, 6], label=f"ex {lab}"); axs[1].plot(tr[:, 0], tr[:, 7], label=f"ey {lab}")
        axs[0].set_title(f"Escenario: {s[0]}"); axs[0].set_ylabel("error x (px)"); axs[1].set_ylabel("error y (px)")
        axs[1].set_xlabel("t (s)")
        for a in axs:
            a.legend(); a.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(os.path.join(d, f"compare_{s[0]}.png"), dpi=110); plt.close(fig)
    with open(os.path.join(d, "compare_metrics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    return table
