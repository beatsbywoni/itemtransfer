#!/usr/bin/env python3
"""
3-A1 supplement: download source files that are not on OSF or GitHub, with the same provenance record.

Run on a computer with internet access (the Mac):

    python3 code/01b_fetch_supplements.py           download (safe to rerun)
    python3 code/01b_fetch_supplements.py --verify  check hashes only

Items (fixed)
  K1-SI    Murawski & Bossaerts (2016), Scientific Reports 6, 34851, Supplementary Information (PDF; article licence
           CC BY 4.0). Table S1 lists the items (value, weight) and the capacity of the eight optimisation instances.
  K8-ZEN   Bowman, Coghill, Murawski & Bossaerts (2023), Science Advances 9, eadd4165: data and code archive
           bmmlab/PECO v1.0 on Zenodo (doi:10.5281/zenodo.7633250; licence "other-open"). The record's metadata is
           saved too, and the archive is checked against the MD5 and size that Zenodo reports.
Outputs
  data_raw/supplements/<file>                         files as downloaded (never changed afterwards)
  data_raw/MANIFEST_supplements.md, .sha256           provenance: URL, time, size, sha256, licence
                                                      (`cd data_raw && shasum -a 256 -c MANIFEST_supplements.sha256`)
Files already present with the recorded sha256 are not downloaded again. Standard library only; HTTP through curl.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
DATA_RAW = PROJ / "data_raw"
OUT = DATA_RAW / "supplements"
UA = "knapsack-reanalysis/1.0"
ITEMS = [
    {"key": "K1-SI", "study": "K1",
     "file": "K1_Murawski_Bossaerts_2016_SciRep_SI.pdf",
     "url": "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fsrep34851/MediaObjects/"
            "41598_2016_BFsrep34851_MOESM1_ESM.pdf",
     "page": "https://doi.org/10.1038/srep34851",
     "license": "CC BY 4.0 (article and supplementary information, Scientific Reports)",
     "what": "Supplementary Information: Table S1 items and capacities of the 8 instances; Table S2 instance properties"},
    {"key": "K8-ZEN-META", "study": "K8",
     "file": "K8_zenodo_7633250_record.json",
     "url": "https://zenodo.org/api/records/7633250",
     "page": "https://doi.org/10.5281/zenodo.7633250",
     "license": "metadata (CC0 on Zenodo)",
     "what": "Zenodo record metadata (file list with MD5, licence id, related GitHub release)"},
    {"key": "K8-ZEN", "study": "K8",
     "file": "K8_bmmlab_PECO-v1.0.zip",
     "url": "https://zenodo.org/api/records/7633250/files/bmmlab/PECO-v1.0.zip/content",
     "page": "https://doi.org/10.5281/zenodo.7633250",
     "license": "other-open (Zenodo); no licence file in the GitHub repository; analysed and cited, not redistributed",
     "what": "bmmlab/PECO v1.0 (GitHub release archived on Zenodo): per-attempt data Xall_figures.csv and code",
     "zenodo_key": "bmmlab/PECO-v1.0.zip"},
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path) -> None:
    if not shutil.which("curl"):
        raise SystemExit("curl is needed")
    part = dest.with_name(dest.name + ".part")
    p = subprocess.run(["curl", "-sS", "-L", "--fail", "--max-time", "600", "-A", UA, "-o", str(part), url],
                       capture_output=True, text=True)
    if p.returncode != 0:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"curl failed ({p.returncode}) for {url}: {p.stderr.strip()[:200]}")
    part.replace(dest)


def load_recorded() -> dict:
    f = DATA_RAW / "MANIFEST_supplements.sha256"
    out = {}
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                digest, name = line.split(None, 1)
                out[name.strip()] = digest
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true", help="only check the files against MANIFEST_supplements.sha256")
    args = ap.parse_args(argv)
    recorded = load_recorded()
    if args.verify:
        bad = 0
        for name, digest in recorded.items():
            p = DATA_RAW / name
            ok = p.exists() and sha256(p) == digest
            bad += not ok
            print(f"{'OK  ' if ok else 'FAIL'} {name}")
        return 1 if bad or not recorded else 0

    OUT.mkdir(parents=True, exist_ok=True)
    state_file = DATA_RAW / "_osf_meta" / "supplements_state.json"
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    zenodo_meta = None
    problems = []
    for it in ITEMS:
        dest = OUT / it["file"]
        rel = f"supplements/{it['file']}"
        if dest.exists() and recorded.get(rel) == sha256(dest) and it["key"] in state:
            print(f"kept       {rel}")
        else:
            when = dt.datetime.now(dt.timezone.utc)
            fetch(it["url"], dest)
            state[it["key"]] = {"downloaded_utc": when.isoformat(timespec="seconds")}
            print(f"downloaded {rel}")
        size = dest.stat().st_size
        digest = sha256(dest)
        check = "file present"
        if it["key"] == "K1-SI":
            check = "PDF header ok" if dest.read_bytes()[:5] == b"%PDF-" else "NOT A PDF"
        elif it["key"] == "K8-ZEN-META":
            zenodo_meta = json.loads(dest.read_text(encoding="utf-8"))
            check = f"Zenodo record {zenodo_meta.get('id')}, doi {zenodo_meta.get('doi')}, licence " \
                    f"{(zenodo_meta.get('metadata') or {}).get('license', {}).get('id')}"
        elif it["key"] == "K8-ZEN":
            entry = next((f for f in (zenodo_meta or {}).get("files", []) if f.get("key") == it["zenodo_key"]), None)
            if entry is None:
                check = "NOT IN ZENODO RECORD"
            else:
                want_md5 = str(entry.get("checksum", "")).replace("md5:", "")
                got_md5 = md5(dest)
                check = (f"MD5 {got_md5} and size {size} match Zenodo" if got_md5 == want_md5 and size == entry.get("size")
                         else f"MISMATCH: Zenodo MD5 {want_md5} size {entry.get('size')}, got {got_md5} size {size}")
        if "NOT" in check or "MISMATCH" in check:
            problems.append(f"{rel}: {check}")
        state[it["key"]].update({"file": rel, "bytes": size, "sha256": digest, "check": check, "url": it["url"]})
    state_file.write_text(json.dumps(state, indent=1), encoding="utf-8")

    lines = [f"{state[it['key']]['sha256']}  {state[it['key']]['file']}" for it in ITEMS]
    (DATA_RAW / "MANIFEST_supplements.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    now = dt.datetime.now(dt.timezone.utc)
    md = ["# MANIFEST of data_raw/supplements/ (project 3)", "",
          f"Written by `code/01b_fetch_supplements.py` (script sha256 `{sha256(Path(__file__))[:16]}`) at "
          f"{now.strftime('%Y-%m-%d %H:%M:%S')} UTC. "
          "Files are kept as downloaded. Check them with `cd data_raw && shasum -a 256 -c MANIFEST_supplements.sha256`.", "",
          "| Item | Study | File | Size (bytes) | sha256 | Check | Downloaded (UTC) | Source | Licence | Content |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for it in ITEMS:
        s = state[it["key"]]
        md.append(f"| {it['key']} | {it['study']} | `{s['file']}` | {s['bytes']} | `{s['sha256']}` | {s['check']} | "
                  f"{s['downloaded_utc']} | [download]({it['url']}) / [page]({it['page']}) | {it['license']} | {it['what']} |")
    (DATA_RAW / "MANIFEST_supplements.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for p in problems:
        print("PROBLEM", p)
    print(f"{len(ITEMS)} files; manifest in data_raw/MANIFEST_supplements.md")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
