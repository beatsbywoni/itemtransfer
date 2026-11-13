"""Figures of the simulation study (300 dpi PNG and PDF, greyscale-safe, no titles inside the figures).

Captions are in figures/captions.md. Every number plotted comes from results/*_summary.csv or results/raw/.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from simcore import FIGURES, RESULTS, collect  # noqa: E402

plt.rcParams.update({"font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 4.5, "pdf.fonttype": 42,
                     "font.family": "DejaVu Sans", "legend.frameon": False})
K, G1, G2 = "#000000", "#555555", "#999999"   # identity is always carried by marker and line style as well
STY = {"two-way": dict(color=K, marker="o", ls="-", mfc=K),
       "participants only": dict(color=G1, marker="s", ls="--", mfc="white"),
       "items only": dict(color=G2, marker="^", ls=":", mfc=G2)}
CRIT = {"scale": dict(color=K, marker="o", ls="-", mfc=K),
        "prediction": dict(color=G1, marker="s", ls="--", mfc="white"),
        "ordering": dict(color=G2, marker="^", ls=":", mfc=G2)}


def save(fig, name):
    fig.savefig(FIGURES / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def tag(ax, letter):
    ax.text(-0.13, 1.04, letter, transform=ax.transAxes, fontweight="bold", fontsize=9, ha="right", va="bottom")


def interval_plot(ax, pos, q05, med, q95, target=None, clip=None, **kw):
    """Median with 5th to 95th percentile of the replications; open diamond = large-sample target."""
    for p, a, m, b in zip(pos, q05, med, q95):
        lo, hi = (a, b) if clip is None else (max(a, clip[0]), min(b, clip[1]))
        ax.plot([p, p], [lo, hi], color=K, lw=1.0, solid_capstyle="butt")
        if clip is not None:
            if a < clip[0]:
                ax.plot(p, clip[0], marker="v", color=K, ms=4)
            if b > clip[1]:
                ax.plot(p, clip[1], marker="^", color=K, ms=4)
        if clip is None or clip[0] <= m <= clip[1]:
            ax.plot(p, m, "o", color=K, ms=4.5)
    if target is not None:
        ok = np.isfinite(target)
        ax.plot(np.asarray(pos)[ok] + 0.28, np.asarray(target)[ok], "D", mfc="white", mec=G1, ms=4)


# ---------------------------------------------------------------------------------------------- figure 1 (S1)
def figure1():
    raw = collect("sim01")
    summ = pd.read_csv(RESULTS / "sim01_summary.csv").set_index(["cell", "measure"])
    conds = [("common", "x", "same slope"), ("ratio_2", "x", "slope x 2"), ("ratio_0.5", "x", "slope x 0.5"),
             ("ratio_0.25", "x", "slope x 0.25"), ("ratio_0", "x", "slope 0"), ("ratio_-1", "x", "slope reversed"),
             ("common", "x_null", "null measure"), ("common", "proxy_both", "proxy, everywhere"),
             ("common", "proxy_train", "proxy, training only"), ("common", "proxy_heldout", "proxy, held-out only")]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 7.0))
    pos = np.arange(len(conds))
    panels = [("ordering", "Ordering (Spearman correlation)", None),
              ("calibration_slope", "Scale (calibration slope)", (-1.6, 3.2)),
              ("logloss_reduction", "Prediction (log-loss reduction)", None)]
    for ax, (st, ylab, clip), letter in zip(axes.flat[:3], panels, "ABC"):
        q = [np.nanpercentile(raw[(raw["cell"] == c) & (raw["measure"] == m)][st], [5, 50, 95]) for c, m, _ in conds]
        tg = [summ.at[(c, m), "target_" + st] for c, m, _ in conds]
        interval_plot(ax, pos, [a[0] for a in q], [a[1] for a in q], [a[2] for a in q], target=np.array(tg), clip=clip)
        ax.axhline(0, color=G2, lw=0.6, zorder=0)
        if st == "calibration_slope":
            ax.axhline(1, color=G2, lw=0.6, ls="--", zorder=0)
            ax.set_ylim(clip[0] - 0.15, clip[1] + 0.15)
        ax.set_xticks(pos)
        ax.set_xticklabels([c[2] for c in conds], fontsize=6.5, rotation=45, ha="right", rotation_mode="anchor")
        ax.axvline(5.5, color=G2, lw=0.5, ls=":")
        ax.set_ylabel(ylab)
        tag(ax, letter)
    # D: weak training relation
    ax = axes[1, 1]
    cells = [("weak_0", "0"), ("weak_0.05", "0.05"), ("weak_0.125", "0.125"), ("weak_0.25", "0.25"), ("common", "0.5")]
    clip = (-12, 22)
    for j, (c, lab) in enumerate(cells):
        g = raw[(raw["cell"] == c) & (raw["measure"] == "x")]
        weak = (g["train_slope_lo"] <= 0) & (g["train_slope_hi"] >= 0)
        for off, sub, mfc in ((-0.17, g[weak], "white"), (0.17, g[~weak], K)):
            if len(sub) < 20:
                continue
            a, m, b = np.percentile(sub["calibration_slope"], [5, 50, 95])
            ax.plot([j + off] * 2, [max(a, clip[0]), min(b, clip[1])], color=K, lw=1.0)
            if a < clip[0]:
                ax.plot(j + off, clip[0], marker="v", color=K, ms=4)
            if b > clip[1]:
                ax.plot(j + off, clip[1], marker="^", color=K, ms=4)
            ax.plot(j + off, m, "o", mfc=mfc, mec=K, ms=4.5)
        ax.text(j, clip[1] + 2.2, f"{100 * weak.mean():.0f}%", ha="center", fontsize=6.5)
        t = summ.at[(c, "x"), "target_calibration_slope"]
        if np.isfinite(t) and t < clip[1]:
            ax.plot(j + 0.38, t, "D", mfc="white", mec=G1, ms=4)
    ax.plot([], [], "o", mfc="white", mec=K, label="flagged as weak training relation")
    ax.plot([], [], "o", mfc=K, mec=K, label="not flagged")
    ax.plot([], [], "D", mfc="white", mec=G1, label="large-sample value")
    ax.legend(loc="lower right", fontsize=6)
    ax.axhline(0, color=G2, lw=0.6, zorder=0)
    ax.axhline(1, color=G2, lw=0.6, ls="--", zorder=0)
    ax.set_ylim(clip[0] - 1, clip[1] + 5)
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels([c[1] for c in cells])
    ax.set_xlabel("True slope in the training families\n(logits per SD; held-out family: 0.5)")
    ax.set_ylabel("Scale (calibration slope)")
    tag(ax, "D")
    fig.tight_layout()
    save(fig, "fig1_separation")


# ---------------------------------------------------------------------------------------------- figure 2 (S2)
def figure2():
    s = pd.read_csv(RESULTS / "sim02_summary.csv")
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.2))
    # A: ordering of the measure and of the level indicator
    a = s[(s["part"] == "a") & (s["size"] == "base")].set_index(["truth", "heldout_measure"])
    kinds = [("continuous", "continuous\n(median split)"), ("four_levels", "four levels"), ("two_levels", "two levels")]
    ax = axes[0, 0]
    for i, (truth, mk) in enumerate((("graded", "o"), ("step", "s"))):
        for j, (kind, _) in enumerate(kinds):
            r = a.loc[(truth, kind)]
            x0 = j + (i - 0.5) * 0.42
            ax.errorbar(x0 - 0.1, r["ordering_mean"], yerr=1.96 * r["ordering_mcse"], fmt=mk, color=K, mfc=K, capsize=0)
            ax.errorbar(x0, r["lev_ordering_levels_mean"], yerr=1.96 * r["lev_ordering_levels_mcse"], fmt=mk,
                        color=G1, mfc="white", capsize=0)
            ax.errorbar(x0 + 0.1, r["lev_ordering_within_mean"], yerr=1.96 * r["lev_ordering_within_mcse"], fmt=mk,
                        color=G2, mfc=G2, ms=3.5, capsize=0)
    ax.plot([], [], "o", color=K, label="measure")
    ax.plot([], [], "o", color=G1, mfc="white", label="level indicator")
    ax.plot([], [], "o", color=G2, ms=3.5, label="measure within levels")
    ax.plot([], [], " ", label="circles: graded relation")
    ax.plot([], [], " ", label="squares: step relation")
    ax.legend(loc="lower center", fontsize=5.6, bbox_to_anchor=(0.5, 1.0), ncol=3, columnspacing=0.8, handletextpad=0.3)
    ax.axhline(0, color=G2, lw=0.6, zorder=0)
    ax.set_xticks(range(3))
    ax.set_xticklabels([k[1] for k in kinds])
    ax.set_xlabel("Measure in the held-out family")
    ax.set_ylabel("Ordering (Spearman correlation)")
    tag(ax, "A")
    # B: log-loss reduction, level indicator minus measure
    ax = axes[0, 1]
    al = s[s["part"] == "a"].set_index(["truth", "heldout_measure", "size"])
    for i, (truth, mk) in enumerate((("graded", "o"), ("step", "s"))):
        for k, (size, mfc) in enumerate((("base", K), ("large", "white"))):
            y = [al.loc[(truth, kind, size), "lev_logloss_diff_mean"] for kind, _ in kinds]
            e = [1.96 * al.loc[(truth, kind, size), "lev_logloss_diff_mcse"] for kind, _ in kinds]
            ax.errorbar(np.arange(3) + (i - 0.5) * 0.36 + (k - 0.5) * 0.12, y, yerr=e, fmt=mk, color=K, mfc=mfc, capsize=0,
                        label=f"{truth} relation, {'48 items, 40 participants' if size == 'base' else '96 items, 80 participants'}")
    ax.axhline(0, color=G2, lw=0.6, zorder=0)
    ax.legend(loc="lower right", fontsize=5.8)
    ax.set_xticks(range(3))
    ax.set_xticklabels([k[1] for k in kinds])
    ax.set_xlabel("Measure in the held-out family")
    ax.set_ylabel("Log-loss reduction:\nlevel indicator minus measure")
    tag(ax, "B")
    # C: range mismatch
    ax = axes[1, 0]
    b = s[s["part"] == "b"].set_index(["relation", "heldout_range", "measure"])
    groups = [(rel, rng) for rel in ("linear", "log", "saturating") for rng in ("same", "shifted", "wider")]
    styles = {"x": dict(marker="o", color=K, mfc=K, label="measure as given"),
              "common_range_x": dict(marker="s", color=G1, mfc="white", label="common range"),
              "log_x": dict(marker="^", color=G2, mfc=G2, label="logarithm of the measure")}
    clip = (-0.2, 2.6)
    for j, (rel, rng) in enumerate(groups):
        for off, m in ((-0.25, "x"), (0.0, "common_range_x"), (0.25, "log_x")):
            if (rel, rng, m) not in b.index:
                continue
            r = b.loc[(rel, rng, m)]
            st = styles[m]
            lo, hi = max(r["calibration_slope_q05"], clip[0]), min(r["calibration_slope_q95"], clip[1])
            ax.plot([j + off] * 2, [lo, hi], color=st["color"], lw=0.9)
            if r["calibration_slope_q95"] > clip[1]:
                ax.plot(j + off, clip[1], marker="^", color=st["color"], ms=3)
            if r["calibration_slope_q05"] < clip[0]:
                ax.plot(j + off, clip[0], marker="v", color=st["color"], ms=3)
            ax.plot(j + off, r["target_calibration_slope"], ls="", marker=st["marker"], color=st["color"], mfc=st["mfc"])
    for st in styles.values():
        ax.plot([], [], ls="", **st)
    ax.legend(loc="lower center", fontsize=5.8, ncol=3, columnspacing=0.6, handletextpad=0.1, bbox_to_anchor=(0.5, 1.0))
    ax.axhline(1, color=G2, lw=0.6, ls="--", zorder=0)
    for v in (2.5, 5.5):
        ax.axvline(v, color=G2, lw=0.5, ls=":")
    ax.set_ylim(clip[0] - 0.1, clip[1] + 0.15)
    ax.set_xticks(range(9))
    ax.set_xticklabels([g[1] for g in groups], fontsize=6)
    for k, rel in enumerate(("linear", "logarithmic", "saturating")):
        ax.text(1 + 3 * k, -0.17, rel, ha="center", fontsize=7, transform=ax.get_xaxis_transform())
    ax.set_xlabel("Range of the measure in the held-out family, by true relation", labelpad=16)
    ax.set_ylabel("Scale (calibration slope)")
    tag(ax, "C")
    # D: reliability
    ax = axes[1, 1]
    c = s[s["part"] == "c"]
    for isd, ls_, mk in ((0.0, "-", "o"), (0.5, "--", "s"), (1.0, ":", "^")):
        g = c[c["item_sd"] == isd].sort_values("n_part")
        xx = np.arange(len(g))
        ax.plot(xx, g["ordering_mean"], ls=ls_, marker=mk, color=K, mfc=K)
        ax.plot(xx, g["corrected_rank_mean"], ls=ls_, marker=mk, color=G1, mfc="white")
        ax.plot(xx, g["noise_free_mean"], ls="", marker="_", color=G2, ms=12, mew=2)
    ax.plot([], [], "-o", color=K, label="observed")
    ax.plot([], [], "-o", color=G1, mfc="white", label="observed / square root of reliability")
    ax.plot([], [], ls="", marker="_", color=G2, ms=12, mew=2, label="without response noise")
    ax.plot([], [], " ", label="item residual SD: 0 (solid), 0.5 (dashed), 1 (dotted)")
    ax.legend(loc="lower right", fontsize=5.8)
    ax.set_xticks(range(4))
    ax.set_xticklabels(["10", "20", "40", "80"])
    ax.set_ylim(0, 1.2)
    ax.set_xlabel("Participants per sample (trials per item)")
    ax.set_ylabel("Ordering (Spearman correlation)")
    tag(ax, "D")
    fig.tight_layout()
    save(fig, "fig2_design_features")


# ---------------------------------------------------------------------------------------------- figure 3 (S3)
FACTORS = [("n_fam", "Item families"), ("n_items", "Items\nper family"), ("n_part", "Participants\nper sample"),
           ("slope", "True slope\n(logits per SD)"), ("item_sd", "Item residual SD\n(logits)"),
           ("part_sd", "Participant SD\n(logits)")]


def _ofat(s, factor, measure):
    g = s[(s["measure"] == measure) & ((s["cell"] == "base") | s["cell"].str.startswith(f"ofat_{factor}_"))]
    return g.sort_values(factor)


def figure3():
    s = pd.read_csv(RESULTS / "sim03_summary.csv")
    fig, axes = plt.subplots(3, 6, figsize=(7.4, 6.0), sharey="row")
    for j, (factor, label) in enumerate(FACTORS):
        g, n = _ofat(s, factor, "x"), _ofat(s, factor, "x_null")
        xx = np.arange(len(g))
        ax = axes[0, j]
        for name, col in (("scale", "cal_excl0"), ("prediction", "ll_pos"), ("ordering", "ord_pos")):
            ax.plot(xx, g[col], label=name, **CRIT[name])
        ax.set_ylim(-0.03, 1.03)
        ax = axes[1, j]
        ax.plot(xx, g["cal_coverage"], label="scale", **CRIT["scale"])
        ax.plot(xx, g["ll_coverage"], label="prediction", **CRIT["prediction"])
        ax.plot(xx, g["ord_coverage_expect"], label="ordering", **CRIT["ordering"])
        ax.axhline(0.95, color=G2, lw=0.6, ls="--", zorder=0)
        ax.set_ylim(0.88, 1.005)
        ax = axes[2, j]
        ax.plot(xx, g["cal_width_median"], label="median width of the interval", **CRIT["scale"])
        ax.plot(xx, g["cal_width_nominal"], label="width that the spread of the estimates justifies", color=G1, marker="x",
                ls="--")
        ax.set_yscale("log")
        ax.set_yticks([0.5, 1, 2, 3])
        ax.set_yticklabels(["0.5", "1", "2", "3"])
        ax.minorticks_off()
        ax.set_xticks(xx)
        ax.set_xticklabels([f"{v:g}" for v in g[factor]])
        ax.set_xlabel(label, fontsize=6.5)
        for r in range(2):
            axes[r, j].set_xticks(xx)
            axes[r, j].set_xticklabels([])
    axes[0, 0].set_ylabel("Detection rate\n(interval excludes 0)")
    axes[1, 0].set_ylabel("Coverage of the\n95% interval")
    axes[2, 0].set_ylabel("Width of the interval\nof the calibration slope")
    axes[0, 5].legend(loc="lower right", fontsize=5.5, handlelength=2.5)
    for ax, letter in zip(axes[:, 0], "ABC"):
        tag(ax, letter)
    fig.tight_layout(w_pad=0.3, rect=(0, 0.04, 1, 1))
    h, l = axes[2, 5].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=6.5, title="Panel C", title_fontsize=6.5)
    save(fig, "fig3_operating_characteristics")


def figure4():
    s = pd.read_csv(RESULTS / "sim03_summary.csv")
    x = s[s["measure"] == "x"].set_index("cell")
    n = s[s["measure"] == "x_null"].set_index("cell")
    cells = ["ofat_item_sd_0", "base", "ofat_item_sd_1", "fact_i24_b0.25_sd0", "fact_i24_b0.25_sd1", "fact_i24_b1_sd0",
             "fact_i24_b1_sd1", "fact_i96_b0.25_sd0", "fact_i96_b0.25_sd1", "fact_i96_b1_sd0", "fact_i96_b1_sd1",
             "small_f3_i24_p20_sd1"]
    labels = ["48 / 0.5 / 0", "48 / 0.5 / 0.5", "48 / 0.5 / 1", "24 / 0.25 / 0", "24 / 0.25 / 1", "24 / 1 / 0", "24 / 1 / 1",
              "96 / 0.25 / 0", "96 / 0.25 / 1", "96 / 1 / 0", "96 / 1 / 1", "small design"]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0), sharex=True)
    pos = np.arange(len(cells))
    panels = [(axes[0, 0], x, "cal_coverage", "Coverage, calibration slope", 0.95),
              (axes[0, 1], x, "ll_coverage", "Coverage, log-loss reduction", 0.95),
              (axes[1, 0], n, "cal_excl0", "False-positive rate, null measure\n(calibration-slope interval excludes 0)", 0.05),
              (axes[1, 1], n, "ll_pos", "False-positive rate, null measure\n(log-loss interval above 0)", 0.025)]
    for (ax, tab, col, ylab, ref), letter in zip(panels, "ABCD"):
        for off, (name, suffix) in zip((-0.22, 0, 0.22), (("two-way", ""), ("participants only", "_po"), ("items only", "_io"))):
            y = tab.loc[cells, col + suffix].to_numpy()
            mc = col.replace("cal_excl0", "cal_excl0_mcse").replace("ll_pos", "ll_pos_mcse") if "coverage" not in col else col + "_mcse"
            mc = (mc + suffix) if "coverage" not in col else (col + "_mcse" + suffix)
            e = 1.96 * tab.loc[cells, mc].to_numpy()
            st = STY[name]
            ax.errorbar(pos + off, y, yerr=e, fmt=st["marker"], color=st["color"], mfc=st["mfc"], capsize=0, label=name, ms=4)
        ax.axhline(ref, color=G2, lw=0.6, ls="--", zorder=0)
        for v in (2.5, 10.5):
            ax.axvline(v, color=G2, lw=0.5, ls=":")
        ax.set_ylabel(ylab)
        tag(ax, letter)
    h, l = axes[0, 0].get_legend_handles_labels()
    for ax in axes[1]:
        ax.set_xticks(pos)
        ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=6)
        ax.set_xlabel("Items per family / true slope / item residual SD")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.legend(h, l, loc="upper center", ncol=3, fontsize=7, title="Units resampled", title_fontsize=7)
    save(fig, "fig4_bootstrap_comparison")


# ---------------------------------------------------------------------------------------------- figure 5 (S4)
def figure5():
    s = pd.read_csv(RESULTS / "sim04_summary.csv").set_index("cell")
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4))
    axes = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]
    axes[3].axis("off")
    rules = [("fit_pooled", "within-family fit, common slope", dict(color=K, marker="o", ls="-", mfc=K)),
             ("fit_separate", "within-family fit, separate slopes", dict(color=G1, marker="s", ls="--", mfc="white")),
             ("transfer_logloss", "transfer among training families", dict(color=G2, marker="^", ls=":", mfc=G2))]
    # A: random validity, by tau and mean validities
    ax = axes[0]
    taus = [0, 0.15, 0.3, 0.5]
    for (ma, mb), st in zip(((0.6, 0.6), (0.65, 0.55), (0.7, 0.5)),
                            (dict(color=G2, marker="^", ls=":", mfc=G2), dict(color=G1, marker="s", ls="--", mfc="white"),
                             dict(color=K, marker="o", ls="-", mfc=K))):
        cells = [f"random_{ma:g}_{mb:g}_tau{t:g}" for t in taus]
        ax.errorbar(range(4), s.loc[cells, "disagree_fit_pooled_vs_logloss"],
                    yerr=1.96 * s.loc[cells, "disagree_fit_pooled_vs_logloss_mcse"], capsize=0,
                    label=f"mean validity {ma:.2f} and {mb:.2f}".replace("0.", "."), **st)
    ax.set_xticks(range(4))
    ax.set_xticklabels(["0", "0.15", "0.3", "0.5"])
    ax.set_xlabel("Between-family SD of validity (Fisher z)")
    ax.set_ylabel("Rate at which the measure that fits better\nwithin the training families transfers worse")
    ax.set_ylim(0, 0.62)
    ax.axhline(0.5, color=G2, lw=0.6, ls="--", zorder=0)
    ax.legend(loc="lower right", fontsize=6.5)
    tag(ax, "A")
    # B: fixed validities
    ax = axes[1]
    cells = ["proxy_0.9_0.9", "proxy_0.9_0", "fixed_0.8_0.8", "fixed_0.7_0.5", "fixed_0.8_0.5", "fixed_0.8_0.3", "fixed_0.8_0"]
    labels = ["1 vs .9/.9", "1 vs .9/0", ".6 vs .8/.8", ".6 vs .7/.5", ".6 vs .8/.5", ".6 vs .8/.3", ".6 vs .8/0"]
    pos = np.arange(len(cells))
    for off, (out, st) in zip((-0.12, 0.12), (("ordering", dict(marker="^", color=G1, mfc="white")),
                                             ("logloss", dict(marker="o", color=K, mfc=K)))):
        ax.errorbar(pos + off, s.loc[cells, f"disagree_fit_pooled_vs_{out}"],
                    yerr=1.96 * s.loc[cells, f"disagree_fit_pooled_vs_{out}_mcse"], fmt=st["marker"], color=st["color"],
                    mfc=st["mfc"], capsize=0, label="transfer judged by " + ("ordering" if out == "ordering" else "log loss"))
    ax.set_xticks(pos)
    ax.set_xticklabels(labels, rotation=45, ha="right", rotation_mode="anchor", fontsize=6.5)
    ax.set_xlabel("Validity of A vs validity of B (training / held-out)")
    ax.set_ylabel("Rate at which the measure that fits better\nwithin the training families transfers worse")
    ax.set_ylim(-0.02, 1.02)
    ax.axhline(0.5, color=G2, lw=0.6, ls="--", zorder=0)
    ax.axvline(1.5, color=G2, lw=0.5, ls=":")
    ax.legend(loc="lower right", fontsize=6.5)
    tag(ax, "B")
    # C: selection rules, mean log-loss reduction of the selected measure
    ax = axes[2]
    cells = ["random_0.65_0.55_tau0", "random_0.65_0.55_tau0.3", "random_0.65_0.55_tau0.5", "fixed_0.7_0.5", "scale_0.35",
             "scale_0.7"]
    labels = ["validity\nSD 0", "validity\nSD 0.3", "validity\nSD 0.5", ".6 vs\n.7/.5", "unit\nSD 0.35", "unit\nSD 0.7"]
    pos = np.arange(len(cells))
    for off, (rule, lab, st) in zip((-0.22, 0, 0.22), rules):
        ax.errorbar(pos + off, s.loc[cells, f"selected_{rule}_vs_logloss_mean"],
                    yerr=1.96 * s.loc[cells, f"selected_{rule}_vs_logloss_mcse"], fmt=st["marker"], color=st["color"],
                    mfc=st["mfc"], capsize=0, label=lab)
    best = np.maximum(s.loc[cells, "logloss_a_mean"], s.loc[cells, "logloss_b_mean"])
    ax.plot(pos, best, ls="", marker="_", color=K, ms=16, mew=1.2, label="better measure on average")
    ax.axhline(0, color=G2, lw=0.6, zorder=0)
    ax.set_xticks(pos)
    ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylim(0, None)
    ax.set_ylabel("Log-loss reduction in the held-out family\nof the selected measure")
    h, l = ax.get_legend_handles_labels()
    axes[3].legend(h, l, loc="center left", fontsize=7, title="Panel C: measure selected by", title_fontsize=7)
    tag(ax, "C")
    fig.tight_layout()
    save(fig, "fig5_ranking")


# ---------------------------------------------------------------------------------------------- figure 6 (S8)
def figure6():
    s = pd.read_csv(RESULTS / "sim08_summary.csv")
    s = s[s["arm"] == "held-out"]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.9), sharey=True)
    for ax, ni, letter in zip(axes, (48, 192, 768), "ABC"):
        g = s[s["n_items"] == ni].sort_values("factor")
        xx = np.arange(len(g))
        for key, lab, col, mk in (("two_way_95", "two-way 95%", K, "o"), ("items_only_95", "items-only 95%", G2, "^")):
            ax.plot(xx, g[f"within_{key}"], color=col, marker=mk, ls="-", mfc=col, label=f"within tolerance, {lab}")
            ax.plot(xx, g[f"outside_{key}"], color=col, marker=mk, ls="--", mfc="white", label=f"outside tolerance, {lab}")
        for v in (1, 5):
            ax.axvline(v, color=G2, lw=0.5, ls=":")
        ax.axhline(0.025, color=G2, lw=0.6, ls="--", zorder=0)
        ax.set_xticks(xx)
        ax.set_xticklabels([f"{v:g}" for v in g["factor"]], fontsize=6.5)
        ax.set_xlabel(f"True calibration slope\n({ni} held-out items)")
        ax.set_ylim(-0.03, 1.03)
        tag(ax, letter)
    axes[0].set_ylabel("Share of data sets")
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, fontsize=6.5)
    save(fig, "fig6_tolerance_rule")


if __name__ == "__main__":
    FIGURES.mkdir(exist_ok=True)
    for f in (figure1, figure2, figure3, figure4, figure5, figure6):
        f()
        print("done", f.__name__)
