"""Does a non-linear frequency function remove the mismatch in scale? (added after review; not pre-specified)

Words unknown to the frequency resource (Zipf value 0) are removed. Two analyses with the public API:
  linear: zipf alone;  cubic: zipf, zipf^2 and zipf^3 together (the 'combined' row), centred at Zipf 3.5.
Writes results/posthoc_nonlinear_frequency.csv and results/run_info_nonlinear_frequency.json.
Usage (from this directory): python3 nonlinear_frequency.py
"""
import json, os, time
import pandas as pd
import itemtransfer as it
import lexical_common as lc

t0 = time.time()
trials_all, words = lc.load_megastudies()
tf, items = lc.build(trials_all, words)
del trials_all
keep = items[items["zipf"] > 0].copy()
tf = tf[tf["item"].isin(set(keep["item"]))]
z = keep["zipf"] - 3.5
keep["zipf_c"], keep["zipf_c2"], keep["zipf_c3"] = z, z ** 2, z ** 3
res = it.transfer(tf, keep, ["zipf_c", "zipf_c2", "zipf_c3"], combined=True, n_boot=200, boot_batch=50, n_splits=500,
                  seed=lc.SEED)
tab = res.table[res.table["model"].isin(["zipf_c", "combined"])].copy()
tab["model"] = tab["model"].map({"zipf_c": "linear", "combined": "cubic"})
tab.to_csv(os.path.join(lc.RESULTS, "posthoc_nonlinear_frequency.csv"), index=False)
json.dump(dict(stage="nonlinear_frequency", seed=lc.SEED, n_boot=200, itemtransfer=it.__version__,
               n_items=keep.groupby("family").size().to_dict(), seconds=round(time.time() - t0, 1)),
          open(os.path.join(lc.RESULTS, "run_info_nonlinear_frequency.json"), "w"), indent=1)
print(tab[["family", "model", "ordering", "calibration_slope", "calibration_slope_lo", "calibration_slope_hi",
           "scale_reading", "logloss_reduction"]].round(3).to_string())
