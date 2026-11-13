"""Figures of the second worked example (greyscale-safe: families and models are distinguished by marker and
line style, not by colour; no in-figure titles). Writes PNG (300 dpi) and PDF to results/figures/ and the plotted
aggregates to results/figure1_binned_accuracy.csv.  Run:  python3 figures_lexical.py
"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import lexical_common as lc

FIG = os.path.join(lc.RESULTS, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "legend.frameon": False,
                     "pdf.fonttype": 42, "font.family": "DejaVu Sans"})
STYLE = {"ELP": dict(color="0.0", marker="o", ls="-", mfc="0.0"),
         "BLP": dict(color="0.0", marker="s", ls="--", mfc="white"),
         "DLP": dict(color="0.45", marker="^", ls="-", mfc="0.45"),
         "MEGALEX": dict(color="0.45", marker="D", ls=":", mfc="white")}
LABEL = {"ELP": "English Lexicon Project", "BLP": "British Lexicon Project", "DLP": "Dutch Lexicon Project",
         "MEGALEX": "MEGALEX"}
XLAB = {"zipf": "Word frequency (Zipf scale)", "length": "Word length (letters)",
        "old20": "Neighbourhood distance (OLD20)"}

# ------------------------------------------------------------------ Figure 1: accuracy against each measure by family
trials_all, words = lc.load_megastudies()
tf, items = lc.build(trials_all, words)
del trials_all
g = tf.groupby("item", sort=False)["correct"].agg(["sum", "size"])
items = items.join(g, on="item")
rows = []
for fam in lc.FAMILIES:
    d = items[items["family"] == fam]
    for m in lc.MEASURES:
        if m == "zipf":
            b = np.where(d[m] == 0, -1, np.floor(d[m] / 0.5)).astype(int)      # unknown words form their own bin
        elif m == "length":
            b = d[m].astype(int).to_numpy()
        else:
            b = np.floor(d[m] / 0.25 + 1e-9).astype(int)
        for k in np.unique(b):
            x = d[b == k]
            rows.append(dict(family=fam, measure=m, bin=int(k), measure_mean=float(x[m].mean()), n_words=len(x),
                             accuracy=float(x["sum"].sum() / x["size"].sum()),
                             logit_accuracy=float(np.log(x["sum"].sum() / (x["size"].sum() - x["sum"].sum())))
                             if 0 < x["sum"].sum() < x["size"].sum() else np.nan))
binned = pd.DataFrame(rows)
binned.to_csv(os.path.join(lc.RESULTS, "figure1_binned_accuracy.csv"), index=False)
MIN_WORDS = 30
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
for ax, m in zip(axes, lc.MEASURES):
    for fam in lc.FAMILIES:
        d = binned[(binned["family"] == fam) & (binned["measure"] == m) & (binned["n_words"] >= MIN_WORDS)]
        st = STYLE[fam]
        ax.plot(d["measure_mean"], d["accuracy"], ls=st["ls"], color=st["color"], marker=st["marker"], ms=3.6,
                mfc=st["mfc"], mec=st["color"], mew=0.8, lw=1.1, label=LABEL[fam])
    ax.set_xlabel(XLAB[m])
    ax.set_ylim(0.2, 1.0)
    ax.grid(axis="y", color="0.9", lw=0.5)
axes[0].set_ylabel("Proportion of correct responses")
axes[2].legend(loc="lower right", fontsize=6.5, handlelength=3.2)
fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(FIG, f"figure_lexical_accuracy_by_measure.{ext}"), dpi=300)
plt.close(fig)

# ------------------------------------------------------------------ Figure 2: the three transfer criteria
tab = pd.read_csv(os.path.join(lc.RESULTS, "step3_transfer.csv"))
# ordering: estimate +/- 1.96 bootstrap standard deviations. The resampled ordering correlations lie below the
# estimate (resampled participants add noise to word accuracies), so the percentile interval excludes the estimate
# in half of the rows; both percentile and basic intervals are in results/step3_interval_check.csv.
bt = pd.read_csv(os.path.join(lc.RESULTS, "step3_bootstrap.csv"))
sd = bt.groupby(["family", "model"])["ordering"].std(ddof=1)
for i, r in tab.iterrows():
    tab.at[i, "ordering_lo"] = r["ordering"] - 1.96 * sd.at[(r["family"], r["model"])]
    tab.at[i, "ordering_hi"] = r["ordering"] + 1.96 * sd.at[(r["family"], r["model"])]
rel = pd.read_csv(os.path.join(lc.RESULTS, "step2_reliability.csv"))
rel = rel[rel["word_set"].str.startswith("family")].set_index("sample")
MODELS = ["zipf", "length", "old20", "combined"]
MST = {"zipf": dict(marker="o", mfc="0.0"), "length": dict(marker="s", mfc="white"),
       "old20": dict(marker="^", mfc="0.6"), "combined": dict(marker="D", mfc="0.0")}
MLAB = {"zipf": "Frequency", "length": "Length", "old20": "OLD20", "combined": "All three measures"}
PANELS = [("ordering", "Ordering (Spearman correlation)", None, (-0.15, 1.0)),
          ("calibration_slope", "Calibration slope", 1.0, (-1.6, 3.6)),
          ("logloss_reduction", "Reduction in log loss", None, (-0.02, 0.2))]
fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.1))
off = {"zipf": -0.27, "length": -0.09, "old20": 0.09, "combined": 0.27}
clipped = []
for ax, (st, ylab, ref, ylim) in zip(axes, PANELS):
    ax.axhline(0, color="0.6", lw=0.6)
    if ref is not None:
        ax.axhline(ref, color="0.0", lw=0.6, ls="--")
    for j, fam in enumerate(lc.FAMILIES):
        for m in MODELS:
            r = tab[(tab["family"] == fam) & (tab["model"] == m)].iloc[0]
            x = j + off[m]
            lo, hi, v = r[st + "_lo"], r[st + "_hi"], r[st]
            inside = ylim[0] <= v <= ylim[1]
            ax.plot([x, x], [max(lo, ylim[0]), min(hi, ylim[1])], color="0.0", lw=0.8)
            if inside:
                ax.plot([x], [v], ls="none", marker=MST[m]["marker"], mfc=MST[m]["mfc"], mec="0.0", mew=0.8, ms=4.2,
                        label=MLAB[m] if j == 0 else None)
            if lo < ylim[0] or hi > ylim[1] or not inside:
                clipped.append((st, fam, m, round(v, 2), round(lo, 2), round(hi, 2)))
                if hi > ylim[1]:
                    ax.plot([x], [ylim[1]], ls="none", marker=(3, 0, 0), color="0.0", ms=3.5, clip_on=False)
                if lo < ylim[0]:
                    ax.plot([x], [ylim[0]], ls="none", marker=(3, 0, 180), color="0.0", ms=3.5, clip_on=False)
        if st == "ordering":
            c = np.sqrt(rel.at[fam, "spearman_sb"])
            ax.plot([j - 0.4, j + 0.4], [c, c], color="0.0", lw=1.0, ls=":")
    ax.set_xticks(range(4))
    ax.set_xticklabels(["ELP", "BLP", "DLP", "MEGALEX"], fontsize=7)
    ax.set_xlabel("Held-out family")
    ax.set_ylabel(ylab)
    ax.set_ylim(*ylim)
    ax.grid(axis="y", color="0.92", lw=0.5)
h, l = axes[2].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, fontsize=7, handletextpad=0.3, columnspacing=2.0)
fig.tight_layout(rect=(0, 0.07, 1, 1))
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(FIG, f"figure_lexical_transfer.{ext}"), dpi=300)
plt.close(fig)
pd.DataFrame(clipped, columns=["statistic", "family", "model", "estimate", "lo", "hi"]).to_csv(
    os.path.join(lc.RESULTS, "figure2_values_outside_axis.csv"), index=False)
print(pd.DataFrame(clipped))
