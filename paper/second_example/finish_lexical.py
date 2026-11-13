"""Post-processing of the second worked example: basic (reflected) intervals for the ordering criterion, a check of
where the downward shift of resampled ordering correlations comes from, and the merged run_info.json.
Run after all stages of run_lexical.py:  python3 finish_lexical.py
"""
import glob, json, os, time
import numpy as np, pandas as pd
import itemtransfer as it
from itemtransfer._data import prepare
from itemtransfer._stats import basic_interval, percentile_interval, wspearman
from itemtransfer.transfer import _bootstrap_fold, _draw, _model_columns
import lexical_common as lc

R = lc.RESULTS
t0 = time.time()
rows = []
for tag, weights in [("", "trials"), ("_equal_weights", "equal")]:
    pt = pd.read_csv(os.path.join(R, f"step3_transfer{tag}.csv")).set_index(["family", "model"])
    bt = pd.read_csv(os.path.join(R, f"step3_bootstrap{tag}.csv"))
    for (f, m), b in bt.groupby(["family", "model"], sort=False):
        for st in ["ordering", "calibration_slope", "logloss_reduction"]:
            v = b[st].to_numpy()
            est = pt.at[(f, m), st]
            lo, hi = percentile_interval(v)
            blo, bhi = basic_interval(est, v)
            rows.append(dict(weights=weights, family=f, model=m, statistic=st, estimate=est,
                             bootstrap_mean=float(np.nanmean(v)), bootstrap_mean_minus_estimate=float(np.nanmean(v) - est),
                             bootstrap_sd=float(np.nanstd(v, ddof=1)), percentile_lo=lo, percentile_hi=hi,
                             estimate_inside_percentile_interval=bool(lo <= est <= hi), basic_lo=blo, basic_hi=bhi))
pd.DataFrame(rows).to_csv(os.path.join(R, "step3_interval_check.csv"), index=False)
x = pd.DataFrame(rows)
print(x[x["weights"] == "trials"].round(4).to_string())

# model differences with basic intervals (ordering differences are affected by the same shift)
bt = pd.read_csv(os.path.join(R, "step3_bootstrap.csv"))
pt = pd.read_csv(os.path.join(R, "step3_transfer.csv")).set_index(["family", "model"])
rows = []
for f in lc.FAMILIES:
    ref = bt[(bt["family"] == f) & (bt["model"] == "zipf")].sort_values("resample")
    for m in ["combined"]:
        oth = bt[(bt["family"] == f) & (bt["model"] == m)].sort_values("resample")
        for st in ["ordering", "logloss_reduction", "brier_reduction"]:
            d = oth[st].to_numpy() - ref[st].to_numpy()
            est = pt.at[(f, m), st] - pt.at[(f, "zipf"), st]
            lo, hi = percentile_interval(d)
            blo, bhi = basic_interval(est, d)
            rows.append(dict(family=f, model=m, reference="zipf", statistic=st, difference=est, percentile_lo=lo,
                             percentile_hi=hi, basic_lo=blo, basic_hi=bhi))
pd.DataFrame(rows).to_csv(os.path.join(R, "step3_three_measures_minus_frequency.csv"), index=False)
print(pd.DataFrame(rows).round(4).to_string())

# where does the shift come from? 1,000-word sample, frequency: resample participants only, items only, both
trials_all, words = lc.load_megastudies()
tf, items = lc.build(trials_all, words, n_words=1000)
del trials_all
data = prepare(tf, items, ["zipf"])
res = it.transfer(tf, items, ["zipf"], n_boot=0, n_splits=20, seed=lc.SEED)
est = res.table.set_index("family")["ordering"]
rows = []
for label in ["participants and items", "participants only", "items only"]:
    rng = np.random.default_rng([lc.SEED, 11])
    wp, wi = _draw(data, 400, rng, two_way=(label != "participants only"))
    if label == "items only":
        wp = {k: np.ones_like(v) for k, v in wp.items()}
    for f in data.families:
        b = _bootstrap_fold(data, f, [f], {"zipf": ["zipf"]}, "trials", wp, wi, rng, prediction=False, heldout=False)
        v = b["zipf"]["ordering"]
        rows.append(dict(resampled=label, family=f, n_words=1000, n_boot=400, ordering=est[f],
                         bootstrap_mean=float(v.mean()), shift=float(v.mean() - est[f]), bootstrap_sd=float(v.std(ddof=1))))
pd.DataFrame(rows).to_csv(os.path.join(R, "step5_ordering_shift.csv"), index=False)
print(pd.DataFrame(rows).round(4).to_string())

info = {}
for p in sorted(glob.glob(os.path.join(R, "run_info_*.json"))):
    d = json.load(open(p))
    info[d["stage"]] = d
s1 = json.load(open(os.path.join(lc.CACHE, "step1_info.json")))
s1["elp_published"] = json.load(open(os.path.join(lc.CACHE, "step1_elp_info.json")))
s1["load_logs"] = json.load(open(os.path.join(lc.CACHE, "load_logs.json")))
info["step1"] = s1
import matplotlib, rapidfuzz, wordfreq, scipy, platform
info["versions"] = dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                        scipy=scipy.__version__, matplotlib=matplotlib.__version__, itemtransfer=it.__version__,
                        wordfreq="3.1.1", rapidfuzz=rapidfuzz.__version__)
info["seeds"] = dict(main=lc.SEED, shared_word_assignment=lc.SEED, word_samples=lc.SEED,
                     equal_size_reference_lexicon=lc.SEED, three_measure_bootstrap=[lc.SEED, 7],
                     ordering_shift_check=[lc.SEED, 11])
info["total_seconds_all_stages"] = round(sum(v.get("seconds", 0) for k, v in info.items() if isinstance(v, dict) and "seconds" in v), 1)
info["finish_seconds"] = round(time.time() - t0, 1)
info["machine"] = "2 cores, 7 GB RAM; stages ran partly in parallel, so wall-clock times include contention"
json.dump(info, open(os.path.join(R, "run_info.json"), "w"), indent=1, default=str)
print("total seconds", info["total_seconds_all_stages"])
