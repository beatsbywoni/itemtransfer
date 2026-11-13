# Analysis plan v1: instance complexity and human performance on the 0-1 knapsack problem across five public datasets

Status: **frozen on 2026-10-26 (KST)** after the author's approval of the decisions listed in §0.2. None of the analyses in §4 to §6 has been run on the outcome data. The SHA-256 hash of this file is recorded in `analysis_plan_v1_20261026.md.sha256` and in `reproducibility/hashes.sha256`; the hash establishes the integrity of the file, not its date, and there is no external time stamp. This plan supersedes the draft of 2026-10-16 (`analysis_plan_v1_draft_20261016.md`, SHA-256 b3e70446...644ce, kept for the record). Changes from the draft are listed in §9.

## 0. What had been seen before the freeze

### 0.1 Before the draft (2026-10-16)

- The published results of the source articles: Murawski and Bossaerts (2016; K1), Franco et al. (2021; K2), Franco et al. (2024; K4), Doroc et al. (2025; K5), Lu et al. (2025; K7) and Bowman et al. (2023; K8). They report, within each study, associations of instance complexity (IC), typical-case complexity (TCC) or Sahni-k with accuracy and time.
- Descriptive statistics of each data part computed during data preparation: participants, trials, mean accuracy, no-response counts and time-out shares (`output/report_3a2_tables.md`, `output/report_3a3_tables.md` §1).
- The per-instance success rates of the eight K1 instances in K1 Supplementary Table S2, read while checking the instance definitions.
- The distributions and intercorrelations of the instance measures, and their agreement with the authors' values (`output/report_3a3_tables.md` §2 to §4).

### 0.2 Between the draft and the freeze (2026-10-26), while checking the revision proposals

- Counts of timed-out and no-response trials per data part and per K5 session, and the number of answered and non-timed-out trials per instance (K5: median 54 non-timed-out trials per instance, minimum 41; K7 main: median 13, minimum 4; K7 pilot: median 2, minimum 0, all 120 instances below 5). The distribution of time-out shares over participants (K7 pilot: at least three quarters of the participants timed out on every trial).
- Participant-level accuracy, time-out share and no-response count in K5, used only to check whether the participant the authors excluded (P012, a cortisol outlier by their rule in `wrangling.Rmd`) differs behaviourally. P012 has accuracy .854 (rank 9 of 42), time-out share .40 and no no-response trial.
- The tie structure of the measures per data part (number of distinct values, instances in tied groups), without any outcome.
- A feasibility prototype of the two-way bootstrap and the logit-scale split-half reliability on synthetic data only.
- **Not seen:** any association between an instance measure and performance in the harmonised data, any split-half or cross-sample correlation of instance difficulty, any accuracy conditional on time-out status, and any model fit on the outcome data.

### 0.3 Decisions approved by the author on 2026-10-26

- No-response decision trials are excluded from the primary analyses; counting them as errors is a sensitivity analysis.
- K5 uses all 42 participants in the primary analyses. The authors excluded P012 because of a baseline cortisol value more than 3 SD from the group mean, which is a criterion of the stress manipulation and not of data quality; analyses of the 41 participants and of the 27 cortisol responders are sensitivity analyses.
- The K7 pilot sample is used only for the comparison of reliability between samples, not for training or evaluation in Q1.
- Sahni-k of the optimisation problem is the primary Sahni-k measure for decision instances as well.
- The six revisions of §9 (two-way bootstrap, logit-scale attenuation correction, fixed interpretation rules, time-out sensitivity, range restriction and coarse measures, the primary result defined as calibration slope and combined model) are adopted.
- Tentative target journal for length and style: Cognitive Science (Regular Article). The target is confirmed after the results are seen; this choice does not affect the analyses.

## 1. Questions

- **Q1 (transfer).** Does the relation between an instance measure and accuracy, estimated on some datasets, predict which instances are hard in a dataset with different instances, participants and setting, and does the size of the relation carry over?
- **Q2 (reliability of instance difficulty).** How reliable is the difficulty ranking of instances within a dataset, and how well does it carry over between samples and settings that used the same instances?
- **Q3 (comparison of measures).** Which measure accounts best for instance difficulty, and how much do the measures overlap?

## 2. Data

- Trial table `data_proc/trials_harmonized.csv` (SHA-256 bba42afb70d8b5ecdf87e3546041add969c1a5537b9006c1ddccdf110650c188) and instance table `data_proc/instance_metrics.csv` (SHA-256 88e0ddc4afd2dcf6d6a6c29114fedbda9b60c0f48c2589485823d687595d8914). Column meanings: `output/report_3a3_tables.md`. K1 instance-level success rates: `data_proc/k1_table_s2.csv` (SHA-256 d310621cec89503428ee689c7da51b717422c6cbd7af1e6b1c2967d62d795944). K5 responder list: `data_proc/k5_responders.csv` (SHA-256 8cc495887f5cb41ca23fc4e14dc06da72a4ae0cfa95efaefe6efa145e5412b81).
- **Data parts** (a data part is one dataset, variant and sample): K2 decision, K2 optimisation, K4 decision, K4 optimisation, K5 decision (two sessions per participant, control and stress), K7 decision main, K7 decision pilot, K8 optimisation (four sessions per participant: placebo PLC and three stimulants MPH, MOD, DEX).
- **Instance families** (sets of instances that no other family shares):

| Family | Variant | Data parts (evaluation part first) | Instances | Notes |
|---|---|---|---|---|
| F1 | decision | K2 (laboratory), K4 (fMRI) | 72 (K4: 56 of them) | 6 items; fixed 22 s exposure |
| F2 | decision | K5 (control and stress sessions) | 72 | 8 items; self-paced, up to 40 s |
| F3 | decision | K7 main (K7 pilot for Q2 only) | 120 | 6 items; self-paced, up to 25 s |
| O1 | optimisation | K2, K4 | 18 | 6 items; up to 60 s |
| O2 | optimisation | K8 (four drug sessions); K1 (instance level only) | 8 | 10 to 12 items; up to 240 s |

- **Trials used.** Decision: answered trials (`no_response` = 0), including those whose solving stage reached the time limit. Optimisation: every attempt, scored as in the source data (the final selection is optimal). No other exclusions in the primary analyses.
- **Instance accuracy** in a data part = correct trials / trials used, per instance. On the logit scale the empirical logit is used: log((correct + 0.5) / (trials used minus correct + 0.5)). The 0.5 is needed because small halves (K7 pilot) produce instances with no error or no correct trial.
- **Resampling units.** The participant is the unit of participant resampling, and all sessions of a participant travel with the participant (K5: both sessions; K8: all four). The instance is the unit of instance resampling, within its family (Q1) or within its data part (Q2, Q3).

## 3. Measures

Primary measures, one per construct, with the transformation fixed in advance (definitions in `code/metrics.py`):

| Construct | Variable | Expected direction (accuracy) |
|---|---|---|
| Instance complexity | `ic` (decision only) | higher IC, higher accuracy |
| Typical-case complexity | `tcc` (reference ensemble; for optimisation at p*) | higher TCC, lower accuracy |
| Sahni-k | `sahni_k_opt` | higher k, lower accuracy |
| Solver effort | log2(1 + `gecode_propagations`) | more effort, lower accuracy |

Secondary measures: `sahni_k_dec` (satisfiable instances only), log2(1 + `n_witness`), log2(1 + `gecode_nodes`), `value_weight_corr`, `input_size`, `alpha_c`, `alpha_p`.

**Range restriction and coarse measures (to be stated with the results).** K5 and K7 were designed with IC at two levels (K5: 36 instances in each band, .027 to .032 and .097 to .105; K7: 60 and 60, no instance between .05 and .12), so IC is bimodal there and has fewer distinct values than instances (K5: 58 of 72; K7: 100 of 120; K2 and K4: all distinct). Sahni-k is 0 for most decision instances (K2 51 of 72, K5 57 of 72, K7 93 of 120), and log solver effort has 13 to 33 distinct values per part. Rank correlations therefore rest on few distinct values for these measures; ties receive average ranks (the default of `scipy.stats.spearmanr`), and the number of distinct values is reported next to every rank correlation. Correlations across the two IC bands of K5 and K7 are driven by the band contrast; this is read as a feature of the source designs, not of the measure.

## 4. Analyses

### 4.1 Uncertainty

- **Primary intervals: two-way bootstrap.** 2,000 resamples (seed 20261016). In each resample, participants are drawn with replacement within each data part and instances are drawn with replacement within each family (Q1) or data part (Q2, Q3). Trials are aggregated to (data part, instance) counts with participant multiplicities, and instance multiplicities enter as frequency weights of the aggregated rows (rank correlations are computed on the expanded list of instances, duplicates included). Every fit is repeated in every resample. Intervals are the 2.5 and 97.5 percentiles. The two-way interval is the interval of every claim about instances (Q1 transfer, Q2 between samples, Q3).
- **Measurement precision: participant-only bootstrap.** The same 2,000 resamples with participants resampled and instances fixed, reported in a separate column as the precision with which the fixed instance set is measured. It is not used for claims about measures or instances.
- Split-half reliabilities (Q2 within a data part) use 1,000 random splits of the participants (seed 20261017).
- Estimates are reported with intervals; no result is called significant or not. The interpretation rules of §7 are fixed in advance.

### 4.2 Q1: transfer between families (decision; primary)

1. For each held-out family (F1, F2, F3), fit on the answered trials of the other two families a binomial model of correctness with one intercept per data part and one slope per measure: logit P(correct) = a_part + b m (each primary measure alone), and a model with all four primary measures: logit P(correct) = a_part + sum_j b_j m_j. Measures enter untransformed beyond §3. Fits use the aggregated counts (equivalent to the trial-level likelihood).
2. Linear predictor for the held-out instances: eta = b m or eta = sum_j b_j m_j (the intercepts do not enter the ranking).
3. In the evaluation part of the held-out family (K2; K5 pooled over sessions; K7 main):
   - Spearman correlation between eta and instance accuracy (sign as learned; a negative value means the learned direction reversed);
   - **calibration slope**: a binomial model of the held-out trials on eta with a free intercept (1 = the effect size carries over, 0 = nothing carries over; above 1 = the relation is steeper in the held-out family).
4. Report each fold and the mean over the three folds, with two-way and participant-only intervals; paired bootstrap differences between the four single-measure models (six pairs) and between each single-measure model and the combined model, on the same resamples.
5. Next to each transfer correlation, report the split-half reliability of instance accuracy in the evaluation part (Q2, logit scale and Spearman) as a descriptive reference for the ceiling of the correlation; it is not a derived bound.

**Primary result of Q1.** For a single measure the correlation in step 3 equals the within-family correlation of the measure with accuracy, signed by the slope learned in training; it carries the sign but not the size of the learned relation. The primary result of Q1 is therefore (i) the calibration slope of each single-measure model and (ii) the transfer correlation and calibration slope of the combined four-measure model. Single-measure transfer correlations are reported as descriptive.

### 4.3 Q2: reliability of instance difficulty

1. **Within each data part:** K2, K4, K5 (each session, and both sessions pooled), K7 main, K7 pilot, K2 optimisation, K4 optimisation, K8 (placebo session, and all sessions pooled). 1,000 random splits of the participants into halves. In each split, instance accuracy in each half; instances with no trial in a half are dropped from that split and the count is recorded. Two reliabilities per split:
   - **logit scale (primary, used for attenuation correction):** Pearson correlation of the empirical logits between halves, corrected with the Spearman-Brown formula;
   - **rank scale (descriptive):** Spearman correlation of the accuracies between halves, corrected with the Spearman-Brown formula.
   Report the median and the 2.5 and 97.5 percentiles over splits.
2. **Between samples or settings** on shared instances: Pearson correlation of the empirical logits and Spearman correlation of the accuracies, with two-way bootstrap intervals (participants within each part, instances within the shared set), and the **attenuation-corrected correlation** r_c = r_logit / sqrt(rel_A rel_B), where rel_A and rel_B are the logit-scale split-half reliabilities of the two parts. The point estimate uses the medians of step 1; inside each bootstrap resample the reliabilities are recomputed as the mean over 10 random splits of the resampled participants. The correction is applied on the logit Pearson scale only, because the Spearman-Brown and attenuation formulas are derived for product-moment correlations of the measured scores; the corrected value can exceed 1 and is reported as computed. The Spearman correlation is reported uncorrected.

| Comparison | Instances | Relation of the two samples |
|---|---|---|
| K2 versus K4, decision | 56 | laboratory versus fMRI; independent participants |
| K2 versus K4, optimisation | 18 | independent participants |
| K5 control versus K5 stress | 72 | same participants (the participant bootstrap keeps both sessions together) |
| K7 main versus K7 pilot | 120 | independent participants |
| K8 placebo versus each drug session | 8 | same participants |
| K1 versus K8 placebo | 8 | independent participants; K1 from Table S2, without an interval on the K1 side |

3. **Time-out share as an instance property** (self-paced decision parts K5, K7 main, K7 pilot): split-half reliability of the per-instance time-out share, as in step 1 (logit of the share, and Spearman), and its between-sample correlation for K5 sessions and K7 main versus pilot.

### 4.4 Q3: comparison of the measures

1. Within each evaluation part (K2, K4, K5 pooled, K7 main): Spearman correlation of each primary and secondary measure with instance accuracy, and the deviance explained (1 minus residual deviance / null deviance of the aggregated binomial model with one intercept) by a model with that measure. Two-way bootstrap intervals (participants within the part, instances within the part).
2. In a model with all four primary measures: the deviance lost when each measure is dropped (its unique contribution), as a share of the null deviance; paired bootstrap differences between the four unique contributions.
3. Overlap: Spearman correlations among the measures (already tabulated), and among the Q1 predictions (eta) of the four single-measure models in each held-out family.

### 4.5 Secondary outcome: time

- Self-paced decision data (K5 pooled, K7 main): log time on task of answered trials, instance means (including timed-out trials, whose time equals the limit; the share of such trials is reported).
- Within-part split-half reliability (Pearson of instance mean log time, Spearman-Brown) and between-sample correlations (K5 sessions; K7 main versus pilot), with intervals as in Q2.
- Transfer between F2 and F3 (two folds): a linear model of instance mean log time on each primary measure, fitted in one family, predicts the other; Spearman correlation and calibration slope (linear regression of the held-out instance means on the prediction) with two-way intervals.
- Fixed-exposure data (K2, K4) are not used for time; their answer latency is reported descriptively.

### 4.6 Secondary variant: optimisation

- O1 (K2 and K4 optimisation, 18 instances) and O2 (K8 all sessions, 8 instances): Spearman correlation of TCC, Sahni-k and solver effort with instance accuracy, with two-way intervals.
- Transfer O1 to O2 and O2 to O1, as in Q1 (binomial model with part intercepts; IC is not defined for optimisation, so three measures and the three-measure combined model).
- With 18 and 8 instances these results are reported as descriptive, and no interpretation rule of §7 is applied to them.

## 5. Sensitivity analyses

Each sensitivity analysis repeats Q1 (fold summaries and combined model), Q2 (the affected within-part reliabilities and between-sample correlations) and Q3 (deviance explained), unless stated otherwise.

1. No-response decision trials counted as errors.
2. K5 restricted to the 41 participants the authors analysed, and to the 27 cortisol responders.
3. K7 without the 13 instances whose target exceeds the sum of all values (alpha_p > 1).
4. F1 evaluated on K4 instead of K2.
5. TCC from a dataset-specific ensemble: integer weights and values drawn uniformly over the item range observed in that dataset, with the same n, alpha_c and profit coordinate (20,000 draws, seeded as in `metrics.py`), replacing the reference-ensemble TCC.
6. Trial-level models with crossed random intercepts for participants and instances (statsmodels `BinomialBayesMixedGLM`) for the Q1 training fits and the Q3 single-measure models, instead of the aggregated fits; reported as a check on the fixed-effect slopes.
7. **Timed-out trials excluded** (self-paced decision parts K5 and K7 main): Q1 with the evaluation and training trials of these parts restricted to trials that ended before the limit, Q2 within-part reliabilities and the K5 between-session correlation, and Q3. This is not run for the K7 pilot, where fewer than 5 non-timed-out trials remain for every instance; the K7 main versus pilot reliability comparison is therefore reported with the limitation that pilot responses were mostly given at the time limit.

Deviations from this plan are reported with their reason in a separate table of the supplement, and analyses added after the freeze are labelled exploratory.

## 6. Placement in the article

- Main text: Q1 (table and figure of calibration slopes and transfer correlations by measure and fold, with the combined model), Q2 (figure of within-part reliabilities and between-sample correlations, corrected and uncorrected), Q3 (table of deviance explained and unique contributions).
- Supplement: time, optimisation, sensitivity analyses, participant-only intervals, measure definitions and agreement with the authors' values, the deviation table.

## 7. Interpretation rules (fixed before the results)

The following wordings are used in the manuscript, and no others, for the primary analyses:

- "The relation **transfers**" (for a measure and fold, or for the fold mean): the two-way interval of the calibration slope excludes 0.
- "The relation **transfers in full**": the two-way interval of the calibration slope includes 1 and excludes 0.
- "The relation **does not transfer**": the two-way interval of the calibration slope includes 0.
- "The relation **reverses**": the two-way interval of the calibration slope lies entirely below 0.
- "Measure A **accounts for instance difficulty better than** measure B" (within a part, or in transfer): the two-way interval of the paired difference (deviance explained, calibration slope or transfer correlation, as named) excludes 0 in A's favour. Otherwise: "the measures were **not distinguished**"; if the point estimate differs, "A was larger in the point estimate, but the interval of the difference included 0".
- "Instance difficulty is **reliable**" within a part: the split-half interval (logit scale) lies above .70; "**moderately reliable**": the median is above .50 and the interval includes .70; otherwise "**unreliable**". These cut-offs are conventions for description and are stated as such.
- "Instance difficulty **carries over between samples**": the two-way interval of the uncorrected logit correlation excludes 0; "**carries over in full**": the corrected correlation's interval includes 1.
- Results of the secondary analyses (time, optimisation) and sensitivity analyses are described with the same words only when the corresponding interval condition holds; otherwise they are described as "consistent with" or "not consistent with" the primary result, by whether the primary point estimate lies in the sensitivity interval.
- Effect sizes are reported as numbers; words such as "strong", "robust" and "substantial" are not used for them.

## 8. Software

Python with the packages pinned in `requirements.txt` (reference environment: macOS, Python 3.11.9); the development environment of the freeze session was Linux, Python 3.10.12, scipy 1.15.3, statsmodels 0.15.0. Final numbers are produced in one environment, recorded in `results/environment.json`, and checked by a second run whose outputs must agree to the reported precision. MiniZinc 2.9.3 with Gecode 6.3.0 for solver effort (already computed; not rerun). Scripts: `code/12_q1_transfer.py`, `13_q2_reliability.py`, `14_q3_measures.py`, `15_secondary.py`, `16_sensitivity.py`, run by `code/run_3b.sh`; results in `results/*.csv` and `results/numbers.json`.

## 9. Changes from the draft of 2026-10-16

| # | Change | Reason |
|---|---|---|
| 1 | Primary intervals resample participants and instances (two-way); participant-only intervals reported as measurement precision (§4.1) | Q1 transfer, Q2 between samples and Q3 are claims about instances; resampling only participants omits instance sampling variation |
| 2 | Attenuation correction on the logit Pearson scale with logit-scale split-half reliabilities; Spearman reported uncorrected; corrected values may exceed 1 (§4.3) | Spearman-Brown and the attenuation formula are derived for product-moment correlations, not rank correlations |
| 3 | Interpretation rules fixed (§7) | To prevent the framing from depending on the results |
| 4 | Sensitivity analysis 7 (timed-out trials excluded) and time-out share as an instance property (§4.3 step 3) | Time-out shares are .342 (K5), .436 (K7 main) and .832 (K7 pilot); responses at the limit may be closer to guesses |
| 5 | Statement on range restriction, ties and coarse measures (§3); distinct values reported with rank correlations | IC is two-banded in K5 and K7; Sahni-k and solver effort have few distinct values |
| 6 | Primary result of Q1 defined as calibration slopes and the combined model; single-measure transfer correlations descriptive (§4.2) | A single-measure transfer correlation carries only the sign of the learned slope |
| 7 | Empirical logit with 0.5 added (§2) | Small halves produce instance accuracies of 0 or 1 |
| 8 | Reliabilities inside the bootstrap recomputed from 10 splits per resample (§4.3) | To give the corrected correlation an interval at acceptable cost |
| 9 | K7 pilot excluded from Q1 training and evaluation (§2) | Decision 0.3; most pilot responses were given at the time limit |
| 10 | Optimisation transfer uses three measures (§4.6) | IC is not defined for optimisation |
