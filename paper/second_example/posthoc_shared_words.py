"""Post hoc (not in PLAN.md; added after the sensitivity analysis showed that the British Lexicon Project's larger
frequency slope disappears when the words shared with the English Lexicon Project are dropped):
within-sample binomial slope of accuracy on Zipf frequency, by word set, for the two English megastudies.
The shared words are the same items in both samples, so a slope difference there is a difference between
samples and procedures, and a slope difference between word sets within one sample is a difference between items.
Point estimates with an item bootstrap (500 resamples, participants fixed).  Run: python3 posthoc_shared_words.py
"""
import os
import numpy as np, pandas as pd
from itemtransfer._fit import fit_logit, fit_logit_batch
import lexical_common as lc

trials, words = lc.load_megastudies()
sh = set(lc.shared_words(words))
rng = np.random.default_rng([lc.SEED, 13])
rows = []
for fam in ["ELP", "BLP"]:
    t = trials[trials["sample"] == fam]
    g = t.groupby("item", sort=True)["correct"].agg(["sum", "size"])
    w = words[words["megastudy"] == fam].set_index("item").loc[g.index]
    for label, mask in [("shared words", w.index.isin(sh)), ("words only in this megastudy", ~w.index.isin(sh)),
                        ("all words", np.ones(len(w), bool))]:
        n, s, z = g["size"].to_numpy(float)[mask], g["sum"].to_numpy(float)[mask], w["zipf"].to_numpy()[mask]
        X = np.column_stack([np.ones(mask.sum()), z])
        fit = fit_logit(X, n, s)
        W = rng.multinomial(len(n), np.full(len(n), 1 / len(n)), size=500).astype(float)
        b, _ = fit_logit_batch(X, np.tile(n, (500, 1)), np.tile(s, (500, 1)), W, n_indicator=1)
        rows.append(dict(sample=fam, word_set=label, n_words=int(mask.sum()), mean_accuracy=float(s.sum() / n.sum()),
                         zipf_mean=float(z.mean()), zipf_sd=float(z.std()), share_zipf_below_2=float((z < 2).mean()),
                         slope=fit.coef[1], slope_lo=np.percentile(b[:, 1], 2.5), slope_hi=np.percentile(b[:, 1], 97.5),
                         intercept=fit.coef[0],
                         spearman=float(pd.Series(z).corr(pd.Series(s / n), method="spearman"))))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(lc.RESULTS, "posthoc_frequency_slope_by_word_set.csv"), index=False)
print(out.round(3).to_string())
