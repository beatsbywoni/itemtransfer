"""Design table and result tables of the simulation study (CSV and Markdown), built from the saved summaries."""
import json

import numpy as np
import pandas as pd

import sim01_separation as s1
import sim02_design_features as s2
import sim03_operating as s3
import sim04_ranking as s4
from simcore import RESULTS, save_json, versions

TABLES = RESULTS / "tables"


def pm(v, se, d=3):
    """value (Monte Carlo SE)"""
    if not np.isfinite(v):
        return ""
    return f"{v:.{d}f} ({se:.{d}f})" if np.isfinite(se) else f"{v:.{d}f}"


def md(df, path, floatfmt=3):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if not np.isfinite(v) else f"{v:.{floatfmt}f}")
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(map(str, r)) + " |" for r in df.astype(str).itertuples(index=False)]
    path.write_text("\n".join(lines) + "\n")
    df.to_csv(path.with_suffix(".csv"), index=False)


def design_table():
    def reps(study):
        s = pd.read_csv(RESULTS / f"{study}_summary.csv")
        return f"{int(s['n_rep'].min()):,} to {int(s['n_rep'].max()):,}" if s["n_rep"].min() != s["n_rep"].max() \
            else f"{int(s['n_rep'].max()):,}"

    n2 = {p: sum(c["part"] == p for c in s2.cells().values()) for p in "abc"}
    r2 = pd.read_csv(RESULTS / "sim02_summary.csv")
    rp = {p: f"{int(r2[r2['part'] == p]['n_rep'].min()):,} to {int(r2[r2['part'] == p]['n_rep'].max()):,}" for p in "abc"}
    rp = {p: (v.split(" to ")[0] if v.split(" to ")[0] == v.split(" to ")[1] else v) for p, v in rp.items()}
    rows = [
        dict(study="S1 Separation of the criteria", script="sim01_separation.py",
             varied="held-out slope as a multiple of the training slope (-1, 0, 0.25, 0.5, 1, 2); null measure; proxy "
                    "measure correlated .7 with the true measure in the training families only, in the held-out family "
                    "only, or everywhere; training slope 0, 0.05, 0.125, 0.25 with held-out slope 0.5",
             fixed="4 families, 48 items, 40 participants, item residual SD 0.5, participant SD 0.8",
             cells=len(s1.cells()), replications=reps("sim01"), bootstrap="two-way, 500 resamples",
             outputs="three criteria with intervals, weak-training flag, large-sample targets"),
        dict(study="S2a Level structure", script="sim02_design_features.py",
             varied="measure in the held-out family: continuous, four levels, two levels; true relation: graded or a "
                    "step at the middle of the range; design size: 48 items and 40 participants, or 96 and 80",
             fixed="4 families, continuous measure in the training families, effect SD 0.5 logits",
             cells=n2["a"], replications=rp["a"], bootstrap="two-way, 500 resamples",
             outputs="criteria, level-indicator baseline, within-level correlations"),
        dict(study="S2b Range mismatch", script="sim02_design_features.py",
             varied="true relation linear, logarithmic or saturating in the measure; range of the measure in the "
                    "held-out family: 1 to 4 (as in training), 2 to 8, 1 to 8",
             fixed="4 families, 48 items, 40 participants, training range 1 to 4, effect SD 0.5 logits in training",
             cells=n2["b"], replications=rp["b"], bootstrap="two-way, 500 resamples",
             outputs="criteria for the measure as given, on the common range, and for its logarithm"),
        dict(study="S2c Reliability of item difficulty", script="sim02_design_features.py",
             varied="participants per sample 10, 20, 40, 80; item residual SD 0, 0.5, 1",
             fixed="4 families, 48 items, slope 0.5", cells=n2["c"], replications=rp["c"], bootstrap="none",
             outputs="ordering observed, without response noise (same items), split-half reliability, corrected ordering"),
        dict(study="S3 Operating characteristics", script="sim03_operating.py",
             varied="one factor at a time around the base case: families 3, 4, 6, 10; items 24, 48, 96, 192; "
                    "participants 20, 40, 80; slope 0.25, 0.5, 1; item residual SD 0, 0.5, 1; participant SD 0, 0.8, 1.6. "
                    "Factorial: items 24 or 96 x slope 0.25 or 1 x item residual SD 0 or 1. Two small designs (3 families, "
                    "24 items, 20 participants, item residual SD 1, slope 0.5 or 0.25). True slope differing between "
                    "families (log-normal factor, SD 0.2 or 0.4; 3 or 10 families)",
             fixed="base case: 4 families, 48 items, 40 participants, slope 0.5, item residual SD 0.5, participant SD 0.8",
             cells=len(s3.cells()), replications=reps("sim03"),
             bootstrap="two-way, 500 resamples; in 15 cells also participants-only and items-only resampling",
             outputs="coverage, width, detection rate (true measure), false-positive rate (null measure)"),
        dict(study="S4 Within-family fit and transfer", script="sim04_ranking.py",
             varied="two measures with validities (correlation with the latent driver of difficulty) that are fixed per "
                    "family, drawn at random per family (between-family SD 0, 0.15, 0.3, 0.5 on the Fisher z scale; "
                    "3, 4, 6, 10 families) or equal but with a unit that differs between families",
             fixed="4 families, 48 items, 40 participants (two cells: 96 and 80), latent slope 1, item residual SD 0.5",
             cells=len(s4.cells()), replications=reps("sim04"), bootstrap="none",
             outputs="rate at which the measure with the better fit within the training families transfers worse"),
        dict(study="S6 Comparison with other analyses", script="sim06_comparators.py",
             varied="nine scenarios: common slope; held-out intercept 2 or 0; held-out slope x 0.5 or x 2; step relation "
                    "with a two-level held-out family; saturating relation with shifted range; no relation with item "
                    "residual SD 0.5 or 1",
             fixed="base case", cells=9, replications=reps("sim06"), bootstrap="two-way, 500 resamples",
             outputs="procedure, grouped cross-validation, Cochran Q with model-based and item-robust SE, "
                     "random-effects meta-analysis"),
        dict(study="S7 Non-collapsibility", script="sim07_noncollapsibility.py",
             varied="held-out family only: participant SD 0, 0.8, 1.6, 2.4; item residual SD 0, 0.5, 1, 1.5; intercept "
                    "-0.5, 0, 1, 2, 3", fixed="base case, identical conditional slope", cells=13,
             replications="large-sample values for all cells; 500 data sets for the two most extreme cells",
             bootstrap="two-way, 500 resamples", outputs="large-sample calibration slope, approximation, band 0.80 to 1.25"),
        dict(study="S8 Tolerance rule", script="sim08_tolerance.py",
             varied="true calibration slope 0.5, 0.8, 0.9, 1, 1.11, 1.25, 2; held-out items 48, 192, 768 (training 48); "
                    "all families 192 or 768 items (slopes 0.8, 1, 1.25)", fixed="4 families, 40 participants",
             cells=27, replications=reps("sim08"), bootstrap="two-way and items-only, 500 resamples, 95% and 90%",
             outputs="shares within, outside and undetermined"),
        dict(study="S5 Interval of the ordering criterion", script="sim05_ordering_interval.py",
             varied="items 48, 192, 768, 3,072; participants 20, 40, 80; item residual SD 0 or 0.5; slope 0.5 or 1",
             fixed="4 families, participant SD 0.8", cells=8, replications=reps("sim05"),
             bootstrap="two-way and items-only, 500 resamples, no prediction criterion",
             outputs="coverage of percentile and basic intervals of the ordering correlation"),
    ]
    df = pd.DataFrame(rows)
    df.columns = ["Study", "Script", "Varied", "Fixed", "Cells", "Replications per cell", "Bootstrap", "Outputs"]
    md(df, TABLES / "design_table.md")


def s1_table():
    s = pd.read_csv(RESULTS / "sim01_summary.csv")
    rows = []
    for r in s.itertuples():
        rows.append({"Condition": r.label, "Measure": r.measure, "Replications": r.n_rep,
                     "Ordering, mean": pm(r.ordering_mean, r.ordering_mcse), "Ordering, target": r.target_ordering,
                     "Calibration slope, median": r.calibration_slope_median, "5%": r.calibration_slope_q05,
                     "95%": r.calibration_slope_q95, "Calibration slope, target": r.target_calibration_slope,
                     "Log-loss reduction, mean": pm(r.logloss_reduction_mean, r.logloss_reduction_mcse, 4),
                     "Log-loss reduction, target": r.target_logloss_reduction,
                     "Weak-training flag": pm(r.weak_rate, r.weak_rate_mcse),
                     "Ordering interval above 0": pm(r.ord_pos, r.ord_pos_mcse),
                     "Slope interval excludes 0": pm(r.cal_excl0, r.cal_excl0_mcse),
                     "Slope interval includes 1": pm(r.cal_incl1, r.cal_incl1_mcse),
                     "Log-loss interval above 0": pm(r.ll_pos, r.ll_pos_mcse),
                     "Log-loss interval below 0": pm(r.ll_neg, r.ll_neg_mcse),
                     "Slope coverage": pm(r.cal_coverage, r.cal_coverage_mcse),
                     "|slope| > 5": r.cal_abs_gt5, "|slope| > 5, flagged": r.cal_flagged_abs_gt5,
                     "|slope| > 5, not flagged": r.cal_unflagged_abs_gt5})
    md(pd.DataFrame(rows), TABLES / "s1_separation.md")


def s2_tables():
    s = pd.read_csv(RESULTS / "sim02_summary.csv")
    a = s[s["part"] == "a"]
    rows = [{"True relation": r.truth, "Held-out measure": r.heldout_measure.replace("_", " "),
             "Items / participants": f"{r.n_items:.0f} / {r.n_part:.0f}", "Replications": r.n_rep,
             "Ordering": pm(r.ordering_mean, r.ordering_mcse), "Ordering interval above 0": pm(r.ord_pos, r.ord_pos_mcse),
             "Ordering, level indicator": pm(r.lev_ordering_levels_mean, r.lev_ordering_levels_mcse),
             "Ordering within levels": pm(r.lev_ordering_within_mean, r.lev_ordering_within_mcse),
             "Calibration slope, median": r.calibration_slope_median, "Calibration slope, target": r.target_calibration_slope,
             "Slope interval includes 1": pm(r.cal_incl1, r.cal_incl1_mcse),
             "Log-loss reduction, measure": pm(r.lev_logloss_measure_mean, r.lev_logloss_measure_mcse, 4),
             "Log-loss reduction, level indicator": pm(r.lev_logloss_levels_mean, r.lev_logloss_levels_mcse, 4),
             "Indicator minus measure": pm(r.lev_logloss_diff_mean, r.lev_logloss_diff_mcse, 4),
             "Indicator better (rate)": pm(r.lev_levels_better_rate, r.lev_levels_better_mcse),
             "Levels detected (rate)": r.lev_detected_rate} for r in a.itertuples()]
    md(pd.DataFrame(rows), TABLES / "s2a_levels.md")
    b = s[s["part"] == "b"]
    names = {"x": "as given", "log_x": "logarithm", "common_range_x": "common range"}
    rows = [{"True relation": r.relation, "Held-out range": {"same": "1 to 4", "shifted": "2 to 8", "wider": "1 to 8"}[r.heldout_range],
             "Measure": names[r.measure], "Replications": r.n_rep, "Ordering": pm(r.ordering_mean, r.ordering_mcse),
             "Calibration slope, target": r.target_calibration_slope, "Calibration slope, median": r.calibration_slope_median,
             "5%": r.calibration_slope_q05, "95%": r.calibration_slope_q95,
             "Slope interval includes 1": pm(r.cal_incl1, r.cal_incl1_mcse),
             "Slope coverage of target": pm(r.cal_coverage, r.cal_coverage_mcse),
             "Median interval width": r.cal_width_median,
             "Log-loss reduction, target": r.target_logloss_reduction,
             "Log-loss reduction, mean": pm(r.logloss_reduction_mean, r.logloss_reduction_mcse, 4),
             "Held-out items used": r.n_heldout_common_mean if hasattr(r, "n_heldout_common_mean") else np.nan}
            for r in b.itertuples()]
    md(pd.DataFrame(rows), TABLES / "s2b_range.md")
    c = s[s["part"] == "c"]
    rows = [{"Participants": int(r.n_part), "Item residual SD": r.item_sd, "Replications": r.n_rep,
             "Reliability (rank scale)": pm(r.rel_rank_mean, r.rel_rank_mcse),
             "Ordering observed": pm(r.ordering_mean, r.ordering_mcse),
             "Ordering without response noise": pm(r.noise_free_mean, r.noise_free_mcse),
             "Observed / noise-free": r.attenuation_mean, "Mean sqrt(reliability)": r.sqrt_rel_rank_mean,
             "Corrected ordering, mean": pm(r.corrected_rank_mean, r.corrected_rank_mcse),
             "Corrected, median": r.corrected_rank_median, "Corrected > 1 (rate)": r.corrected_gt1_rate,
             "Reliability not positive (rate)": r.rel_not_positive_rate,
             "SD of (observed - noise-free)": r.observed_minus_noise_free_sd,
             "SD of (corrected - noise-free)": r.corrected_minus_noise_free_sd} for r in c.itertuples()]
    md(pd.DataFrame(rows), TABLES / "s2c_reliability.md")


def s3_tables():
    s = pd.read_csv(RESULTS / "sim03_summary.csv")
    x = s[s["measure"] == "x"]
    rows = []
    for r in x.itertuples():
        d = {"Cell": r.cell, "Families": r.n_fam, "Items": r.n_items, "Participants": r.n_part, "Slope": r.slope,
             "Item SD": r.item_sd, "Participant SD": r.part_sd, "Replications": r.n_rep,
             "Slope: coverage": pm(r.cal_coverage, r.cal_coverage_mcse), "Slope: median width": r.cal_width_median,
             "Slope: nominal width": r.cal_width_nominal,
             "Slope: detection": pm(r.cal_excl0, r.cal_excl0_mcse), "Slope: includes 1": pm(r.cal_incl1, r.cal_incl1_mcse),
             "Log loss: target": r.ll_target, "Log loss: mean": pm(r.logloss_reduction_mean, r.logloss_reduction_mcse, 4),
             "Log loss: coverage": pm(r.ll_coverage, r.ll_coverage_mcse),
             "Log loss: coverage of design mean": pm(r.ll_coverage_expect, r.ll_coverage_expect_mcse),
             "Log loss: detection": pm(r.ll_pos, r.ll_pos_mcse),
             "Ordering: mean": pm(r.ordering_mean, r.ordering_mcse),
             "Ordering: coverage of design mean": pm(r.ord_coverage_expect, r.ord_coverage_expect_mcse),
             "Ordering: detection": pm(r.ord_pos, r.ord_pos_mcse),
             "Weak-training flag": pm(r.weak_rate, r.weak_rate_mcse)}
        rows.append(d)
    md(pd.DataFrame(rows), TABLES / "s3_true_measure.md")
    rows = []
    for r in x[x["cal_coverage_po"].notna()].itertuples():
        rows.append({"Cell": r.cell, "Items": r.n_items, "Slope": r.slope, "Item SD": r.item_sd, "Participant SD": r.part_sd,
                     "Slope coverage: two-way": pm(r.cal_coverage, r.cal_coverage_mcse),
                     "participants only": pm(r.cal_coverage_po, r.cal_coverage_mcse_po),
                     "items only": pm(r.cal_coverage_io, r.cal_coverage_mcse_io),
                     "Slope width: two-way": r.cal_width_median, "width: participants only": r.cal_width_median_po,
                     "width: items only": r.cal_width_median_io, "width: nominal": r.cal_width_nominal,
                     "Log-loss coverage: two-way": pm(r.ll_coverage, r.ll_coverage_mcse),
                     "LL participants only": pm(r.ll_coverage_po, r.ll_coverage_mcse_po),
                     "LL items only": pm(r.ll_coverage_io, r.ll_coverage_mcse_io),
                     "Slope detection: two-way": pm(r.cal_excl0, r.cal_excl0_mcse),
                     "detection: items only": pm(r.cal_excl0_io, r.cal_excl0_mcse_io),
                     "LL detection: two-way": pm(r.ll_pos, r.ll_pos_mcse),
                     "LL detection: items only": pm(r.ll_pos_io, r.ll_pos_mcse_io)})
    md(pd.DataFrame(rows), TABLES / "s3_bootstrap_comparison.md")
    n = s[s["measure"] == "x_null"]
    rows = []
    for r in n.itertuples():
        rows.append({"Cell": r.cell, "Replications": r.n_rep, "Weak-training flag": pm(r.weak_rate, r.weak_rate_mcse),
                     "Slope interval excludes 0": pm(r.cal_excl0, r.cal_excl0_mcse),
                     "excludes 0 and not flagged": pm(r.cal_excl0_notweak, r.cal_excl0_notweak_mcse),
                     "Log-loss interval above 0": pm(r.ll_pos, r.ll_pos_mcse),
                     "Log-loss interval below 0": pm(r.ll_neg, r.ll_neg_mcse),
                     "Ordering interval excludes 0": pm(r.ord_excl0, r.ord_excl0_mcse),
                     "Slope excl. 0, participants only": pm(getattr(r, "cal_excl0_po", np.nan), getattr(r, "cal_excl0_mcse_po", np.nan)),
                     "Log loss > 0, participants only": pm(getattr(r, "ll_pos_po", np.nan), getattr(r, "ll_pos_mcse_po", np.nan)),
                     "Ordering excl. 0, participants only": pm(getattr(r, "ord_excl0_po", np.nan), getattr(r, "ord_excl0_mcse_po", np.nan)),
                     "Slope excl. 0, items only": pm(getattr(r, "cal_excl0_io", np.nan), getattr(r, "cal_excl0_mcse_io", np.nan)),
                     "Log loss > 0, items only": pm(getattr(r, "ll_pos_io", np.nan), getattr(r, "ll_pos_mcse_io", np.nan)),
                     "Ordering excl. 0, items only": pm(getattr(r, "ord_excl0_io", np.nan), getattr(r, "ord_excl0_mcse_io", np.nan))})
    md(pd.DataFrame(rows), TABLES / "s3_null_measure.md")
    h = x[x["hetero"] > 0]
    rows = [{"Families": r.n_fam, "SD of log slope factor": r.hetero, "Replications": r.n_rep,
             "Target of the draw: 5%": r.target_rep_q05, "median": r.target_rep_median, "95%": r.target_rep_q95,
             "Coverage of the target of the draw": pm(r.cal_coverage, r.cal_coverage_mcse),
             "Interval includes 1": pm(r.cal_incl1, r.cal_incl1_mcse),
             "Includes 1 when target < 0.75 or > 1.33": pm(r.cal_incl1_when_target_far, r.cal_incl1_when_target_far_mcse),
             "Draws with such a target": int(r.n_target_far), "Median width": r.cal_width_median} for r in h.itertuples()]
    md(pd.DataFrame(rows), TABLES / "s3_slope_differs.md")


def s4_table():
    s = pd.read_csv(RESULTS / "sim04_summary.csv")
    rows = []
    for r in s.itertuples():
        d = r._asdict()
        rows.append({"Cell": r.cell, "Scenario": r.kind, "Families": r.n_fam, "Items / participants": f"{r.n_items} / {r.n_part}",
                     "Replications": r.n_rep,
                     "A selected by fit (common slope)": r.a_selected_fit_pooled,
                     "A better in held-out: ordering": r.a_wins_ordering, "A better in held-out: log loss": r.a_wins_logloss,
                     "Disagreement, fit vs ordering": pm(d["disagree_fit_pooled_vs_ordering"], d["disagree_fit_pooled_vs_ordering_mcse"]),
                     "Disagreement, fit vs log loss": pm(d["disagree_fit_pooled_vs_logloss"], d["disagree_fit_pooled_vs_logloss_mcse"]),
                     "Separate slopes vs log loss": pm(d["disagree_fit_separate_vs_logloss"], d["disagree_fit_separate_vs_logloss_mcse"]),
                     "Transfer among training families vs log loss": pm(d["disagree_transfer_logloss_vs_logloss"], d["disagree_transfer_logloss_vs_logloss_mcse"]),
                     "Material, ordering (> .10 worse)": pm(d["material_fit_pooled_vs_ordering"], d["material_fit_pooled_vs_ordering_mcse"]),
                     "Material, log loss (> .01 worse)": pm(d["material_fit_pooled_vs_logloss"], d["material_fit_pooled_vs_logloss_mcse"]),
                     "Fit winner has lower true held-out validity": pm(d["wrong_truth_fit_pooled"], d["wrong_truth_fit_pooled_mcse"]),
                     "True rankings differ (no sampling error)": pm(d["true_disagreement"], d["true_disagreement_mcse"]),
                     "LL of A": pm(d["logloss_a_mean"], d["logloss_a_mcse"], 4), "LL of B": pm(d["logloss_b_mean"], d["logloss_b_mcse"], 4),
                     "LL, selected by fit": pm(d["selected_fit_pooled_vs_logloss_mean"], d["selected_fit_pooled_vs_logloss_mcse"], 4),
                     "LL, selected by separate fit": pm(d["selected_fit_separate_vs_logloss_mean"], d["selected_fit_separate_vs_logloss_mcse"], 4),
                     "LL, selected by transfer among training families": pm(d["selected_transfer_logloss_vs_logloss_mean"], d["selected_transfer_logloss_vs_logloss_mcse"], 4),
                     "Calibration slope A, median": d["calibration_a_median"], "Calibration slope B, median": d["calibration_b_median"]})
    md(pd.DataFrame(rows), TABLES / "s4_ranking.md")


def ordering_interval_table():
    """Percentile and basic (reflected) interval of the ordering criterion, by items and participants."""
    frames = [pd.read_csv(RESULTS / "sim03_summary.csv").assign(source="S3")]
    if (RESULTS / "sim05_summary.csv").exists():
        frames.append(pd.read_csv(RESULTS / "sim05_summary.csv").assign(source="S5", n_fam=4, part_sd=0.8))
    s = pd.concat(frames, ignore_index=True)
    s = s[(s["source"] == "S5") | (s["cell"].isin(["base", "ofat_n_items_24", "ofat_n_items_96", "ofat_n_items_192",
                                                   "ofat_n_part_20", "ofat_n_part_80", "ofat_item_sd_0",
                                                   "ofat_item_sd_1", "ofat_slope_0.25", "ofat_slope_1"]))]
    x = s[s["measure"] == "x"].set_index(["source", "cell"])
    n = s[s["measure"] == "x_null"].set_index(["source", "cell"])
    rows = []
    for key, r in x.sort_values(["n_items", "n_part", "item_sd", "slope"]).iterrows():
        z = n.loc[key] if key in n.index else None
        rows.append({"Source": key[0], "Items": int(r["n_items"]), "Participants": int(r["n_part"]), "Slope": r["slope"],
                     "Item SD": r["item_sd"], "Replications": int(r["n_rep"]),
                     "Expected ordering": r["ord_expected"], "Large-sample ordering": r["ord_target"],
                     "Shift of interval centre": pm(r["ord_centre_shift"], r["ord_centre_shift_mcse"]),
                     "Median width": r["ord_width_median"],
                     "Percentile interval excludes own estimate": pm(r["ord_excludes_own_estimate"], r["ord_excludes_own_estimate_mcse"]),
                     "Coverage of expected ordering: percentile": pm(r["ord_cov_expected_percentile"], r["ord_cov_expected_percentile_mcse"]),
                     "basic": pm(r["ord_cov_expected_basic"], r["ord_cov_expected_basic_mcse"]),
                     "Coverage of large-sample ordering: percentile": pm(r["ord_cov_large_sample_percentile"], r["ord_cov_large_sample_percentile_mcse"]),
                     "basic ": pm(r["ord_cov_large_sample_basic"], r["ord_cov_large_sample_basic_mcse"]),
                     "Detection (interval above 0): percentile": pm(r["ord_pos"], r["ord_pos_mcse"]),
                     "basic  ": pm(r["ord_pos_basic"], r["ord_pos_basic_mcse"]),
                     "Coverage of expected ordering: items-only percentile":
                         pm(r.get("ord_cov_expected_percentile_io", np.nan), r.get("ord_cov_expected_percentile_mcse_io", np.nan)),
                     "Null measure, interval excludes 0: percentile": pm(z["ord_excl0"], z["ord_excl0_mcse"])
                     if z is not None else "",
                     "basic   ": pm(z["ord_excl0_basic"], z["ord_excl0_basic_mcse"]) if z is not None else "",
                     "items-only percentile": pm(z.get("ord_excl0_io", np.nan), z.get("ord_excl0_mcse_io", np.nan))
                     if z is not None else ""})
    md(pd.DataFrame(rows), TABLES / "ordering_interval.md")


def s6_table():
    s = pd.read_csv(RESULTS / "sim06_summary.csv")
    rows = []
    for r in s.itertuples():
        rows.append({"Scenario": r.label, "Replications": r.n_rep,
                     "Procedure: ordering": pm(r.ordering_mean, r.ordering_mcse),
                     "calibration slope, median": r.calibration_slope_median, "large-sample value": r.target_calibration_slope,
                     "slope interval excludes 0": pm(r.cal_excl0, r.cal_excl0_mcse),
                     "slope interval includes 1": pm(r.cal_incl1, r.cal_incl1_mcse),
                     "reading within tolerance": pm(r.within, r.within_mcse),
                     "reading outside tolerance": pm(r.outside, r.outside_mcse),
                     "log-loss reduction (recalibrated)": pm(r.logloss_reduction_mean, r.logloss_reduction_mcse, 4),
                     "log-loss interval above 0": pm(r.ll_pos, r.ll_pos_mcse),
                     "log-loss interval below 0": pm(r.ll_neg, r.ll_neg_mcse),
                     "weak-training flag": pm(r.weak, r.weak_mcse),
                     "Grouped CV: score": pm(r.gcv_score_mean, r.gcv_score_mcse, 4),
                     "score 5%": r.gcv_score_q05, "score 95%": r.gcv_score_q95,
                     "score positive": pm(r.gcv_positive, r.gcv_positive_mcse),
                     "Q test rejects, model-based SE": pm(r.q_reject_model, r.q_reject_model_mcse),
                     "Q test rejects, item-robust SE": pm(r.q_reject_item, r.q_reject_item_mcse),
                     "item-robust SE / model-based SE": pm(r.se_ratio_mean, r.se_ratio_mcse, 2),
                     "Random effects: tau = 0": pm(r.tau_zero, r.tau_zero_mcse),
                     "mean tau": pm(r.re_tau_mean, r.re_tau_mcse), "mean slope": pm(r.re_mean_mean, r.re_mean_mcse),
                     "CI excludes 0": pm(r.re_ci_excl0, r.re_ci_excl0_mcse),
                     "prediction interval, median width": r.re_pi_width_median,
                     "prediction interval excludes 0": pm(r.re_pi_excl0, r.re_pi_excl0_mcse),
                     "Identity: max |calibration slope - ratio of slopes|": f"{r.identity_max_abs_diff:.1e}",
                     "correlation": f"{r.identity_correlation:.6f}", "data sets used": r.identity_n})
    md(pd.DataFrame(rows), TABLES / "s6_comparators.md")


def s7_table():
    t = pd.read_csv(RESULTS / "sim07_targets.csv")
    names = {"part_sd": "participant SD", "item_sd": "item residual SD", "intercept": "intercept"}
    rows = [{"Held-out family differs in": names[r.factor], "Value (training: 0.8, 0.5, 1)": r.value,
             "Large-sample calibration slope": r.calibration_slope, "Approximation": r.approximation,
             "Difference": r.difference_from_approximation, "Outside 0.80 to 1.25": "yes" if r.outside_band else "no",
             "Large-sample ordering": r.ordering, "Large-sample log-loss reduction": r.logloss_reduction}
            for r in t.itertuples()]
    md(pd.DataFrame(rows), TABLES / "s7_noncollapsibility.md")
    f = pd.read_csv(RESULTS / "sim07_summary.csv")
    rows = [{"Cell": r.cell, "Replications": r.n_rep, "Large-sample value": r.target, "Median estimate": r.median,
             "Coverage of the large-sample value": pm(r.coverage_of_target, r.coverage_of_target_mcse),
             "Interval includes 1": pm(r.includes_1, r.includes_1_mcse), "Within tolerance": pm(r.within, r.within_mcse),
             "Outside tolerance": pm(r.outside, r.outside_mcse), "Undetermined": r.undetermined,
             "Median width": r.median_width, "Log-loss reduction, mean": pm(r.logloss_reduction_mean, r.logloss_reduction_mcse, 4),
             "Log-loss interval above 0": pm(r.logloss_above_0, r.logloss_above_0_mcse)} for r in f.itertuples()]
    md(pd.DataFrame(rows), TABLES / "s7_finite_sample.md")


def s8_tables():
    s = pd.read_csv(RESULTS / "sim08_summary.csv")
    rows = []
    for r in s.itertuples():
        d = r._asdict()
        row = {"Items varied in": "held-out family" if r.arm == "held-out" else "all families", "Items": r.n_items,
               "True calibration slope": r.factor, "Large-sample value": r.target, "Replications": r.n_rep}
        for key, lab in (("two_way_95", "two-way 95%"), ("two_way_90", "two-way 90%"), ("items_only_95", "items-only 95%"),
                         ("items_only_90", "items-only 90%")):
            row[f"Within, {lab}"] = pm(d[f"within_{key}"], d[f"within_{key}_mcse"])
            row[f"Outside, {lab}"] = pm(d[f"outside_{key}"], d[f"outside_{key}_mcse"])
            row[f"Undetermined, {lab}"] = d[f"undetermined_{key}"]
            row[f"Median width, {lab}"] = d[f"width_{key}"]
        rows.append(row)
    md(pd.DataFrame(rows), TABLES / "s8_tolerance.md")
    c = pd.read_csv(RESULTS / "sim03_classification_bias_rmse.csv")
    rows = [{"Cell": r.cell, "Families": int(r.n_fam), "Items": int(r.n_items), "Participants": int(r.n_part), "Slope": r.slope,
             "Item SD": r.item_sd, "Participant SD": r.part_sd, "Replications": r.n_rep,
             "Within tolerance": pm(r.within, r.within_mcse), "Outside tolerance": pm(r.outside, r.outside_mcse),
             "Undetermined": r.undetermined,
             "Within, items-only": pm(getattr(r, "within_items_only", np.nan), getattr(r, "within_items_only_mcse", np.nan)),
             "Outside, items-only": pm(getattr(r, "outside_items_only", np.nan), getattr(r, "outside_items_only_mcse", np.nan)),
             "Calibration slope: bias": pm(r.cal_bias, r.cal_bias_mcse), "median bias": r.cal_median_bias,
             "RMSE": r.cal_rmse, "Log-loss reduction: bias": pm(r.ll_bias, r.ll_bias_mcse, 4),
             "RMSE ": f"{r.ll_rmse:.4f}" if np.isfinite(r.ll_rmse) else "", "target": r.ll_target} for r in c.itertuples()]
    md(pd.DataFrame(rows), TABLES / "s3_classification_bias_rmse.md")


def run_info():
    info = dict(versions=versions(), studies={})
    total = 0.0
    for st in ("sim00", "sim01", "sim02", "sim03", "sim04", "sim05", "sim06", "sim07", "sim08"):
        p = RESULTS / f"{st}_run_info.json"
        if p.exists():
            d = json.loads(p.read_text())
            info["studies"][st] = d
            total += sum(r["wall_seconds"] for r in d.get("runs", [])) + d.get("seconds", 0)
    # two runs were stopped by the two-hour limit of the session and resumed from their saved chunks; their
    # wall time is not in the per-study files and is taken from the progress lines of the run logs
    stopped = {"sim02 (first 104 of 420 chunks, results/run_all.log)": 703.0,
               "sim03 (first 543 of 580 chunks, results/run_stage3.log)": 7200.0,
               "sim05 (first attempt without the items-only comparison, discarded)": 400.0,
               "sim06 (first 44 of 90 chunks, stopped by a restart of the container)": 700.0}
    info["runs_stopped_and_resumed_wall_seconds"] = stopped
    total += sum(stopped.values())
    info["note"] = ("Two cores. During sim00, sim01 and sim04 the cores were shared with another job of the same "
                    "project, so those wall times overstate the cost by a factor of about 2 to 3.")
    info["total_wall_seconds_simulation"] = round(total, 1)
    info["total_wall_hours_simulation"] = round(total / 3600, 2)
    save_json("run_info.json", info)


if __name__ == "__main__":
    TABLES.mkdir(exist_ok=True)
    for f in (design_table, s1_table, s2_tables, s3_tables, s4_table, ordering_interval_table, s6_table, s7_table,
              s8_tables, run_info):
        f()
    print("tables written to", TABLES)
