#!/usr/bin/env bash
# 3-A1 (project 3): back up the public OSF and GitHub materials of the knapsack datasets K2, K4, K5 and K7.
# Run once on the Mac, from any directory:
#   bash code/run_3a_download.sh
# Expected on the first run: about 250 MB from OSF and about 50 MB of GitHub archives (a few minutes on a normal line).
# Rerunning is safe: files already present with the expected sha256 are skipped and nothing is overwritten or deleted.
# Extra arguments are passed to 01_osf_download.py, for example
#   bash .../run_3a_download.sh --dry-run      offline check of the plan
#   bash .../run_3a_download.sh --list-only    list the OSF files without downloading
#   bash .../run_3a_download.sh --verify       re-hash the kept files
# Results: data_raw/MANIFEST.md, data_raw/_osf_meta/, output/log_3a.txt
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(dirname "$HERE")"
ROOT="$(dirname "$PROJ")"

# Python 3.9 or later; only the standard library is used. Order: $PYTHON, a project virtual environment, python3 on PATH.
PY=""
for cand in "${PYTHON:-}" "$PROJ/.venv/bin/python" "$(command -v python3 || true)"; do
  if [ -n "$cand" ] && [ -x "$cand" ] && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$cand"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9 or later was not found. Install it from python.org, or run with PYTHON=/path/to/python3." >&2
  exit 1
fi

mkdir -p "$PROJ/output" "$PROJ/data_raw"
CAF=""
if command -v caffeinate >/dev/null 2>&1; then CAF="caffeinate -i"; fi   # keep the Mac awake while downloading
echo "[run_3a_download] $(date '+%Y-%m-%d %H:%M:%S')  python: $PY ($("$PY" -V 2>&1))"
$CAF "$PY" "$HERE/01_osf_download.py" ${1+"$@"}
