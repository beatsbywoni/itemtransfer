#!/usr/bin/env bash
# 3-A2 (project 3): unpack the archives, extract instance and trial tables, check them against the authors' files and
# the articles, build the dataset table and the instance-overlap matrix, and compute the PRISMA flow. Reads data_raw/,
# writes data_proc/, output/report_3a2_tables.md and output/prisma_flow_3a2.*. Rerunning is safe.
#   bash code/run_3a2.sh
# Needs Python 3.9+ with pandas and numpy.
# Not run here: 02b_convert_rds.py (needs pyreadr; its CSV outputs are kept in data_proc/k5_authors/), and the steps
# that need internet access (01b_fetch_supplements.py, 06_prisma_search.py, 06b_prisma_search_more.py; see
# run_3a2_supp.sh). 07_prisma_flow.py reads the search exports those steps left in data_proc/.
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
echo "[run_3a2] $(date '+%Y-%m-%d %H:%M:%S')  python: $PY ($("$PY" -c 'import sys, pandas; print(sys.version.split()[0], "pandas", pandas.__version__)'))"
for step in 02_unpack_raw.py 03_extract_datasets.py 04_validate_against_authors.py 05_inventory_tables.py 07_prisma_flow.py; do
  echo "[run_3a2] ---- $step"
  "$PY" "$HERE/$step"
done
echo "[run_3a2] done $(date '+%Y-%m-%d %H:%M:%S')"
