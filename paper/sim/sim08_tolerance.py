"""S8. Error rates of the tolerance rule for the calibration slope (band 0.80 to 1.25).

"within tolerance": the whole interval lies inside the band; "outside tolerance": the whole interval lies outside;
"undetermined" otherwise. True calibration slopes are set by the held-out slope (factor times the training slope
of 0.5). Arm "held-out": only the held-out family has 48, 192 or 768 items (training families 48). Arm "all": all
four families have 192 or 768 items (true slopes 0.8, 1 and 1.25 only). 40 participants. Replications: 1,000 per
cell with 48 or 192 held-out items, 300 in all other cells (run time). Intervals: two-way 95% and 90% percentile, items-only 95%.
"""
import sys
import time

import numpy as np
import pandas as pd

from itemtransfer._stats import percentile_interval
from itemtransfer.transfer import _bootstrap_fold, _draw, _point_fold  # noqa: F401  (module functions)
from simcore import RESULTS, collect, families, generate, large_sample_targets, mean_se, rate, run_study

STUDY, SEED, N_BOOT = "sim08", 2608, 500
BAND = (0.80, 1.25)
FACTORS = (0.5, 0.8, 0.9, 1.0, 1.11, 1.25, 2.0)


def cells():
    c = {}
    for ni, n_rep in ((48, 1000), (192, 1000), (768, 300)):
        for f in FACTORS:
            c[f"heldout_i{ni}_c{f:g}"] = dict(arm="held-out", n_items=ni, factor=f, n_rep=n_rep,
                                              fams=families(4, held=dict(n_items=ni, slope=-0.5 * f)))
    for f in (0.8, 1.0, 1.25):
        c[f"all_i192_c{f:g}"] = dict(arm="all", n_items=192, factor=f, n_rep=300,
                                     fams=families(4, n_items=192, held=dict(slope=-0.5 * f)))
    for f in (0.8, 1.0, 1.25):
        c[f"all_i768_c{f:g}"] = dict(arm="all", n_items=768, factor=f, n_rep=300,
                                     fams=families(4, n_items=768, held=dict(slope=-0.5 * f)))
    for k, cid in enumerate(c):
        c[cid]["seed"] = k
    return c


def one_rep(cell, rng):
    data = generate(cell["fams"], rng)
    models = {"x": ["x"]}
    pt, _, _, _ = _point_fold(data, "H", ["H1"], models, "trials")
    row = dict(calibration_slope=pt["x"]["calibration_slope"], train_slope=pt["x"]["b"][0])
    for suffix in ("", "_io"):
        wp, wi = _draw(data, N_BOOT, rng)
        if suffix:
            wp = {k: np.ones_like(v) for k, v in wp.items()}
        bt = _bootstrap_fold(data, "H", ["H1"], models, "trials", wp, wi, rng, ordering=False, prediction=False,
                             heldout=False)["x"]["calibration_slope"]
        row["lo95" + suffix], row["hi95" + suffix] = percentile_interval(bt, 0.95)
        row["lo90" + suffix], row["hi90" + suffix] = percentile_interval(bt, 0.90)
    return [row]


def classify(lo, hi):
    within = (lo >= BAND[0]) & (hi <= BAND[1])
    outside = (hi < BAND[0]) | (lo > BAND[1])
    return within, outside


def summary(df, cs):
    rows = []
    for cid, cell in cs.items():
        g = df[df["cell"] == cid]
        t = large_sample_targets(cell["fams"], seed=cell["seed"], reps=2, items_total=60_000).iloc[0]["calibration_slope"]
        s = dict(cell=cid, arm=cell["arm"], n_items=cell["n_items"], factor=cell["factor"], n_rep=len(g), target=t,
                 median=float(g["calibration_slope"].median()))
        for name, (lo, hi) in (("two_way_95", (g["lo95"], g["hi95"])), ("two_way_90", (g["lo90"], g["hi90"])),
                               ("items_only_95", (g["lo95_io"], g["hi95_io"])), ("items_only_90", (g["lo90_io"], g["hi90_io"]))):
            w, o = classify(lo, hi)
            s[f"within_{name}"], s[f"within_{name}_mcse"], _ = rate(w)
            s[f"outside_{name}"], s[f"outside_{name}_mcse"], _ = rate(o)
            s[f"undetermined_{name}"] = 1 - s[f"within_{name}"] - s[f"outside_{name}"]
            s[f"coverage_{name}"], s[f"coverage_{name}_mcse"], _ = rate((lo <= t) & (t <= hi))
            s[f"width_{name}"] = float((hi - lo).median())
        rows.append(s)
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / f"{STUDY}_summary.csv", index=False)
    return out


def s3_classification():
    """Reading at a true calibration slope of 1 in every common-slope cell of S3, and bias and RMSE (saved raw results)."""
    raw = collect("sim03")
    raw = raw[raw["measure"] == "x"]
    summ = pd.read_csv(RESULTS / "sim03_summary.csv")
    summ = summ[summ["measure"] == "x"].set_index("cell")
    rows = []
    for cid, g in raw.groupby("cell", sort=False):
        m = summ.loc[cid]
        s = dict(cell=cid, n_fam=m["n_fam"], n_items=m["n_items"], n_part=m["n_part"], slope=m["slope"],
                 item_sd=m["item_sd"], part_sd=m["part_sd"], hetero=m["hetero"], n_rep=len(g))
        w, o = classify(g["calibration_slope_lo"], g["calibration_slope_hi"])
        s["within"], s["within_mcse"], _ = rate(w)
        s["outside"], s["outside_mcse"], _ = rate(o)
        s["undetermined"] = 1 - s["within"] - s["outside"]
        if "calibration_slope_lo_io" in g and g["calibration_slope_lo_io"].notna().any():
            w, o = classify(g["calibration_slope_lo_io"], g["calibration_slope_hi_io"])
            s["within_items_only"], s["within_items_only_mcse"], _ = rate(w)
            s["outside_items_only"], s["outside_items_only_mcse"], _ = rate(o)
        if m["hetero"] == 0:
            ct, lt = m["cal_target"], m["ll_target"]
            e = g["calibration_slope"] - ct
            s["cal_bias"], s["cal_bias_mcse"] = mean_se(e)
            s["cal_median_bias"] = float(e.median())
            s["cal_rmse"] = float(np.sqrt(np.mean(e ** 2)))
            s["cal_empirical_sd"] = float(g["calibration_slope"].std(ddof=1))
            e = g["logloss_reduction"] - lt
            s["ll_bias"], s["ll_bias_mcse"] = mean_se(e)
            s["ll_rmse"] = float(np.sqrt(np.mean(e ** 2)))
            s["ll_target"], s["cal_target"] = lt, ct
        rows.append(s)
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "sim03_classification_bias_rmse.csv", index=False)
    return out


if __name__ == "__main__":
    pilot = "--pilot" in sys.argv
    cs = cells()
    if pilot:
        STUDY += "_pilot"
        for c in cs.values():
            c["n_rep"] = 4
    t0 = time.time()
    df = run_study(STUDY, one_rep, cs, n_rep=1000, chunk_size=4 if pilot else 50, study_seed=SEED)
    out = summary(df, cs)
    pd.set_option("display.width", 300)
    print(out[["cell", "n_rep", "target", "median", "within_two_way_95", "outside_two_way_95", "within_two_way_90",
               "outside_two_way_90", "within_items_only_95", "outside_items_only_95", "width_two_way_95",
               "width_items_only_95", "coverage_two_way_95", "coverage_items_only_95"]].round(3).to_string())
    if not pilot:
        print(s3_classification().round(3).to_string())
    print(f"{time.time() - t0:.0f} s")
