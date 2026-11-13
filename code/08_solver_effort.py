#!/usr/bin/env python3
"""
3-A3 step 2: solver effort (Gecode search statistics through MiniZinc) for every instance.

    MINIZINC=/path/to/minizinc python3 code/08_solver_effort.py

Needs MiniZinc with the Gecode solver (the MiniZinc bundle includes it; used here: MiniZinc 2.9.3, Gecode 6.3.0).
Without MiniZinc the step reports that it was skipped and leaves the existing output untouched, so the later steps
can still run on a machine without it.

Models (code/metrics.py): optimisation = 0/1 variables, capacity constraint, maximise value; decision = the MiniZinc
knapsack global constraint with weight <= c and value >= p. Both search the items in input order, trying 1 before 0.
These are the models that reproduce the statistics stored in the K2 authors' instance files (checked below).

Inputs   data_proc/instances.csv (03_extract_datasets.py) and, if present, data_proc/instances_K8.csv (03b_extract_k8.py)
         data_raw/e6cwf/decisionInstances_selected.csv, optimisationInstances_selected.csv (authors' solver output)
Outputs  data_proc/solver_effort_gecode.csv   one row per instance: Gecode statistics, solver versions, model hash
         data_proc/solver_effort_checks.csv   agreement with the K2 authors' statistics (and with K8's propagation
                                              counts, by rank, when K8 is present)
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402

PROJ = Path(__file__).resolve().parent.parent
DP = PROJ / "data_proc"
E6 = PROJ / "data_raw" / "e6cwf"


def main() -> int:
    mzn = M.find_minizinc()
    if not mzn:
        print("08_solver_effort: MiniZinc not found (set MINIZINC=/path/to/minizinc); skipped, existing "
              "data_proc/solver_effort_gecode.csv left as it is")
        return 0
    ver = M.minizinc_version(mzn)
    model_hash = {"optimisation": hashlib.sha256(M.MZN_OPT.encode()).hexdigest()[:16],
                  "decision": hashlib.sha256(M.MZN_DEC.encode()).hexdigest()[:16]}
    frames = [pd.read_csv(DP / "instances.csv")]
    if (DP / "instances_K8.csv").exists():
        frames.append(pd.read_csv(DP / "instances_K8.csv"))
    inst = pd.concat(frames, ignore_index=True)
    rows = []
    cache = {}
    for r in inst.itertuples():
        target = None if r.variant == "optimisation" else int(r.target)
        key = (r.weights, r.values, int(r.capacity), target)
        if key not in cache:
            cache[key] = M.gecode_stats(r.weights, r.values, int(r.capacity), target, minizinc=mzn)
        st = cache[key]
        rows.append({"dataset": r.dataset, "variant": r.variant, "sample": r.sample, "instance_key": r.instance_key,
                     "hash_full": r.hash_full, **{f"gecode_{k}": st.get(k) for k in M.GECODE_FIELDS},
                     "gecode_unsat": st["unsat"], "gecode_decided_before_search": st["decided_before_search"],
                     "minizinc_version": ver["minizinc"], "gecode_version": ver["gecode"],
                     "model_sha256_16": model_hash[r.variant]})
    out = pd.DataFrame(rows)
    for k in list(M.GECODE_FIELDS) + ["unsat", "decided_before_search"]:
        out[f"gecode_{k}"] = out[f"gecode_{k}"].astype("Int64")
    out.to_csv(DP / "solver_effort_gecode.csv", index=False)

    checks = []
    fields = {"propagations": "propagations_MZN", "nodes": "nodes_MZN", "failures": "failures_MZN",
              "peakDepth": "peak_depth_MZN", "solutions": "no_solutions_MZN"}
    for variant, fname, tcol in (("decision", "decisionInstances_selected.csv", "profit"),
                                 ("optimisation", "optimisationInstances_selected.csv", None)):
        a = pd.read_csv(E6 / fname)
        stats = []
        for r in a.itertuples():
            key = (r.weights, r.values, int(r.capacity), None if tcol is None else int(getattr(r, tcol)))
            if key not in cache:
                cache[key] = M.gecode_stats(*key, minizinc=mzn)
            stats.append(cache[key])
        for k, col in fields.items():
            mine = pd.Series([st.get(k) for st in stats], dtype=float)
            same = int((mine.values == a[col].values).sum())
            note = ""
            if same < len(a):
                rho = mine.rank().corr(a[col].rank())
                note = f"Spearman rho = {rho:.3f}"
                if k == "propagations" and variant == "decision":
                    note += (f"; the authors' flattened model had {int(a.variables_MZN.iloc[0])} variables and "
                             f"{int(a.propagators_MZN.iloc[0])} propagators, this one {int(stats[0]['variables'])} and "
                             f"{int(stats[0]['propagators'])}")
            checks.append({"comparison": f"K2 {variant} instances: Gecode {k} equals the authors' {col}",
                           "agree": same, "n": len(a), "note": note})
    k8 = DP / "instances_K8.csv"
    if k8.exists():
        k = pd.read_csv(k8)
        if "author_mzn_props" in k:
            g = out[out.dataset == "K8"].merge(k[["instance_key", "author_mzn_props"]], on="instance_key")
            rho = g.gecode_propagations.rank().corr(g.author_mzn_props.rank())
            checks.append({"comparison": "K8 instances: Spearman rho of Gecode propagations with the authors' mzn_props",
                           "agree": int(round(rho * 1000)), "n": 1000, "note": f"rho = {rho:.3f} over {len(g)} instances "
                           f"(the authors' counts are about {np.median(g.author_mzn_props / g.gecode_propagations):.0f} "
                           "times larger: different model or version)"})
    pd.DataFrame(checks).to_csv(DP / "solver_effort_checks.csv", index=False)
    print(f"solver effort: {len(out)} instance rows ({len(cache)} distinct runs); MiniZinc {ver['minizinc']}, "
          f"Gecode {ver['gecode']}")
    for c in checks:
        print(f"  {c['comparison']}: {c['agree']}/{c['n']} {c['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
