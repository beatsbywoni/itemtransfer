#!/usr/bin/env python3
"""
3-A2 step 1: unpack the archives kept in data_raw/ into data_proc/unpacked/. data_raw/ is only read, never changed.

    python3 code/02_unpack_raw.py           unpack; rerunning keeps files that are already there and identical
    python3 code/02_unpack_raw.py --check   report what would be written, write nothing

What is unpacked
  data zips (behavioural data, task inputs)    -> data_proc/unpacked/<node>/<archive name>/<members>
      every member except macOS metadata (__MACOSX/, .DS_Store)
  task builds (Unity .app or Windows builds)   -> data_proc/unpacked/<node>/<archive name>/<members under DATAinf/>
      only the task's input/output folder DATAinf/ (instance files and parameters); program files are skipped
  GitHub snapshots data_raw/github/*.tar.gz     -> data_proc/unpacked/github/<owner>__<repo>/<selected members>
      README and LICENSE files, Assets/DATAinf/ (task inputs and example outputs), task scripts (*.cs outside
      vendor folders), ProjectSettings/ProjectVersion.txt, Data/; every file of bmmlab/KS-IC_SupplementaryInfo
Unity .meta files are skipped everywhere. data_proc/unpacked/UNPACK_MANIFEST.csv lists every written file with its source
archive (and that archive's sha256), member name, size and sha256. Standard library only (Python 3.9+).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
import re
import sys
import tarfile
import zipfile
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
MAX_TOTAL = 3 * 10 ** 9          # refuse to write more than 3 GB in one run (guards against malformed archives)
FULL_REPOS = {"bmmlab__KS-IC_SupplementaryInfo"}
REPO_KEEP = [r"^README[^/]*$", r"^LICENSE[^/]*$", r"^Assets/DATAinf/", r"^Assets/(?!TobiiPro/)(?:.*/)?[^/]+\.cs$",
             r"^ProjectSettings/ProjectVersion\.txt$", r"^Data/"]
BUILD_HINT = re.compile(r"(\.app/Contents/|_Data/|\.exe$)")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_parts(name: str):
    parts = [p for p in name.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts) or name.startswith("/"):
        return None
    return parts


def skip_member(name: str) -> bool:
    base = name.rstrip("/").rsplit("/", 1)[-1]
    return name.startswith("__MACOSX/") or "/__MACOSX/" in name or base == ".DS_Store" or base.endswith(".meta")


class Writer:
    def __init__(self, out_root: Path, check: bool):
        self.out_root, self.check = out_root, check
        self.rows, self.written, self.kept, self.conflicts, self.total = [], 0, 0, [], 0

    def put(self, rel_parts, data: bytes, archive: str, archive_sha: str, member: str) -> None:
        dest = self.out_root.joinpath(*rel_parts)
        digest = sha256_bytes(data)
        self.rows.append({"archive": archive, "archive_sha256": archive_sha, "member": member,
                          "path": dest.relative_to(self.out_root).as_posix(), "bytes": len(data), "sha256": digest})
        if dest.exists():
            if sha256_file(dest) == digest:
                self.kept += 1
            else:
                self.conflicts.append(dest.relative_to(self.out_root).as_posix())
            return
        self.total += len(data)
        if self.total > MAX_TOTAL:
            raise SystemExit("refusing to write more than 3 GB; check the archives")
        if not self.check:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".tmp")
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dest)
        self.written += 1


def unpack_zip(z: Path, data_raw: Path, w: Writer) -> None:
    rel = z.relative_to(data_raw)
    archive, archive_sha = rel.as_posix(), sha256_file(z)
    with zipfile.ZipFile(z) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        build = any(BUILD_HINT.search(i.filename) for i in infos)
        n = 0
        for i in infos:
            name = i.filename
            if skip_member(name) or (build and "/DATAinf/" not in "/" + name):
                continue
            parts = safe_parts(name)
            if parts is None:
                print(f"  skipped unsafe member {name!r} in {archive}")
                continue
            if (i.external_attr >> 16) & 0o170000 == 0o120000:   # symbolic link stored in the zip
                continue
            w.put([*rel.parent.parts, rel.stem, *parts], zf.read(i), archive, archive_sha, name)
            n += 1
    print(f"  {archive}: {n} files" + (" (task build: DATAinf only)" if build else ""))


def unpack_repo(t: Path, data_raw: Path, w: Writer) -> None:
    rel = t.relative_to(data_raw)
    archive, archive_sha = rel.as_posix(), sha256_file(t)
    repo = t.name.split("@", 1)[0]
    keep = [re.compile(p) for p in REPO_KEEP]
    n = 0
    with tarfile.open(t, "r:gz") as tf:
        for m in tf:
            if not m.isfile():
                continue
            parts = safe_parts(m.name)
            if parts is None or len(parts) < 2:
                continue
            inner = "/".join(parts[1:])            # drop the "<repo>-<commit>/" prefix
            if skip_member(inner):
                continue
            if repo not in FULL_REPOS and not any(k.search(inner) for k in keep):
                continue
            data = tf.extractfile(m).read()
            w.put(["github", repo, *parts[1:]], data, archive, archive_sha, m.name)
            n += 1
    print(f"  {archive}: {n} files")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    ap.add_argument("--data-raw", type=Path, default=PROJ / "data_raw")
    ap.add_argument("--out", type=Path, default=PROJ / "data_proc" / "unpacked")
    a = ap.parse_args(argv)
    data_raw, out_root = a.data_raw.resolve(), a.out.resolve()
    w = Writer(out_root, a.check)
    print(f"Unpacking {data_raw} -> {out_root}" + (" (check only)" if a.check else ""))
    for z in sorted(p for p in data_raw.rglob("*.zip") if not any(s.startswith("_") for s in p.relative_to(data_raw).parts)):
        unpack_zip(z, data_raw, w)
    for t in sorted((data_raw / "github").glob("*.tar.gz")):
        unpack_repo(t, data_raw, w)
    if not a.check:
        out_root.mkdir(parents=True, exist_ok=True)
        rows = sorted(w.rows, key=lambda r: r["path"])
        buf = io.StringIO()
        cw = csv.DictWriter(buf, fieldnames=["path", "bytes", "sha256", "archive", "member", "archive_sha256"],
                            lineterminator="\n")
        cw.writeheader()
        cw.writerows(rows)
        new = buf.getvalue().encode("utf-8")
        mpath = out_root / "UNPACK_MANIFEST.csv"
        if not mpath.exists() or mpath.read_bytes() != new:
            tmp = mpath.with_name(mpath.name + ".tmp")
            tmp.write_bytes(new)
            os.replace(tmp, mpath)
    print(f"Done: {len(w.rows)} files in the unpack set; {w.written} {'would be ' if a.check else ''}written, "
          f"{w.kept} already present and identical, {len(w.conflicts)} conflicts")
    for c in w.conflicts:
        print(f"  CONFLICT (left as it is): {c}")
    return 1 if w.conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
