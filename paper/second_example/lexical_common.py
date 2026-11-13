"""Shared set-up for the second worked example: item families, shared-word assignment, analysis tables.

Vocabulary as in DESIGN.md. Item = one word of one language; item family = one megastudy; sample = its participants.
"""
import os, unicodedata
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
RESULTS = os.path.join(HERE, "results")
FAMILIES = ["ELP", "BLP", "DLP", "MEGALEX"]
LANG = {"ELP": "en", "BLP": "en", "DLP": "nl", "MEGALEX": "fr"}
MEASURES = ["zipf", "length", "old20"]
SEED = 20261113


def _key(s):
    return unicodedata.normalize("NFC", s).lower()


def load_megastudies():
    """All word trials of the four megastudies with language-specific item identifiers.
    Returns trials (participant, item, sample, correct) and the word table with the recomputed measures."""
    words = pd.read_pickle(os.path.join(CACHE, "items_measures.pkl"))
    frames = []
    for fam in FAMILIES:
        t = pd.read_pickle(os.path.join(CACHE, f"trials_{fam}.pkl"))
        u = pd.unique(t["item"])
        ids = {s: LANG[fam] + ":" + _key(s) for s in u}
        frames.append(pd.DataFrame({"participant": t["participant"].astype(str).to_numpy(),
                                    "item": t["item"].map(ids).to_numpy(), "sample": fam,
                                    "correct": t["correct"].to_numpy().astype(np.int8)}))
    return pd.concat(frames, ignore_index=True), words


def shared_words(words):
    e = set(words.loc[words["megastudy"] == "ELP", "item"])
    b = set(words.loc[words["megastudy"] == "BLP", "item"])
    return np.array(sorted(e & b))


def assign_shared(words, assignment="primary", seed=SEED):
    """Family of every shared English word: {item: 'ELP' or 'BLP'}; 'dropped' returns an empty mapping."""
    sh = shared_words(words)
    perm = np.random.default_rng(seed).permutation(len(sh))
    first = sh[perm[: len(sh) // 2]]
    rest = sh[perm[len(sh) // 2:]]
    if assignment == "primary":
        return {**{w: "ELP" for w in first}, **{w: "BLP" for w in rest}}
    if assignment == "opposite":
        return {**{w: "BLP" for w in first}, **{w: "ELP" for w in rest}}
    if assignment == "dropped":
        return {}
    raise ValueError(assignment)


def build(trials, words, assignment="primary", n_words=None, seed=SEED):
    """Analysis tables for the transfer: families share no item.

    n_words: optional size of a fixed-seed random sample of words per family (drawn after the assignment).
    """
    sh = set(shared_words(words))
    fam_of = assign_shared(words, assignment, seed)
    w = words.copy()
    keep = ~w["item"].isin(sh) | (w["item"].map(fam_of) == w["megastudy"])
    w = w[keep].rename(columns={"megastudy": "family"})
    if n_words is not None:
        rng = np.random.default_rng(seed)
        parts = []
        for fam in FAMILIES:
            sub = w[w["family"] == fam].sort_values("item")
            parts.append(sub.iloc[np.sort(rng.choice(len(sub), size=n_words, replace=False))])
        w = pd.concat(parts)
    items = w[["item", "family"] + MEASURES + ["old20_equal_lexicon"]].reset_index(drop=True)
    assert not items["item"].duplicated().any()
    pair = pd.MultiIndex.from_frame(items[["item", "family"]])
    t = trials[pd.MultiIndex.from_arrays([trials["item"], trials["sample"]]).isin(pair)].copy()
    t["family"] = t["sample"]
    return t.reset_index(drop=True), items
