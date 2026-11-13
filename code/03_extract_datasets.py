#!/usr/bin/env python3
"""
3-A2 step 2: read the four datasets in their original formats and write instance and trial tables.

    python3 code/03_extract_datasets.py

Inputs
  data_proc/unpacked/            written by 02_unpack_raw.py (K2, K4, K5 raw task output files)
  data_raw/pks4b/Data/           K7 csv files (read directly)
Outputs (data_proc/)
  instances.csv                  one row per instance as used in a dataset x variant x sample, with content hashes and
                                 the optimum recomputed by enumeration (2^n subsets, n <= 8)
  trials_K2_dec.csv, trials_K2_opt.csv, trials_K4_dec.csv, trials_K4_opt.csv, trials_K5_dec.csv, trials_K7_dec.csv
                                 trial-level rows in a common column layout (dataset-specific columns are kept with a
                                 prefix); the codebook and the harmonised table are built in 3-A3
  extraction_checks.csv          consistency checks: instance numbering within datasets, recomputed solutions against the
                                 authors' flags, response-time fields against the time stamps, trial counts
Conventions
  answer: 1 = YES, 0 = NO, NA = no response in time. correct: 1/0 as recorded by the task (no response = 0).
  rt_answer_s: time on the answer screen until the key press (decision tasks with a separate answer screen).
  time_on_task_s: time from the onset of the full problem to the end of the solving stage, only where participants could
  end that stage themselves (K5, K7, optimisation tasks); NA where the solving stage had a fixed length (K2, K4 decision).
Requires pandas and numpy only.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
UNP = PROJ / "data_proc" / "unpacked"
OUT = PROJ / "data_proc"
DIRS = {
    "K2": UNP / "fxdwq" / "Behavioural Data" / "Behavioural Data",
    "K4": UNP / "964pf" / "Behavioral Data" / "Raw" / "Raw" / "Raw",
    "K5": UNP / "hjq8z" / "Behavioural data" / "Knapsack raw txt files" / "Knapsack raw txt files",
    "K7": PROJ / "data_raw" / "pks4b" / "Data",
}
FNAME = re.compile(r"^(?P<pid>[^_]+)_(?P<when>.+?)_(?P<task>Dec|Opt|End)_(?P<kind>TrialInfo|InstancesInfo|TimeStamps|Clicks)\.txt$")
CHECKS = []


def check(dataset, name, ok, detail="", kind="error"):
    """kind 'error': the extraction itself is inconsistent (the script exits with status 1);
    kind 'finding': the source data disagree with themselves or with the authors' metadata (reported, not fatal)."""
    CHECKS.append({"dataset": dataset, "check": name, "ok": bool(ok), "kind": kind, "detail": detail})


# ---------------------------------------------------------------------------------------------------------------------
# instance helpers
# ---------------------------------------------------------------------------------------------------------------------
def ints(s):
    return [int(float(x)) for x in str(s).replace(" ", "").split(",") if x != ""]


def canon(w, v):
    return "|".join(f"{a}:{b}" for a, b in sorted(zip(w, v)))


def h(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def solve(w, v, c, p=None):
    """Exact optimum by enumeration; for the decision problem also the number of witnesses (subsets with weight <= c and
    value >= p)."""
    n = len(w)
    best = -1
    best_sets = []
    witnesses = 0
    for mask in range(1 << n):
        sw = sv = 0
        for i in range(n):
            if mask >> i & 1:
                sw += w[i]
                sv += v[i]
        if sw > c:
            continue
        if p is not None and sv >= p:
            witnesses += 1
        if sv > best:
            best, best_sets = sv, [mask]
        elif sv == best:
            best_sets.append(mask)
    cap_opt = min(sum(w[i] for i in range(n) if m >> i & 1) for m in best_sets)
    return {"p_star": best, "c_star": cap_opt, "n_optimal_sets": len(best_sets), "n_witness": witnesses if p is not None else None}


# ---------------------------------------------------------------------------------------------------------------------
# reading the Unity task output files (K2, K4, K5)
# ---------------------------------------------------------------------------------------------------------------------
def read_unity(path: Path):
    meta, header, rows = {}, None, []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if header is None:
            if line.startswith(("block;", "instanceNumber;")):
                header = line.split(";")
            elif ";" in line:
                meta["legend"] = line
            elif ":" in line:
                k, _, val = line.partition(":")
                meta[k.strip()] = val.strip()
            continue
        if not line.strip():
            continue
        f = line.split(";")
        if len(f) > len(header) and all(x == "" for x in f[len(header):]):
            f = f[:len(header)]
        if len(f) != len(header):
            f = (f + [""] * len(header))[:len(header)]
        rows.append(dict(zip(header, f)))
    return meta, header, rows


def discover(folder: Path, task: str):
    groups = defaultdict(dict)
    for p in sorted(folder.iterdir()):
        m = FNAME.match(p.name)
        if m and m.group("task") == task:
            when = dt.datetime.strptime(m.group("when"), "%d %B, %Y, %H-%M")
            groups[(m.group("pid"), when)][m.group("kind")] = p
    return dict(sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def events_by_trial(ts_rows):
    ev = defaultdict(list)
    for r in ts_rows:
        try:
            ev[(int(r["block"]), int(r["trial"]))].append((r["eventType"], float(r["elapsedTime"])))
        except (ValueError, KeyError):
            continue
    return ev


# ---------------------------------------------------------------------------------------------------------------------
# K2 and K4: decision and optimisation tasks (same software family)
# ---------------------------------------------------------------------------------------------------------------------
def k24_decision(ds):
    trials, inst = [], {}
    for (pid, when), files in discover(DIRS[ds] / "Dec", "Dec").items():
        meta, _, tr = read_unity(files["TrialInfo"])
        _, _, ir = read_unity(files["InstancesInfo"])
        ev = events_by_trial(read_unity(files["TimeStamps"])[2]) if "TimeStamps" in files else {}
        imap = {int(r["instanceNumber"]): r for r in ir}
        rt_field = "timeSpent" if "timeSpent" in tr[0] else "timeSpentAprox"
        for r in tr:
            k = int(r["instanceNumber"])
            i = imap[k]
            w, v, c, p = ints(i["w"]), ints(i["v"]), int(i["c"]), int(i["p"])
            key = str(k)
            rec = inst.setdefault(key, {"w": w, "v": v, "c": c, "p": p, "author_id": i["id"], "author_type": i["type"],
                                        "author_sol": i["sol"], "sessions": set(), "trials": 0})
            if (rec["w"], rec["v"], rec["c"], rec["p"]) != (w, v, c, p):
                check(ds, "decision instance number maps to one content", False, f"{pid} instance {k}")
            rec["sessions"].add(pid)
            rec["trials"] += 1
            e = dict(ev.get((int(r["block"]), int(r["trial"])), []))
            t11, t2, t21 = e.get("11"), e.get("2"), e.get("21")
            ans = int(r["answer"])
            rt_ts = (t21 - t2) / 1000 if t2 is not None and t21 is not None else np.nan
            # K2's TrialInfo 'timeSpent' is the length of the answer screen (about 2 s on every trial), not the response
            # time; the key press is only in the time stamps (event 21). K4's 'timeSpentAprox' is the response time.
            rt = rt_ts if ds == "K2" else num(r[rt_field])
            trials.append({
                "dataset": ds, "sample": "main", "participant": f"{ds}_{pid}", "session": 1, "condition": "",
                "session_date": when.date().isoformat(), "block": int(r["block"]), "trial": int(r["trial"]),
                "variant": "decision", "instance_key": key, "answer": ans if ans in (0, 1) else np.nan,
                "correct": int(r["correct"]), "no_response": int(ans not in (0, 1)),
                "rt_answer_s": rt if ans in (0, 1) else np.nan, "time_on_task_s": np.nan, "timed_out": np.nan,
                "solve_window_s": (t2 - t11) / 1000 if t11 is not None and t2 is not None else np.nan,
                "rt_answer_ts_s": rt_ts, "x_rt_field_trialinfo": num(r[rt_field]),
                "x_randomYes": r.get("randomYes(1=Left:No/Right:Yes)"), "x_error": r.get("error", ""),
            })
    return trials, inst


def k24_optimisation(ds):
    trials, inst = [], {}
    for (pid, when), files in discover(DIRS[ds] / "Opt", "Opt").items():
        _, _, tr = read_unity(files["TrialInfo"])
        _, _, ir = read_unity(files["InstancesInfo"])
        clicks = defaultdict(int)
        if "Clicks" in files:
            for r in read_unity(files["Clicks"])[2]:
                try:
                    clicks[(int(r["block"]), int(r["trial"]))] += 1
                except (ValueError, KeyError):
                    pass
        imap = {int(r["instanceNumber"]): r for r in ir}
        for r in tr:
            k = int(r["instanceNumber"])
            i = imap[k]
            w, v, c = ints(i["w"]), ints(i["v"]), int(i["c"])
            key = str(k)
            rec = inst.setdefault(key, {"w": w, "v": v, "c": c, "p": None, "author_id": i["id"], "author_type": i["type"],
                                        "author_pOpt": i.get("pOpt"), "author_cOpt": i.get("cOpt"),
                                        "author_itemsOpt": i.get("itemsOpt"), "sessions": set(), "trials": 0})
            if (rec["w"], rec["v"], rec["c"]) != (w, v, c):
                check(ds, "optimisation instance number maps to one content", False, f"{pid} instance {k}")
            rec["sessions"].add(pid)
            rec["trials"] += 1
            trials.append({
                "dataset": ds, "sample": "main", "participant": f"{ds}_{pid}", "session": 1, "condition": "",
                "session_date": when.date().isoformat(), "block": int(r["block"]), "trial": int(r["trial"]),
                "variant": "optimisation", "instance_key": key, "submitted": int(r["submitted"]),
                "time_on_task_s": num(r["timeSpent"]), "correct": int(r["correct"]),
                "profit_selected": num(r["profitSel"]), "capacity_selected": num(r["capacitySel"]),
                "profit_opt_task": num(r["profitOpt"]), "items_selected": r["itemsSelected"],
                "n_clicks": clicks.get((int(r["block"]), int(r["trial"])), 0), "x_error": r.get("error", ""),
            })
    return trials, inst


# ---------------------------------------------------------------------------------------------------------------------
# K5: stress study (sessions are separate files; one session was restarted twice and is split over three files)
# ---------------------------------------------------------------------------------------------------------------------
def k5_decision():
    trials, inst = [], {}
    by_session = defaultdict(list)
    for (code, when), files in discover(DIRS["K5"], "End").items():
        by_session[code].append((when, files))
    for code, parts in sorted(by_session.items()):
        stress, session, tod, pnum = int(code[1]), int(code[2]), code[3], code[4:7]
        seq = 0
        n_pause = 0
        for when, files in sorted(parts, key=lambda x: x[0]):
            _, _, tr = read_unity(files["TrialInfo"])
            _, _, ir = read_unity(files["InstancesInfo"])
            ev = events_by_trial(read_unity(files["TimeStamps"])[2])
            imap = {int(r["instanceNumber"]): r for r in ir}
            for r in tr:
                if r.get("error", "") != "" or r["answer"] == "3":
                    n_pause += 1               # rows written when the task was paused for a saliva sample
                    continue
                seq += 1
                k = int(r["instanceNumber"])
                i = imap[k]
                w, v, c, p = ints(i["w"]), ints(i["v"]), int(i["c"]), int(i["p"])
                key = str(k)
                rec = inst.setdefault(key, {"w": w, "v": v, "c": c, "p": p, "author_id": i["id"], "author_type": i["type"],
                                            "author_sol": i["sol"], "sessions": set(), "trials": 0})
                if (rec["w"], rec["v"], rec["c"], rec["p"]) != (w, v, c, p):
                    check("K5", "instance number maps to one content", False, f"{code} instance {k}")
                rec["sessions"].add(code)
                rec["trials"] += 1
                e = ev.get((int(r["block"]), int(r["trial"])), [])
                names = [x[0] for x in e]
                t_trial = next((t for n, t in e if n == "Trial"), None)
                t_end = next((t for n, t in e if n in ("ParticipantSkip", "TrialAnswer")), None)
                t_ans_screen = next((t for n, t in e if n == "TrialAnswer"), None)
                t_ans = next((t for n, t in e if n == "ParticipantAnswer"), None)
                ans = int(r["answer"])
                tot = (t_end - t_trial) / 1000 if t_trial is not None and t_end is not None else np.nan
                trials.append({
                    "dataset": "K5", "sample": "main", "participant": f"K5_P{pnum}", "session": session,
                    "condition": "stress" if stress == 1 else "control", "session_date": when.date().isoformat(),
                    "block": (seq - 1) // 12 + 1, "trial": seq, "variant": "decision", "instance_key": key,
                    "answer": ans if ans in (0, 1) else np.nan, "correct": int(r["correct"]),
                    "no_response": int(ans not in (0, 1)), "rt_answer_s": num(r["timeSpent"]),
                    "time_on_task_s": min(tot, 40.0) if tot == tot else np.nan,
                    "timed_out": (0 if "ParticipantSkip" in names else 1) if e else np.nan,
                    "solve_window_s": np.nan,
                    "rt_answer_ts_s": (t_ans - t_ans_screen) / 1000 if t_ans is not None and t_ans_screen is not None else np.nan,
                    "x_perceived_difficulty": num(r.get("complexAnswer")), "x_session_code": code,
                    "x_time_of_session": tod, "x_source_file": files["TrialInfo"].name, "x_file_trial": int(r["trial"]),
                    "x_randomYes": r.get("randomYes(1=Left:No/Right:Yes)"),
                })
        check("K5", f"session {code}: trials kept", True, f"{seq} trials, {n_pause} pause rows dropped, {len(parts)} file(s)")
    return trials, inst


# ---------------------------------------------------------------------------------------------------------------------
# K7: csv files (main experiment and pilot)
# ---------------------------------------------------------------------------------------------------------------------
def k7_decision():
    trials, inst = [], {}
    for sample, fname in (("main", "KP80_individual_trial.csv"), ("pilot", "KP80_individual_trial_pilot.csv")):
        d = pd.read_csv(DIRS["K7"] / fname)
        for r in d.itertuples(index=False):
            w, v, c, p = ints(r.item_weights), ints(r.item_values), int(r.target_capacity), int(r.target_profit)
            key = str(int(r.instance_ID))
            rec = inst.setdefault((sample, key), {"w": w, "v": v, "c": c, "p": p, "author_sol": int(r.solution),
                                                   "author_ic": float(r.ic), "alpha_c": float(r.alpha_c),
                                                   "alpha_p": float(r.alpha_p), "author_hard": bool(r.hardness),
                                                   "sessions": set(), "trials": 0})
            if (rec["w"], rec["v"], rec["c"], rec["p"]) != (w, v, c, p):
                check("K7", "instance_ID maps to one content", False, f"{sample} {key}")
            rec["sessions"].add(int(r.subID))
            rec["trials"] += 1
            ch = int(r.sub_choice)
            trials.append({
                "dataset": "K7", "sample": sample, "participant": f"K7_{sample}_{int(r.subID):02d}", "session": 1,
                "condition": "feedback" if bool(r.feedbackON) else "no_feedback", "session_date": "",
                "block": int(r.block), "trial": int(r.trial), "variant": "decision", "instance_key": key,
                "answer": ch if ch in (0, 1) else np.nan, "correct": int(r.correctness), "no_response": int(ch not in (0, 1)),
                "rt_answer_s": np.nan, "time_on_task_s": float(r.timeSpent),
                "timed_out": int(float(r.timeSpent) >= 24.999), "solve_window_s": np.nan, "rt_answer_ts_s": np.nan,
                "x_hardness": bool(r.hardness), "x_ic_round": float(r.ic_round),
            })
    return trials, inst


# ---------------------------------------------------------------------------------------------------------------------
def instance_rows(ds, variant, inst, sample_of=lambda key: ("main", key)):
    rows = []
    for key, rec in inst.items():
        sample, ikey = sample_of(key)
        w, v, c, p = rec["w"], rec["v"], rec["c"], rec["p"]
        sol = solve(w, v, c, p)
        sum_v = sum(v)
        row = {"dataset": ds, "variant": variant, "sample": sample, "instance_key": ikey, "n_items": len(w),
               "capacity": c, "target": p, "weights": ",".join(map(str, w)), "values": ",".join(map(str, v)),
               "hash_full": h(canon(w, v) + f"#c={c}#p={p if p is not None else ''}"), "hash_items": h(canon(w, v)),
               "hash_items_cap": h(canon(w, v) + f"#c={c}"),
               "sum_w": sum(w), "sum_v": sum_v, "p_star": sol["p_star"], "c_star": sol["c_star"],
               "n_optimal_sets": sol["n_optimal_sets"], "n_participants": len(rec["sessions"]), "n_trials": rec["trials"]}
        if p is not None:
            row.update(sat=int(sol["p_star"] >= p), n_witness=sol["n_witness"], ic=abs(p - sol["p_star"]) / sum_v,
                       ic_signed=(p - sol["p_star"]) / sum_v)
        for k in ("author_id", "author_type", "author_sol", "author_pOpt", "author_cOpt", "author_itemsOpt", "author_ic",
                  "alpha_c", "alpha_p", "author_hard"):
            if k in rec:
                row[k] = rec[k]
        if ds in ("K2", "K4") and "author_id" in rec:      # ids look like "98-0.41-0.63" (decision) or "144-0.41"
            parts = str(rec["author_id"]).split("-")
            row["alpha_c"] = float(parts[1]) if len(parts) > 1 else np.nan
            row["alpha_p"] = float(parts[2]) if len(parts) > 2 else np.nan
        rows.append(row)
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    all_inst = []
    tables = {}
    for ds in ("K2", "K4"):
        t, i = k24_decision(ds)
        tables[f"{ds}_dec"] = t
        all_inst += instance_rows(ds, "decision", i)
        t, i = k24_optimisation(ds)
        tables[f"{ds}_opt"] = t
        all_inst += instance_rows(ds, "optimisation", i)
    t, i = k5_decision()
    tables["K5_dec"] = t
    all_inst += instance_rows("K5", "decision", i)
    t, i = k7_decision()
    tables["K7_dec"] = t
    all_inst += instance_rows("K7", "decision", i, sample_of=lambda key: key)

    inst = pd.DataFrame(all_inst).sort_values(["dataset", "variant", "sample", "instance_key"],
                                              key=lambda s: s.map(lambda x: (0, int(x)) if str(x).isdigit() else (1, str(x))))
    # recomputed solutions against the authors' flags
    for (ds, var), g in inst.groupby(["dataset", "variant"]):
        if var == "decision":
            col = "author_sol"
            if col in g:
                a = pd.to_numeric(g[col], errors="coerce")
                ok = (a == g["sat"]).all()
                check(ds, "recomputed satisfiability equals the authors' flag", ok,
                      f"{int((a == g['sat']).sum())}/{len(g)} agree")
            if ds == "K5":
                a = pd.to_numeric(g["author_type"], errors="coerce")
                diff = (a - g["ic_signed"]).abs()
                off = g[diff > 1e-9]
                detail = "; ".join(f"instance {r.instance_key}: authors' value implies p* = "
                                   f"{r.target - float(r.author_type) * r.sum_v:.0f}, enumeration gives {r.p_star}"
                                   for r in off.itertuples())
                check(ds, "recomputed signed IC equals the authors' 'type' column", off.empty,
                      f"{len(g) - len(off)}/{len(g)} agree" + (f"; {detail}" if detail else ""), kind="finding")
            if ds == "K7":
                dev = float(np.nanmax(np.abs(g["author_ic"] - g["ic"])))
                check(ds, "recomputed IC equals the authors' ic column", dev < 1e-6, f"max |diff| = {dev:.3g}")
        else:
            a = pd.to_numeric(g["author_pOpt"], errors="coerce")
            ok = (a == g["p_star"]).all()
            check(ds, "recomputed optimum equals the authors' pOpt", ok, f"{int((a == g['p_star']).sum())}/{len(g)} agree")
    inst.to_csv(OUT / "instances.csv", index=False)

    common = ["dataset", "sample", "participant", "session", "condition", "session_date", "block", "trial", "variant",
              "instance_key"]
    for name, t in tables.items():
        df = pd.DataFrame(t)
        hmap = inst[(inst.dataset == df.dataset.iloc[0]) & (inst.variant == df.variant.iloc[0])]
        hmap = hmap.set_index(["sample", "instance_key"])["hash_full"]
        df["hash_full"] = [hmap.get((s, k)) for s, k in zip(df["sample"], df["instance_key"])]
        cols = common + ["hash_full"] + [c for c in df.columns if c not in common + ["hash_full"]]
        df = df[cols].sort_values(["sample", "participant", "session", "trial"]).reset_index(drop=True)
        df.to_csv(OUT / f"trials_{name}.csv", index=False)
        per = df.groupby(["participant", "session"]).size()
        check(df.dataset.iloc[0], f"{name}: participants x sessions x trials", True,
              f"{df.participant.nunique()} participants, {len(per)} sessions, trials per session {sorted(per.unique().tolist())}, "
              f"{len(df)} rows")
        if "rt_answer_ts_s" in df and df["rt_answer_ts_s"].notna().any():
            src = "x_rt_field_trialinfo" if "x_rt_field_trialinfo" in df else "rt_answer_s"
            both = df[[src, "rt_answer_ts_s"]].dropna()
            dev = float((both[src] - both["rt_answer_ts_s"]).abs().median()) if len(both) else np.nan
            same = dev < 0.05
            check(df.dataset.iloc[0], f"{name}: TrialInfo time field vs answer time from time stamps (median |diff| s)",
                  same or df.dataset.iloc[0] == "K2",
                  f"{dev:.4f} s over {len(both)} trials" + ("" if same else "; the TrialInfo field is the answer-screen "
                                                                     "length, so the time stamps are used"))
        if "solve_window_s" in df and df["solve_window_s"].notna().any():
            s = df["solve_window_s"].dropna()
            long = df[df["solve_window_s"] > 22.1]
            check(df.dataset.iloc[0], f"{name}: solving stage length (s)", long.empty,
                  f"min {s.min():.3f}, median {s.median():.3f}, max {s.max():.3f}; longer than 22.1 s: " +
                  (", ".join(f"{r.participant} block {r.block} trial {r.trial} ({r.solve_window_s:.1f} s)"
                             for r in long.itertuples()) or "none"), kind="finding")
    pd.DataFrame(CHECKS).to_csv(OUT / "extraction_checks.csv", index=False)
    bad = [c for c in CHECKS if not c["ok"] and c["kind"] == "error"]
    found = [c for c in CHECKS if not c["ok"] and c["kind"] == "finding"]
    print(f"instances: {len(inst)} rows; trial tables: " + ", ".join(f"{k} {len(v)}" for k, v in tables.items()))
    print(f"checks: {len(CHECKS)}; extraction errors {len(bad)}; source-data findings {len(found)}")
    for c in bad:
        print("  ERROR  ", c)
    for c in found:
        print("  FINDING", c)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
