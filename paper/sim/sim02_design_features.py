"""S2. Design features of the held-out family: level structure, range mismatch, reliability of item difficulty."""
import sys
import time

import numpy as np
import pandas as pd

from simcore import (RESULTS, analyse, families, generate, large_sample_targets, level_baseline, mean_se, rate,
                     restrict_range, run_study, split_half_reliability, summarise)
from itemtransfer._stats import spearman

STUDY, SEED, N_BOOT = "sim02", 2602, 500
R3 = float(np.sqrt(3))
DRIVERS = {"continuous": ("uniform", -R3, R3),                       # SD 1
           "four_levels": ("levels", [-1.342, -0.447, 0.447, 1.342], 0.1),  # SD 1
           "two_levels": ("levels", [-1.0, 1.0], 0.1)}                # SD 1
RANGES = {"same": (1.0, 4.0), "shifted": (2.0, 8.0), "wider": (1.0, 8.0)}
# slopes chosen so that the effect has SD 0.5 logits in a training family (measure uniform on 1 to 4)
# and intercepts so that the mean logit of a training family is 0.5
RELATIONS = {"linear": (("linear",), -0.577, 1.94), "log": (("log",), -1.257, 1.57),
             "saturating": (("sat", 2.0), -3.67, 3.02)}


def cells():
    c = {}
    # (a) level structure
    for size, (ni, npart) in {"base": (48, 40), "large": (96, 80)}.items():
        for truth, effect in {"graded": ("linear",), "step": ("step", 0.0)}.items():
            for dname, drv in DRIVERS.items():
                fams = families(4, n_items=ni, n_part=npart, driver=DRIVERS["continuous"], effect=effect,
                                held=dict(driver=drv))
                c[f"a_{truth}_{dname}_{size}"] = dict(part="a", fams=fams, truth=truth, heldout_measure=dname, size=size,
                                                      n_items=ni, n_part=npart, n_rep=1000 if size == "base" else 500)
    # (b) range mismatch
    for rel, (effect, slope, icpt) in RELATIONS.items():
        for rname, (lo, hi) in RANGES.items():
            fams = families(4, driver=("uniform", 1.0, 4.0), effect=effect, slope=slope, intercept=icpt,
                            measures={"x": ("driver",), "log_x": ("log",)}, held=dict(driver=("uniform", lo, hi)))
            c[f"b_{rel}_{rname}"] = dict(part="b", fams=fams, relation=rel, heldout_range=rname, low=max(lo, 1.0),
                                         high=min(hi, 4.0))
    # (c) reliability of item difficulty
    for npart in (10, 20, 40, 80):
        for isd in (0.0, 0.5, 1.0):
            c[f"c_p{npart}_sd{isd:g}"] = dict(part="c", fams=families(4, n_part=npart, item_sd=isd), n_part=npart,
                                              item_sd=isd, n_rep=2000)
    for k, cid in enumerate(c):
        c[cid]["seed"] = k
    return c




def one_rep(cell, rng):
    fams = cell["fams"]
    if cell["part"] == "a":
        data = generate(fams, rng)
        row = analyse(data, ["x"], rng, n_boot=N_BOOT)[0]
        x = data.X["H"][:, 0]
        lb = level_baseline(data, "x", rng)
        if lb["n_levels"] == 0:  # continuous measure: median split as a two-level indicator, for comparison only
            lb = level_baseline(data, "x", rng, levels=(x > np.median(x)).astype(int))
        row.update({"lev_" + k: v for k, v in lb.items()})
        return [row]
    if cell["part"] == "b":
        data = generate(fams, rng)
        rows = analyse(data, ["x", "log_x"], rng, n_boot=N_BOOT, boot_ordering=False)
        if cell["heldout_range"] != "same":
            sub = restrict_range(data, {"x": (cell["low"], cell["high"])})
            r = analyse(sub, ["x"], rng, n_boot=N_BOOT, boot_ordering=False, prefix="common_range_")[0]
            r["n_heldout_common"] = sub.n_items("H")
            rows.append(r)
        return rows
    data, truth = generate(fams, rng, return_truth=True)
    row = analyse(data, ["x"], rng, n_boot=0, prediction=False)[0]
    sign = np.sign(row["train_slope"])
    row["ordering_noise_free"] = spearman(sign * data.X["H"][:, 0], truth["H"]["p"])
    row["rel_logit"], row["rel_rank"] = split_half_reliability(data, rng=rng)
    return [row]


def summary(df, cs):
    rows, trows = [], []
    for cid, cell in cs.items():
        g_all = df[df["cell"] == cid]
        meas = list(cell["fams"][0].measures)
        tg = large_sample_targets(cell["fams"], seed=cell["seed"]).assign(cell=cid)
        if cell["part"] == "b" and cell["heldout_range"] != "same":
            t2 = large_sample_targets(cell["fams"], measures=["x"], seed=cell["seed"],
                                      limits={"x": (cell["low"], cell["high"])})
            t2["measure"] = "common_range_x"
            tg = pd.concat([tg, t2.assign(cell=cid)], ignore_index=True)
        trows.append(tg)
        for m, g in g_all.groupby("measure", sort=False):
            t = tg[tg["measure"] == m].iloc[0].to_dict()
            s = summarise(g, t)
            for st in ("train_slope", "ordering", "calibration_slope", "logloss_reduction"):
                s["target_" + st] = t[st]
            meta = {k: v for k, v in cell.items() if k not in ("fams", "seed", "n_rep")}
            if cell["part"] == "a":
                for k in ("lev_ordering_levels", "lev_logloss_measure", "lev_logloss_levels", "lev_ordering_within",
                          "lev_level_accuracy_r"):
                    s[k + "_mean"], s[k + "_mcse"] = mean_se(g[k])
                d = g["lev_logloss_levels"] - g["lev_logloss_measure"]
                s["lev_logloss_diff_mean"], s["lev_logloss_diff_mcse"] = mean_se(d)
                s["lev_levels_better_rate"], s["lev_levels_better_mcse"], _ = rate(d > 0)
                s["lev_n_levels"] = int(g["lev_n_levels"].median())
                s["lev_detected_rate"] = float(g["lev_detected"].mean())
            if cell["part"] == "b" and "n_heldout_common" in g and g["n_heldout_common"].notna().any():
                s["n_heldout_common_mean"] = float(g["n_heldout_common"].mean())
            if cell["part"] == "c":
                ok = g["rel_rank"] > 0
                s["rel_rank_mean"], s["rel_rank_mcse"] = mean_se(g["rel_rank"])
                s["rel_logit_mean"], s["rel_logit_mcse"] = mean_se(g["rel_logit"])
                s["rel_not_positive_rate"] = float((~ok).mean())
                s["noise_free_mean"], s["noise_free_mcse"] = mean_se(g["ordering_noise_free"])
                corr = (g["ordering"] / np.sqrt(g["rel_rank"].where(ok)))
                corr_l = (g["ordering"] / np.sqrt(g["rel_logit"].where(g["rel_logit"] > 0)))
                s["corrected_rank_mean"], s["corrected_rank_mcse"] = mean_se(corr)
                s["corrected_rank_median"] = float(corr.median())
                s["corrected_logit_mean"], s["corrected_logit_mcse"] = mean_se(corr_l)
                s["corrected_gt1_rate"] = float((corr > 1).mean())
                s["attenuation_mean"] = s["ordering_mean"] / s["noise_free_mean"]
                s["sqrt_rel_rank_mean"] = float(np.sqrt(g["rel_rank"].where(ok)).mean())
                s["corrected_minus_noise_free_sd"] = float((corr - g["ordering_noise_free"]).std())
                s["observed_minus_noise_free_sd"] = float((g["ordering"] - g["ordering_noise_free"]).std())
            rows.append(dict(cell=cid, measure=m, **meta, **s))
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
    pd.set_option("display.width", 250)
    a = out[out["part"] == "a"]
    print(a[["cell", "ordering_mean", "target_ordering", "ord_pos", "calibration_slope_median", "target_calibration_slope",
             "logloss_reduction_mean", "lev_ordering_levels_mean", "lev_logloss_levels_mean", "lev_logloss_diff_mean",
             "lev_levels_better_rate", "lev_ordering_within_mean", "lev_detected_rate"]].round(3).to_string())
    b = out[out["part"] == "b"]
    print(b[["cell", "measure", "ordering_mean", "calibration_slope_median", "target_calibration_slope", "cal_incl1",
             "cal_width_median", "logloss_reduction_mean", "target_logloss_reduction"]].round(3).to_string())
    c = out[out["part"] == "c"]
    print(c[["cell", "ordering_mean", "noise_free_mean", "target_ordering", "rel_rank_mean", "rel_logit_mean",
             "corrected_rank_mean", "corrected_logit_mean", "corrected_gt1_rate", "rel_not_positive_rate"]].round(3).to_string())
    print(f"{time.time() - t0:.0f} s")
