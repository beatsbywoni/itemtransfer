#!/usr/bin/env python3
"""
3-A3 step 3: complexity measures for every instance, recomputed from the instance definitions, and their agreement
with the values the original authors published.

    python3 code/09_instance_metrics.py

Inputs   data_proc/instances.csv (03), data_proc/instances_K8.csv (03b, if present),
         data_proc/solver_effort_gecode.csv (08, if present),
         data_raw/e6cwf/*.csv (K2 authors' instance files with solver statistics and Sahni-k),
         data_proc/unpacked/964pf/.../KSDec_clean.csv, KSOpt_clean.csv (K4 authors' instance fields: phaseT, ICexpost)
Measures (definitions in code/metrics.py)
  ic, ic_signed          decision only; |p - p*| / sum(v) and (p - p*) / sum(v)
  alpha_c, alpha_p       c / sum(w); p / sum(v) for decision instances
  alpha_p_opt            p* / sum(v); the profit coordinate of an optimisation instance
  p_sat_ref, tcc         satisfiability probability of random instances (n items, weights and values i.i.d.
                         Uniform(0, 1)) at (alpha_c, alpha_p) for decision instances and at (alpha_c, alpha_p_opt) for
                         optimisation instances; 20,000 Monte Carlo draws with a seed fixed by (n, alpha_c, profit
                         coordinate); tcc = 1 - |2 p_sat - 1|
  sahni_k_opt            for all instances (the optimisation problem underlying a decision instance included)
  sahni_k_dec            decision instances, satisfiable ones only
  n_witness              decision instances: number of subsets that satisfy both constraints
  value_weight_corr, input_size (n log2 c)
  gecode_*               from 08_solver_effort.py
Outputs  data_proc/instance_metrics.csv, data_proc/instance_metrics_checks.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402

PROJ = Path(__file__).resolve().parent.parent
DP = PROJ / "data_proc"
E6 = PROJ / "data_raw" / "e6cwf"
K4W = DP / "unpacked" / "964pf" / "Behavioral Data" / "Work" / "preprocessed" / "preprocessed"
SAMPLES = 20000
CHECKS = []


def check(dataset, name, agree, n, detail=""):
    CHECKS.append({"dataset": dataset, "check": name, "agree": int(agree), "n": int(n), "detail": detail})


def main() -> int:
    frames = [pd.read_csv(DP / "instances.csv")]
    if (DP / "instances_K8.csv").exists():
        frames.append(pd.read_csv(DP / "instances_K8.csv"))
    inst = pd.concat(frames, ignore_index=True)
    inst = inst.rename(columns={"alpha_c": "author_alpha_c", "alpha_p": "author_alpha_p"})
    psat_cache = {}
    rows = []
    for r in inst.itertuples(index=False):
        w, v, c = M.parse_items(r.weights), M.parse_items(r.values), int(r.capacity)
        dec = r.variant == "decision"
        p = int(r.target) if dec else None
        e = M.enumerate_instance(w, v, c, p)
        a_c = M.alpha_c(c, w)
        a_p = M.alpha_p(p, v) if dec else np.nan
        a_po = e["p_star"] / sum(v)
        coord = a_p if dec else a_po
        key = (len(w), a_c, coord)
        if key not in psat_cache:
            psat_cache[key] = M.p_sat_reference(len(w), a_c, coord, samples=SAMPLES)
        ps = psat_cache[key]
        rows.append({
            "dataset": r.dataset, "variant": r.variant, "sample": r.sample, "instance_key": r.instance_key,
            "hash_full": r.hash_full, "hash_items": r.hash_items, "n_items": len(w), "capacity": c,
            "target": p if dec else np.nan, "sum_w": sum(w), "sum_v": sum(v), "p_star": e["p_star"],
            "c_star": e["c_star"], "n_optimal_sets": e["n_optimal_sets"],
            "sat": e.get("sat", np.nan), "n_witness": e.get("n_witness", np.nan),
            "ic": M.ic(p, e["p_star"], sum(v)) if dec else np.nan,
            "ic_signed": M.ic(p, e["p_star"], sum(v), signed=True) if dec else np.nan,
            "alpha_c": a_c, "alpha_p": a_p, "alpha_p_opt": a_po, "p_sat_ref": ps, "tcc": M.tcc_from_psat(ps),
            "sahni_k_opt": M.sahni_k_opt(w, v, c, e["p_star"]),
            "sahni_k_dec": (M.sahni_k_dec(w, v, c, p) if dec else np.nan),
            "value_weight_corr": M.value_weight_corr(w, v), "input_size": M.input_size(len(w), c)})
    met = pd.DataFrame(rows)
    met["sahni_k_dec"] = met["sahni_k_dec"].astype("Int64")
    se = DP / "solver_effort_gecode.csv"
    if se.exists():
        g = pd.read_csv(se)
        keep = ["dataset", "variant", "sample", "instance_key"] + [c for c in g.columns if c.startswith("gecode_")]
        met = met.merge(g[keep], on=["dataset", "variant", "sample", "instance_key"], how="left")
        n_miss = int(met.gecode_nodes.isna().sum())
        check("all", "instances with Gecode statistics", len(met) - n_miss, len(met),
              "" if not n_miss else "missing: " + ", ".join(sorted(set(met[met.gecode_nodes.isna()].dataset))))
    else:
        check("all", "instances with Gecode statistics", 0, len(met), "solver_effort_gecode.csv not found (run 08)")
    author_cols = [c for c in inst.columns if c.startswith("author_")]
    met = met.merge(inst[["dataset", "variant", "sample", "instance_key"] + author_cols],
                    on=["dataset", "variant", "sample", "instance_key"], how="left")

    # ---- agreement with the authors' values ----
    # K2: authors' instance files (exact normalised capacity and profit, optimum, Sahni-k)
    d6 = pd.read_csv(E6 / "decisionInstances_selected.csv")
    o6 = pd.read_csv(E6 / "optimisationInstances_selected.csv")
    k2d = met[(met.dataset == "K2") & (met.variant == "decision")].merge(
        d6, left_on="author_id", right_on="problem", how="inner")
    check("K2", "decision: alpha_c equals the authors' ncapacity", (np.abs(k2d.alpha_c - k2d.ncapacity) < 1e-9).sum(),
          len(k2d))
    check("K2", "decision: alpha_p equals the authors' nprofit", (np.abs(k2d.alpha_p - k2d.nprofit) < 1e-9).sum(),
          len(k2d))
    check("K2", "decision: satisfiability equals the authors' solution_MZN", (k2d.sat == k2d.solution_MZN).sum(), len(k2d))
    k2o = met[(met.dataset == "K2") & (met.variant == "optimisation")].merge(
        o6, left_on="author_id", right_on="problem", how="inner")
    check("K2", "optimisation: optimum equals the authors' profitOpt", (k2o.p_star == k2o.profitOpt).sum(), len(k2o))
    check("K2", "optimisation: Sahni-k equals the authors' sahniK", (k2o.sahni_k_opt == k2o.sahniK).sum(), len(k2o))
    check("K2", "optimisation: alpha_p_opt equals the authors' nProfitOpt",
          (np.abs(k2o.alpha_p_opt - k2o.nProfitOpt) < 1e-9).sum(), len(k2o))
    pool = pd.read_csv(E6 / "optimisationInstancesInfo.csv")
    agree = sum(M.sahni_k_opt(M.parse_items(r.weights), M.parse_items(r.values), int(r.capacity), int(r.profitOpt))
                == int(r.sahniK) for r in pool.itertuples())
    check("K2", "pool of generated optimisation instances: Sahni-k equals the authors' sahniK", agree, len(pool),
          "all generated 6-item instances in optimisationInstancesInfo.csv")
    # K2/K4 decision and optimisation: phase-transition labels (K4 preprocessed files)
    for fname, variant in (("KSDec_clean.csv", "decision"), ("KSOpt_clean.csv", "optimisation")):
        f = K4W / fname
        if not f.exists():
            check("K4", f"{variant}: phase-transition labels", 0, 0, f"{fname} not found")
            continue
        k4 = pd.read_csv(f).drop_duplicates("id")
        cols = ["id", "phaseT"] + (["ICexpost"] if "ICexpost" in k4 else []) + (["sahniK"] if "sahniK" in k4 else [])
        m = met[(met.dataset == "K4") & (met.variant == variant)].merge(k4[cols], left_on="author_id", right_on="id")
        hi, lo = m[m.phaseT == 1].tcc, m[m.phaseT == 0].tcc
        auc = float((hi.values[:, None] > lo.values[None, :]).mean() + 0.5 * (hi.values[:, None] == lo.values[None, :]).mean())
        check("K4", f"{variant}: tcc separates the authors' phase-transition labels (AUC x 1000)", round(auc * 1000), 1000,
              f"phaseT = 1: tcc mean {hi.mean():.3f} (n = {len(hi)}); phaseT = 0: mean {lo.mean():.3f} (n = {len(lo)}); "
              f"p_sat at phaseT = 1: {m[m.phaseT == 1].p_sat_ref.min():.2f}-{m[m.phaseT == 1].p_sat_ref.max():.2f}")
        if "ICexpost" in m:
            check("K4", f"{variant}: ic equals the authors' ICexpost", (np.abs(m.ic - m.ICexpost) < 1e-9).sum(), len(m))
        if "sahniK" in m:
            check("K4", f"{variant}: Sahni-k equals the authors' sahniK", (m.sahni_k_opt == m.sahniK).sum(), len(m))
    # K5: signed IC in the authors' 'type' column (instance 56 is a known discrepancy in the source file)
    k5 = met[met.dataset == "K5"]
    d = np.abs(k5.ic_signed - pd.to_numeric(k5.author_type, errors="coerce"))
    check("K5", "signed IC equals the authors' type column", (d < 1e-9).sum(), len(k5),
          "differs for instance " + ", ".join(map(str, k5[d >= 1e-9].instance_key.tolist())) if (d >= 1e-9).any() else "")
    # K7: IC and normalised capacity and profit
    k7 = met[met.dataset == "K7"]
    check("K7", "ic equals the authors' ic", (np.abs(k7.ic - k7.author_ic) < 1e-6).sum(), len(k7))
    check("K7", "alpha_c equals the authors' alpha_c", (np.abs(k7.alpha_c - k7.author_alpha_c) < 1e-6).sum(), len(k7))
    check("K7", "alpha_p equals the authors' alpha_p", (np.abs(k7.alpha_p - k7.author_alpha_p) < 1e-6).sum(), len(k7))
    # K2/K4 instance ids carry the generation targets of alpha_c and alpha_p (two decimals); integer capacities and
    # targets move the realised values slightly
    for ds in ("K2", "K4"):
        g = met[(met.dataset == ds) & (met.variant == "decision")]
        dc, dp = np.abs(g.alpha_c - g.author_alpha_c), np.abs(g.alpha_p - g.author_alpha_p)
        check(ds, "decision: alpha_c and alpha_p within 0.01 of the targets in the authors' instance ids",
              ((dc <= 0.01) & (dp <= 0.01)).sum(), len(g), f"max deviation {dc.max():.4f} (alpha_c), {dp.max():.4f} (alpha_p)")
    # K8: author per-instance fields (also checked in 03b)
    k8 = met[met.dataset == "K8"]
    if len(k8):
        check("K8", "Sahni-k equals the authors' sahni_k", (k8.sahni_k_opt == k8.author_sahni_k).sum(), len(k8))
        check("K8", "value-weight r equals the authors' v_w_corr_pearson",
              (np.abs(k8.value_weight_corr - k8.author_vw_corr) < 1e-6).sum(), len(k8))
        check("K8", "n log2 C equals the authors' Complexity", (np.abs(k8.input_size - k8.author_complexity) < 1e-6).sum(),
              len(k8))
    # shared instances get identical measures
    dup = met.groupby("hash_full").filter(lambda g: len(g) > 1)
    cols = ["ic", "alpha_c", "alpha_p", "p_sat_ref", "sahni_k_opt", "value_weight_corr"]
    same = dup.groupby("hash_full")[cols].nunique(dropna=False).le(1).all(axis=1)
    check("all", "instances shared between datasets or samples have identical measures", same.sum(), len(same))

    met.to_csv(DP / "instance_metrics.csv", index=False)
    ch = pd.DataFrame(CHECKS)
    ch.to_csv(DP / "instance_metrics_checks.csv", index=False)
    print(f"instance metrics: {len(met)} rows ({met.groupby(['dataset', 'variant']).size().to_dict()}); "
          f"{len(psat_cache)} phase-diagram points simulated")
    for c in CHECKS:
        print(f"  {c['dataset']}: {c['check']}: {c['agree']}/{c['n']} {c['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
