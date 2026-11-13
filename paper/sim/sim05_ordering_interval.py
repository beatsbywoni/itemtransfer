"""S5 (added on request). Bootstrap interval of the ordering criterion: percentile or basic (reflected)?

The two-way bootstrap resamples participants and items. Resampled participants add noise to the item accuracies
and resampled items add ties, so the resampled ordering correlations are centred closer to zero than the estimate.
This script extends the range of S3 to many items, where the shift is large relative to the width of the interval.
Base case otherwise (4 families, slope 0.5, item residual SD 0.5, participant SD 0.8). No prediction criterion.
For comparison, the interval of a bootstrap that resamples items only is computed as well (suffix _io).
"""
import sys
import time

import numpy as np
import pandas as pd

from simcore import RESULTS, analyse, families, generate, large_sample_targets, run_study, summarise

STUDY, SEED, N_BOOT = "sim05", 2605, 500
MS = {"x": ("driver",), "x_null": ("null",)}


def cells():
    c = {}
    for ni in (48, 192, 768, 3072):
        c[f"i{ni}_p40"] = dict(n_items=ni, n_part=40)
    for npart in (20, 80):
        c[f"i768_p{npart}"] = dict(n_items=768, n_part=npart)
    c["i768_p40_sd0"] = dict(n_items=768, n_part=40, item_sd=0.0)
    c["i768_p40_slope1"] = dict(n_items=768, n_part=40, slope=1.0)
    for k, cid in enumerate(c):
        ni = c[cid]["n_items"]
        n_rep = 500 if ni < 768 else (300 if cid == "i768_p40" else 200)
        c[cid] = dict(dict(item_sd=0.5, slope=0.5), **c[cid], seed=k, n_rep=n_rep)
    return c


def fams_of(cell):
    return families(4, n_items=cell["n_items"], n_part=cell["n_part"], slope=-cell["slope"], item_sd=cell["item_sd"],
                    measures=MS)


def one_rep(cell, rng):
    # the null measure is left out with 3,072 items (its unstable fits dominate the run time there)
    measures = ["x", "x_null"] if cell["n_items"] < 3000 else ["x"]
    return analyse(generate(fams_of(cell), rng), measures, rng, n_boot=N_BOOT, prediction=False, items_only=True)


def summary(df, cs):
    rows = []
    for cid, cell in cs.items():
        tg = large_sample_targets(fams_of(cell), seed=cell["seed"], reps=2)
        for m, g in df[df["cell"] == cid].groupby("measure", sort=False):
            s = summarise(g, tg[tg["measure"] == m].iloc[0].to_dict(), null=(m == "x_null"))
            rows.append(dict(cell=cid, measure=m, **{k: v for k, v in cell.items() if k not in ("seed", "n_rep")}, **s))
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / f"{STUDY}_summary.csv", index=False)
    return out


if __name__ == "__main__":
    pilot = "--pilot" in sys.argv
    cs = cells()
    if pilot:
        STUDY += "_pilot"
        for c in cs.values():
            c["n_rep"] = 4
    t0 = time.time()
    df = run_study(STUDY, one_rep, cs, n_rep=500, chunk_size=4 if pilot else 25, study_seed=SEED)
    out = summary(df, cs)
    pd.set_option("display.width", 250)
    print(out[["cell", "measure", "n_rep", "ordering_mean", "ord_target", "ord_centre_shift", "ord_width_median",
               "ord_excludes_own_estimate", "ord_cov_expected_percentile", "ord_cov_expected_basic",
               "ord_cov_large_sample_percentile", "ord_cov_large_sample_basic", "ord_cov_expected_percentile_io",
               "ord_excl0", "ord_excl0_basic", "ord_excl0_io"]].round(3).to_string())
    print(f"{time.time() - t0:.0f} s")
