#!/usr/bin/env python3
"""
3-A1 data backup for project 3 (human performance on 0-1 knapsack instances; multi-dataset reanalysis).

Downloads the public OSF materials of the four datasets (K2, K4, K5, K7), takes snapshots of the GitHub repositories that
those OSF projects link to (task code with the instance input files; analysis code), saves the OSF wiki pages, and writes
provenance records. Run it on a computer with internet access (the Mac):

    bash code/run_3a_download.sh          # calls this file

Direct use (paths are resolved relative to this file, so it can be called from anywhere):

    python3 01_osf_download.py              list OSF nodes, download, snapshot GitHub, save wikis, write MANIFEST
    python3 01_osf_download.py --list-only  list only (writes data_raw/_osf_meta/listing.*); nothing is downloaded
    python3 01_osf_download.py --dry-run    offline: print the plan and the current state; no network access
    python3 01_osf_download.py --verify     offline: re-hash every downloaded file and compare with the recorded sha256

Options: --refresh (list OSF again instead of reusing cached API responses), --max-mb N (size cap per file, default 100),
--include NODE:/path (fetch an excluded file, or everything under a folder when the path ends in /), --max-wait S (longest
wait after an OSF rate-limit response, default 3600), --backend auto|curl|urllib, --no-github, --no-wikis.

Outputs (relative to 03_knapsack-ipd-meta/)
  data_raw/<OSF node id>/<path on OSF>               OSF files, in the folder structure of each OSF component
  data_raw/github/<owner>__<repo>@<commit>.tar.gz    repository snapshots at pinned commits (as served by GitHub)
  data_raw/_osf_meta/listing.json, listing.csv       every OSF node and file seen, with the action taken and the reason
  data_raw/_osf_meta/state.json                      checkpoint: status, sha256, size, source and time of every file
  data_raw/_osf_meta/api/                            cached OSF API responses (a rerun does not repeat API requests)
  data_raw/_osf_meta/wikis/                          OSF wiki pages (markdown, as stored on OSF)
  data_raw/MANIFEST.md, data_raw/MANIFEST.sha256     provenance; check with `cd data_raw && shasum -a 256 -c MANIFEST.sha256`
  output/log_3a.txt                                  run log (appended)

Safety: rerunning is safe. A file that is already present with the expected sha256 is skipped, and nothing in data_raw/ is
overwritten or deleted (a present file whose hash differs is reported and left as it is). Only the Python standard library
is used (Python 3.9 or later). HTTP goes through curl when it is available (curl uses the macOS system certificates),
otherwise through urllib. OSF rate-limits anonymous API requests; a full run needs roughly 80 API requests, the script waits
when OSF answers HTTP 429, and cached responses mean that a rerun continues where the last one stopped. Setting the
environment variable OSF_TOKEN (an OSF personal access token) raises the limit but is not needed.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import email.utils
import hashlib
import json
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_VERSION = "1.0 (2026-10-16)"
HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
OSF_API = "https://api.osf.io/v2"
GITHUB_ARCHIVE = "https://github.com"
USER_AGENT = "knapsack-reanalysis-backup/1.0 (research data backup)"
STAMP_TZ = dt.timezone.utc   # time stamps in logs and manifests are in UTC

# ---------------------------------------------------------------------------------------------------------------------
# What to fetch. Node structure, sizes and wiki links were checked through the OSF API on 2026-10-16.
# Every OSF component under each root is listed; the exclusions below are recorded in the manifest with their reasons.
# An "exclude" entry without "path" drops a whole component; a path ending in "/" drops a folder (it is not listed);
# any other path drops one file.
# ---------------------------------------------------------------------------------------------------------------------
SOURCES = [
    {"study": "K2", "root": "t2jv7", "doi": "10.17605/OSF.IO/T2JV7",
     "paper": "Franco, Yadav, Bossaerts & Murawski (2021). Journal of Mathematical Psychology, 104, 102592",
     "exclude": [
         {"node": "e6cwf", "path": "/decisionInstancesInfo.csv",
          "reason": "pool of generated decision instances with solver statistics (881 MB); not needed while the metrics "
                    "can be recomputed from the selected instances (fetch later with --include e6cwf:/decisionInstancesInfo.csv)"},
     ]},
    {"study": "K4", "root": "g4h7y", "doi": None,
     "paper": "Franco, Bossaerts & Murawski (2024). PLOS Computational Biology, 20(9), e1012447",
     "exclude": [
         {"node": "t8eyj", "reason": "raw fMRI data component (BIDS); outside the behavioural reanalysis"},
         {"node": "964pf", "path": "/Neuroimaging Results/",
          "reason": "fMRI group-level maps and reports (531 MB); outside the behavioural reanalysis"},
         {"node": "b6v2w", "path": "/Neuroimaging Data Analysis/",
          "reason": "fMRI analysis scripts; outside the behavioural reanalysis"},
     ]},
    {"study": "K5", "root": "y7m3s", "doi": None,
     "paper": "Doroc, Yadav & Murawski (2025). Communications Psychology, 3, 179",
     "exclude": [
         {"node": "hjq8z", "path": "/Eye tracking data/", "reason": "raw eye-tracking recordings (11.6 GB); not needed"},
         {"node": "hjq8z", "path": "/Skin conductance data/", "reason": "raw skin-conductance recordings (377 MB); not needed"},
         {"node": "nc94u", "path": "/et_pp.rds", "reason": "pre-processed gaze data (326 MB); not needed"},
         {"node": "nc94u", "path": "/gsr_pp.rds", "reason": "pre-processed skin-conductance data (107 MB); not needed"},
         {"node": "x9wf2", "path": "/saliva_instructions.mp4", "reason": "saliva-collection instruction video; not needed"},
     ]},
    {"study": "K7", "root": "pks4b", "doi": "10.17605/OSF.IO/PKS4B",
     "paper": "Lu, Murawski, Bossaerts & Suzuki (2025). Scientific Reports, 15",
     "exclude": []},
]

# Repositories linked from the OSF wikis, pinned to the commit seen on 2026-10-16. "files" and "bytes" are the number and
# total size of the regular files in `git archive` of that commit; a downloaded archive is compared with them.
GITHUB = [
    {"study": "K2", "repo": "bmmlab/KS-IC_SupplementaryInfo", "commit": "3c4e446029553d1c0f47d1f36e456acc578dcda8",
     "role": "analysis code: instance generation and selection, behavioural analysis", "linked_from": "OSF abpjy wiki",
     "license": "no license file", "files": 12, "bytes": 9480024,
     "note": "the submodule 'Code/Instance Generation/kp-complexity' (commit 2754f2fc) has no .gitmodules entry and is not part of the archive"},
    {"study": "K2", "repo": "jpfranco123/Knapsack-Optimization", "commit": "502963eb943f48dc079295cebe0358d243ef9f56",
     "role": "optimisation task (Unity) with instance input files", "linked_from": "OSF 7y3d4 wiki",
     "license": "no license file", "files": 488, "bytes": 12831919},
    {"study": "K2", "repo": "jpfranco123/KS-Decision-T1", "commit": "f3b04ff20643c1a387ceba053f909aac34f4e244",
     "role": "decision task (Unity) with instance input files", "linked_from": "OSF gsm9r wiki",
     "license": "no license file", "files": 225, "bytes": 1317197},
    {"study": "K2", "repo": "jpfranco123/Math-Task", "commit": "24bbbe97b4b07d97910920b3f42e07312f8cae97",
     "role": "math task (Unity)", "linked_from": "OSF mdw8n wiki",
     "license": "no license file", "files": 2605, "bytes": 55530313},
    {"study": "K4", "repo": "jpfranco123/KS-Decision-T2", "commit": "2fa3fda345efe59730bd4283961c220164c5583b",
     "role": "fMRI decision task (Unity) with per-participant instance sequences", "linked_from": "OSF apu5h wiki",
     "license": "GPL-3.0 (LICENSE file)", "files": 285, "bytes": 1398753},
    {"study": "K5", "repo": "krdoroc/acute-stress-task-only", "commit": "dc5edc16976b40cddc27e1e98664a9fe6586c4c5",
     "role": "stress-study decision task (Unity) with instance input files", "linked_from": "OSF 85dxy wiki",
     "license": "GPL-3.0 (LICENSE file)", "files": 2566, "bytes": 278248171},
]

FILE_OK = ("downloaded", "present")


# ---------------------------------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------------------------------
def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(t: dt.datetime) -> str:
    return t.replace(microsecond=0).isoformat()


def stamp(t: dt.datetime) -> str:
    return t.astimezone(STAMP_TZ).strftime("%Y-%m-%d %H:%M:%S UTC")


def human(n) -> str:
    """Decimal units (1 MB = 1,000,000 bytes), as shown on OSF."""
    if n is None:
        return "?"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1000 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1000
    return f"{n:.1f} TB"


def sha256_file(path: Path):
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def write_bytes_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def write_json(path: Path, obj) -> None:
    write_bytes_atomic(path, (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))


def with_query(url: str, query: str) -> str:
    return url + ("&" if "?" in url else "?") + query


def rel_href(rel):
    """href of a JSON:API relationship ('links.related' is either a dict with 'href' or a plain string)."""
    related = ((rel or {}).get("links") or {}).get("related")
    return related.get("href") if isinstance(related, dict) else related


def rel_count(rel):
    related = ((rel or {}).get("links") or {}).get("related")
    if isinstance(related, dict):
        meta = related.get("meta") or {}
        if "count" in meta:
            return meta["count"]
    return None


def retry_after_seconds(value) -> int:
    if not value:
        return 60
    try:
        return max(1, int(float(value)))
    except ValueError:
        try:
            when = email.utils.parsedate_to_datetime(value)
            return max(1, int((when - now_utc()).total_seconds()))
        except Exception:
            return 60


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s or "page").strip("_") or "page"


def target_for(data_raw: Path, node: str, path: str) -> Path:
    """Local path for an OSF file. Rejects path components that could leave the node folder."""
    parts = [p for p in path.split("/") if p]
    if not parts or any(p in (".", "..") or "\x00" in p or "\\" in p for p in parts):
        raise ValueError(f"unsafe path from OSF: {node}:{path}")
    return data_raw.joinpath(node, *parts)


def tar_stats(path: Path) -> dict:
    """Count regular files and their total size in a .tar.gz without extracting it."""
    n = b = 0
    top = set()
    with tarfile.open(path, "r:gz") as t:
        for m in t:
            if m.isfile():
                n += 1
                b += m.size
            first = m.name.split("/", 1)[0]
            if first and first != "pax_global_header":
                top.add(first)
    return {"files": n, "bytes": b, "top": sorted(top)}


class Log:
    def __init__(self, path):
        self.path = path
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str = "") -> None:
        print(msg, flush=True)
        if self.path:
            stamp = now_utc().astimezone(STAMP_TZ).strftime("%Y-%m-%d %H:%M:%S")
            with open(self.path, "a", encoding="utf-8") as f:
                for line in (msg.splitlines() or [""]):
                    f.write(f"[{stamp}] {line}\n")


# ---------------------------------------------------------------------------------------------------------------------
# HTTP (curl or urllib) and the cached OSF API client
# ---------------------------------------------------------------------------------------------------------------------
class TransportError(Exception):
    pass


class HttpError(Exception):
    pass


class RateLimited(Exception):
    def __init__(self, wait: int):
        super().__init__(f"OSF API rate limit; retry after {wait} s")
        self.wait = wait


def parse_header_block(raw: str) -> dict:
    blocks = [b for b in re.split(r"\r?\n\r?\n", raw.strip()) if b.strip()]
    out = {}
    if blocks:
        for line in blocks[-1].splitlines()[1:]:
            key, sep, value = line.partition(":")
            if sep:
                out[key.strip().lower()] = value.strip()
    return out


def curl_version():
    exe = shutil.which("curl")
    if not exe:
        return None
    try:
        first = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20).stdout.split("\n")[0]
        return " ".join(first.split()[:2])
    except Exception:
        return None


class Http:
    def __init__(self, backend: str, token=None):
        self.backend = backend
        self.token = token
        self.tmpdir = Path(tempfile.mkdtemp(prefix="p3_osf_"))
        self.ssl_context = None
        if backend == "urllib":
            try:
                import certifi  # optional; helps python.org builds that lack a certificate store
                self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                self.ssl_context = ssl.create_default_context()

    def get(self, url: str, dest: Path, timeout: int, auth: bool = False):
        """GET url and write the body to dest. Returns (status, headers of the final response, final url)."""
        headers = {"User-Agent": USER_AGENT}
        if auth and self.token:
            headers["Authorization"] = "Bearer " + self.token
        if self.backend == "curl":
            return self._curl(url, dest, timeout, headers)
        return self._urllib(url, dest, timeout, headers)

    def _curl(self, url, dest, timeout, headers):
        hdr = self.tmpdir / "headers.txt"
        cmd = ["curl", "-sS", "-L", "--globoff", "--connect-timeout", "30", "--max-time", str(timeout),
               "-D", str(hdr), "-o", str(dest), "-w", "%{http_code} %{url_effective}"]
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
        cmd.append(url)
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise TransportError(f"curl exit {p.returncode}: {p.stderr.strip()[:300]}")
        code, _, final = p.stdout.strip().partition(" ")
        raw = hdr.read_text(errors="replace") if hdr.exists() else ""
        return int(code or 0), parse_header_block(raw), final or url

    def _urllib(self, url, dest, timeout, headers):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=self.ssl_context) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
                return r.status, {k.lower(): v for k, v in r.headers.items()}, r.geturl()
        except urllib.error.HTTPError as e:
            with open(dest, "wb") as f:
                f.write(e.read() or b"")
            return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, url
        except (urllib.error.URLError, OSError, ssl.SSLError) as e:
            raise TransportError(f"{type(e).__name__}: {e}")


class OsfApi:
    """GET requests to the OSF API with an on-disk cache, retries and rate-limit handling."""

    def __init__(self, http: Http, cache_dir: Path, refresh: bool, max_wait: int, log: Log, retry_delay: float):
        self.http, self.cache_dir, self.refresh = http, cache_dir, refresh
        self.max_wait, self.log, self.retry_delay = max_wait, log, retry_delay
        self.requests = self.cache_hits = self.waited = 0
        cache_dir.mkdir(parents=True, exist_ok=True)

    def _sleep(self, seconds: float, why: str) -> None:
        seconds = max(0.0, float(seconds))
        self.log(f"    {why}")
        end = time.time() + seconds
        while True:
            left = end - time.time()
            if left <= 0:
                return
            if left > 90:
                self.log(f"    ... {int(left // 60)} min left")
            time.sleep(min(60.0, left))

    def raw(self, url: str, essential: bool = True) -> bytes:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        body_path, meta_path = self.cache_dir / f"{key}.body", self.cache_dir / f"{key}.json"
        if not self.refresh and body_path.exists() and meta_path.exists():
            self.cache_hits += 1
            return body_path.read_bytes()
        attempt = waited_here = 0
        while True:
            attempt += 1
            tmp = self.http.tmpdir / "api_body"
            try:
                status, headers, _ = self.http.get(url, tmp, timeout=120, auth=True)
            except TransportError as e:
                if attempt >= 5:
                    raise
                self._sleep(self.retry_delay * 2 ** attempt, f"network error ({e}); retrying")
                continue
            self.requests += 1
            if status == 200:
                data = tmp.read_bytes()
                write_bytes_atomic(body_path, data)
                write_json(meta_path, {"url": url, "fetched_at_utc": iso(now_utc()), "status": status, "bytes": len(data)})
                return data
            if status == 429:
                wait = retry_after_seconds(headers.get("retry-after"))
                if (not essential and wait > 90) or waited_here + wait > self.max_wait:
                    raise RateLimited(wait)
                self._sleep(wait + 1, f"OSF API rate limit reached (HTTP 429); waiting {wait} s, then continuing. "
                                      "Ctrl-C is safe: rerun the same command later to resume.")
                waited_here += wait + 1
                self.waited += wait + 1
                continue
            if status >= 500 and attempt < 5:
                self._sleep(self.retry_delay * 2 ** attempt, f"OSF API HTTP {status}; retrying")
                continue
            snippet = tmp.read_bytes()[:300].decode("utf-8", "replace") if tmp.exists() else ""
            raise HttpError(f"HTTP {status} for {url}: {snippet}")

    def json(self, url: str, essential: bool = True):
        return json.loads(self.raw(url, essential).decode("utf-8"))

    def pages(self, url: str, essential: bool = True):
        while url:
            j = self.json(url, essential)
            for item in j.get("data") or []:
                yield item
            url = (j.get("links") or {}).get("next")


# ---------------------------------------------------------------------------------------------------------------------
# listing
# ---------------------------------------------------------------------------------------------------------------------
class Rules:
    def __init__(self, src: dict, max_bytes: int, includes):
        self.node_ex, self.folder_ex, self.file_ex = {}, [], {}
        for e in src.get("exclude", []):
            if not e.get("path"):
                self.node_ex[e["node"]] = e["reason"]
            elif e["path"].endswith("/"):
                self.folder_ex.append((e["node"], e["path"], e["reason"]))
            else:
                self.file_ex[(e["node"], e["path"])] = e["reason"]
        self.max_bytes = max_bytes
        self.includes = includes

    def _included(self, node: str, path: str) -> bool:
        return any(n == node and (path == p or (p.endswith("/") and path.startswith(p))) for n, p in self.includes)

    def node(self, node: str):
        return None if self._included(node, "/") else self.node_ex.get(node)

    def folder(self, node: str, path: str):
        if any(n == node and (p.startswith(path) or path.startswith(p)) for n, p in self.includes):
            return None
        for n, p, reason in self.folder_ex:
            if n == node and path.startswith(p):
                return reason
        return None

    def file(self, node: str, path: str, size):
        if self._included(node, path):
            return None
        reason = self.file_ex.get((node, path))
        if reason:
            return reason
        for n, p, r in self.folder_ex:
            if n == node and path.startswith(p):
                return r
        if size is not None and size > self.max_bytes:
            return f"larger than the size cap ({human(size)} > {human(self.max_bytes)}; use --max-mb or --include)"
        return None


def list_folder(api: OsfApi, src: dict, node: str, url: str, rules: Rules, entries: list) -> None:
    for item in api.pages(url):
        a = item.get("attributes") or {}
        path = a.get("materialized_path") or ("/" + (a.get("name") or ""))
        base = {"study": src["study"], "root": src["root"], "node": node, "path": path, "name": a.get("name"),
                "osf_id": item.get("id")}
        if a.get("kind") == "folder":
            reason = rules.folder(node, path)
            entries.append(dict(base, kind="folder", action="excluded" if reason else "listed", reason=reason))
            href = rel_href((item.get("relationships") or {}).get("files"))
            if not reason and href:
                list_folder(api, src, node, with_query(href, "page[size]=100"), rules, entries)
            continue
        hashes = (a.get("extra") or {}).get("hashes") or {}
        links = item.get("links") or {}
        size = a.get("size")
        reason = rules.file(node, path, size)
        entries.append(dict(base, kind="file", size=size, sha256_osf=hashes.get("sha256"), md5_osf=hashes.get("md5"),
                            date_modified=a.get("date_modified"), version=a.get("current_version"), guid=a.get("guid"),
                            download_url=links.get("download"), html_url=links.get("html"),
                            action="excluded" if reason else "download", reason=reason))


def crawl_source(api: OsfApi, src: dict, rules: Rules, api_base: str, log: Log):
    nodes, entries = [], []
    root = api.json(f"{api_base}/nodes/{src['root']}/?related_counts=children,wikis")["data"]
    queue = [(root, None, 0)]
    while queue:
        n, parent, depth = queue.pop(0)
        nid = n["id"]
        a, rel = n.get("attributes") or {}, n.get("relationships") or {}
        rec = {"study": src["study"], "root": src["root"], "node": nid, "parent": parent, "depth": depth,
               "title": a.get("title"), "category": a.get("category"), "public": a.get("public"),
               "date_created": a.get("date_created"), "date_modified": a.get("date_modified"),
               "license_url": rel_href(rel.get("license")), "node_license": a.get("node_license"),
               "wiki_enabled": a.get("wiki_enabled"), "wiki_count": rel_count(rel.get("wikis")),
               "children_count": rel_count(rel.get("children")),
               "html": (n.get("links") or {}).get("html") or f"https://osf.io/{nid}/",
               "excluded": rules.node(nid), "n_files": 0, "n_listed_bytes": 0, "providers": None}
        nodes.append(rec)
        indent = "  " * (depth + 1)
        if rec["excluded"]:
            log(f"{indent}{nid}  {rec['title']}: excluded ({rec['excluded']})")
            continue
        first = len(entries)
        list_folder(api, src, nid, with_query(f"{api_base}/nodes/{nid}/files/osfstorage/", "page[size]=100"), rules, entries)
        files = [e for e in entries[first:] if e["kind"] == "file"]
        rec["n_files"] = len(files)
        rec["n_listed_bytes"] = sum(e["size"] or 0 for e in files)
        kids = []
        if rec["children_count"] is None or rec["children_count"] > 0:   # the count is unknown or positive: list them
            kids = list(api.pages(with_query(f"{api_base}/nodes/{nid}/children/",
                                             "related_counts=children,wikis&page[size]=100")))
            rec["children_count"] = len(kids)
        if not files and not kids:   # empty leaf: record its storage providers (files on an add-on would be missed)
            rec["providers"] = [(p.get("attributes") or {}).get("provider")
                                for p in api.pages(with_query(f"{api_base}/nodes/{nid}/files/", "page[size]=100"))]
        n_get = sum(1 for e in files if e["action"] == "download")
        log(f"{indent}{nid}  {rec['title']}: {len(files)} files ({human(rec['n_listed_bytes'])}), "
            f"{n_get} to fetch" + (f", storage {rec['providers']}" if rec["providers"] else ""))
        for child in kids:
            queue.append((child, nid, depth + 1))
    return nodes, entries


def resolve_licenses(api: OsfApi, nodes: list) -> dict:
    out = {}
    for url in sorted({n["license_url"] for n in nodes if n.get("license_url")}):
        try:
            a = api.json(url).get("data", {}).get("attributes", {})
            out[url] = {"name": a.get("name"), "url": a.get("url")}
        except (HttpError, TransportError) as e:
            out[url] = {"name": None, "error": str(e)}
    return out


def license_label(node: dict, licenses: dict) -> str:
    if not node or not node.get("license_url"):
        return "not specified on OSF"
    name = (licenses.get(node["license_url"]) or {}).get("name") or node["license_url"]
    nl = node.get("node_license") or {}
    holders = ", ".join(h for h in (nl.get("copyright_holders") or []) if h)
    extra = ", ".join(x for x in (nl.get("year"), holders) if x)
    return f"{name} ({extra})" if extra else name


# ---------------------------------------------------------------------------------------------------------------------
# downloads
# ---------------------------------------------------------------------------------------------------------------------
def fetch_to(http: Http, url: str, dest: Path, check, retry_delay: float, log: Log, attempts: int = 3) -> dict:
    """Download url to dest via dest.part; check(part) returns an error string or None. Never overwrites dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    error = None
    for k in range(1, attempts + 1):
        t0 = time.time()
        try:
            status, _, final = http.get(url, part, timeout=3600)
        except TransportError as e:
            status, final, error = None, None, str(e)
        if status == 200:
            error = check(part)
            if error is None:
                sha, size = sha256_file(part)
                os.replace(part, dest)
                return {"ok": True, "sha256": sha, "bytes": size, "seconds": round(time.time() - t0, 1), "final_url": final}
        elif status is not None:
            error = f"HTTP {status}"
        if k < attempts:
            delay = retry_delay * 3 ** (k - 1)
            log(f"      attempt {k} failed ({error}); retrying in {delay:.0f} s")
            time.sleep(delay)
    return {"ok": False, "error": error}


def download_osf_files(http: Http, entries: list, nodes_by_id: dict, licenses: dict, state: dict, data_raw: Path,
                       log: Log, retry_delay: float, save) -> None:
    todo = [e for e in entries if e["kind"] == "file" and e["action"] == "download"]
    log(f"\n[2/4] OSF files: {len(todo)} to fetch or check ({human(sum(e['size'] or 0 for e in todo))})")
    for i, e in enumerate(todo, 1):
        key = f"{e['node']}:{e['path']}"
        dest = target_for(data_raw, e["node"], e["path"])
        rel = dest.relative_to(data_raw).as_posix()
        expected_sha, expected_size = e.get("sha256_osf"), e.get("size")
        old = state["files"].get(key) or {}
        common = {"study": e["study"], "node": e["node"], "osf_path": e["path"], "path": rel,
                  "source_url": e.get("download_url"), "osf_page": e.get("html_url"), "osf_version": e.get("version"),
                  "osf_date_modified": e.get("date_modified"), "sha256_osf": expected_sha,
                  "license": license_label(nodes_by_id.get(e["node"]), licenses)}
        tag = f"  [{i}/{len(todo)}]"
        if dest.exists():
            sha, size = sha256_file(dest)
            ok = sha == expected_sha if expected_sha else (expected_size is None or size == expected_size)
            if ok:
                rec = dict(old) if old.get("status") in FILE_OK else {"status": "present", "first_seen_utc": iso(now_utc())}
                rec.update(common, sha256=sha, bytes=size, sha256_osf_match=(sha == expected_sha) if expected_sha else None)
                state["files"][key] = rec
                log(f"{tag} present   {rel}")
            else:
                state["files"][key] = dict(common, status="mismatch_existing", sha256=sha, bytes=size,
                                           checked_at_utc=iso(now_utc()))
                log(f"{tag} WARNING   {rel}: a file is already there but its sha256 differs from OSF; left untouched")
            save()
            continue
        if not e.get("download_url"):
            state["files"][key] = dict(common, status="failed", error="no download link in the OSF listing")
            log(f"{tag} FAILED    {rel}: no download link in the OSF listing")
            save()
            continue
        log(f"{tag} get       {rel} ({human(expected_size)})")

        def check(part: Path, expected_sha=expected_sha, expected_size=expected_size):
            sha, size = sha256_file(part)
            if expected_sha and sha != expected_sha:
                return f"sha256 differs from OSF (got {sha[:12]}, expected {expected_sha[:12]}; {size} bytes)"
            if expected_size is not None and size != expected_size:
                return f"size differs from OSF ({size} bytes, expected {expected_size})"
            return None

        res = fetch_to(http, e["download_url"], dest, check, retry_delay, log)
        if res["ok"]:
            state["files"][key] = dict(common, status="downloaded", sha256=res["sha256"], bytes=res["bytes"],
                                       sha256_osf_match=(res["sha256"] == expected_sha) if expected_sha else None,
                                       downloaded_at_utc=iso(now_utc()), final_url=res["final_url"], seconds=res["seconds"])
        else:
            state["files"][key] = dict(common, status="failed", error=res["error"], failed_at_utc=iso(now_utc()))
            log(f"      FAILED: {res['error']}")
        save()


def snapshot_github(http: Http, github: list, state: dict, data_raw: Path, base: str, log: Log, retry_delay: float,
                    save) -> None:
    log(f"\n[3/4] GitHub snapshots: {len(github)} repositories at pinned commits")
    for i, g in enumerate(github, 1):
        owner, repo = g["repo"].split("/")
        dest = data_raw / "github" / f"{owner}__{repo}@{g['commit'][:12]}.tar.gz"
        rel = dest.relative_to(data_raw).as_posix()
        key = f"{g['repo']}@{g['commit']}"
        url = f"{base}/{owner}/{repo}/archive/{g['commit']}.tar.gz"
        old = state["github"].get(key) or {}
        common = {"study": g["study"], "repo": g["repo"], "commit": g["commit"], "path": rel, "source_url": url,
                  "repo_url": f"https://github.com/{g['repo']}/tree/{g['commit']}", "license": g.get("license"),
                  "linked_from": g.get("linked_from"), "role": g.get("role")}
        tag = f"  [{i}/{len(github)}]"

        def content_check(stats: dict) -> str:
            exp = (g.get("files"), g.get("bytes"))
            if exp == (stats["files"], stats["bytes"]):
                return "ok"
            return f"differs: {stats['files']} files / {stats['bytes']} bytes (expected {exp[0]} / {exp[1]})"

        if dest.exists():
            sha, size = sha256_file(dest)
            if old.get("status") in FILE_OK and old.get("sha256") == sha:
                state["github"][key] = dict(old, **common)
                log(f"{tag} present   {rel}")
            elif old.get("status") in FILE_OK:
                state["github"][key] = dict(common, status="mismatch_existing", sha256=sha, bytes=size)
                log(f"{tag} WARNING   {rel}: sha256 differs from the recorded value; left untouched")
            else:
                try:
                    stats = tar_stats(dest)
                    state["github"][key] = dict(common, status="present", sha256=sha, bytes=size,
                                                content_check=content_check(stats), first_seen_utc=iso(now_utc()))
                    log(f"{tag} present   {rel} (content {state['github'][key]['content_check']})")
                except (tarfile.TarError, OSError, EOFError) as ex:
                    state["github"][key] = dict(common, status="mismatch_existing", sha256=sha, bytes=size,
                                                error=f"unreadable archive: {ex}")
                    log(f"{tag} WARNING   {rel}: present but not a readable archive; left untouched")
            save()
            continue
        log(f"{tag} get       {g['repo']} @ {g['commit'][:12]}")
        stats_box = {}

        def check(part: Path):
            try:
                stats_box.update(tar_stats(part))
            except (tarfile.TarError, OSError, EOFError) as ex:
                return f"not a readable .tar.gz ({ex})"
            return None

        res = fetch_to(http, url, dest, check, retry_delay, log)
        if res["ok"]:
            cc = content_check(stats_box)
            state["github"][key] = dict(common, status="downloaded", sha256=res["sha256"], bytes=res["bytes"],
                                        archive_files=stats_box.get("files"), archive_file_bytes=stats_box.get("bytes"),
                                        content_check=cc, downloaded_at_utc=iso(now_utc()), seconds=res["seconds"])
            if cc != "ok":
                log(f"      note: content {cc}")
        else:
            state["github"][key] = dict(common, status="failed", error=res["error"], failed_at_utc=iso(now_utc()))
            log(f"      FAILED: {res['error']}")
        save()


def save_wikis(api: OsfApi, nodes: list, wiki_dir: Path, data_raw: Path, state: dict, api_base: str, log: Log, save) -> None:
    # components with wiki pages; when OSF gave no count, try any component whose wiki is not switched off
    targets = [n for n in nodes if not n["excluded"] and ((n.get("wiki_count") or 0) > 0 or
                                                          (n.get("wiki_count") is None and n.get("wiki_enabled") is not False))]
    log(f"\n[4/4] OSF wiki pages: {len(targets)} components with a wiki")
    state["wikis_pending"] = False
    for n in targets:
        try:
            for w in api.pages(with_query(f"{api_base}/nodes/{n['node']}/wikis/", "page[size]=100"), essential=False):
                wa = w.get("attributes") or {}
                name = wa.get("name") or w.get("id")
                url = (w.get("links") or {}).get("download")
                if not url:
                    continue
                body = api.raw(url, essential=False)
                dest = wiki_dir / f"{n['node']}__{safe_name(name)}.md"
                if dest.exists() and dest.read_bytes() != body:   # wiki changed since an earlier run: keep both
                    dest = wiki_dir / f"{n['node']}__{safe_name(name)}__{now_utc():%Y%m%d}.md"
                if not dest.exists():
                    write_bytes_atomic(dest, body)
                state["wikis"][f"{n['node']}:{name}"] = {
                    "study": n["study"], "node": n["node"], "page": name, "path": dest.relative_to(data_raw).as_posix(),
                    "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "source_url": url,
                    "osf_date_modified": wa.get("date_modified"), "saved_at_utc": iso(now_utc())}
                log(f"  {n['node']}  {name}: {len(body)} bytes")
        except RateLimited:
            state["wikis_pending"] = True
            log("  OSF rate limit: the remaining wiki pages were skipped; rerun the same command later to fetch them")
            break
        except (HttpError, TransportError) as e:
            state["wikis_pending"] = True
            log(f"  {n['node']}: wiki not saved ({e})")
        save()


# ---------------------------------------------------------------------------------------------------------------------
# records
# ---------------------------------------------------------------------------------------------------------------------
LISTING_FIELDS = ["study", "root", "node", "node_title", "kind", "path", "size", "sha256_osf", "md5_osf", "date_modified",
                  "version", "guid", "action", "reason", "status", "local_path", "download_url", "html_url"]


def write_listing(meta_dir: Path, sources, github, nodes, entries, licenses, state, listed_at) -> None:
    write_json(meta_dir / "listing.json", {"listed_at_utc": listed_at, "script_version": SCRIPT_VERSION,
                                           "sources": sources, "github": github, "licenses": licenses,
                                           "nodes": nodes, "entries": entries})
    titles = {n["node"]: n["title"] for n in nodes}
    rows = []
    for n in nodes:
        if n["excluded"]:
            rows.append({"study": n["study"], "root": n["root"], "node": n["node"], "node_title": n["title"],
                         "kind": "component", "path": "", "action": "excluded", "reason": n["excluded"]})
    for e in entries:
        st = state["files"].get(f"{e['node']}:{e['path']}") or {}
        rows.append({**{k: e.get(k) for k in LISTING_FIELDS if k in e}, "node_title": titles.get(e["node"]),
                     "status": st.get("status", ""), "local_path": st.get("path", "")})
    tmp = meta_dir / "listing.csv.tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LISTING_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, meta_dir / "listing.csv")


def md_cell(x) -> str:
    return "" if x is None else str(x).replace("|", "\\|").replace("\n", " ")


def write_manifest(data_raw: Path, sources, github, nodes, entries, licenses, state, run: dict) -> None:
    nodes_by_id = {n["node"]: n for n in nodes}
    files = sorted((v for v in state["files"].values() if v.get("status") in FILE_OK), key=lambda v: v["path"])
    gh = sorted((v for v in state["github"].values() if v.get("status") in FILE_OK), key=lambda v: v["path"])
    wk = sorted(state["wikis"].values(), key=lambda v: v["path"])
    lines = [f"{v['sha256']}  {v['path']}" for v in files + gh + wk]
    write_bytes_atomic(data_raw / "MANIFEST.sha256", ("\n".join(lines) + "\n").encode("utf-8") if lines else b"")

    L = ["# MANIFEST of data_raw/ (project 3: human performance on 0-1 knapsack instances)", "",
         f"Written by `code/01_osf_download.py` version {SCRIPT_VERSION} (script sha256 `{run['script_sha256'][:16]}`) "
         f"at {run['ended_stamp']}. Mode: {run['mode']}. Python {run['python']}; HTTP via {run['http']}; {run['platform']}.",
         f"OSF listing time (UTC): {run.get('listed_at_utc') or 'n/a'}. OSF API requests in this run: {run['api_requests']} "
         f"(answered from cache: {run['api_cache_hits']}; waited for rate limits: {run['api_waited_s']} s).", "",
         "Check the files with `cd data_raw && shasum -a 256 -c MANIFEST.sha256`. Files in `data_raw/` are kept as "
         "downloaded (zip archives are not unpacked here); every transformation is done by scripts in `code/` and written "
         "to `data_proc/`.", "",
         "## Sources", "",
         "| Study | OSF project | Title | Article | License (OSF) | DOI |", "|---|---|---|---|---|---|"]
    for s in sources:
        n = nodes_by_id.get(s["root"]) or {}
        L.append(f"| {s['study']} | [{s['root']}](https://osf.io/{s['root']}/) | {md_cell(n.get('title'))} | "
                 f"{md_cell(s.get('paper'))} | {md_cell(license_label(n, licenses) if n else '')} | {md_cell(s.get('doi') or '')} |")
    L += ["", "## OSF components", "",
          "| Study | Node | Parent | Title | Category | Modified (OSF) | Files listed | Action |", "|---|---|---|---|---|---|---|---|"]
    for n in nodes:
        act = f"excluded: {n['excluded']}" if n["excluded"] else "listed"
        if n.get("providers"):
            act += f"; storage providers {n['providers']}"
        L.append(f"| {n['study']} | [{n['node']}]({n['html']}) | {md_cell(n.get('parent') or '')} | {md_cell(n.get('title'))} | "
                 f"{md_cell(n.get('category'))} | {md_cell((n.get('date_modified') or '')[:10])} | "
                 f"{n.get('n_files', 0)} ({human(n.get('n_listed_bytes'))}) | {md_cell(act)} |")
    L += ["", f"## OSF files kept ({len(files)} files, {human(sum(v['bytes'] for v in files))})", "",
          "| Study | Local path | Bytes | sha256 | Equal to OSF sha256 | OSF version | Source | Retrieved (UTC) | License |",
          "|---|---|---|---|---|---|---|---|---|"]
    match_label = {True: "yes", False: "NO", None: "n/a"}
    for v in files:
        when = v.get("downloaded_at_utc") or f"present ({v.get('first_seen_utc', '')})"
        L.append(f"| {v['study']} | `{md_cell(v['path'])}` | {v['bytes']} | `{v['sha256']}` | "
                 f"{match_label[v.get('sha256_osf_match')]} | {md_cell(v.get('osf_version'))} | "
                 f"[download]({v.get('source_url')}) / [page]({v.get('osf_page')}) | {md_cell(when)} | {md_cell(v.get('license'))} |")
    L += ["", f"## GitHub snapshots ({len(gh)})", "",
          "| Study | Repository @ commit | Local file | Bytes | sha256 | Content check | License | Linked from | Role |",
          "|---|---|---|---|---|---|---|---|---|"]
    for v in gh:
        L.append(f"| {v['study']} | [{v['repo']} @ {v['commit'][:12]}]({v['repo_url']}) | `{v['path']}` | {v['bytes']} | "
                 f"`{v['sha256']}` | {md_cell(v.get('content_check'))} | {md_cell(v.get('license'))} | "
                 f"{md_cell(v.get('linked_from'))} | {md_cell(v.get('role'))} |")
    notes = [g for g in github if g.get("note")]
    for g in notes:
        L.append(f"\nNote ({g['repo']}): {g['note']}.")
    L += ["", f"## OSF wiki pages ({len(wk)})", "", "| Study | Node | Page | Local file | Bytes | sha256 | Modified (OSF) |",
          "|---|---|---|---|---|---|---|"]
    for v in wk:
        L.append(f"| {v['study']} | {v['node']} | {md_cell(v['page'])} | `{v['path']}` | {v['bytes']} | `{v['sha256']}` | "
                 f"{md_cell((v.get('osf_date_modified') or '')[:10])} |")
    if state.get("wikis_pending"):
        L.append("\nSome wiki pages were not saved in the last run (rate limit or error); a rerun fetches them.")
    skipped = [e for e in entries if e["action"] == "excluded"]
    L += ["", f"## Not downloaded ({len(skipped)} files or folders, plus excluded components above)", "",
          "| Study | Node | Path | Kind | Size | Reason |", "|---|---|---|---|---|---|"]
    for e in skipped:
        L.append(f"| {e['study']} | {e['node']} | `{md_cell(e['path'])}` | {e['kind']} | "
                 f"{human(e.get('size')) if e['kind'] == 'file' else 'not listed'} | {md_cell(e['reason'])} |")
    problems = [v for v in list(state["files"].values()) + list(state["github"].values())
                if v.get("status") not in FILE_OK]
    planned = [e for e in entries if e["kind"] == "file" and e["action"] == "download"
               and (state["files"].get(f"{e['node']}:{e['path']}") or {}).get("status") is None]
    L += ["", "## Problems", ""]
    if not problems and not planned:
        L.append("None.")
    for v in problems:
        L.append(f"- {v.get('status')}: `{v.get('path')}` {md_cell(v.get('error') or '')}")
    if planned:
        L.append(f"- {len(planned)} listed files not fetched yet ({human(sum(e['size'] or 0 for e in planned))}); "
                 "run without --list-only to fetch them.")
    L.append("")
    write_bytes_atomic(data_raw / "MANIFEST.md", "\n".join(L).encode("utf-8"))


def load_state(path: Path) -> dict:
    state = {"files": {}, "github": {}, "wikis": {}, "runs": []}
    if path.exists():
        try:
            state.update(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, OSError) as e:
            raise SystemExit(f"cannot read {path}: {e}")
    return state


# ---------------------------------------------------------------------------------------------------------------------
# modes
# ---------------------------------------------------------------------------------------------------------------------
def dry_run(args, sources, github, data_raw: Path, state: dict, log: Log) -> int:
    log("Dry run: no network access; nothing is written except these lines in the log.")
    log(f"  Python {platform.python_version()} ({sys.executable}); curl: {curl_version() or 'not found'}")
    log(f"  data_raw: {data_raw} (writable: {os.access(data_raw if data_raw.exists() else data_raw.parent, os.W_OK)})")
    log(f"  size cap per file: {human(args.max_mb * 1_000_000)}; includes: {args.include or 'none'}")
    for s in sources:
        log(f"  {s['study']}: OSF {s['root']} ({s.get('paper')}); all public components are listed")
        for e in s["exclude"]:
            log(f"      exclude {e['node']}:{e.get('path', '(component)')}: {e['reason']}")
    if not args.no_github:
        log(f"  GitHub: {len(github)} repositories at pinned commits")
        for g in github:
            log(f"      {g['study']} {g['repo']} @ {g['commit'][:12]} ({g['files']} files, {human(g['bytes'])} unpacked)")
    ok = sum(1 for v in state["files"].values() if v.get("status") in FILE_OK)
    log(f"  current state: {ok} OSF files kept, {sum(1 for v in state['github'].values() if v.get('status') in FILE_OK)} "
        f"GitHub snapshots, {len(state['wikis'])} wiki pages, {len(state['runs'])} earlier runs")
    log("  expected on a first run (2026-10-16 listing): about 250 MB from OSF and 50 MB of GitHub archives; "
        "about 80 OSF API requests")
    return 0


def verify(data_raw: Path, state: dict, log: Log) -> int:
    bad = n = 0
    for group in ("files", "github", "wikis"):
        for v in state[group].values():
            if group != "wikis" and v.get("status") not in FILE_OK:
                continue
            n += 1
            p = data_raw / v["path"]
            if not p.exists():
                bad += 1
                log(f"  MISSING   {v['path']}")
                continue
            sha, _ = sha256_file(p)
            if sha != v["sha256"]:
                bad += 1
                log(f"  CHANGED   {v['path']}")
    log(f"Verified {n} files: {n - bad} unchanged, {bad} missing or changed.")
    return 1 if bad else 0


def summarize(state: dict, entries: list, started_iso: str, log: Log) -> int:
    log("\nSummary")
    studies = sorted({e["study"] for e in entries} | {v["study"] for v in state["files"].values()})
    for s in studies:
        st = [v for v in state["files"].values() if v["study"] == s]
        ex = [e for e in entries if e["study"] == s and e["kind"] == "file" and e["action"] == "excluded"]
        kept = [v for v in st if v.get("status") in FILE_OK]
        new = [v for v in kept if (v.get("downloaded_at_utc") or "") >= started_iso]
        log(f"  {s}: kept {len(kept)} files ({human(sum(v['bytes'] for v in kept))}), {len(new)} of them fetched in this "
            f"run; excluded {len(ex)}; problems {sum(1 for v in st if v.get('status') not in FILE_OK)}")
    gh = state["github"].values()
    log(f"  GitHub: {sum(1 for v in gh if v.get('status') in FILE_OK)} snapshots kept, "
        f"{sum(1 for v in gh if v.get('status') not in FILE_OK)} problems")
    log(f"  Wiki pages: {len(state['wikis'])}" + (" (some pending)" if state.get("wikis_pending") else ""))
    problems = [v for v in list(state["files"].values()) + list(gh) if v.get("status") not in FILE_OK]
    for v in problems:
        log(f"  PROBLEM {v.get('status')}: {v.get('path')} {v.get('error') or ''}")
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-only", action="store_true", help="list OSF nodes and files; download nothing")
    ap.add_argument("--dry-run", action="store_true", help="offline: show the plan and the current state")
    ap.add_argument("--verify", action="store_true", help="offline: re-hash kept files against the recorded sha256")
    ap.add_argument("--refresh", action="store_true", help="list OSF again instead of using cached API responses")
    ap.add_argument("--max-mb", type=float, default=100.0, help="size cap per OSF file in MB of 1,000,000 bytes (default 100)")
    ap.add_argument("--include", action="append", default=[], metavar="NODE:/path", help="fetch an excluded file or folder")
    ap.add_argument("--max-wait", type=int, default=3600, help="longest wait (s) after an OSF HTTP 429 (default 3600)")
    ap.add_argument("--backend", choices=["auto", "curl", "urllib"], default="auto")
    ap.add_argument("--no-github", action="store_true", help="skip the GitHub snapshots")
    ap.add_argument("--no-wikis", action="store_true", help="skip the OSF wiki pages")
    # for tests (a mock OSF server and temporary folders)
    ap.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    ap.add_argument("--api-base", default=OSF_API, help=argparse.SUPPRESS)
    ap.add_argument("--github-base", default=GITHUB_ARCHIVE, help=argparse.SUPPRESS)
    ap.add_argument("--data-raw", type=Path, default=PROJ / "data_raw", help=argparse.SUPPRESS)
    ap.add_argument("--log", type=Path, default=PROJ / "output" / "log_3a.txt", help=argparse.SUPPRESS)
    ap.add_argument("--retry-delay", type=float, default=5.0, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    sources, github = SOURCES, GITHUB
    if args.config:
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
        sources, github = cfg["sources"], cfg.get("github", [])
    includes = []
    for spec in args.include:
        node, sep, path = spec.partition(":")
        if not sep or not node:
            ap.error(f"--include expects NODE:/path, got {spec!r}")
        includes.append((node, path if path.startswith("/") else "/" + path))

    data_raw = args.data_raw.resolve()
    meta_dir = data_raw / "_osf_meta"
    log = Log(args.log)
    state_path = meta_dir / "state.json"
    state = load_state(state_path)
    mode = "dry-run" if args.dry_run else "verify" if args.verify else "list-only" if args.list_only else "download"
    started = now_utc()
    log(f"\n=== 3-A1 OSF/GitHub backup, mode {mode}, {stamp(started)} (script {SCRIPT_VERSION}) ===")
    if args.dry_run:
        return dry_run(args, sources, github, data_raw, state, log)
    if args.verify:
        return verify(data_raw, state, log)

    backend = args.backend
    if backend == "auto":
        backend = "curl" if shutil.which("curl") else "urllib"
    data_raw.mkdir(parents=True, exist_ok=True)
    if args.refresh and (meta_dir / "api").exists():   # keep the old responses; never delete
        os.replace(meta_dir / "api", meta_dir / f"api_superseded_{started:%Y%m%dT%H%M%SZ}")
    http = Http(backend, os.environ.get("OSF_TOKEN") or None)
    api = OsfApi(http, meta_dir / "api", args.refresh, args.max_wait, log, args.retry_delay)
    run = {"mode": mode, "started_utc": iso(started), "python": platform.python_version(),
           "http": curl_version() if backend == "curl" else f"urllib (Python {platform.python_version()})",
           "platform": platform.platform(), "script_sha256": sha256_file(Path(__file__))[0], "listed_at_utc": None}
    log(f"Python {run['python']}; HTTP via {run['http']}; data_raw = {data_raw}")

    def save() -> None:
        write_json(state_path, state)

    nodes, entries, licenses, rc = [], [], {}, 0
    try:
        log("\n[1/4] Listing the OSF projects")
        for src in sources:
            log(f"  {src['study']}  OSF {src['root']}")
            n, e = crawl_source(api, src, Rules(src, int(args.max_mb * 1_000_000), includes), args.api_base, log)
            nodes += n
            entries += e
        licenses = resolve_licenses(api, nodes)
        run["listed_at_utc"] = iso(now_utc())
        write_listing(meta_dir, sources, github, nodes, entries, licenses, state, run["listed_at_utc"])
        n_get = [e for e in entries if e["kind"] == "file" and e["action"] == "download"]
        log(f"  listed {len(nodes)} components and {sum(1 for e in entries if e['kind'] == 'file')} files; "
            f"{len(n_get)} files ({human(sum(e['size'] or 0 for e in n_get))}) selected, "
            f"{sum(1 for e in entries if e['action'] == 'excluded')} files or folders excluded")
        if not args.list_only:
            nodes_by_id = {n["node"]: n for n in nodes}
            download_osf_files(http, entries, nodes_by_id, licenses, state, data_raw, log, args.retry_delay, save)
            if args.no_github:
                log("\n[3/4] GitHub snapshots: skipped (--no-github)")
            else:
                snapshot_github(http, github, state, data_raw, args.github_base.rstrip("/"), log, args.retry_delay, save)
            if args.no_wikis:
                log("\n[4/4] OSF wiki pages: skipped (--no-wikis)")
            else:
                save_wikis(api, nodes, meta_dir / "wikis", data_raw, state, args.api_base, log, save)
    except RateLimited as e:
        log(f"\nStopped: {e}. Everything fetched so far is kept; rerun the same command later to continue.")
        rc = 2
    except KeyboardInterrupt:
        log("\nInterrupted. Everything fetched so far is kept; rerun the same command to continue.")
        rc = 130
    except (HttpError, TransportError, ValueError) as e:
        log(f"\nStopped by an error: {e}")
        rc = 3
    finally:
        ended = now_utc()
        run.update(ended_utc=iso(ended), ended_stamp=stamp(ended), api_requests=api.requests, api_cache_hits=api.cache_hits,
                   api_waited_s=api.waited, exit_code=rc)
        if nodes:
            write_listing(meta_dir, sources, github, nodes, entries, licenses, state, run["listed_at_utc"])
            write_manifest(data_raw, sources, github, nodes, entries, licenses, state, run)
        state["runs"].append(run)
        save()
        shutil.rmtree(http.tmpdir, ignore_errors=True)   # the system temp folder of this run, not a project folder
    problems_rc = summarize(state, entries, run["started_utc"], log)
    rc = rc or problems_rc
    log(f"  OSF API requests: {api.requests} (cached: {api.cache_hits}); waited {api.waited} s for rate limits")
    log(f"  Manifest: {data_raw / 'MANIFEST.md'}")
    log(f"  Log: {args.log}")
    if rc == 0 and not args.list_only:
        log("\nDownload finished.")
    elif rc == 0:
        log("\nListing finished (--list-only).")
    else:
        log(f"\nFinished with problems to check (exit {rc}); see the last lines of the log.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
