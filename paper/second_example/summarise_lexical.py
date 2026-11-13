"""Print and save, for each item family, the counts that PROVENANCE.md compares with the data papers.

Usage:  python3 -I summarise_lexical.py [--root original] [--elp-items elp_bates/Items.csv.gz]
Writes summary_lexical.csv and summary_lexical.json next to this script.
The optional --elp-items file is a THIRD-PARTY mirror of the elexicon.wustl.edu item table; it is used only to
check recomputed word accuracy and length against published values and is labelled as such in the output.
"""
import argparse, json, os, sys, time, platform
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np, pandas as pd
import load_lexical as L

PAPER = {  # counts stated in the data papers / OSF project descriptions (sources in PROVENANCE.md)
    "ELP": {"participants": 816, "words": 40481},
    "BLP": {"participants": 78, "words": 28730},
    "DLP": {"participants": 39, "words": 14089},
    "MEGALEX": {"participants": 96, "words": 28466},
}
PROBE = {  # FEASIBILITY.md table (GitHub mirrors)
    "ELP": {"participants": 814, "words": 40481, "trials": 1372240, "median": 34, "min": 30, "acc": 0.839},
    "BLP": {"participants": 78, "words": 28728, "trials": 1120470, "median": 39, "min": 38, "acc": 0.757},
    "DLP": {"participants": 39, "words": 14089, "trials": 549471, "median": 39, "min": 39, "acc": 0.841},
    "MEGALEX": {"participants": 96, "words": 28466, "trials": 1311740, "median": 46, "min": 37, "acc": 0.889},
}
PUB = {"ELP": ("pub_I_Mean_Accuracy", "pub_Length"), "BLP": ("pub_accuracy", "pub_nletters"),
       "DLP": ("pub_accuracy", "pub_nchar"), "MEGALEX": ("pub_acy", "pub_nblettres")}

ap = argparse.ArgumentParser()
ap.add_argument("--root", default=L.DEFAULT_ROOT)
ap.add_argument("--elp-items", default=None)
a = ap.parse_args()
t0 = time.time()
rows, logs = [], {}
for fam in L.FAMILIES:
    tr, it, log = L.load_elp(a.root, items_csv=a.elp_items) if fam == "ELP" else L.load_family(fam, a.root)
    logs[fam] = log
    per = tr.groupby("item")["correct"].agg(["size", "mean"])
    dup = int(tr.duplicated(["participant", "item"]).sum())
    r = {"family": fam, "participants": int(tr["participant"].nunique()), "words": int(tr["item"].nunique()),
         "trials": int(len(tr)), "resp_per_word_median": float(per["size"].median()),
         "resp_per_word_min": int(per["size"].min()), "resp_per_word_max": int(per["size"].max()),
         "mean_accuracy_trials": round(float(tr["correct"].mean()), 6),
         "mean_accuracy_items": round(float(per["mean"].mean()), 6),
         "duplicate_participant_item_rows": dup, "items_table_rows": int(len(it)),
         "items_not_in_trials": int((~it["item"].isin(per.index)).sum()),
         "paper_participants": PAPER[fam]["participants"], "paper_words": PAPER[fam]["words"],
         "probe_participants": PROBE[fam]["participants"], "probe_words": PROBE[fam]["words"],
         "probe_trials": PROBE[fam]["trials"]}
    acc_col, len_col = PUB[fam]
    if acc_col in it:
        m = it.set_index("item").join(per)
        pa = pd.to_numeric(m[acc_col], errors="coerce")
        ok = pa.notna() & m["mean"].notna()
        r["published_accuracy_n"] = int(ok.sum())
        r["published_accuracy_max_abs_diff"] = round(float((pa[ok] - m.loc[ok, "mean"]).abs().max()), 6)
        r["published_accuracy_share_within_0.005"] = round(float(((pa[ok] - m.loc[ok, "mean"]).abs() <= 0.005).mean()), 6)
        r["published_accuracy_pearson"] = round(float(np.corrcoef(pa[ok], m.loc[ok, "mean"])[0, 1]), 6)
        pl = pd.to_numeric(m[len_col], errors="coerce"); okl = pl.notna()
        r["published_length_n"] = int(okl.sum())
        r["published_length_equal_share"] = round(float((pl[okl] == m.loc[okl, "length"]).mean()), 6)
    rows.append(r)
    print(f"\n== {fam}")
    for k, v in r.items():
        print(f"   {k}: {v}")
    print("   log:", json.dumps(log, ensure_ascii=False))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(HERE, "summary_lexical.csv"), index=False)
meta = {"run_seconds": round(time.time() - t0, 1), "python": platform.python_version(), "numpy": np.__version__,
        "pandas": pd.__version__, "root": a.root, "elp_items": a.elp_items, "logs": logs, "summary": rows}
json.dump(meta, open(os.path.join(HERE, "summary_lexical.json"), "w"), indent=1, ensure_ascii=False)
print("\nrun seconds", meta["run_seconds"])
