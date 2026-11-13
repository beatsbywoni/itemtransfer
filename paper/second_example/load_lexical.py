"""Loaders for the four lexical decision megastudies (original authors' releases).

Every function reads the files exactly as downloaded from the authors' OSF projects (see PROVENANCE.md and
original/MANIFEST.sha256) and returns

    trials : participant, item, family, sample, correct      (word trials only, one row per response)
    items  : item, family, length, + the item-level values the authors published
    log    : dict with every count needed to reconstruct the exclusions

Vocabulary follows DESIGN.md: item = one word; item family = one megastudy; sample = the participants of that
megastudy (one sample per family here).

Exclusions (complete list; nothing else is dropped):
  all families  nonword / pseudoword trials (they are not items of the example: no frequency exists for them).
  ELP           (a) six raw files that the depositors themselves list as redundant or questionable in the OSF wiki
                    of project n63s2 (ELP_SKIPLIST below);
                (b) trials whose accuracy field is neither 0 nor 1 (the field then holds the code of a key that
                    was not a response key; no word/nonword decision was recorded).
  BLP           none.
  DLP           block 50, a repetition of block 1 that the authors ship in a separate file
                (dlp-trials-block-50.txt.zip); the main trial file does not contain it and it is not loaded.
  MEGALEX       trials flagged repetition == 1 by the authors (a word shown a second time to the same person).
Time-outs are kept as errors where the authors scored them as errors (DLP response code "T").
No participant, no word and no trial is removed on the basis of accuracy or response time.

Important reading detail: the words "null", "nan", "NA" and similar are real stimuli. All tables are read with
keep_default_na=False so that they stay strings (the feasibility probe lost two BLP words this way).

Only numpy and pandas are needed. Files are opened read-only; nothing in them is executed.
"""
from __future__ import annotations

import os
import re
import zipfile

import numpy as np
import pandas as pd

DEFAULT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "original")

FAMILIES = ("ELP", "BLP", "DLP", "MEGALEX")

# Listed by the depositors in the wiki of https://osf.io/n63s2/ (November 2021 update) as
# "redundant or questionable files" for the lexical decision task.
ELP_SKIPLIST = ("9999.LDT", "793DATA.LDT", "Data999.LDT", "Data1000.LDT", "Data1010.LDT", "Data1016.LDT")

_ELP_TRIAL = re.compile(r"^(\d+),(\d+),([01]),(-?\d+),(-?\d+),(.*)$")


def _tidy(df, family):
    out = pd.DataFrame({
        "participant": (family + "_" + df["participant"].astype(str)).astype("category"),
        "item": df["item"].astype(str).to_numpy(),
        "family": family,
        "sample": family,
        "correct": df["correct"].to_numpy().astype(np.int8),
    })
    out["family"] = out["family"].astype("category")
    out["sample"] = out["sample"].astype("category")
    return out.reset_index(drop=True)


def _read_tab_zip(zpath, member):
    with zipfile.ZipFile(zpath) as z:
        with z.open(member) as f:
            return pd.read_csv(f, sep="\t", low_memory=False, keep_default_na=False, na_values=["NA"],
                               dtype={"spelling": str})


# --------------------------------------------------------------------------------------------------------- ELP
def load_elp(root=DEFAULT_ROOT, items_csv=None):
    """English Lexicon Project, raw lexical decision files (OSF n63s2, ldt_raw.zip, version 2 of 2021-11-20).

    One .LDT file per participant with two sessions. Trial lines have six comma-separated fields:
    trial order, item serial number, lexicality (1 = word), accuracy, RT, item.

    items_csv: optional path to an item-characteristics table generated from elexicon.wustl.edu (columns Word,
    Length, Ortho_N, OLD, LgSUBTLWF, I_Mean_Accuracy, ...). The website could not be read in this session, so the
    default is None and the items table then holds only what the raw files contain (item, serial number, length).
    """
    zpath = os.path.join(root, "elp", "ldt_raw.zip")
    rows, log = [], {"files_in_zip": 0, "files_skipped": list(ELP_SKIPLIST)}
    with zipfile.ZipFile(zpath) as z:
        names = sorted(z.namelist())
        log["files_in_zip"] = len(names)
        for name in names:
            if name in ELP_SKIPLIST:
                continue
            lines = z.read(name).decode("latin-1").splitlines()
            subject = None
            for i, line in enumerate(lines):
                if subject is None and line.startswith("Univ,") and i + 1 < len(lines):
                    subject = lines[i + 1].split(",")[3].strip()
                m = _ELP_TRIAL.match(line)
                if m:
                    rows.append((subject, name, int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(6)))
    raw = pd.DataFrame(rows, columns=["participant", "file", "itemno", "lexicality", "acc", "item"])
    if raw.groupby("participant")["file"].nunique().max() != 1:
        raise ValueError("ELP: a subject number occurs in more than one retained file")
    log["files_used"] = int(raw["file"].nunique())
    log["trials_all"] = int(len(raw))
    log["trials_nonword_dropped"] = int((raw["lexicality"] == 0).sum())
    words = raw[raw["lexicality"] == 1]
    log["word_trials_before_exclusion"] = int(len(words))
    valid = words["acc"].isin([0, 1])
    log["word_trials_invalid_key_dropped"] = int((~valid).sum())
    words = words[valid].rename(columns={"acc": "correct"})
    trials = _tidy(words, "ELP")

    items = (raw[raw["lexicality"] == 1][["item", "itemno"]].drop_duplicates().sort_values("itemno")
             .reset_index(drop=True))
    items["family"] = "ELP"
    items["length"] = items["item"].str.len()
    items = items[["item", "family", "length", "itemno"]]
    if items_csv is not None:
        pub = pd.read_csv(items_csv, keep_default_na=False, na_values=["NA", "NULL", "#"], dtype={"Word": str},
                          low_memory=False)
        pub = pub.rename(columns={c: "pub_" + c for c in pub.columns if c != "Word"})
        items = items.merge(pub, how="left", left_on="item", right_on="Word").drop(columns=["Word"])
        log["items_with_published_values"] = int(items.filter(like="pub_").notna().any(axis=1).sum())
    return trials, items, log


# --------------------------------------------------------------------------------------------- BLP and DLP
def _load_crr(root, sub, family):
    t = _read_tab_zip(os.path.join(root, sub, f"{sub}-trials.txt.zip"), f"{sub}-trials.txt")
    log = {"trials_all": int(len(t)), "trials_nonword_dropped": int((t["lexicality"] != "W").sum())}
    w = t[t["lexicality"] == "W"].rename(columns={"spelling": "item", "accuracy": "correct"})
    log["word_trials_before_exclusion"] = int(len(w))
    log["word_trials_dropped"] = 0
    log["word_response_codes"] = {str(k): int(v) for k, v in w["response"].value_counts().items()}
    trials = _tidy(w, family)

    it = _read_tab_zip(os.path.join(root, sub, f"{sub}-items.txt.zip"), f"{sub}-items.txt")
    it = it[it["lexicality"] == "W"].drop(columns=["lexicality"])
    it = it.rename(columns={c: "pub_" + c for c in it.columns if c != "spelling"})
    st = _read_tab_zip(os.path.join(root, sub, f"{sub}-stimuli.txt.zip"), f"{sub}-stimuli.txt")
    st = st.drop_duplicates("spelling")
    st = st.rename(columns={c: "pub_" + c for c in st.columns if c != "spelling"})
    items = it.merge(st, how="left", on="spelling").rename(columns={"spelling": "item"})
    items.insert(1, "family", family)
    items.insert(2, "length", items["item"].str.len())
    return trials, items.reset_index(drop=True), log


def load_blp(root=DEFAULT_ROOT):
    """British Lexicon Project (OSF b5sdk): blp-trials.txt.zip, blp-items.txt.zip, blp-stimuli.txt.zip."""
    return _load_crr(root, "blp", "BLP")


def load_dlp(root=DEFAULT_ROOT):
    """Dutch Lexicon Project (OSF uw7t6): dlp-trials.txt.zip (block 50 is not in this file), items, stimuli."""
    trials, items, log = _load_crr(root, "dlp", "DLP")
    log["block_50_not_loaded"] = "dlp-trials-block-50.txt.zip (repetition of block 1)"
    return trials, items, log


# ----------------------------------------------------------------------------------------------------- MEGALEX
_MEGA_ITEM_COLS = ["row", "item", "pub_rt.m", "pub_rt.sd", "pub_rt.n", "pub_zrt.m", "pub_zrt.sd", "pub_zrt.n",
                   "pub_acy", "pub_acy.n", "pub_nblettres", "pub_puort", "pub_old20", "pub_fb", "pub_ff", "pub_ft"]


def load_megalex(root=DEFAULT_ROOT):
    """MEGALEX, visual lexical decision (OSF 7z6th).

    Trials: member Visual.WpuispW.essais_ElTec.txt of "By trials Auditory & Visual-MEGALEX.zip"; semicolon
    separated, the header names nine columns and the data rows carry an extra leading row number.
    Items: vw.ParItems.DVandIV.txt (25,776 words; the authors left out words below 67% accuracy).
    """
    zpath = os.path.join(root, "megalex", "By trials Auditory & Visual-MEGALEX.zip")
    cols = ["row", "item", "numinit", "participant", "block", "trial_num_block", "category", "correct", "rt",
            "repetition"]
    with zipfile.ZipFile(zpath) as z:
        with z.open("Visual.WpuispW.essais_ElTec.txt") as f:
            t = pd.read_csv(f, sep=";", skiprows=1, header=None, names=cols, dtype={"item": str},
                            keep_default_na=False, na_values=["NA"], encoding="utf-8")
    log = {"trials_all": int(len(t)), "trials_nonword_dropped": int((t["category"] != "w").sum())}
    w = t[t["category"] == "w"]
    log["word_trials_before_exclusion"] = int(len(w))
    log["word_trials_repetition_dropped"] = int((w["repetition"] != 0).sum())
    w = w[w["repetition"] == 0]
    trials = _tidy(w, "MEGALEX")

    pub = pd.read_csv(os.path.join(root, "megalex", "vw.ParItems.DVandIV.txt"), sep=";", skiprows=1, header=None,
                      names=_MEGA_ITEM_COLS, dtype={"item": str}, keep_default_na=False, na_values=["NA"],
                      encoding="utf-8").drop(columns=["row"])
    items = pd.DataFrame({"item": sorted(w["item"].unique())})
    items["family"] = "MEGALEX"
    items["length"] = items["item"].str.len()
    items = items.merge(pub, how="left", on="item")
    log["items_with_published_values"] = int(items["pub_acy"].notna().sum())
    return trials, items, log


LOADERS = {"ELP": load_elp, "BLP": load_blp, "DLP": load_dlp, "MEGALEX": load_megalex}


def load_family(family, root=DEFAULT_ROOT, **kwargs):
    return LOADERS[family](root, **kwargs)


def load_all(root=DEFAULT_ROOT, elp_items_csv=None):
    """Return {family: (trials, items, log)} for the four megastudies."""
    out = {}
    for fam in FAMILIES:
        out[fam] = load_elp(root, items_csv=elp_items_csv) if fam == "ELP" else LOADERS[fam](root)
    return out
