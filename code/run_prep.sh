#!/bin/bash
# Rebuild data_proc/ for the knapsack example from the raw files in data_raw/.
# Usage (from the repository root, bash on Linux, macOS or WSL):
#   bash code/run_3a_download.sh     # once, needs internet: downloads the authors' repositories into data_raw/
#   bash code/run_prep.sh            # no internet needed
# Needs Python 3.9+ with pandas and numpy. Step 08 needs MiniZinc with Gecode (the article used MiniZinc 2.9.3
# with Gecode 6.3.0); without MiniZinc the step is skipped and the distributed data_proc/solver_effort_gecode.csv is kept.
# Optional, not needed for the article: 02b_convert_rds.py (needs pyreadr) and 04_validate_against_authors.py
# compare the tables with the authors' processed files and write data_proc/k5_responders.csv, which fills the
# column k5_responder of the harmonised table. Run them after step 03 and before step 10.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
"$PY" -c 'import sys, pandas, numpy; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || { echo "Python 3.9+ with pandas and numpy is needed (set PYTHON=/path/to/python)." >&2; exit 1; }
STEPS="02_unpack_raw.py 03_extract_datasets.py"
if command -v minizinc >/dev/null 2>&1; then STEPS="$STEPS 08_solver_effort.py"; else echo "[run_prep] minizinc not found: step 08 skipped, existing solver_effort_gecode.csv kept"; fi
STEPS="$STEPS 09_instance_metrics.py 10_harmonize_trials.py"
for step in $STEPS; do
  echo "[run_prep] ---- $step"
  "$PY" "$HERE/$step"
  if [ "$step" = "03_extract_datasets.py" ]; then
    # K8 (optimisation task, not used in the article) needs the supplementary PDF fetched by 01b_fetch_supplements.py
    echo "[run_prep] ---- 03b_extract_k8.py (optional)"
    "$PY" "$HERE/03b_extract_k8.py" || echo "[run_prep] 03b_extract_k8.py did not finish: the K8 tables are left as they are"
  fi
done
echo "[run_prep] done"
