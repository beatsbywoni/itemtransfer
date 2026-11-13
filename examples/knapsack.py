"""Worked example: four difficulty measures for the knapsack decision task.

Three item families are used, named after the studies that generated the
items: Franco (two samples that share items: Franco 2021 in the laboratory,
Franco 2024 in the scanner), Doroc (one sample tested in two sessions) and Lu
(a main sample, plus a pilot sample that enters the reliability ceiling
only). The measures are instance complexity, typical-case complexity,
Sahni-k and solver effort (log2 of one plus the number of propagations of a
constraint solver).

Usage::

    python examples/knapsack.py [DATA_DIR] [OUT_DIR]

``DATA_DIR`` must contain ``trials_harmonized.csv``. By default the script
looks for ``data_proc/`` in the repository root and writes to
``paper/knapsack_report``.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import itemtransfer as it

SOURCE_MEASURES = {"ic": "instance_complexity", "tcc": "typical_case_complexity", "sahni_k_opt": "sahni_k",
                   "solver": "solver_effort"}
MEASURES = list(SOURCE_MEASURES.values())
SAMPLE_NAME = {"K2_dec": "Franco 2021", "K4_dec": "Franco 2024", "K5_dec": "Doroc 2025",
               "K7_dec_main": "Lu 2025 main", "K7_dec_pilot": "Lu 2025 pilot"}
FAMILY_OF_SAMPLE = {"Franco 2021": "Franco", "Franco 2024": "Franco", "Doroc 2025": "Doroc",
                    "Lu 2025 main": "Lu", "Lu 2025 pilot": "Lu"}
EVALUATE = {"Franco": "Franco 2021", "Doroc": "Doroc 2025", "Lu": "Lu 2025 main"}
SEED_BOOT, SEED_SPLIT = 20261016, 20261017


def default_data_dir():
    return Path(__file__).resolve().parents[1] / "data_proc"


def load_all_trials(data_dir=None):
    """All trials with the sample label used in the published analysis and its trial selection
    (decision trials without a response are excluded)."""
    data_dir = default_data_dir() if data_dir is None else Path(data_dir)
    t = pd.read_csv(data_dir / "trials_harmonized.csv", low_memory=False)
    variant = t["variant"].map({"decision": "dec", "optimisation": "opt"})
    label = t["dataset"] + "_" + variant
    t["part"] = np.where(t["dataset"].eq("K7"), label + "_" + t["sample"].astype(str), label)
    t["solver"] = np.log2(1.0 + t["gecode_propagations"].astype(float))
    t["part"] = t["part"].map(SAMPLE_NAME).fillna(t["part"])
    t = t.rename(columns={k: v for k, v in SOURCE_MEASURES.items() if k != "solver"})
    t = t.rename(columns={"solver": "solver_effort"})
    t["correct"] = t["correct"].astype(int)
    no_response = t["no_response"].fillna(0).astype(int).eq(1)
    return t[~(t["variant"].eq("decision") & no_response)].reset_index(drop=True)


def load_knapsack(data_dir=None, pilot=True):
    """Return (trials, items) in the format of the package for the three decision families."""
    t = load_all_trials(data_dir)
    samples = [s for s in FAMILY_OF_SAMPLE if pilot or s != "Lu 2025 pilot"]
    d = t[t["part"].isin(samples)]
    trials = pd.DataFrame({"participant": d["participant"].to_numpy(), "item": d["hash_full"].to_numpy(),
                           "family": d["part"].map(FAMILY_OF_SAMPLE).to_numpy(), "sample": d["part"].to_numpy(),
                           "correct": d["correct"].to_numpy()})
    items = (d.drop_duplicates("hash_full").assign(family=lambda x: x["part"].map(FAMILY_OF_SAMPLE))
             .rename(columns={"hash_full": "item"})[["item", "family"] + MEASURES].reset_index(drop=True))
    return trials, items


def session_trials(data_dir=None):
    """Trials of the Doroc 2025 sample with one sample label per session (same participants in both)."""
    t = load_all_trials(data_dir)
    d = t[t["part"].eq("Doroc 2025")]
    return pd.DataFrame({"participant": d["participant"].to_numpy(), "item": d["hash_full"].to_numpy(),
                         "sample": ("Doroc 2025 " + d["condition"].astype(str)).to_numpy(), "correct": d["correct"].to_numpy()})


def main(data_dir=None, out_dir=None, n_boot=2000, n_sim=200, n_jobs=2):
    out_dir = Path(__file__).resolve().parents[1] / "paper" / "knapsack_report" if out_dir is None else Path(out_dir)
    t0 = time.time()
    trials, items = load_knapsack(data_dir)
    out = it.report(trials, items, MEASURES, out_dir=out_dir, evaluate=EVALUATE, reliability_only=["Lu 2025 pilot"],
                    range_limits={"instance_complexity": (None, 0.17)}, n_boot=n_boot, n_sim=n_sim, n_jobs=n_jobs, seed=SEED_BOOT)
    sessions = session_trials(data_dir)
    it.reliability(sessions, seed=SEED_SPLIT).to_csv(out_dir / "sessions_Doroc_reliability.csv", index=False)
    it.agreement(sessions, "Doroc 2025 control", "Doroc 2025 stress", n_boot=n_boot, seed=SEED_SPLIT).to_csv(
        out_dir / "sessions_Doroc_agreement.csv", index=False)
    main_trials = trials[trials["sample"] != "Lu 2025 pilot"]
    if n_sim:
        # interval check including the bootstrap interval of the log-loss reduction (design built on instance complexity)
        design = it.design_from_data(main_trials, items, "instance_complexity", seed=SEED_BOOT)
        chk = it.check_intervals(design, n_sim=n_sim, n_boot=200, evaluate=EVALUATE, prediction=True, n_jobs=n_jobs,
                                 seed=SEED_BOOT)
        chk.to_csv(out_dir / "interval_check_prediction.csv", index=False)
    res = it.transfer(main_trials, items, MEASURES, evaluate=EVALUATE, n_boot=0, seed=SEED_BOOT)
    try:
        fig = it.plot_transfer(res, "instance_complexity")
        fig.savefig(out_dir / "transfer_instance_complexity.png", dpi=150)
    except ImportError:
        pass
    elapsed = time.time() - t0
    (out_dir / "timing.txt").write_text(f"total run time: {elapsed:.1f} s (n_boot={n_boot}, n_sim={n_sim}, n_jobs={n_jobs})\n")
    print(out["markdown"])
    print(f"written to {out_dir} in {elapsed:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2] if len(sys.argv) > 2 else None)
