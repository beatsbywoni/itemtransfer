#!/usr/bin/env python3
"""
3-A3 step 1: K8 trial table and instance definitions; K1 instance-level summary.

    python3 code/03b_extract_k8.py

K8 = Bowman, Coghill, Murawski & Bossaerts (2023), Science Advances 9, eadd4165: 40 participants, 4 sessions
(placebo PLC, methylphenidate MPH, modafinil MOD, dextroamphetamine DEX), 8 optimisation instances x 2 attempts per
session, 240 s per attempt. The archive (Zenodo 7633250 = github.com/bmmlab/PECO v1.0) holds one row per attempt
(Xall_figures.csv) with each instance's capacity, optimum, Sahni-k and value-weight correlation, but not the item
weights and values.

The eight instances are those of K1 = Murawski & Bossaerts (2016), Scientific Reports 6, 34851 (Supplementary
Table S1, CC BY 4.0). TABLE_S1 below is a transcription of that table; it is checked twice and the step fails if
either check fails:
  1. against the PDF: every value row and weight row must occur, in order, in the text of the PDF (pdftotext, or pypdf
     when pdftotext is missing; skipped with a warning if neither is available);
  2. against K8: for every instance, capacity, optimum (exhaustive search), Sahni-k, value-weight Pearson r and
     n log2(C) must equal the per-instance fields of Xall_figures.csv (instance_num 0-7 = Table S1 instances 1-8).
K1 itself has no public attempt-level data. Its Table S2 (instance properties and success rates over 308 submitted
attempts by 20 participants) is read from the PDF text when available, for an instance-level comparison only.

Inputs   data_raw/supplements/K8_bmmlab_PECO-v1.0.zip, data_raw/supplements/K1_Murawski_Bossaerts_2016_SciRep_SI.pdf
Outputs  data_proc/instances_K8.csv        same columns as instances.csv, plus the K8 authors' per-instance fields
         data_proc/trials_K8_opt.csv       one row per attempt, in the layout of the other optimisation tables
         data_proc/k1_table_s2.csv         K1 Table S2 rows that could be read from the PDF (if any)
         data_proc/extraction_checks_K8.csv
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics as M  # noqa: E402

PROJ = Path(__file__).resolve().parent.parent
SUP = PROJ / "data_raw" / "supplements"
ZIP = SUP / "K8_bmmlab_PECO-v1.0.zip"
PDF = SUP / "K1_Murawski_Bossaerts_2016_SciRep_SI.pdf"
OUT = PROJ / "data_proc"
# K1 Supplementary Table S1: instance -> (capacity, values, weights), items in table order
TABLE_S1 = {
    1: (1900, [500, 350, 505, 505, 640, 435, 465, 50, 220, 170], [750, 406, 564, 595, 803, 489, 641, 177, 330, 252]),
    2: (1044, [300, 350, 400, 450, 47, 20, 8, 70, 5, 5], [205, 252, 352, 447, 114, 50, 28, 251, 19, 20]),
    3: (850, [15, 14, 3, 3, 10, 9, 28, 28, 31, 25, 24, 1], [129, 144, 77, 77, 66, 60, 184, 184, 229, 184, 219, 72]),
    4: (1500, [37, 72, 106, 32, 45, 71, 23, 44, 85, 62], [50, 820, 700, 46, 220, 530, 107, 180, 435, 360]),
    5: (14, [2, 3, 4, 5, 6, 9, 8, 7, 6, 5, 8, 9], [3, 4, 6, 3, 5, 13, 6, 9, 2, 4, 7, 7]),
    6: (3800, [107, 35, 120, 206, 88, 34, 28, 110, 88, 101, 74, 53], [599, 196, 670, 1204, 502, 202, 145, 600, 453, 601, 404, 299]),
    7: (1300, [201, 84, 113, 303, 227, 251, 129, 147, 86, 127, 144, 167], [192, 80, 106, 288, 212, 240, 121, 140, 82, 120, 137, 160]),
    8: (265, [31, 141, 46, 30, 74, 105, 119, 160, 59, 71], [21, 97, 32, 21, 52, 75, 86, 116, 43, 54]),
}
CHECKS = []


def check(name, ok, detail="", kind="error"):
    CHECKS.append({"dataset": "K8", "check": name, "ok": bool(ok), "kind": kind, "detail": detail})


def h(s: str) -> str:          # same instance hash as 03_extract_datasets.py
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def canon(w, v) -> str:
    return "|".join(f"{a}:{b}" for a, b in sorted(zip(w, v)))


def pdf_text(path: Path):
    if not path.exists():
        return None, "PDF not found"
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout, "pdftotext"
    try:
        import pypdf
        return "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(path)).pages), "pypdf"
    except ImportError:
        return None, "neither pdftotext nor pypdf is available"


def numbers(text: str) -> list[int]:
    return [int(x.replace(",", "")) for x in re.findall(r"(?<![\d.])\d{1,3}(?:,\d{3})*(?![\d.])|(?<![\d.,])\d+(?![\d.,])",
                                                       text)]


def contains_run(haystack: list[int], needle: list[int]) -> bool:
    n = len(needle)
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))


def main() -> int:
    if not ZIP.exists():
        print(f"03b_extract_k8: {ZIP.relative_to(PROJ)} not found; run code/01b_fetch_supplements.py first")
        return 1
    with zipfile.ZipFile(ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith("/Xall_figures.csv") or n == "Xall_figures.csv")
        x = pd.read_csv(io.BytesIO(z.read(name)))
    check("archive file", True, f"{name}: {len(x)} rows x {x.shape[1]} columns", kind="finding")

    # 1. transcription against the PDF text
    text, how = pdf_text(PDF)
    if text is None:
        check("Table S1 transcription found in the PDF text", True, f"not checked: {how}", kind="finding")
    else:
        nums = numbers(text)
        missing = [f"instance {i} {lab}" for i, (c, v, w) in TABLE_S1.items()
                   for lab, row in (("values", v), ("weights", w)) if not contains_run(nums, row)]
        caps = [i for i, (c, v, w) in TABLE_S1.items() if c not in nums]
        check("Table S1 transcription found in the PDF text", not missing and not caps,
              f"read with {how}; all 16 value/weight rows and 8 capacities found" if not missing and not caps else
              f"read with {how}; not found: {', '.join(missing + [f'capacity of instance {i}' for i in caps])}")

    # 2. transcription against the K8 per-instance fields
    per = x.groupby("instance_num").agg(capacity=("capacity", "first"), solution_value=("solution_value", "first"),
                                        sahni_k=("sahni_k", "first"), r=("v_w_corr_pearson", "first"),
                                        complexity=("Complexity", "first"), mzn_props=("mzn_props", "first"),
                                        alpha=("alpha", "first"), n_values=("capacity", "nunique"))
    check("one capacity per instance in the archive", (per.n_values == 1).all(), str(per.n_values.to_dict()))
    rows = []
    for i, (c, v, w) in TABLE_S1.items():
        e = M.enumerate_instance(w, v, c)
        sk = M.sahni_k_opt(w, v, c, e["p_star"])
        r = M.value_weight_corr(w, v)
        cx = M.input_size(len(w), c)
        a = per.loc[i - 1]
        ok = (a.capacity == c and a.solution_value == e["p_star"] and a.sahni_k == sk and abs(a.r - r) < 1e-6
              and abs(a.complexity - cx) < 1e-6)
        check(f"instance {i}: capacity, optimum, Sahni-k, r and n log2 C equal K8 instance_num {i - 1}", ok,
              f"capacity {c}/{a.capacity:g}; optimum {e['p_star']}/{a.solution_value:g}; Sahni-k {sk}/{a.sahni_k:g}; "
              f"r {r:.6f}/{a.r:.6f}; n log2 C {cx:.4f}/{a.complexity:.4f}")
        n_part = x[x.instance_num == i - 1].participant_id.nunique()
        rows.append({"dataset": "K8", "variant": "optimisation", "sample": "main", "instance_key": i, "n_items": len(w),
                     "capacity": c, "target": np.nan, "weights": ",".join(map(str, w)), "values": ",".join(map(str, v)),
                     "hash_full": h(canon(w, v) + f"#c={c}#p="), "hash_items": h(canon(w, v)),
                     "hash_items_cap": h(canon(w, v) + f"#c={c}"), "sum_w": sum(w), "sum_v": sum(v),
                     "p_star": e["p_star"], "c_star": e["c_star"], "n_optimal_sets": e["n_optimal_sets"],
                     "n_participants": n_part, "n_trials": int((x.instance_num == i - 1).sum()),
                     "author_id": i - 1, "author_pOpt": a.solution_value, "author_sahni_k": a.sahni_k,
                     "author_vw_corr": a.r, "author_complexity": a.complexity, "author_mzn_props": a.mzn_props,
                     "author_alpha": a.alpha, "source_instances": "K1 Supplementary Table S1"})
    inst = pd.DataFrame(rows)
    inst.to_csv(OUT / "instances_K8.csv", index=False)

    # trial table (one row per attempt). The archive has no presentation order within a session, so `trial` is
    # instance x attempt in table order.
    t = pd.DataFrame({
        "dataset": "K8", "sample": "main", "participant": [f"K8_{int(p):02d}" for p in x.participant_id],
        "session": x.session_num.astype(int), "condition": x.treatment_cat, "session_date": "",
        "block": np.nan, "trial": (x.instance_num * 2 + x.attempt_num + 1).astype(int), "variant": "optimisation",
        "instance_key": (x.instance_num + 1).astype(int), "attempt": (x.attempt_num + 1).astype(int),
        "submitted": x.attempt_submitted.astype(int), "time_on_task_s": x.time_on_task,
        "correct": x.attempt_correct.astype(int), "profit_selected": x.attempt_value,
        "capacity_selected": x.attempt_weight, "profit_opt_task": x.solution_value, "items_selected": "",
        "n_clicks": x.length_of_sequence, "x_value_pct_optimum": x.attempt_value_pct_solution,
        "x_unique_sets_visited": x.num_unique_sets_in_seq, "x_old_treatment": x.old_treatment})
    hmap = dict(zip(inst.instance_key, inst.hash_full))
    t.insert(10, "hash_full", t.instance_key.map(hmap))
    t = t.sort_values(["participant", "session", "trial"]).reset_index(drop=True)
    t.to_csv(OUT / "trials_K8_opt.csv", index=False)
    per_ps = t.groupby(["participant", "session"]).size()
    check("participants x sessions x attempts", True,
          f"{t.participant.nunique()} participants, {len(per_ps)} sessions, attempts per session "
          f"{sorted(per_ps.unique().tolist())}, {len(t)} rows (complete design 40 x 4 x 16 = 2,560)", kind="finding")
    ok_corr = (t.correct == (t.profit_selected == t.profit_opt_task).astype(int)).all()
    check("correct = attempt value equals the optimum", ok_corr,
          f"{int((t.correct == (t.profit_selected == t.profit_opt_task).astype(int)).sum())}/{len(t)} rows")
    over = t[(t.capacity_selected > t.instance_key.map(dict(zip(inst.instance_key, inst.capacity))))]
    check("submitted attempts within capacity", over.empty, f"{len(over)} attempts over capacity")
    diff = x[x.old_treatment.notna() & (x.old_treatment != x.treatment_cat)]
    check("treatment_cat agrees with old_treatment", diff.empty,
          f"{len(diff)} rows differ, {x.old_treatment.isna().sum()} rows without old_treatment; treatment_cat is used "
          "(the README notes that participant records were re-ordered)", kind="finding")
    check("time on task within the 240 s limit", (t.time_on_task_s <= 240.5).all(),
          f"max {t.time_on_task_s.max():.3f} s; not submitted: {int((t.submitted == 0).sum())}")

    # K1 Table S2 (instance-level, from the PDF text)
    if text is not None:
        props = {"Number of available items": "n_items", "Number of items in solution": "n_items_solution",
                 "Pearson correlation value/weight": "r_value_weight_printed", "Sahni-k": "sahni_k",
                 "Success rate": "success_rate", "Mean attempt value (% of solution value)": "mean_value_ratio"}
        s2 = {}
        for label, col in props.items():
            m = re.search(re.escape(label) + r"[^\n\d-]*((?:[-\d.,]+\s+){7}[-\d.,]+)", text)
            if m:
                s2[col] = [float(z.replace(",", "")) for z in m.group(1).split()]
        if s2:
            k1 = pd.DataFrame({"instance": range(1, 9), **s2})
            k1.to_csv(OUT / "k1_table_s2.csv", index=False)
            if "sahni_k" in s2:
                mine = [M.sahni_k_opt(w, v, c) for c, v, w in TABLE_S1.values()]
                check("K1 Table S2 Sahni-k equals the recomputed Sahni-k", mine == [int(z) for z in s2["sahni_k"]],
                      f"Table S2 {s2['sahni_k']}; recomputed {mine}")
            if "r_value_weight_printed" in s2:
                mine = [round(M.value_weight_corr(w, v), 3) for c, v, w in TABLE_S1.values()]
                off = [i + 1 for i, (a, b) in enumerate(zip(s2["r_value_weight_printed"], mine)) if abs(a - b) > 0.0015]
                check("K1 Table S2 value-weight r equals the r recomputed from Table S1", not off,
                      f"differs for instance {off}: printed {[s2['r_value_weight_printed'][i - 1] for i in off]}, "
                      f"recomputed {[mine[i - 1] for i in off]} (K8's archive has the recomputed value)" if off else
                      "all 8 agree", kind="finding")
            check("K1 Table S2 rows read from the PDF", True, ", ".join(s2), kind="finding")
        else:
            check("K1 Table S2 rows read from the PDF", False, "no rows matched", kind="finding")

    pd.DataFrame(CHECKS).to_csv(OUT / "extraction_checks_K8.csv", index=False)
    bad = [c for c in CHECKS if not c["ok"] and c["kind"] == "error"]
    print(f"K8: {len(inst)} instances, {len(t)} attempts; checks {len(CHECKS)}, errors {len(bad)}")
    for c in CHECKS:
        if not c["ok"] or c["kind"] == "finding":
            print(f"  {'ERROR  ' if (not c['ok'] and c['kind'] == 'error') else 'FINDING'} {c['check']}: {c['detail']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
