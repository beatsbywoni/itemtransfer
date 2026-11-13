#!/usr/bin/env python3
"""
3-A2 step 1b: convert the K5 authors' processed R data files to CSV, so that later steps need pandas only.

    python3 code/02b_convert_rds.py

Reads data_raw/nc94u/ks_agg_data.rds and stress_variables.rds (Doroc, Yadav & Murawski, 2025; OSF nc94u, CC-BY 4.0) and
writes data_proc/k5_authors/ks_agg_data.csv and stress_variables.csv, plus a small README with the source hashes.
Requires pandas and pyreadr (pip install pyreadr). Run once; existing outputs with identical content are left as they are.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
SRC = PROJ / "data_raw" / "nc94u"
OUT = PROJ / "data_proc" / "k5_authors"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    try:
        import pyreadr
    except ImportError:
        print("pyreadr is needed: pip install pyreadr")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    notes = ["# K5 authors' processed data as CSV", "",
             "Converted by code/02b_convert_rds.py from the R data files on OSF (nc94u). Column meanings: see",
             "data_raw/cusk9/Analysis scripts/wrangling.Rmd. P012 (the cortisol outlier) is not in these files.", "",
             "| source | sha256 | rows | columns | output |", "|---|---|---|---|---|"]
    for name in ("ks_agg_data", "stress_variables"):
        src = SRC / f"{name}.rds"
        df = pyreadr.read_r(str(src))[None]
        dest = OUT / f"{name}.csv"
        text = df.to_csv(index=False, lineterminator="\n")
        if not dest.exists() or dest.read_text(encoding="utf-8") != text:
            dest.write_text(text, encoding="utf-8")
        notes.append(f"| data_raw/nc94u/{name}.rds | `{sha(src)}` | {len(df)} | {df.shape[1]} | {dest.name} |")
        print(f"{name}: {df.shape[0]} rows x {df.shape[1]} columns -> {dest.relative_to(PROJ)}")
    (OUT / "README.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
