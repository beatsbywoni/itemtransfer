"""S7. Family differences that are not differences in the slope.

The analysis model has no random effects, so the calibration slope is a ratio of marginal slopes. The conditional
slope (0.5 logits per SD) is the same in all families; the held-out family differs from the training families
(participant SD 0.8, item residual SD 0.5, intercept 1) in one respect only. Large-sample calibration slopes for
all cells, and finite-sample runs (500 data sets each) for the two cells that deviate most from 1.
"""
import sys
import time

import numpy as np
import pandas as pd

from simcore import RESULTS, analyse, families, generate, large_sample_targets, mean_se, rate, run_study

STUDY, SEED, N_BOOT = "sim07", 2607, 500
BAND = (0.80, 1.25)
BASE = dict(part_sd=0.8, item_sd=0.5, intercept=1.0)
LEVELS = dict(part_sd=(0.0, 0.8, 1.6, 2.4), item_sd=(0.0, 0.5, 1.0, 1.5), intercept=(-0.5, 0.0, 1.0, 2.0, 3.0))


def all_cells():
    c = {}
    for factor, values in LEVELS.items():
        for v in values:
            c[f"{factor}_{v:g}"] = dict(factor=factor, value=v, fams=families(4, held={factor: v}))
    for k, cid in enumerate(c):
        c[cid]["seed"] = k
    return c


def approximation(cell):
    """Ratio of marginal slopes from the logistic-normal approximation, slope / sqrt(1 + 0.346 * sigma^2), with
    sigma^2 the variance of participant effects plus item residuals in each family."""
    h = dict(BASE, **{cell["factor"]: cell["value"]})
    att = lambda d: 1 / np.sqrt(1 + 0.346 * (d["part_sd"] ** 2 + d["item_sd"] ** 2))  # noqa: E731
    return att(h) / att(BASE)


def targets():
    rows = []
    for cid, cell in all_cells().items():
        t = large_sample_targets(cell["fams"], seed=cell["seed"], reps=3).iloc[0]
        cs = t["calibration_slope"]
        rows.append(dict(cell=cid, factor=cell["factor"], value=cell["value"], calibration_slope=cs,
                         calibration_slope_sd=t["calibration_slope_sd"], approximation=approximation(cell),
                         train_slope=t["train_slope"], heldout_slope=t["heldout_slope"], ordering=t["ordering"],
                         logloss_reduction=t["logloss_reduction"], outside_band=bool(cs < BAND[0] or cs > BAND[1])))
    out = pd.DataFrame(rows)
    out["difference_from_approximation"] = out["calibration_slope"] - out["approximation"]
    out.to_csv(RESULTS / f"{STUDY}_targets.csv", index=False)
    return out


def one_rep(cell, rng):
    return analyse(generate(cell["fams"], rng), ["x"], rng, n_boot=N_BOOT, boot_ordering=False)


if __name__ == "__main__":
    t0 = time.time()
    tg = targets()
    pd.set_option("display.width", 250)
    print(tg.round(3).to_string())
    extreme = tg.assign(dev=np.abs(np.log(tg["calibration_slope"]))).sort_values("dev").tail(2)["cell"].tolist()
    cs = {k: v for k, v in all_cells().items() if k in extreme}
    pilot = "--pilot" in sys.argv
    df = run_study(STUDY + ("_pilot" if pilot else ""), one_rep, cs, n_rep=20 if pilot else 500,
                   chunk_size=20 if pilot else 50, study_seed=SEED)
    rows = []
    for cid in cs:
        g = df[df["cell"] == cid]
        t = tg[tg["cell"] == cid].iloc[0]
        lo, hi = g["calibration_slope_lo"], g["calibration_slope_hi"]
        s = dict(cell=cid, n_rep=len(g), target=t["calibration_slope"], median=float(g["calibration_slope"].median()))
        s["mean"], s["mean_mcse"] = mean_se(g["calibration_slope"])
        for name, x in (("coverage_of_target", (lo <= t["calibration_slope"]) & (t["calibration_slope"] <= hi)),
                        ("includes_1", (lo <= 1) & (hi >= 1)), ("excludes_0", (lo > 0) | (hi < 0)),
                        ("within", (lo >= BAND[0]) & (hi <= BAND[1])), ("outside", (hi < BAND[0]) | (lo > BAND[1])),
                        ("logloss_above_0", g["logloss_reduction_lo"] > 0)):
            s[name], s[name + "_mcse"], _ = rate(x)
        s["undetermined"] = 1 - s["within"] - s["outside"]
        s["median_width"] = float((hi - lo).median())
        s["logloss_reduction_mean"], s["logloss_reduction_mcse"] = mean_se(g["logloss_reduction"])
        s["logloss_target"] = t["logloss_reduction"]
        rows.append(s)
    out = pd.DataFrame(rows)
    if not pilot:
        out.to_csv(RESULTS / f"{STUDY}_summary.csv", index=False)
    print(out.round(3).T.to_string())
    print(f"{time.time() - t0:.0f} s")
