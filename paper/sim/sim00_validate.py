"""Checks that precede the simulation study.

1. The engine of the study (simcore.analyse) gives the same numbers as the public
   itemtransfer.transfer() and itemtransfer.diagnose() on the same data.
2. itemtransfer.check_intervals() on the equivalent package Design agrees with the engine.
3. Number of bootstrap resamples: how much do interval end points move between 250, 500, 1,000 and 2,000?
4. Noise of the large-sample targets.
"""
import json
import sys
import time

import numpy as np
import pandas as pd

import itemtransfer as it
from itemtransfer.simulate import _to_frames
from simcore import (RESULTS, analyse, families, generate, large_sample_targets, level_baseline, save_json, versions)

MS = {"x": ("driver",), "x_null": ("null",)}


def check_public_api(n=5):
    rows = []
    for k in range(n):
        rng = np.random.default_rng([100, k])
        fams = families(4, measures=MS, held=dict(driver=("levels", [-1.0, 1.0], 0.1)))
        data = generate(fams, rng)
        mine = analyse(data, ["x", "x_null"], np.random.default_rng(k), n_boot=0, n_splits=500)
        trials, items = _to_frames(data)
        res = it.transfer(trials, items, ["x", "x_null"], combined=False, holdout=["H"], n_boot=300, seed=k)
        diag = it.diagnose(trials, items, ["x", "x_null"], result=res, n_boot=0)
        lb = level_baseline(data, "x", np.random.default_rng(k), n_splits=500)
        dl = diag["level_baseline"].query("family == 'H' and measure == 'x'").iloc[0]
        for j, m in enumerate(["x", "x_null"]):
            pub = res.table.query("model == @m").iloc[0]
            rows.append(dict(data_set=k, measure=m,
                             d_train_slope=abs(pub["train_slope"] - mine[j]["train_slope"]),
                             d_ordering=abs(pub["ordering"] - mine[j]["ordering"]),
                             d_calibration_slope=abs(pub["calibration_slope"] - mine[j]["calibration_slope"]),
                             d_logloss_reduction=abs(pub["logloss_reduction"] - mine[j]["logloss_reduction"]),
                             d_level_logloss=abs(dl["logloss_reduction_levels"] - lb["logloss_levels"]) if m == "x" else 0,
                             d_level_ordering=abs(dl["ordering_levels"] - lb["ordering_levels"]) if m == "x" else 0))
    return pd.DataFrame(rows)


def check_check_intervals(n_sim=300, n_boot=300):
    design = it.Design(families=[it.FamilyDesign(n, 48, ("normal", 0.0, 1.0), [it.SampleDesign(n + "1", 40, intercept=1.0)])
                                 for n in ("H", "T1", "T2", "T3")],
                       slope=-0.5, participant_sd=0.8, item_sd=0.5, null_measure=True)
    chk = it.check_intervals(design, n_sim=n_sim, n_boot=n_boot, prediction=True, n_jobs=2, seed=11)
    chk = chk[chk["family"] == "H"].assign(source="itemtransfer.check_intervals")
    fams = families(4, measures=MS)
    rows = []
    for k in range(n_sim):
        rng = np.random.default_rng([101, k])
        rows += analyse(generate(fams, rng), ["x", "x_null"], rng, n_boot=n_boot, boot_ordering=False)
    df = pd.DataFrame(rows)
    out = []
    for m, g in df.groupby("measure"):
        lo, hi = g["calibration_slope_lo"], g["calibration_slope_hi"]
        out.append(dict(family="H", measure=m, source="simcore.analyse",
                        mean_estimate=g["calibration_slope"].mean(), median_estimate=g["calibration_slope"].median(),
                        coverage=np.mean((lo <= 1) & (hi >= 1)) if m == "x" else np.nan,
                        median_width=(hi - lo).median(), rate_excludes_0=np.mean((lo > 0) | (hi < 0)),
                        rate_weak_training=np.mean((g["train_slope_lo"] <= 0) & (g["train_slope_hi"] >= 0)),
                        logloss_mean=g["logloss_reduction"].mean(),
                        logloss_rate_above_0=np.mean(g["logloss_reduction_lo"] > 0), n_sim=n_sim, n_boot=n_boot))
    cols = ["source", "family", "measure", "target", "mean_estimate", "median_estimate", "coverage", "coverage_se",
            "median_width", "rate_excludes_0", "rate_weak_training", "logloss_target", "logloss_mean",
            "logloss_coverage", "logloss_rate_above_0", "n_sim", "n_boot"]
    return pd.concat([chk, pd.DataFrame(out)], ignore_index=True).reindex(columns=cols)


def bootstrap_size(n_data=200, sizes=(250, 500, 1000, 2000)):
    """Same data sets, intervals from independent bootstraps of different size, against a 4,000-resample reference."""
    fams = families(4, measures={"x": ("driver",)})
    rows = []
    for k in range(n_data):
        rng = np.random.default_rng([102, k])
        data = generate(fams, rng)
        ref = analyse(data, ["x"], np.random.default_rng([103, k]), n_boot=4000, boot_ordering=False)[0]
        for B in sizes:
            r = analyse(data, ["x"], np.random.default_rng([104, k, B]), n_boot=B, boot_ordering=False)[0]
            rows.append(dict(data_set=k, n_boot=B,
                             cal_width_ref=ref["calibration_slope_hi"] - ref["calibration_slope_lo"],
                             d_cal_lo=r["calibration_slope_lo"] - ref["calibration_slope_lo"],
                             d_cal_hi=r["calibration_slope_hi"] - ref["calibration_slope_hi"],
                             ll_width_ref=ref["logloss_reduction_hi"] - ref["logloss_reduction_lo"],
                             d_ll_lo=r["logloss_reduction_lo"] - ref["logloss_reduction_lo"],
                             d_ll_hi=r["logloss_reduction_hi"] - ref["logloss_reduction_hi"],
                             cal_covers_1=r["calibration_slope_lo"] <= 1 <= r["calibration_slope_hi"],
                             cal_covers_1_ref=ref["calibration_slope_lo"] <= 1 <= ref["calibration_slope_hi"]))
    df = pd.DataFrame(rows)
    out = []
    for B, g in df.groupby("n_boot"):
        out.append(dict(n_boot=B, n_data_sets=len(g),
                        cal_endpoint_rmsd_over_width=float(np.sqrt(np.mean(np.r_[g["d_cal_lo"], g["d_cal_hi"]] ** 2))
                                                           / g["cal_width_ref"].mean()),
                        logloss_endpoint_rmsd_over_width=float(np.sqrt(np.mean(np.r_[g["d_ll_lo"], g["d_ll_hi"]] ** 2))
                                                               / g["ll_width_ref"].mean()),
                        cal_coverage=float(g["cal_covers_1"].mean()), cal_coverage_reference=float(g["cal_covers_1_ref"].mean()),
                        coverage_decisions_changed=float((g["cal_covers_1"] != g["cal_covers_1_ref"]).mean())))
    return pd.DataFrame(out)


if __name__ == "__main__":
    quick = "--pilot" in sys.argv
    info = RESULTS / "sim00_run_info.json"
    if info.exists() and not json.loads(info.read_text())["pilot"] and "--force" not in sys.argv and not quick:
        print("sim00: results present, skipped (use --force to repeat)")
        sys.exit(0)
    t0 = time.time()
    a = check_public_api(2 if quick else 5)
    a.to_csv(RESULTS / "sim00_public_api_agreement.csv", index=False)
    print(a.drop(columns=["data_set", "measure"]).max().to_string())
    b = check_check_intervals(40 if quick else 300, 100 if quick else 300)
    b.to_csv(RESULTS / "sim00_check_intervals_agreement.csv", index=False)
    print(b.round(3).T.to_string())
    c = bootstrap_size(20 if quick else 150)
    c.to_csv(RESULTS / "sim00_bootstrap_size.csv", index=False)
    print(c.round(4).to_string())
    d = large_sample_targets(families(4, measures=MS), reps=5)
    d.to_csv(RESULTS / "sim00_target_noise.csv", index=False)
    print(d.round(5).T.to_string())
    save_json("sim00_run_info.json", dict(seconds=round(time.time() - t0, 1), pilot=quick, versions=versions()))
