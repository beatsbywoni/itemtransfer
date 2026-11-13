"""Build supplement.md. Part 1 holds the final methods and results; Parts 2 to 4 are dated working documents."""
from pathlib import Path
import json, re
import pandas as pd

B = Path(__file__).resolve().parents[1]
def rd(p): return (B / p).read_text()
def demote(t, by=1):
    return re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1)) + by) + " ", t, flags=re.M)
def drop_wide_tables(t, max_cols=9, note="*(Table with {n} columns omitted from this document because of its width; the complete table is in the CSV files of the repository folder `{folder}`.)*", folder=""):
    out, block = [], []
    def flush():
        if block:
            n = max(line.count("|") - 1 for line in block)
            out.extend(block if n <= max_cols else [note.format(n=n, folder=folder)])
            block.clear()
    for line in t.split("\n"):
        if line.startswith("|"):
            block.append(line)
        else:
            flush(); out.append(line)
    flush()
    return "\n".join(out)
caps = rd("sim/figures/captions.md")
def cap(n):
    m = re.search(rf"\*\*Figure {n}\. (.*?)\*\*\n(.*?)(?=\n\n\*\*Figure|\Z)", caps, flags=re.S)
    return (m.group(1).strip() + " " + " ".join(m.group(2).split())) if m else ""
def ci(r, st, d=2):
    return f"{r[st]:.{d}f} [{r[st + '_lo']:.{d}f}, {r[st + '_hi']:.{d}f}]"

TITLE = "Do item difficulty measures generalise to new stimulus sets? Leave-one-family-out validation, its pitfalls, and the itemtransfer package"
o = ["# Supplementary material", "", TITLE, "", "Hongwon Jeong", "",
     "Part 1 gives the final methods and results that the article relies on and that are not in its tables. Parts 2 to 4 are working documents, kept as they were written and dated: the report of the simulation study (Part 2), the analysis plan and the report of the lexical decision example (Part 3), and the output of the software for the knapsack example (Part 4). Statements in Parts 2 to 4 that were superseded later are marked there, and Part 1 states the final version. The working documents use the short names of the megastudies (ELP = English Lexicon Project, BLP = British Lexicon Project, DLP = Dutch Lexicon Project) and OLD20 for neighbourhood distance.", "",
     "# Part 1. Final methods and results", "",
     "## 1.1 What each criterion estimates, and what is resampled", "",
     "| Criterion | Quantity in the held-out family | Target in the simulation study | Resampled for the interval |", "|---|---|---|---|",
     "| Ordering | Spearman correlation between the transferred predictor and observed item accuracy | The mean of this correlation over data sets with new items and new participants of the same numbers. It is not the correlation with error-free accuracy | Items within families (training fit repeated). Participants are kept as observed |",
     "| Scale | Calibration slope: slope of a logistic regression of the held-out responses on the transferred predictor. The slopes are population-averaged, that is, from a model without random effects | Its value in a data set with 120,000 items per family, with abilities integrated out | Participants within samples and items within families |",
     "| Prediction | Relative reduction in log loss against an intercept-only model; both intercepts estimated on one half of the held-out items and scored on the other half | As for scale | Participants within samples and items within families |", "",
     "The items-only interval for ordering contained its target in 90.5% to 99% of the data sets in the 23 complete, balanced conditions in which it was examined (Part 2, S5). It was not examined for sparse or unbalanced designs, for several samples per family, or for predictors made of several measures; for such designs its coverage is not established. The simulation check of the software reports coverage for the calibration slope and the prediction criterion, not for ordering.", "",
     "## 1.2 Link between the calibration slope and the prediction criterion", "",
     "Let the transferred predictor of item i be z_i (the trained slope times the measure), and let the logit of the probability of a correct response in the held-out family be a + c z_i, so that c is the calibration slope. The prediction criterion compares two models whose intercepts are re-estimated in the held-out family: the model a' + z_i, with the slope fixed at its trained value, and the model a'' without the measure. Expand the expected log-likelihood per response of the model a' + k z_i around k = 0 to second order in k. The first derivative with respect to k at k = 0 is the covariance between z and the probability of a correct response, which to first order in the effect is c w Var(z), where w is the mean of p(1 - p) and Var(z) is the variance of the transferred predictor over the held-out responses. The second derivative is - w Var(z). The expected gain of the model with slope k over the model without the measure is therefore approximately w Var(z) (c k - k^2 / 2), and at the trained slope, k = 1, it is (1/2) w Var(z) (2c - 1).", "",
     "This is a local approximation for small effects. It ignores terms of third and higher order, and the exact break-even point depends on the size of the trained effect and on the distribution of the measure. The table gives the exact values by numerical integration (script `sim/exact_breakeven.py`, file `sim/results/exact_breakeven.csv`). For a standard normal measure the break-even calibration slope is 0.49 to 0.50 up to a trained slope of 0.5 logits per standard deviation, 0.48 at a slope of 1, 0.44 at 2 and 0.40 at 3. For a measure that is uniform between -4 and 4, whose spread is larger, the break-even point is lower, and a calibration slope of 0.5 leaves a clearly positive reduction in log loss at larger slopes (7.9% at a trained slope of 1 with intercept 0). The statement in the article is therefore limited to effects of small to medium size, and the software computes the reduction in log loss exactly and never uses the approximation.", ""]
o += rd("sim/results/tables/exact_breakeven.md").strip().split("\n")
o += ["", "## 1.3 Rule for detecting a level structure", "",
      "A measure is treated as having a level structure in a family (a) when it takes at most six distinct values there, or (b) when its sorted values can be cut at their largest gaps into two to six groups such that the smallest gap between neighbouring groups is more than twice the widest range within a group and every group contains at least two items. Both numbers (six levels, ratio 2) are arguments of the function `diagnose` and can be changed. The rules of the other diagnostics are in the article; all are heuristics.", "",
      "## 1.4 Settings of the analyses", "",
      "| Analysis | Package version | Bootstrap resamples | Random divisions of held-out items (estimate / within each resample) | Seed | Weights | Other settings |", "|---|---|---|---|---|---|---|"]
k = json.load(open(B / "knapsack_report/run_info.json")); l = json.load(open(B / "second_example/results/run_info_step3.json"))
o += [f"| Knapsack example | {k['version']} | {k['n_boot']} | {k['n_splits']} / 10 | 20261016 (bootstrap), 20261017 (divisions) | every response counted once | Evaluation samples: Franco 2021, Doroc 2025, Lu 2025 main. Reliability only: Lu 2025 pilot. Ordering interval from items only. Tolerance 0.80 to 1.25. Reliability from {k['n_splits_reliability']} splits. Simulation check: {k['n_sim']} data sets with {k['n_boot_sim']} resamples |",
      f"| Lexical decision example, main analysis | {l['itemtransfer']} | {l['settings']['n_boot']}, in batches of {l['settings']['boot_batch']} | {l['settings']['n_splits']} / {l['settings']['n_splits_boot']} | {l['seed']} | every response counted once | Ordering interval from items only. Tolerance 0.80 to 1.25. Sensitivity analyses: 200 resamples |",
      "| Simulation study, S1 to S5 | 0.1.0 (the functions used are unchanged in 0.2.0) | 500 | 100 / 10 | 2601 to 2605; generator seeded by study, condition and replication | every response counted once | 1,000 or 2,000 data sets per condition unless stated in Part 2 |",
      "| Simulation study, S6 to S8 | 0.2.0 | 500 | 100 / 10 | 2606 to 2608 | every response counted once | See Part 2 |",
      "| Mixed models | R 4.6.2, lme4 2.1.0 | none | none | 2610 to 2615 (simulation) | not applicable | See 1.6 and 1.8 |", "",
      "The test suite of version 0.1.0 had 73 tests; version 0.2.0, which produced the results of both examples, has 78. In every analysis the model has one intercept per sample, an item that two samples share is one unit in the resampling of items, and when a family is held out none of its samples enters the training fit.", "",
      "## 1.5 Knapsack example: recomputation of the measures (step 1)", "",
      "Every measure was recomputed from the weights and values of the objects with one implementation. Instance complexity, the capacity and target ratios that enter typical-case complexity, satisfiability, the best attainable value and Sahni-k agreed with every value that the source studies report, with one exception: for one item of the Doroc family the stored instance complexity corresponds to a best attainable value of 128, whereas enumeration gives 130, which places the item just below its designed level without changing whether it has a solution. Typical-case complexity was computed from the probability that a random instance with the same number of objects, capacity ratio and target ratio has a solution (estimated from 20,000 random instances with independent uniform weights and values) as 1 minus the absolute value of twice this probability minus 1. Solver effort is the base-2 logarithm of 1 plus the number of propagations of the Gecode constraint solver (Gecode 6.3.0 through MiniZinc 2.9.3) on the model of Franco et al. (2021). The recomputed propagation counts correlated .88 with the published counts for the Franco decision items; the difference is attributed to the solver versions.", "",
      "## 1.6 Knapsack example: evaluation sample of the Franco family, and mixed model", "",
      "The Franco family is evaluated on the Franco et al. (2021) sample (all 72 items). The plan of the earlier analysis of these data, frozen on 26 October 2026 before any result was computed, fixed this choice and named the evaluation on the Franco et al. (2024a) sample (56 of the 72 items) as a sensitivity analysis. Its result (file `knapsack_report/sensitivity_franco2024_evaluation.csv`, 2,000 resamples):", "",
      "| Measure | Items | Responses | Ordering | Calibration slope | Reduction in log loss |", "|---|---|---|---|---|---|"]
s = pd.read_csv(B / "knapsack_report/sensitivity_franco2024_evaluation.csv")
nm = {"instance_complexity": "Instance complexity", "typical_case_complexity": "Typical-case complexity"}
for _, r in s.iterrows():
    o.append(f"| {nm[r.model]} | {int(r.n_items)} | {int(r.n_trials):,} | {ci(r, 'ordering')} | {ci(r, 'calibration_slope')} | {ci(r, 'logloss_reduction', 3)} |")
o += ["", "Mixed model (script `glmm/glmm_knapsack.R`, files `glmm/glmm_knapsack_slopes.csv` and `glmm/glmm_knapsack_ratios.csv`). The four samples of the transfer analysis were analysed together (11,450 responses, 118 participants, 264 items) with `lme4::glmer`, binomial family, Laplace approximation, optimiser bobyqa. Model with one slope per family: `correct ~ 0 + sample + family:measure + (1 | participant) + (1 | item)`; model with a common slope: `correct ~ 0 + sample + measure + (1 | participant) + (1 | item)`. The two were compared by a likelihood-ratio test with 2 degrees of freedom. For the ratio of slopes, the model `correct ~ 0 + sample + measure_training + measure_heldout + (1 | participant) + (1 | item)` was fitted once per held-out family, where the two predictors are the measure in the other families and in the held-out family; the interval of the ratio is a delta-method interval. All six fits converged and none was singular. The ratio without random effects in the last column comes from the same fixed effects in an ordinary logistic regression; it differs from the calibration slope of the article for the Franco family, because here both Franco samples are in the held-out part.", "",
      "| Measure | Held-out family | Slope in the other families | Slope in the held-out family | Ratio, mixed model | Ratio, no random effects | Test of equal slopes in the three families |", "|---|---|---|---|---|---|---|"]
gr = pd.read_csv(B / "glmm/glmm_knapsack_ratios.csv"); gs = pd.read_csv(B / "glmm/glmm_knapsack_slopes.csv")
mm = {"ic": "Instance complexity", "tcc": "Typical-case complexity"}
for _, r in gr.iterrows():
    t = gs[(gs.measure == r.measure)].iloc[0]
    o.append(f"| {mm[r.measure]} | {r.heldout_family} | {r.conditional_train_slope:.2f} | {r.conditional_heldout_slope:.2f} | {r.conditional_ratio:.2f} [{r.conditional_ratio_lo:.2f}, {r.conditional_ratio_hi:.2f}] | {r.marginal_ratio:.2f} | chi-square({int(t.lrt_df)}) = {t.lrt_chisq_equal_slopes:.2f}, p = {t.lrt_p:.2g} |")
o += ["", "## 1.7 Lexical decision example: flow of the data, final results, timeline", "",
      "Flow of the data (counts from the loader, see Part 3 and `second_example/PROVENANCE.md`).", "",
      "| Megastudy | Participants | Words | Word responses, all | Words in the transfer analysis | Word responses in the transfer analysis | Exclusions before the count of word responses |", "|---|---|---|---|---|---|---|",
      "| English Lexicon Project | 814 | 40,481 | 1,372,240 | 30,992 | 1,050,513 | 6 of 820 participant files that the depositors mark as redundant or faulty; 722 word responses without a valid accuracy code. The article of the project reports 816 participants; the deposit does not identify them, so 814 is used |",
      "| British Lexicon Project | 78 | 28,730 | 1,120,470 | 19,241 | 750,388 | none |",
      "| Dutch Lexicon Project | 39 | 14,089 | 549,471 | 14,089 | 549,471 | block 50, which the authors exclude; time-outs count as errors, as the authors scored them |",
      "| MEGALEX | 96 | 28,466 | 1,311,740 | 28,466 | 1,311,740 | none |",
      "| Total | | | 4,353,921 | 92,788 | 3,662,112 | |", "",
      "Nonword responses are not used. The difference between 4,353,921 and 3,662,112 responses is due to the 18,978 words that the two English megastudies share: each was assigned at random to one megastudy, and its responses in the other megastudy are left out of the transfer analysis (they are used for the agreement between samples in step 2).", "",
      "Final transfer results for all four models (file `second_example/results/step3_transfer.csv`, version 0.2.0; ordering intervals from resampled items, the others from participants and items). Table 7 of the article is taken from the same file.", "",
      "| Held-out megastudy | Model | Training slope | Slope fitted in the family | Ordering | Calibration slope | Reduction in log loss |", "|---|---|---|---|---|---|---|"]
names = {"ELP": "English Lexicon Project", "BLP": "British Lexicon Project", "DLP": "Dutch Lexicon Project", "MEGALEX": "MEGALEX"}
t = pd.read_csv(B / "second_example/results/step3_transfer.csv")
mn = {"zipf": "Frequency", "length": "Length", "old20": "Neighbourhood distance", "combined": "Three measures"}
for f, nmf in names.items():
    for m, ml in mn.items():
        r = t[(t.family == f) & (t.model == m)].iloc[0]
        ts = "" if pd.isna(r.train_slope) else f"{r.train_slope:.2f}"
        hs = "" if pd.isna(r.heldout_slope) else ci(r, "heldout_slope")
        o.append(f"| {nmf} | {ml} | {ts} | {hs} | {ci(r, 'ordering')} | {ci(r, 'calibration_slope')} | {ci(r, 'logloss_reduction', 3)} |")
o += ["", "Non-linear frequency function (not planned; file `second_example/results/posthoc_nonlinear_frequency.csv`, 200 resamples). Words unknown to the frequency resource were removed, and frequency was entered linearly or as a cubic polynomial.", "",
      "| Held-out megastudy | Words | Linear: calibration slope | Cubic: calibration slope | Linear: reduction in log loss | Cubic: reduction in log loss |", "|---|---|---|---|---|---|"]
tn = pd.read_csv(B / "second_example/results/posthoc_nonlinear_frequency.csv").set_index(["family", "model"])
for f, nmf in names.items():
    a, c = tn.loc[(f, "linear")], tn.loc[(f, "cubic")]
    o.append(f"| {nmf} | {int(a.n_items):,} | {ci(a, 'calibration_slope')} | {ci(c, 'calibration_slope')} | {a.logloss_reduction:.3f} | {c.logloss_reduction:.3f} |")
o += ["", "Neighbourhood distance was computed against the complete word list of the megastudy to which a word belongs (40,481, 28,730, 14,089 and 28,466 words), so a shared English word has the value of the megastudy to which it was assigned, and the values are not on one scale. With reference lists of equal size (a random 14,089 words of each list) the trained slopes were about half as large, the reversal of sign for the Dutch megastudy remained, and the reductions in log loss stayed at or below .001 (Part 3). A common, fixed reference list for the two English megastudies was not examined.", "",
      "Timeline (all on 13 November 2026, Korean time). The dates of the plan are the times recorded in the file; the plan was not registered externally.", "",
      "| Time | Event | What was known |", "|---|---|---|",
      "| before 10:12 | Feasibility check on copies of the data with rough versions of the measures | Within each megastudy: correlations of accuracy with frequency (.53 to .69) and length, slopes of frequency (about 0.70 in three megastudies, 1.06 in the British one), one split-half reliability each, raw agreement of the two English megastudies (.73) |",
      "| 10:12 | Analysis plan written (Part 3), after step 1 | As above. No transfer result |",
      "| 10:14 | Item file of the English Lexicon Project obtained; used in step 1 only | |",
      "| after 10:14 | Steps 2 to 5 run as planned | |",
      "| 12:09 | Additions after the transfer results had been seen, listed in the plan as deviations | Transfer results. Added: analysis without words unknown to the frequency resource, comparison of the three-measure model with frequency, slopes on fixed word sets, examination of the ordering interval |",
      "| afternoon | Simulation of the ordering interval (Part 2, S5); package changed to the items-only interval; tolerance of 0.80 to 1.25 introduced in place of the planned rule (interval includes 1) | All results of the example |",
      "| evening | Transfer analysis rerun with version 0.2.0 (identical calibration slopes and reductions in log loss); cubic frequency function added | |", "",
      "![](../second_example/results/figures/figure_lexical_transfer.png)", "",
      "**Figure S1.** Ordering, calibration slope and reduction in log loss for the three measures and the three-measure model in each held-out megastudy. Dotted lines in the left panel mark the square root of the rank-scale reliability. This figure was drawn before the ordering interval was changed: its ordering intervals are the earlier ones from the bootstrap over participants and items, which are centred too low. The final intervals are in the table above.", "",
      "## 1.8 Mixed model in the simulation study (Table 6 of the article)", "",
      "Script `glmm/glmm_simulation.R`, files `glmm/glmm_simulation_raw.csv` (one row per data set) and `glmm/glmm_simulation_summary.csv`. Data were generated in R as in the base condition (four families, 48 items and 40 participants each, complete design, intercept 1, slope 0.5, item residual SD 0.5, ability SD 0.8), with the changes named in the scenario; 200 data sets per scenario, seeds 2610 to 2615. Mixed model: `y ~ 0 + family + x_training + x_heldout + (1 | participant) + (1 | item)` against `y ~ 0 + family + x + (1 | participant) + (1 | item)`, `lme4::glmer` with `nAGQ = 0` (a fast approximation in which the fixed effects are estimated in the penalised least-squares step) and optimiser bobyqa; likelihood-ratio test with 1 degree of freedom. The comparison without random effects uses the same fixed effects in `glm` and a likelihood-ratio test. All 1,200 fits returned estimates; none was excluded.", "",
      "| Scenario | Data sets | Ratio of slopes, mixed model (median) | Ratio, no random effects (median) | Equal slopes rejected, mixed model | Equal slopes rejected, no random effects |", "|---|---|---|---|---|---|"]
g = pd.read_csv(B / "glmm/glmm_simulation_summary.csv")
for _, r in g.iterrows():
    o.append(f"| {r.scenario} | {int(r.n)} | {r.glmm_ratio_median:.2f} | {r.glm_ratio_median:.2f} | {r.glmm_reject_equal:.3f} | {r.glm_reject_equal:.3f} |")
o += ["", "## 1.9 Where each table and figure of the article comes from", "",
      "| Article | Result files (repository folder `paper/`) | Script |", "|---|---|---|",
      "| Figure 1 | none (schematic) | `figures/make_schematic.py` |",
      "| Figures 2 to 4 | `sim/results/sim01_summary.csv`, `sim02_summary.csv`, `sim03_summary.csv` and the files of large-sample values | `sim/make_figures.py` |",
      "| Table 3 | `sim/results/tables/s3_bootstrap_comparison.csv` | `sim/make_tables.py` |",
      "| Table 4 | `sim/results/tables/ordering_interval.csv` | `sim/make_tables.py` |",
      "| Table 5 | `sim/results/tables/s6_comparators.csv` | `sim/make_tables.py` |",
      "| Table 6 | `glmm/glmm_simulation_summary.csv` | `glmm/glmm_simulation.R` |",
      "| Text on the tolerance rule and on the model without random effects | `sim/results/tables/s8_tolerance.csv`, `s7_noncollapsibility.csv` | `sim/sim08_tolerance.py`, `sim/sim07_noncollapsibility.py` |",
      "| Table 7 | `second_example/results/step3_transfer.csv`, `step2_reliability.csv` | `second_example/run_lexical.py` |",
      "| Table 8 | `second_example/results/step3_transfer.csv`, `sensitivity_transfer.csv`, `posthoc_nonlinear_frequency.csv` | `run_lexical.py`, `nonlinear_frequency.py` |",
      "| Figure 5 | `second_example/results/figure1_binned_accuracy.csv` | `second_example/figures_lexical.py` |",
      "| Table 9 | `knapsack_report/reliability.csv` | `itemtransfer/examples/knapsack.py` |",
      "| Table 10, Figure 6 | `knapsack_report/transfer.csv`, `weak_training.csv`, `predictions.csv` | `itemtransfer/examples/knapsack.py`, `figures/make_knapsack_figure.py` |",
      "| Knapsack diagnostics in the text | `knapsack_report/levels.csv`, `range.csv`, `weighting.csv`, `measure_correlations.csv`, `interval_check.csv`, `sensitivity_franco2024_evaluation.csv`, `glmm/glmm_knapsack_*.csv` | as above |", "",
      "# Part 2. Simulation study: full report (working document, 13 November 2026)", "",
      "Figure numbers in this part refer to the figures of the report: its Figures 1, 2 and 3 are Figures 2, 3 and 4 of the article; its Figures 4, 5 and 6 are shown at the end of this part. Sections S1 to S5 were run with version 0.1.0 of the package and S6 to S8 with version 0.2.0. Statements that were superseded are marked \"Status\".", "",
      demote(rd("sim/SIMULATION_REPORT.md")), ""]
for n, f in [(4, "fig4_bootstrap_comparison"), (5, "fig5_ranking"), (6, "fig6_tolerance_rule")]:
    o += [f"![](../sim/figures/{f}.png)", "", f"**Simulation report, Figure {n}.** {cap(n)}", ""]
o += ["# Part 3. Lexical decision example: analysis plan and report (working documents, 13 November 2026)", "",
      "The plan (3.1) is reproduced as it was written, with its dated list of deviations. The report (3.2) was compiled before the simulation study was complete. Three of its statements are superseded and the final versions are in Part 1: the intervals of the ordering correlation (now from resampled items), the rule for the calibration slope (now a tolerance instead of \"the interval includes 1\"), and the remark that a non-linear frequency function had not been tried (see 1.7).", "",
      "## 3.1 Analysis plan", "", demote(rd("second_example/PLAN.md"), 2), "",
      "## 3.2 Report", "", demote(rd("second_example/results/LEXICAL_REPORT.md"), 2), "",
      "# Part 4. Knapsack example: output of the software (version 0.2.0)", "",
      "The following report was written by `itemtransfer.report`. Column names are those of the software. Tables with more than nine columns are not reproduced here; they are in the CSV files of the repository.", "",
      demote(drop_wide_tables(rd("knapsack_report/report.md"), folder="paper/knapsack_report"), 2)]
text = "\n".join(o)
(Path(__file__).resolve().parent / "supplement.md").write_text(text)
print(len(text.split()))
