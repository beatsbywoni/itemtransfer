"""S3. Operating characteristics of the intervals: coverage, detection rate, false-positive rate.

Base case: 4 families, 48 items and 40 participants per family, slope -0.5 logits per SD of the measure, item
residual SD 0.5, participant SD 0.8. One factor at a time, a 2 x 2 x 2 factorial (items, slope, item residual SD),
two small designs, and an arm in which the true slope differs between families.
"""
import sys
import time
from dataclasses import replace

import numpy as np
import pandas as pd

from simcore import RESULTS, analyse, expected_data, families, generate, large_sample_targets, rate, run_study, summarise
from itemtransfer.transfer import _point_fold

STUDY, SEED, N_BOOT = "sim03", 2603, 500
MS = {"x": ("driver",), "x_null": ("null",)}
BASE = dict(n_fam=4, n_items=48, n_part=40, slope=0.5, item_sd=0.5, part_sd=0.8)
LEVELS = dict(n_fam=(3, 6, 10), n_items=(24, 96, 192), n_part=(20, 80), slope=(0.25, 1.0), item_sd=(0.0, 1.0),
              part_sd=(0.0, 1.6))


def _cell(arm, po, hetero=0.0, **kw):
    d = dict(BASE, **kw)
    return dict(arm=arm, participants_only=po, hetero=hetero, **d)


def cells():
    c = {"base": _cell("base", True)}
    for factor, values in LEVELS.items():
        for v in values:
            c[f"ofat_{factor}_{v:g}"] = _cell("one factor", factor in ("item_sd", "part_sd"), **{factor: v})
    for ni in (24, 96):
        for sl in (0.25, 1.0):
            for isd in (0.0, 1.0):
                c[f"fact_i{ni}_b{sl:g}_sd{isd:g}"] = _cell("factorial", True, n_items=ni, slope=sl, item_sd=isd)
    c["small_f3_i24_p20_sd1"] = _cell("small", True, n_fam=3, n_items=24, n_part=20, item_sd=1.0)
    c["small_f3_i24_p20_sd1_b0.25"] = _cell("small", True, n_fam=3, n_items=24, n_part=20, item_sd=1.0, slope=0.25)
    for nf in (3, 10):
        for tau in (0.2, 0.4):
            c[f"hetero_f{nf}_tau{tau:g}"] = _cell("slope differs between families", False, hetero=tau, n_fam=nf)
    for k, cid in enumerate(c):
        c[cid]["seed"] = k
    return c


def fams_of(cell):
    return families(cell["n_fam"], n_items=cell["n_items"], n_part=cell["n_part"], slope=-cell["slope"],
                    item_sd=cell["item_sd"], part_sd=cell["part_sd"], measures=MS)


def one_rep(cell, rng):
    fams = fams_of(cell)
    extra = {}
    if cell["hetero"]:
        # true slope of each family: base slope times a log-normal factor; the target is specific to the draw
        fams = [replace(f, slope=f.slope * float(np.exp(rng.normal(0, cell["hetero"])))) for f in fams]
        big = expected_data([replace(f, measures={"x": ("driver",)}) for f in fams], rng, 8000 // cell["n_items"])
        pt, _, _, _ = _point_fold(big, "H", big.family_samples["H"], {"x": ["x"]}, "trials")
        extra = dict(target_rep=pt["x"]["calibration_slope"], slope_heldout=fams[0].slope,
                     slope_train_mean=float(np.mean([f.slope for f in fams[1:]])))
    rows = analyse(generate(fams, rng), ["x", "x_null"], rng, n_boot=N_BOOT, participants_only=cell["participants_only"],
                   items_only=cell["participants_only"])
    rows[0].update(extra)
    return rows


def summary(df, cs):
    rows, trows = [], []
    for cid, cell in cs.items():
        tg = large_sample_targets(fams_of(cell), seed=cell["seed"],
                                  items_total=120_000 if cell["n_fam"] <= 6 else 60_000).assign(cell=cid)
        trows.append(tg)
        for m, g in df[df["cell"] == cid].groupby("measure", sort=False):
            t = tg[tg["measure"] == m].iloc[0].to_dict()
            s = summarise(g, t, null=(m == "x_null"))
            if cell["hetero"] and m == "x":
                lo, hi, tr = g["calibration_slope_lo"], g["calibration_slope_hi"], g["target_rep"]
                s["cal_coverage"], s["cal_coverage_mcse"], _ = rate((lo <= tr) & (tr <= hi))
                s["cal_target"] = np.nan
                s["target_rep_q05"], s["target_rep_median"], s["target_rep_q95"] = np.percentile(tr, [5, 50, 95])
                s["cal_incl1_when_target_far"], s["cal_incl1_when_target_far_mcse"], s["n_target_far"] = \
                    rate(((lo <= 1) & (hi >= 1))[(tr < 0.75) | (tr > 1.33)])
                for st in ("ll_coverage", "ll_coverage_expect", "ord_coverage", "ord_coverage_expect"):
                    s[st] = np.nan  # targets of the common-slope design do not apply
            meta = {k: v for k, v in cell.items() if k not in ("seed", "n_rep")}
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
            c["n_rep"] = 10
    t0 = time.time()
    df = run_study(STUDY, one_rep, cs, n_rep=1000, chunk_size=10 if pilot else 50, study_seed=SEED)
    out = summary(df, cs)
    pd.set_option("display.width", 250)
    x = out[out["measure"] == "x"]
    print(x[["cell", "n_rep", "calibration_slope_median", "cal_coverage", "cal_coverage_po", "cal_width_median",
             "cal_width_median_po", "cal_excl0", "ll_target", "logloss_reduction_mean", "ll_coverage",
             "ll_coverage_expect", "ll_coverage_po", "ll_pos", "ll_pos_po", "ord_pos", "ord_coverage_expect"]].round(3).to_string())
    n = out[out["measure"] == "x_null"]
    print(n[["cell", "weak_rate", "cal_excl0", "cal_excl0_po", "cal_excl0_notweak", "ll_pos", "ll_pos_po", "ll_neg",
             "ord_excl0", "ord_excl0_po"]].round(3).to_string())
    print(f"{time.time() - t0:.0f} s")
