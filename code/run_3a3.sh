#!/usr/bin/env bash
# 3-A3 (project 3): K8 extraction, solver effort, instance measures, harmonised trial table and codebook tables.
#   bash code/run_3a3.sh
# Needs Python 3.9+ with pandas and numpy (pyarrow for the parquet copy), and the outputs of run_3a2.sh and
# run_3a2_supp.sh (data_raw/supplements). 08_solver_effort.py also needs MiniZinc with Gecode (MINIZINC=/path/to/minizinc);
# without it that step is skipped and the existing data_proc/solver_effort_gecode.csv is used. Rerunning is safe.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(dirname "$HERE")"
ROOT="$(dirname "$PROJ")"
PY=""
for cand in "${PYTHON:-}" "$PROJ/.venv/bin/python" "$(command -v python3 || true)"; do
  if [ -n "$cand" ] && [ -x "$cand" ] && "$cand" -c 'import sys, pandas, numpy; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$cand"
    break
  fi
done
if [ -z "$PY" ]; then echo "Python 3.9+ with pandas and numpy was not found (set PYTHON=/path/to/python)." >&2; exit 1; fi
echo "[run_3a3] $(date '+%Y-%m-%d %H:%M:%S')  python: $PY ($("$PY" -c 'import sys, pandas, numpy; print(sys.version.split()[0], "pandas", pandas.__version__, "numpy", numpy.__version__)'))"
for step in 03b_extract_k8.py 08_solver_effort.py 09_instance_metrics.py 10_harmonize_trials.py 11_codebook_tables.py; do
  echo "[run_3a3] ---- $step"
  "$PY" "$HERE/$step"
done
echo "[run_3a3] done $(date '+%Y-%m-%d %H:%M:%S')"
