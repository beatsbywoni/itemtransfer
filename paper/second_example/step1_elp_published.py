"""Step 1, English Lexicon Project: compare the recomputed measures and word accuracy with the item-level values
published on elexicon.wustl.edu (original/elp/elexicon_items.csv, obtained 2026-11-13; see PROVENANCE.md).
The published values are used for this comparison only; no measure of the transfer analysis depends on them.
Appends rows to results/step1_recompute_vs_published.csv and writes results/step1_elp_accuracy_vs_published.csv.
Run after prep_measures.py:  python3 -I step1_elp_published.py   (the file is treated as untrusted data)
"""
import hashlib, json, os, sys, unicodedata
import numpy as np, pandas as pd
from scipy.stats import pearsonr, spearmanr
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "original", "elp", "elexicon_items.csv")
assert hashlib.sha256(open(P, "rb").read()).hexdigest() == "6d9825d242a740c8373e273393020d964103231550b28804cac27fe448135020"
pub = pd.read_csv(P, dtype=str, keep_default_na=False)
n_rows = len(pub)
for c in pub.columns[1:]:
    pub[c] = pd.to_numeric(pub[c].str.replace(",", "").replace("#", np.nan), errors="coerce")
pub["key"] = pub["Word"].map(lambda s: unicodedata.normalize("NFC", s).lower())
dupkeys = int(pub["key"].duplicated().sum())
words = pd.read_pickle(os.path.join(HERE, "cache", "items_measures.pkl"))
d = words[words["megastudy"] == "ELP"].copy()
exact = d.merge(pub.drop(columns=["key"]), how="left", left_on="string", right_on="Word")
n_exact = int(exact["Word"].notna().sum())
tr = pd.read_pickle(os.path.join(HERE, "cache", "trials_ELP.pkl"))
acc = tr.groupby("item", observed=True)["correct"].agg(["mean", "size"])
exact["acc"] = exact["string"].map(acc["mean"]); exact["n_resp"] = exact["string"].map(acc["size"])
NAME = "English Lexicon Project"
rows = []
def compare(measure, label, mine, theirs, kind):
    mine, theirs = np.asarray(mine, float), np.asarray(theirs, float)
    ok = np.isfinite(mine) & np.isfinite(theirs); a, b = mine[ok], theirs[ok]; diff = a - b
    same = kind == "same quantity"
    rows.append(dict(megastudy=NAME, measure=measure, published=label, kind=kind, n_words=len(mine),
        n_compared=int(ok.sum()), n_published_missing=int((~np.isfinite(theirs)).sum()),
        pearson=float(pearsonr(a, b)[0]), spearman=float(spearmanr(a, b)[0]),
        n_equal=int((np.abs(diff) < 1e-9).sum()) if same else np.nan,
        share_equal=float((np.abs(diff) < 1e-9).mean()) if same else np.nan,
        n_within_0_05=int((np.abs(diff) <= 0.05 + 1e-9).sum()) if same else np.nan,
        mean_difference=float(diff.mean()) if same else np.nan,
        max_abs_difference=float(np.abs(diff).max()) if same else np.nan))
    return ok, diff
compare("length", "Length (elexicon item file)", exact["length"], exact["Length"], "same quantity")
compare("length", "Length against number of characters", exact["n_char"], exact["Length"], "same quantity")
compare("old20", "OLD (elexicon item file)", exact["old20"], exact["OLD"], "same quantity")
compare("old20_equal_lexicon", "OLD (elexicon item file)", exact["old20_equal_lexicon"], exact["OLD"], "same quantity")
compare("zipf", "Log_Freq_HAL (elexicon item file)", exact["zipf"], exact["Log_Freq_HAL"], "other norm")
compare("zipf", "LgSUBTLWF (elexicon item file)", exact["zipf"], exact["LgSUBTLWF"], "other norm")
path = os.path.join(HERE, "results", "step1_recompute_vs_published.csv")
old = pd.read_csv(path)
old = old[~old["published"].str.contains("elexicon|Length against")]
pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(path, index=False)
ok = exact["I_Mean_Accuracy"].notna() & exact["acc"].notna()
a, b = exact.loc[ok, "acc"].to_numpy(), exact.loc[ok, "I_Mean_Accuracy"].to_numpy()
accrow = dict(megastudy=NAME, n_words=len(exact), n_matched_exact_string=n_exact, n_compared=int(ok.sum()),
              pearson=float(pearsonr(a, b)[0]), spearman=float(spearmanr(a, b)[0]),
              share_within_0_005=float((np.abs(a - b) <= 0.005 + 1e-12).mean()),
              share_within_0_05=float((np.abs(a - b) <= 0.05).mean()), mean_difference=float((a - b).mean()),
              max_abs_difference=float(np.abs(a - b).max()),
              median_responses_recomputed=float(exact.loc[ok, "n_resp"].median()),
              median_obs_published=float(exact.loc[ok, "Obs"].median()),
              note="published accuracy is rounded to two decimals; Obs is the number of observations the website "
                   "reports, which is lower than the number of raw responses")
pd.DataFrame([accrow]).to_csv(os.path.join(HERE, "results", "step1_elp_accuracy_vs_published.csv"), index=False)
info = dict(rows_in_file=n_rows, duplicate_lowercase_keys_in_file=dupkeys, elp_words=len(d), matched_exact=n_exact,
            length_differs_words_with_apostrophe=int(((exact["length"] != exact["Length"]) & exact["string"].str.contains("'")).sum()),
            length_differs_total=int((exact["length"] != exact["Length"]).sum()),
            old_missing=int(exact["OLD"].isna().sum()))
json.dump(info, open(os.path.join(HERE, "cache", "step1_elp_info.json"), "w"), indent=1)
print(info); print(pd.DataFrame(rows).drop(columns=["kind","megastudy"]).round(3).to_string()); print(accrow)
