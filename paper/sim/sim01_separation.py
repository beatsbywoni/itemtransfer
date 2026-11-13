"""S1. Separation of the criteria: what does each of the three criteria respond to?

Base design: four families (one held out, three for training), 48 items and 40 participants per family, true
slope -0.5 logits per SD of the measure, item residual SD 0.5, participant SD 0.8, intercept 1.
"""
import sys
import time

import numpy as np
import pandas as pd

from simcore import RESULTS, analyse, families, generate, large_sample_targets, run_study, summarise

STUDY, SEED, N_BOOT = "sim01", 2601, 500
PROXIES = {"x": ("driver",),
           "proxy_train": ("corr", 0.7),   # correlated with x in the training families, not in the held-out family
           "proxy_heldout": ("corr", 0.0),  # the reverse
           "proxy_both": ("corr", 0.7),
           "x_null": ("null",)}
PROXIES_HELD = {"x": ("driver",), "proxy_train": ("corr", 0.0), "proxy_heldout": ("corr", 0.7),
                "proxy_both": ("corr", 0.7), "x_null": ("null",)}


def cells():
    c = {}
    c["common"] = dict(fams=families(4, measures=PROXIES, held=dict(measures=PROXIES_HELD)), n_rep=2000,
                       label="common slope; proxies and null measure", ratio=1.0, train_slope=-0.5)
    for ratio in (-1.0, 0.0, 0.25, 0.5, 2.0):
        c[f"ratio_{ratio:g}"] = dict(fams=families(4, held=dict(slope=-0.5 * ratio)), ratio=ratio, train_slope=-0.5,
                                     label=f"held-out slope = {ratio:g} x training slope")
    for ts in (0.0, -0.05, -0.125, -0.25):
        fams = families(4, slope=ts, held=dict(slope=-0.5))
        c[f"weak_{abs(ts):g}"] = dict(fams=fams, ratio=np.nan, train_slope=ts,
                                      label=f"training slope {ts:g}, held-out slope -0.5")
    for k, cid in enumerate(c):
        c[cid]["seed"] = k
    return c


def one_rep(cell, rng):
    fams = cell["fams"]
    return analyse(generate(fams, rng), list(fams[0].measures), rng, n_boot=N_BOOT)


def summary(df, cs):
    rows, trows = [], []
    for cid, cell in cs.items():
        tg = large_sample_targets(cell["fams"], seed=cell["seed"]).assign(cell=cid)
        trows.append(tg)
        for m, g in df[df["cell"] == cid].groupby("measure", sort=False):
            t = tg[tg["measure"] == m].iloc[0].to_dict()
            undefined = abs(t["train_slope"]) < 0.01  # large-sample training slope is zero: no target for the ratio
            s = summarise(g, t, null=undefined)
            for st in ("train_slope", "heldout_slope", "ordering", "calibration_slope", "logloss_reduction"):
                s["target_" + st] = np.nan if (undefined and st in ("calibration_slope", "ordering")) else t[st]
            # the calibration slope where the weak-training flag is raised and where it is not
            weak = (g["train_slope_lo"] <= 0) & (g["train_slope_hi"] >= 0)
            for name, sub in (("flagged", g[weak]), ("unflagged", g[~weak])):
                cs_ = sub["calibration_slope"]
                s[f"cal_{name}_n"] = len(sub)
                s[f"cal_{name}_median"] = cs_.median() if len(sub) else np.nan
                s[f"cal_{name}_q05"], s[f"cal_{name}_q95"] = (np.percentile(cs_, [5, 95]) if len(sub) else (np.nan,) * 2)
                s[f"cal_{name}_abs_gt5"] = float((cs_.abs() > 5).mean()) if len(sub) else np.nan
            s["cal_abs_gt5"] = float((g["calibration_slope"].abs() > 5).mean())
            s["cal_negative"] = float((g["calibration_slope"] < 0).mean())
            rows.append(dict(cell=cid, label=cell["label"], measure=m, **s))
    pd.concat(trows).to_csv(RESULTS / f"{STUDY}_targets.csv", index=False)
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / f"{STUDY}_summary.csv", index=False)
    return out


if __name__ == "__main__":
    pilot = "--pilot" in sys.argv
    cs = cells()
    if pilot:
        STUDY += "_pilot"
        for c in cs.values():
            c["n_rep"] = 20
    t0 = time.time()
    df = run_study(STUDY, one_rep, cs, n_rep=1000, chunk_size=20 if pilot else 100, study_seed=SEED)
    out = summary(df, cs)
    cols = ["cell", "measure", "n_rep", "train_slope_mean", "ordering_mean", "target_ordering", "calibration_slope_median",
            "target_calibration_slope", "logloss_reduction_mean", "target_logloss_reduction", "weak_rate", "cal_excl0",
            "cal_coverage", "ll_pos", "ll_neg", "ord_pos"]
    print(out[cols].round(3).to_string())
    print(f"{time.time() - t0:.0f} s")
