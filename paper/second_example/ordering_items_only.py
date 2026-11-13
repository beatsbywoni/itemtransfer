"""Interval of the ordering correlation from a bootstrap of items only (participants kept as observed).

Added after the simulation study showed that the two-way percentile interval of the ordering correlation is
centred too low with many items. Uses the same internal function as itemtransfer.transfer(ordering_boot="items").
Writes results/step3_ordering_items_only.csv and results/run_info_ordering_items_only.json.
Usage (from this directory): python3 ordering_items_only.py
"""
import json, os, time
import numpy as np, pandas as pd
import itemtransfer as it
from itemtransfer._data import prepare
from itemtransfer._stats import child_rng, percentile_interval
from itemtransfer.transfer import _bootstrap_fold, _draw, _batch_sizes, _model_columns, _resolve_evaluate
import lexical_common as lc

N_BOOT, BOOT_BATCH = 1000, 50
t0 = time.time()
trials_all, words = lc.load_megastudies()
tf, items = lc.build(trials_all, words)
del trials_all
data = prepare(tf, items, lc.MEASURES)
models = _model_columns(data.measures, True)
ev = _resolve_evaluate(data, None)
rng = child_rng(lc.SEED, 11)
parts = {}
for size in _batch_sizes(N_BOOT, BOOT_BATCH):
    wp, wi = _draw(data, size, rng)
    w1 = {k: np.ones_like(v) for k, v in wp.items()}
    for f in data.families:
        res = _bootstrap_fold(data, f, ev[f], models, "trials", w1, wi, rng, ordering=True, prediction=False,
                              heldout=False)
        for name in models:
            parts.setdefault((f, name), []).append(res[name]["ordering"])
    print(len(parts[(data.families[0], "zipf")]) * BOOT_BATCH, round(time.time() - t0), flush=True)
point = pd.read_csv(os.path.join(lc.RESULTS, "step3_transfer.csv")).set_index(["family", "model"])
rows = []
for (f, name), p in parts.items():
    b = np.concatenate(p)
    lo, hi = percentile_interval(b)
    est = point.at[(f, name), "ordering"]
    rows.append(dict(family=f, model=name, ordering=est, ordering_lo=lo, ordering_hi=hi, bootstrap_mean=b.mean(),
                     estimate_inside_interval=bool(lo <= est <= hi), n_boot=len(b)))
pd.DataFrame(rows).to_csv(os.path.join(lc.RESULTS, "step3_ordering_items_only.csv"), index=False)
json.dump(dict(stage="ordering_items_only", seed=[lc.SEED, 11], n_boot=N_BOOT, boot_batch=BOOT_BATCH,
               itemtransfer=it.__version__, seconds=round(time.time() - t0, 1)),
          open(os.path.join(lc.RESULTS, "run_info_ordering_items_only.json"), "w"), indent=1)
