#!/bin/bash
# Runs the whole simulation study. Resume-safe: finished chunks are skipped, so the script can be restarted.
# Install the package first (pip install . in the repository root).
cd "$(dirname "$0")" || exit 1
set -e
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python sim00_validate.py
python sim01_separation.py
python sim04_ranking.py
python sim02_design_features.py
python sim03_operating.py
python sim05_ordering_interval.py
python sim06_comparators.py
python sim07_noncollapsibility.py
python sim08_tolerance.py
python make_figures.py
python make_tables.py
