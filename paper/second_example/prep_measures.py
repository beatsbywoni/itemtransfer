"""Step 1 of the second worked example: recompute the three measures for every word with one implementation
and compare them with the values the megastudy authors published.

Run from this directory:  python3 prep_measures.py
Inputs : cache/pubitems_<megastudy>.pkl (written by cache_trials.py from original/ only),
         original/frequency/SUBTLEX-*.xlsx
Outputs: cache/items_measures.pkl (word-level table; not for redistribution, see LEXICAL_REPORT.md),
         results/step1_*.csv, cache/step1_info.json
No published ELP item value is read anywhere.
"""
import json, os, time, unicodedata
import numpy as np, pandas as pd
import openpyxl, rapidfuzz, wordfreq
from rapidfuzz.distance import Levenshtein
from rapidfuzz.process import cdist
from scipy.stats import spearmanr, pearsonr

HERE = os.path.dirname(os.path.abspath(__file__))
LANG = {"ELP": "en", "BLP": "en", "DLP": "nl", "MEGALEX": "fr"}
NAME = {"ELP": "English Lexicon Project", "BLP": "British Lexicon Project", "DLP": "Dutch Lexicon Project",
        "MEGALEX": "MEGALEX"}
SEED_EQUAL_LEXICON = 20261113
t0 = time.time()


def n_letters(s):
    """Number of Unicode letters in the NFC-normalised string (an accented letter counts once; apostrophes and
    full stops are not letters)."""
    return sum(unicodedata.category(c).startswith("L") for c in unicodedata.normalize("NFC", s))


def old20(words, lexicon, k=20, chunk=1000):
    """Mean Levenshtein distance from each word to its k nearest other entries of `lexicon` (unit costs).
    `lexicon` holds distinct strings; an entry identical to the word is excluded once (the word itself)."""
    lex = list(lexicon)
    lexset = set(lex)
    out = np.empty(len(words))
    for a in range(0, len(words), chunk):
        w = words[a:a + chunk]
        D = cdist(w, lex, scorer=Levenshtein.distance, dtype=np.uint8, workers=2)
        part = np.sort(np.partition(D, k, axis=1)[:, :k + 1], axis=1).astype(float)
        for i, x in enumerate(w):
            out[a + i] = part[i, 1:k + 1].mean() if x in lexset else part[i, :k].mean()
    return out


items = {}
counts = []
for fam in LANG:
    pub = pd.read_pickle(os.path.join(HERE, "cache", f"pubitems_{fam}.pkl"))
    d = pd.DataFrame({"megastudy": fam, "string": pub["item"].to_numpy()})
    d["key"] = d["string"].map(lambda s: unicodedata.normalize("NFC", s).lower())
    assert not d["key"].duplicated().any()
    d["item"] = LANG[fam] + ":" + d["key"]
    d["length"] = d["key"].map(n_letters).astype(float)
    d["n_char"] = d["key"].str.len()
    d["zipf"] = [wordfreq.zipf_frequency(w, LANG[fam]) for w in d["key"]]
    lex = d["key"].tolist()
    d["old20"] = old20(lex, lex)
    rng = np.random.default_rng(SEED_EQUAL_LEXICON)
    sub = sorted(rng.choice(len(lex), size=14089, replace=False)) if len(lex) > 14089 else range(len(lex))
    d["old20_equal_lexicon"] = old20(lex, [lex[i] for i in sub])
    items[fam] = (d, pub)
    counts.append(dict(megastudy=NAME[fam], language=LANG[fam], n_words=len(d),
                       n_zipf_unknown=int((d["zipf"] == 0).sum()), share_zipf_unknown=float((d["zipf"] == 0).mean()),
                       zipf_min_known=float(d.loc[d["zipf"] > 0, "zipf"].min()), zipf_median=float(d["zipf"].median()),
                       zipf_max=float(d["zipf"].max()),
                       n_words_with_non_letter=int((d["length"] != d["n_char"]).sum()),
                       n_words_with_capital=int((d["string"] != d["string"].str.lower()).sum()),
                       n_words_non_ascii=int((~d["key"].map(str.isascii)).sum()),
                       length_min=int(d["length"].min()), length_max=int(d["length"].max()),
                       length_median=float(d["length"].median()),
                       old20_reference_lexicon_size=len(lex), old20_median=float(d["old20"].median()),
                       old20_min=float(d["old20"].min()), old20_max=float(d["old20"].max()),
                       old20_equal_lexicon_median=float(d["old20_equal_lexicon"].median())))
    print(fam, "measures done", round(time.time() - t0, 1), flush=True)
pd.DataFrame(counts).to_csv(os.path.join(HERE, "results", "step1_measure_counts.csv"), index=False)


# ------------------------------------------------------------------ comparison with published values
def read_xlsx(path, word_col, value_col):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    head = list(next(rows))
    wi, vi = head.index(word_col), head.index(value_col)
    out = {}
    for r in rows:
        if r[wi] is None or r[vi] is None:
            continue
        k = unicodedata.normalize("NFC", str(r[wi])).lower()
        v = float(r[vi])
        if k not in out or v > out[k]:      # entries that differ only in case: keep the more frequent one
            out[k] = v
    return out


F = os.path.join(HERE, "original", "frequency")
subtlex = {
    "SUBTLEX-US Zipf (file)": read_xlsx(os.path.join(F, "SUBTLEX-US frequency list with PoS and Zipf information.xlsx"),
                                        "Word", "Zipf-value"),
    "SUBTLEX-UK Zipf (file)": read_xlsx(os.path.join(F, "SUBTLEX-UK.xlsx"), "Spelling", "LogFreq(Zipf)"),
    "SUBTLEX-NL Zipf (file)": read_xlsx(os.path.join(F, "SUBTLEX-NL with pos and Zipf cd minimally 2.xlsx"),
                                        "Word", "Zipf"),
}
print("subtlex read", {k: len(v) for k, v in subtlex.items()}, round(time.time() - t0, 1), flush=True)

rows = []


def compare(fam, measure, label, mine, theirs, kind):
    mine, theirs = np.asarray(mine, float), np.asarray(theirs, float)
    ok = np.isfinite(mine) & np.isfinite(theirs)
    a, b = mine[ok], theirs[ok]
    diff = a - b
    row = dict(megastudy=NAME[fam], measure=measure, published=label, kind=kind, n_words=len(mine),
               n_compared=int(ok.sum()), n_published_missing=int((~np.isfinite(theirs)).sum()),
               pearson=float(pearsonr(a, b)[0]), spearman=float(spearmanr(a, b)[0]),
               n_equal=int((np.abs(diff) < 1e-9).sum()) if kind == "same quantity" else np.nan,
               share_equal=float((np.abs(diff) < 1e-9).mean()) if kind == "same quantity" else np.nan,
               n_within_0_05=int((np.abs(diff) <= 0.05 + 1e-9).sum()) if kind == "same quantity" else np.nan,
               mean_difference=float(diff.mean()) if kind == "same quantity" else np.nan,
               max_abs_difference=float(np.abs(diff).max()) if kind == "same quantity" else np.nan)
    rows.append(row)
    return ok, diff


def num(s):
    return pd.to_numeric(s, errors="coerce").to_numpy(float)


d, pub = items["BLP"]
compare("BLP", "length", "nletters (stimulus file)", d["length"], num(pub["pub_nletters"]), "same quantity")
compare("BLP", "length", "nletters against number of characters", d["n_char"], num(pub["pub_nletters"]), "same quantity")
compare("BLP", "old20", "OLD20 (stimulus file)", d["old20"], num(pub["pub_OLD20"]), "same quantity")
compare("BLP", "old20_equal_lexicon", "OLD20 (stimulus file)", d["old20_equal_lexicon"], num(pub["pub_OLD20"]), "same quantity")
compare("BLP", "zipf", "log10(SUBTLEX count + 1) (stimulus file)", d["zipf"], np.log10(num(pub["pub_subtlex.frequency"]) + 1), "other norm")
compare("BLP", "zipf", "log10(BNC count + 1) (stimulus file)", d["zipf"], np.log10(num(pub["pub_bnc.frequency"]) + 1), "other norm")
compare("BLP", "zipf", "SUBTLEX-UK Zipf (file)", d["zipf"], d["key"].map(subtlex["SUBTLEX-UK Zipf (file)"]), "other norm")
compare("BLP", "zipf", "SUBTLEX-US Zipf (file)", d["zipf"], d["key"].map(subtlex["SUBTLEX-US Zipf (file)"]), "other norm")

d, pub = items["DLP"]
nchar = num(pub["pub_nchar"])
ok, diff = compare("DLP", "length", "nchar (stimulus file)", d["length"], nchar, "same quantity")
compare("DLP", "length", "nchar against number of characters", d["n_char"], nchar, "same quantity")
utf8 = d["key"].map(lambda s: len(s.encode("utf-8")))
latin_as_utf8x = d["key"].map(lambda s: len(s) + 2 * sum(not c.isascii() for c in s))
compare("DLP", "length", "nchar against letters + 2 per non-ASCII letter", latin_as_utf8x, nchar, "same quantity")
compare("DLP", "length", "nchar against UTF-8 bytes", utf8, nchar, "same quantity")
dis = d.loc[ok].assign(published_nchar=nchar[ok], difference=diff)
dis = dis[np.abs(dis["difference"]) > 1e-9]
dis = dis.assign(n_non_ascii=dis["key"].map(lambda s: sum(not c.isascii() for c in s)),
                 n_non_letter=dis["n_char"] - dis["length"])
dis[["string", "length", "n_char", "published_nchar", "difference", "n_non_ascii", "n_non_letter"]].to_csv(
    os.path.join(HERE, "results", "step1_dlp_length_discrepancies.csv"), index=False)
miss = d.loc[~np.isfinite(nchar)]
dlp_len = dict(n_published_missing=int((~np.isfinite(nchar)).sum()), n_differ=int(len(dis)),
               n_differ_with_non_ascii=int((dis["n_non_ascii"] > 0).sum()),
               n_differ_explained_by_two_extra_per_non_ascii=int((dis["published_nchar"] == dis["n_char"] + 2 * dis["n_non_ascii"]).sum()),
               n_differ_with_non_letter=int((dis["n_non_letter"] > 0).sum()),
               n_non_ascii_words_total=int((~d["key"].map(str.isascii)).sum()),
               n_non_ascii_words_with_published_value=int((~d.loc[ok, "key"].map(str.isascii)).sum()),
               n_missing_with_non_ascii=int((~miss["key"].map(str.isascii)).sum()),
               n_missing_with_apostrophe=int(miss["key"].str.contains("'").sum()))
compare("DLP", "old20", "OLD20 (stimulus file)", d["old20"], num(pub["pub_OLD20"]), "same quantity")
compare("DLP", "zipf", "log10(SUBTLEX-NL count + 1) (stimulus file)", d["zipf"], np.log10(num(pub["pub_subtlex.frequency"]) + 1), "other norm")
compare("DLP", "zipf", "log10(CELEX count + 1) (stimulus file)", d["zipf"], np.log10(num(pub["pub_celex.frequency"]) + 1), "other norm")
compare("DLP", "zipf", "SUBTLEX-NL Zipf (file)", d["zipf"], d["key"].map(subtlex["SUBTLEX-NL Zipf (file)"]), "other norm")

d, pub = items["MEGALEX"]
compare("MEGALEX", "length", "nblettres (item file)", d["length"], num(pub["pub_nblettres"]), "same quantity")
compare("MEGALEX", "old20", "old20 (item file)", d["old20"], num(pub["pub_old20"]), "same quantity")
compare("MEGALEX", "old20_equal_lexicon", "old20 (item file)", d["old20_equal_lexicon"], num(pub["pub_old20"]), "same quantity")
for c in ["fb", "ff", "ft"]:
    compare("MEGALEX", "zipf", f"{c} (item file)", d["zipf"], num(pub["pub_" + c]), "other norm")

d, pub = items["ELP"]
compare("ELP", "zipf", "SUBTLEX-US Zipf (file)", d["zipf"], d["key"].map(subtlex["SUBTLEX-US Zipf (file)"]), "other norm")
compare("ELP", "zipf", "SUBTLEX-UK Zipf (file)", d["zipf"], d["key"].map(subtlex["SUBTLEX-UK Zipf (file)"]), "other norm")

pd.DataFrame(rows).to_csv(os.path.join(HERE, "results", "step1_recompute_vs_published.csv"), index=False)

# wordfreq coverage against the norms: unknown to wordfreq but present in the norm, and the reverse
cov = []
for fam, norm in [("ELP", "SUBTLEX-US Zipf (file)"), ("BLP", "SUBTLEX-UK Zipf (file)"), ("DLP", "SUBTLEX-NL Zipf (file)")]:
    d = items[fam][0]
    innorm = d["key"].isin(subtlex[norm].keys())
    cov.append(dict(megastudy=NAME[fam], norm=norm, n_words=len(d), n_in_norm=int(innorm.sum()),
                    n_wordfreq_unknown=int((d["zipf"] == 0).sum()),
                    n_wordfreq_unknown_but_in_norm=int(((d["zipf"] == 0) & innorm).sum()),
                    n_in_wordfreq_but_not_in_norm=int(((d["zipf"] > 0) & ~innorm).sum())))
pd.DataFrame(cov).to_csv(os.path.join(HERE, "results", "step1_frequency_coverage.csv"), index=False)

allitems = pd.concat([items[f][0] for f in LANG], ignore_index=True)
allitems.to_pickle(os.path.join(HERE, "cache", "items_measures.pkl"))
info = dict(wordfreq=wordfreq.__version__ if hasattr(wordfreq, "__version__") else "3.1.1",
            rapidfuzz=rapidfuzz.__version__, numpy=np.__version__, pandas=pd.__version__,
            seed_equal_lexicon=SEED_EQUAL_LEXICON, dlp_length=dlp_len, seconds=round(time.time() - t0, 1),
            finished=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
json.dump(info, open(os.path.join(HERE, "cache", "step1_info.json"), "w"), indent=1)
print(json.dumps(info, indent=1))
print(pd.DataFrame(counts).T.to_string())
print(pd.DataFrame(rows).drop(columns=["kind", "n_words"]).round(3).to_string())
print(pd.DataFrame(cov).to_string())
