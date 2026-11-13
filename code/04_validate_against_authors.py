#!/usr/bin/env python3
"""
3-A2 step 3: check the extracted tables (03_extract_datasets.py) against the authors' processed files and the numbers
reported in the articles, and derive the K5 cortisol-responder subset with the authors' rule.

    python3 code/04_validate_against_authors.py

Outputs (data_proc/)
  validation_vs_authors.csv   one row per comparison: what was compared, how many units agree, and the reported value
  k5_responders.csv           K5 participants classed as cortisol responders by the authors' rule (needs pyreadr)
Comparisons
  K2  article (Franco et al., 2021): 13 decision trials without a response from 8 participants; decision accuracy 83.1%
      (SD .08); optimisation performance 83.2% (SD .08); time on the optimisation task 43.5 s (SD 8.9)
  K4  authors' preprocessed KSDec_clean.csv and KSOpt_clean.csv (964pf); article: mean decision performance .78
  K5  authors' preprocessed ks_agg_data and stress_variables (nc94u; the CSV copies written by 02b_convert_rds.py);
      article (Doroc et al., 2025): 42 recruited, one cortisol outlier, 41 analysed, 27 responders, one participant with
      143 instead of 144 trials
  K7  article (Lu et al., 2025): 36 participants in the main experiment, 17 in the pilot, 80 knapsack trials each
Requires pandas and numpy. Without data_proc/k5_authors/*.csv the K5 comparisons with the authors' files are skipped.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
DP = PROJ / "data_proc"
K4P = DP / "unpacked" / "964pf" / "Behavioral Data" / "Work" / "preprocessed" / "preprocessed"
K5A = DP / "k5_authors"
ROWS = []


def row(ds, what, n, agree, reported="", detail="", ok=None):
    ok = (agree == n) if ok is None else ok
    ROWS.append({"dataset": ds, "comparison": what, "n_compared": n, "n_agree": agree, "reported": reported,
                 "ours": detail, "ok": bool(ok)})


def k2():
    d = pd.read_csv(DP / "trials_K2_dec.csv")
    o = pd.read_csv(DP / "trials_K2_opt.csv")
    nr = d[d.no_response == 1]
    row("K2", "decision trials without a response (trials / participants)", 2, int(len(nr) == 13) + int(nr.participant.nunique() == 8),
        "13 / 8", f"{len(nr)} / {nr.participant.nunique()}")
    acc = d[d.no_response == 0].groupby("participant").correct.mean()
    row("K2", "decision accuracy, mean (SD) over participants, trials with a response", 1,
        int(round(acc.mean(), 3) == 0.831 and round(acc.std(), 2) == 0.08), ".831 (.08)", f"{acc.mean():.4f} ({acc.std():.4f})")
    ok_trials = o[o.time_on_task_s >= 1]
    acc = ok_trials.groupby("participant").correct.mean()
    row("K2", "optimisation performance, mean (SD), trials submitted after >= 1 s", 1,
        int(round(acc.mean(), 3) == 0.832), ".832 (.08)", f"{acc.mean():.4f} ({acc.std():.4f})")
    early = o.groupby("participant").submitted.sum()
    keep = early[early > 0].index
    t = ok_trials[ok_trials.participant.isin(keep)].groupby("participant").time_on_task_s.mean()
    same = abs(t.mean() - 43.5) < 0.05 and abs(t.std() - 8.9) < 0.05
    row("K2", "optimisation time on task, mean (SD) s, excluding participants who never submitted early", 1, int(same),
        "43.5 (8.9); article: 3 participants excluded",
        f"{t.mean():.2f} ({t.std():.2f}); {len(early) - len(keep)} participants never submitted early in the files")


def k4():
    a = pd.read_csv(K4P / "KSDec_clean.csv")
    m = pd.read_csv(DP / "trials_K4_dec.csv")
    m["pID"] = m.participant.str.replace("K4_", "", regex=False)
    m["instanceNumber"] = m.instance_key.astype(int)
    j = m.merge(a, on=["pID", "instanceNumber"], how="outer", indicator=True, suffixes=("", "_a"))
    b = j[j._merge == "both"]
    agree = int(((b.answer == b.answer_a) & (b.correct == b.correct_a) & ((b.rt_answer_s - b.timeSpent).abs() < 1e-6)).sum())
    row("K4", "decision trials vs authors' KSDec_clean.csv (answer, correct, response time)", len(j), agree,
        f"{len(a)} rows in the authors' file", f"{len(m)} rows extracted; {int((j._merge != 'both').sum())} unmatched")
    acc = m.groupby("participant").correct.mean().mean()
    row("K4", "decision accuracy, mean over participants", 1, int(round(acc, 2) == 0.78), ".78", f"{acc:.4f}")
    ao = pd.read_csv(K4P / "KSOpt_clean.csv")
    mo = pd.read_csv(DP / "trials_K4_opt.csv")
    mo["pID"] = mo.participant.str.replace("K4_", "", regex=False)
    mo["instanceNumber"] = mo.instance_key.astype(int)
    jo = mo.merge(ao, on=["pID", "instanceNumber"], how="outer", indicator=True, suffixes=("", "_a"))
    bo = jo[jo._merge == "both"]
    agree = int(((bo.correct == bo.correct_a) & ((bo.time_on_task_s - bo.timeSpent).abs() < 1e-6)).sum())
    miss = jo[jo._merge == "left_only"]
    row("K4", "optimisation trials vs authors' KSOpt_clean.csv (correct, time on task)", len(bo), agree,
        f"{len(ao)} rows in the authors' file",
        f"{len(mo)} rows extracted; not in the authors' file: " +
        ", ".join(f"{r.pID} instance {r.instanceNumber} ({r.time_on_task_s:.2f} s)" for r in miss.itertuples()))


def k5():
    t = pd.read_csv(DP / "trials_K5_dec.csv")
    row("K5", "participants and sessions in the raw files", 2,
        int(t.participant.nunique() == 42) + int(t.groupby(["participant", "session"]).ngroups == 84), "42 recruited, 2 sessions each",
        f"{t.participant.nunique()} participants, {t.groupby(['participant', 'session']).ngroups} sessions")
    per = t.groupby("participant").size()
    row("K5", "participants with 143 instead of 144 trials", 1, int((per == 143).sum() == 1), "1",
        f"{int((per == 143).sum())} ({', '.join(per[per == 143].index)})")
    if not (K5A / "ks_agg_data.csv").exists():
        print("data_proc/k5_authors/ks_agg_data.csv is missing (run 02b_convert_rds.py): the comparisons with the "
              "authors' K5 files and the responder list are skipped (an existing k5_responders.csv is kept)")
        return
    k = pd.read_csv(K5A / "ks_agg_data.csv")
    t["ParticipantID"] = t.participant.str.replace("K5_", "", regex=False)
    t["stress"] = (t.condition == "stress").astype(int)
    t["inst_number"] = t.instance_key.astype(int)
    k["stress"] = k.stress.astype(int)
    k["inst_number"] = k.inst_number.astype(int)
    j = t.merge(k, on=["ParticipantID", "stress", "inst_number"], how="outer", indicator=True, suffixes=("", "_a"))
    b = j[j._merge == "both"]
    ans_a = b.answer_a.where(b.answer_a.isin([0, 1]))
    same = ((b.answer == ans_a) | (b.answer.isna() & ans_a.isna())) & (b.correct == b.correct_a) & \
           ((b.rt_answer_s - b.answer_time).abs() < 1e-6) & (b.session == b.session_a) & (b.trial == b.trial_a)
    only = sorted(j.loc[j._merge == "left_only", "ParticipantID"].unique())
    row("K5", "trials vs authors' ks_agg_data (answer, correct, answer time, session, trial order)", len(b), int(same.sum()),
        f"{len(k)} rows, {k.ParticipantID.nunique()} participants in the authors' file",
        f"{len(t)} rows extracted; only in ours: {', '.join(only) or 'none'} (the cortisol outlier)")
    tot = (b.time_on_task_s - b.time_on_task).abs() < 0.01
    miss = b[~tot]
    row("K5", "time on task vs authors' time_on_task (|diff| < 0.01 s)", len(b), int(tot.sum()), "",
        "differences only where the authors interpolated missing time stamps: " +
        ", ".join(f"{r.ParticipantID} stress={r.stress} trial {r.trial}" for r in miss.itertuples()),
        ok=bool(miss.time_on_task_s.isna().all()))
    sv = pd.read_csv(K5A / "stress_variables.csv")
    sv["stress"] = sv.stress.astype(int)
    means = sv.groupby(["ParticipantID", "stress"]).cortisol.mean().unstack()
    higher_mean = set(means.index[(means[1] - means[0]) > 0])
    inc = sv[["ParticipantID", "stress", "max_cort_diff"]].drop_duplicates().pivot(index="ParticipantID", columns="stress",
                                                                                     values="max_cort_diff")
    larger = set(inc.index[(inc[1] - inc[0]) > 0])
    resp = sorted(p for p in inc.index if p in higher_mean and p in larger and inc.loc[p, 1] > 1.5)
    pd.DataFrame({"participant": [f"K5_{p}" for p in resp], "ParticipantID": resp,
                  "max_cort_diff_stress": [inc.loc[p, 1] for p in resp]}).to_csv(DP / "k5_responders.csv", index=False)
    row("K5", "cortisol responders by the authors' rule", 1, int(len(resp) == 27), "27 of 41",
        f"{len(resp)} of {sv.ParticipantID.nunique()}")


def k7():
    t = pd.read_csv(DP / "trials_K7_dec.csv")
    n = t.groupby("sample").participant.nunique().to_dict()
    per = t.groupby("participant").size().unique().tolist()
    row("K7", "participants (main / pilot) and knapsack trials per participant", 3,
        int(n.get("main") == 36) + int(n.get("pilot") == 17) + int(per == [80]), "36 / 17; 80",
        f"{n.get('main')} / {n.get('pilot')}; {per}")


def main() -> int:
    for f in (k2, k4, k5, k7):
        f()
    out = pd.DataFrame(ROWS)
    out.to_csv(DP / "validation_vs_authors.csv", index=False)
    with pd.option_context("display.width", 220, "display.max_colwidth", 90):
        print(out[["dataset", "comparison", "n_compared", "n_agree", "reported", "ours", "ok"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
