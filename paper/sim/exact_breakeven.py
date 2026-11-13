"""Exact break-even point of the prediction criterion (added after review).

The article gives a second-order approximation: the gain in log-likelihood from the transferred predictor is
proportional to (2c - 1), where c is the calibration slope. This script computes the exact expected reduction in
log loss, with both intercepts re-estimated, for a standard normal measure and for a uniform measure, and finds the
value of c at which the reduction is zero. No simulation: numerical integration.
Writes results/exact_breakeven.csv and results/tables/exact_breakeven.md. Usage: python3 exact_breakeven.py
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import optimize
H = Path(__file__).resolve().parent
sig = lambda x: 1 / (1 + np.exp(-x))
def reduction(c, b, a0, dist):
    if dist == "normal":
        z = np.linspace(-8, 8, 40001); w = np.exp(-z ** 2 / 2)
    else:                                   # uniform on [-4, 4]
        z = np.linspace(-4, 4, 40001); w = np.ones_like(z)
    w = w / w.sum(); p = sig(a0 + c * b * z)
    def loss(a, k):
        q = np.clip(sig(a + k * b * z), 1e-300, 1 - 1e-16)
        return -np.sum(w * (p * np.log(q) + (1 - p) * np.log(1 - q)))
    l1 = optimize.minimize_scalar(lambda a: loss(a, 1)).fun
    l0 = optimize.minimize_scalar(lambda a: loss(a, 0)).fun
    return (l0 - l1) / l0
rows = []
for dist in ("normal", "uniform"):
    for b in (0.25, 0.5, 1.0, 2.0, 3.0):
        for a0 in (0.0, 1.0, 2.0):
            cstar = optimize.brentq(lambda c: reduction(c, b, a0, dist), 0.02, 0.99)
            rows.append(dict(measure=dist, trained_slope=b, intercept=a0, break_even_c=cstar,
                             reduction_at_c_0_45=reduction(0.45, b, a0, dist), reduction_at_c_0_5=reduction(0.5, b, a0, dist),
                             reduction_at_c_1=reduction(1.0, b, a0, dist)))
d = pd.DataFrame(rows); d.to_csv(H / "results" / "exact_breakeven.csv", index=False)
lines = ["| Measure | Trained slope (logits per unit) | Intercept | Break-even calibration slope | Reduction in log loss at c = 0.5 | at c = 1 |", "|---|---|---|---|---|---|"]
for _, r in d.iterrows():
    lines.append(f"| {r.measure} | {r.trained_slope:g} | {r.intercept:g} | {r.break_even_c:.3f} | {r.reduction_at_c_0_5:.4f} | {r.reduction_at_c_1:.4f} |")
(H / "results" / "tables" / "exact_breakeven.md").write_text("\n".join(lines) + "\n")
print(d.round(4).to_string())
