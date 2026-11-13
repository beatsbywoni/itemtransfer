"""Figure for the knapsack example. Reads paper/knapsack_report/*.csv and the item table of the example script.
Usage: python3 make_knapsack_figure.py   (run from any directory except the project root)
"""
import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REP = ROOT / "paper" / "knapsack_report"
spec = importlib.util.spec_from_file_location("knapsack_example", ROOT / "examples" / "knapsack.py")
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
trials, items = ex.load_knapsack(pilot=False)
tr = pd.read_csv(REP / "transfer.csv")
pred = pd.read_csv(REP / "predictions.csv")
weak = pd.read_csv(REP / "weak_training.csv")
FAM = ["Franco", "Doroc", "Lu"]
LABEL = {"instance_complexity": "Instance complexity", "typical_case_complexity": "Typical-case complexity",
         "sahni_k": "Sahni-k", "solver_effort": "Solver effort"}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
fig = plt.figure(figsize=(7.6, 6.2))
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05], hspace=0.5, wspace=0.6)

# ---- row 1: item accuracy against instance complexity, with the transferred relation
m = "instance_complexity"
for j, f in enumerate(FAM):
    ax = fig.add_subplot(gs[0, j])
    p = pred[(pred["family"] == f) & (pred["model"] == m)].merge(items[["item", m]], on="item")
    row = tr[(tr["family"] == f) & (tr["model"] == m)].iloc[0]
    other = items[items["family"] != f][m]
    ax.axvspan(other.min(), other.max(), color="0.92", zorder=0)
    ax.scatter(p[m], p["accuracy"], s=9, color="k", alpha=0.55, linewidths=0)
    x = np.linspace(0, p[m].max() * 1.03, 200)
    b = row["train_slope"]
    # intercept that reproduces the overall accuracy of the held-out sample given the trained slope
    lo, hi = -10.0, 10.0
    for _ in range(60):
        a = (lo + hi) / 2
        if np.sum(p["n_trials"] / (1 + np.exp(-(a + b * p[m])))) > p["n_correct"].sum():
            hi = a
        else:
            lo = a
    ax.plot(x, 1 / (1 + np.exp(-(a + b * x))), color="k", lw=1.2, label="trained slope")
    # slope fitted in the held-out family itself (Newton steps on the binomial likelihood)
    X = np.column_stack([np.ones(len(p)), p[m]]); beta = np.array([a, b])
    for _ in range(50):
        mu = 1 / (1 + np.exp(-X @ beta)); W = p["n_trials"].to_numpy() * mu * (1 - mu)
        beta = beta + np.linalg.solve(X.T @ (X * W[:, None]), X.T @ (p["n_correct"].to_numpy() - p["n_trials"].to_numpy() * mu))
    ax.plot(x, 1 / (1 + np.exp(-(beta[0] + beta[1] * x))), color="0.45", lw=1.2, ls="--", label="slope fitted in this family")
    ax.set_ylim(0, 1.03); ax.set_xlim(left=-0.01)
    ax.set_title(f"Held out: {f} items", fontsize=8.5)
    ax.set_xlabel("Instance complexity")
    if j == 0:
        ax.set_ylabel("Item accuracy"); ax.legend(frameon=False, fontsize=6.5, loc="lower right")
    ax.text(-0.3, 1.08, "ABC"[j], transform=ax.transAxes, fontweight="bold", fontsize=10)

# ---- row 2: the three criteria for the four measures
STATS = [("ordering", "Ordering\n(Spearman correlation)", None), ("calibration_slope", "Scale\n(calibration slope)", (-1.5, 4.2)),
         ("logloss_reduction", "Prediction\n(reduction in log loss)", None)]
mk = {"Franco": "o", "Doroc": "s", "Lu": "^"}
for j, (st, lab, lim) in enumerate(STATS):
    ax = fig.add_subplot(gs[1, j])
    for i, meas in enumerate(LABEL):
        for k, f in enumerate(FAM):
            r = tr[(tr["family"] == f) & (tr["model"] == meas)].iloc[0]
            wk = weak[(weak["family"] == f) & (weak["measure"] == meas)]["weak"].iloc[0] in (True, "yes", "True")
            xx = i + (k - 1) * 0.22
            if st == "calibration_slope" and wk:
                ax.plot(xx, lim[0] + 0.25, marker="x", color="0.5", ms=4)   # not interpretable: no value shown
                continue
            lo_, hi_ = r[st + "_lo"], r[st + "_hi"]
            if lim is not None:
                if lo_ < lim[0]:
                    ax.plot(xx, lim[0] + 0.05, marker="v", color="k", ms=3)
                if hi_ > lim[1]:
                    ax.plot(xx, lim[1] - 0.05, marker="^", color="k", ms=3)
                lo_, hi_ = max(lo_, lim[0]), min(hi_, lim[1])
            ax.plot([xx, xx], [lo_, hi_], color="k", lw=0.9)
            if lim is None or lim[0] <= r[st] <= lim[1]:
                ax.plot(xx, r[st], marker=mk[f], ms=4.5, color="k", mfc="white" if wk else "k", ls="none",
                        label=f"{f} items" if (i == 0) else None)
    ax.axhline(0, color="0.6", lw=0.7)
    if st == "calibration_slope":
        ax.axhspan(0.80, 1.25, color="0.88", zorder=0); ax.set_ylim(*lim)
    ax.set_xticks(range(4)); ax.set_xticklabels(LABEL.values(), fontsize=6.5, rotation=30, ha="right")
    ax.set_ylabel(lab)
    if j == 2:
        ax.legend(frameon=False, fontsize=6.5, title="Held-out family", title_fontsize=6.5, loc="upper right")
    ax.text(-0.3, 1.06, "DEF"[j], transform=ax.transAxes, fontweight="bold", fontsize=10)
for ext in ("png", "pdf"):
    fig.savefig(HERE / f"figure_knapsack.{ext}", dpi=300, bbox_inches="tight")
