#!/usr/bin/env python3
"""
3-A3 step 4: one harmonised trial table for all datasets, with the instance measures attached.

    python3 code/10_harmonize_trials.py

Inputs   data_proc/trials_{K2_dec,K2_opt,K4_dec,K4_opt,K5_dec,K7_dec}.csv (03), data_proc/trials_K8_opt.csv (03b, if
         present), data_proc/instance_metrics.csv (09), data_proc/k5_responders.csv (04, optional)
Outputs  data_proc/trials_harmonized.csv       canonical text version
         data_proc/trials_harmonized.parquet   same table (written only if pyarrow is installed)
         data_proc/harmonize_checks.csv
The column meanings are documented in output/report_3a3_codebook.md. Nothing is filtered here: no-response trials,
time-outs and practice-free pilot data stay in the table with flags, and the analysis plan decides what to use.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
DP = PROJ / "data_proc"
SOURCES = {  # table -> (study, context, time limit of the solving stage in s, self-paced, answer window in s)
    "K2_dec": ("Franco et al. 2021", "behavioural laboratory", 22, 0, 2),
    "K2_opt": ("Franco et al. 2021", "behavioural laboratory", 60, 1, np.nan),
    "K4_dec": ("Franco et al. 2024", "fMRI scanner", 22, 0, 2),
    "K4_opt": ("Franco et al. 2024", "outside the scanner, after fMRI", 60, 1, np.nan),
    "K5_dec": ("Doroc et al. 2025", "acute stress study (TSST and control sessions)", 40, 1, 3),
    "K7_dec": ("Lu et al. 2025", "self-performance estimation study", 25, 1, 3),
    "K8_opt": ("Bowman et al. 2023", "drug study (placebo and three stimulants)", 240, 1, np.nan),
}
METRICS = ["n_items", "capacity", "target", "sum_w", "sum_v", "p_star", "sat", "n_witness", "ic", "ic_signed",
           "alpha_c", "alpha_p", "alpha_p_opt", "p_sat_ref", "tcc", "sahni_k_opt", "sahni_k_dec", "value_weight_corr",
           "input_size", "gecode_propagations", "gecode_nodes", "gecode_failures", "gecode_peakDepth"]
COLUMNS = ["dataset", "study", "sample", "context", "variant", "participant", "session", "condition", "block", "trial",
           "attempt", "instance_key", "hash_full", "correct", "answer", "no_response", "answer_rt_s", "time_on_task_s",
           "timed_out", "submitted", "profit_selected", "capacity_selected", "value_ratio", "n_clicks", "items_selected",
           "time_limit_s", "self_paced", "answer_window_s", "k5_responder"] + METRICS
CODEBOOK = {  # column -> description (rendered into output/report_3a3_tables.md by 11_codebook_tables.py)
    "dataset": "K2, K4, K5, K7, K8 (codes of the inventory)",
    "study": "source article",
    "sample": "main; K7 also pilot (a separate group of participants on the same 120 instances)",
    "context": "setting of the data collection",
    "variant": "decision (is there a subset with weight <= capacity and value >= target?) or optimisation (find the "
               "most valuable subset within the capacity)",
    "participant": "dataset-prefixed participant id (unique across datasets)",
    "session": "session number within participant (K5: 2 sessions; K8: 4 sessions; others 1)",
    "condition": "K5 stress or control session; K7 feedback or no_feedback group; K8 PLC, MPH, MOD or DEX; empty "
                 "otherwise",
    "block": "block within session as recorded by the task (empty for K8, which did not record it)",
    "trial": "trial within session as recorded by the task; K8: instance x attempt in table order (the archive has no "
             "presentation order)",
    "attempt": "attempt number for repeated presentations within a session (K8: 1 or 2); 1 otherwise",
    "instance_key": "instance id within dataset and variant (matches data_proc/instance_metrics.csv)",
    "hash_full": "hash of the instance (sorted weight:value pairs, capacity, target); equal hashes = same instance",
    "correct": "decision: answer equals satisfiability; optimisation: selected value equals the optimum (as coded by "
               "the authors; no-response decision trials are coded 0)",
    "answer": "decision: 1 = yes (a subset exists), 0 = no; empty when no answer was given",
    "no_response": "decision: 1 if no answer was given in the answer window",
    "answer_rt_s": "decision: latency of the yes/no key press on the answer screen (s); not recorded in K7",
    "time_on_task_s": "time from instance onset until the participant moved on (self-paced decision tasks K5, K7) or "
                      "submitted or ran out of time (optimisation); empty for K2 and K4 decision trials, which showed "
                      "the instance for a fixed 22 s",
    "timed_out": "self-paced decision: the solving stage ended at the time limit; optimisation: not submitted before "
                 "the limit; empty for fixed-time K2 and K4 decision trials",
    "submitted": "optimisation: 1 if the participant submitted before the time limit",
    "profit_selected": "optimisation: value of the final selection",
    "capacity_selected": "optimisation: weight of the final selection",
    "value_ratio": "optimisation: profit_selected / p_star",
    "n_clicks": "optimisation: number of item clicks (K8: length of the sequence of visited sets)",
    "items_selected": "optimisation: 0/1 vector of the final selection in item order (not in the K8 archive)",
    "time_limit_s": "time limit of the solving stage (K2/K4 decision: fixed exposure)",
    "self_paced": "1 if the participant could end the solving stage early",
    "answer_window_s": "decision: length of the answer screen",
    "k5_responder": "K5: 1 if the participant is a cortisol responder in the authors' analysis (27 of 41)",
    "n_items": "number of items", "capacity": "capacity c", "target": "decision: target profit p",
    "sum_w": "sum of item weights", "sum_v": "sum of item values", "p_star": "optimum value (exhaustive search)",
    "sat": "decision: 1 if satisfiable (p_star >= target)",
    "n_witness": "decision: number of subsets that satisfy both constraints",
    "ic": "decision: instance complexity |target - p_star| / sum_v",
    "ic_signed": "decision: (target - p_star) / sum_v (positive = unsatisfiable)",
    "alpha_c": "normalised capacity c / sum_w",
    "alpha_p": "decision: normalised profit target / sum_v",
    "alpha_p_opt": "p_star / sum_v (profit coordinate of the optimisation problem)",
    "p_sat_ref": "probability that a random instance (same n; weights and values i.i.d. Uniform(0, 1)) at this "
                 "(alpha_c, profit coordinate) is satisfiable; 20,000 Monte Carlo draws",
    "tcc": "typical-case complexity: 1 - |2 p_sat_ref - 1| (1 on the phase transition, 0 far from it)",
    "sahni_k_opt": "Sahni-k of the optimisation problem: fewest fixed items for which greedy completion reaches p_star",
    "sahni_k_dec": "decision analogue: fewest fixed items for which greedy completion reaches the target "
                   "(satisfiable instances only)",
    "value_weight_corr": "Pearson correlation of item values and weights",
    "input_size": "n log2(c)",
    "gecode_propagations": "Gecode propagations (MiniZinc 2.9.3, Gecode 6.3.0; models in code/metrics.py)",
    "gecode_nodes": "Gecode search nodes", "gecode_failures": "Gecode failed nodes",
    "gecode_peakDepth": "Gecode peak search depth",
}
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"check": name, "ok": bool(ok), "detail": detail})


def main() -> int:
    met = pd.read_csv(DP / "instance_metrics.csv")
    # The responder list is optional: it comes from the authors' RDS files (02b_convert_rds.py, 04_validate_against_authors.py)
    # and only fills the column k5_responder, which the analyses of the article do not use.
    rf = DP / "k5_responders.csv"
    resp = set(pd.read_csv(rf).participant) if rf.exists() else None
    if resp is None:
        print("data_proc/k5_responders.csv not found: the column k5_responder is left empty")
    parts = []
    for name, (study, context, limit, paced, window) in SOURCES.items():
        f = DP / f"trials_{name}.csv"
        if not f.exists():
            check(f"{name}: source table present", name == "K8_opt", f"{f.name} not found")
            continue
        t = pd.read_csv(f)
        n0 = len(t)
        dec = t.variant.iloc[0] == "decision"
        out = pd.DataFrame({
            "dataset": t.dataset, "study": study, "sample": t["sample"], "context": context, "variant": t.variant,
            "participant": t.participant, "session": t.session, "condition": t.condition, "block": t.block,
            "trial": t.trial, "attempt": t["attempt"] if "attempt" in t else 1, "instance_key": t.instance_key,
            "hash_full": t.hash_full, "correct": t.correct,
            "answer": t["answer"] if dec else np.nan, "no_response": t["no_response"] if dec else np.nan,
            "answer_rt_s": t["rt_answer_s"] if dec else np.nan,
            # K2/K4 decision trials show the instance for a fixed time, so there is no time on task
            "time_on_task_s": (t["time_on_task_s"] if (not dec or paced) else np.nan),
            "timed_out": (t["timed_out"] if (dec and paced) else (1 - t["submitted"] if not dec else np.nan)),
            "submitted": (t["submitted"] if not dec else np.nan),
            "profit_selected": (t["profit_selected"] if not dec else np.nan),
            "capacity_selected": (t["capacity_selected"] if not dec else np.nan),
            "n_clicks": (t["n_clicks"] if not dec else np.nan),
            "items_selected": (t["items_selected"] if not dec else np.nan),
            "time_limit_s": limit, "self_paced": paced, "answer_window_s": window,
            "k5_responder": (t.participant.isin(resp).astype(int) if name == "K5_dec" and resp is not None else np.nan)})
        m = met[(met.dataset == t.dataset.iloc[0]) & (met.variant == t.variant.iloc[0])]
        out = out.merge(m[["sample", "instance_key"] + METRICS], on=["sample", "instance_key"], how="left",
                        validate="many_to_one")
        if not dec:
            out["value_ratio"] = out.profit_selected / out.p_star
        check(f"{name}: rows kept", len(out) == n0, f"{len(out)} of {n0}")
        check(f"{name}: every trial has instance measures", out.ic.notna().all() if dec else out.p_star.notna().all(),
              f"{int(out.p_star.isna().sum())} trials without measures")
        if dec:
            ok = ((out.answer == out.sat) == (out.correct == 1)) | (out.no_response == 1)
            check(f"{name}: correct = (answer equals satisfiability) for answered trials", ok.all(),
                  f"{int((~ok).sum())} trials disagree")
        else:
            ok = (out.correct == (out.profit_selected == out.p_star).astype(int))
            check(f"{name}: correct = (selected value equals the optimum)", ok.all(), f"{int((~ok).sum())} trials disagree")
        parts.append(out)
    h = pd.concat(parts, ignore_index=True)
    h["value_ratio"] = h.get("value_ratio")
    assert set(COLUMNS) == set(CODEBOOK), sorted(set(COLUMNS) ^ set(CODEBOOK))
    h = h[COLUMNS]
    for c in ("session", "block", "trial", "attempt", "instance_key", "correct", "self_paced"):
        h[c] = h[c].astype("Int64")
    for c in ("answer", "no_response", "timed_out", "submitted", "k5_responder", "sat", "n_witness", "sahni_k_opt",
              "sahni_k_dec", "gecode_propagations", "gecode_nodes", "gecode_failures", "gecode_peakDepth", "p_star"):
        h[c] = pd.to_numeric(h[c], errors="coerce").astype("Int64")
    h = h.sort_values(["dataset", "variant", "sample", "participant", "session", "trial", "attempt"]).reset_index(drop=True)
    check("participant ids are unique across datasets", h.groupby("participant").dataset.nunique().max() == 1)
    h.to_csv(DP / "trials_harmonized.csv", index=False)
    try:
        import pyarrow  # noqa: F401
        h.to_parquet(DP / "trials_harmonized.parquet", index=False)
        pq = "written"
    except ImportError:
        pq = "not written (pyarrow not installed)"
    check("parquet copy", True, pq)
    pd.DataFrame(CHECKS).to_csv(DP / "harmonize_checks.csv", index=False)
    summary = h.groupby(["dataset", "variant", "sample"]).agg(trials=("correct", "size"),
                                                               participants=("participant", "nunique"),
                                                               instances=("instance_key", "nunique"))
    print(f"harmonised trials: {len(h)} rows, {h.shape[1]} columns; parquet {pq}")
    print(summary.to_string())
    bad = [c for c in CHECKS if not c["ok"]]
    for c in CHECKS:
        print(f"  {'OK  ' if c['ok'] else 'FAIL'} {c['check']}: {c['detail']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
