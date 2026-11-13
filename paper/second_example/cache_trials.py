"""Load the four megastudies from original/ with load_lexical.py and cache the tidy tables (cache/ is not a result)."""
import json, os, pickle, sys, time
import load_lexical as ll
here = os.path.dirname(os.path.abspath(__file__))
t0 = time.time()
out = ll.load_all()            # elp_items_csv=None: no published ELP item values are read
logs = {}
for fam, (tr, it, log) in out.items():
    tr.to_pickle(os.path.join(here, "cache", f"trials_{fam}.pkl"))
    it.to_pickle(os.path.join(here, "cache", f"pubitems_{fam}.pkl"))
    logs[fam] = log
    print(fam, len(tr), len(it), tr["participant"].nunique(), round(time.time() - t0, 1), flush=True)
json.dump(logs, open(os.path.join(here, "cache", "load_logs.json"), "w"), indent=1, default=str)
print("seconds", time.time() - t0)
