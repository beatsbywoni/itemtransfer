# Simulation study: what leave-one-family-out transfer validation can and cannot show

Status: all runs finished on 13 November 2026. Every number below comes from a file in `results/`
(`*_summary.csv`, `*_targets.csv`, `tables/*.md`); the scripts that made them are `sim00` to `sim08`, the figures
are in `figures/` (captions in `figures/captions.md`). Rates are followed by their Monte Carlo standard error in
parentheses, as recommended by Morris, White and Crowther (2019).

## Questions

The procedure judges a measure on a held-out item family by three criteria: ordering (Spearman correlation
between the transferred predictor and item accuracy), scale (calibration slope) and prediction (relative
log-loss reduction with the intercept calibrated on half of the held-out items). The simulation asks five
questions that do not depend on a particular task.

1. Do the three criteria respond to different properties of the data, and when do they disagree?
2. Which features of the held-out family (designed levels, range of the measure, reliability of item
   difficulty) change what a criterion can show?
3. Do the bootstrap intervals have the coverage they claim, how often is a real relation detected, and how often
   is a relation "detected" for a measure without one?
4. Does the measure that fits better within the training families also transfer better?
5. (Added during the work, on request.) Should the interval of the ordering criterion be a percentile interval
   or a basic (reflected) interval?
6. to 8. (Added after an internal review.) What does the procedure give beyond grouped cross-validation, a test
   of slope heterogeneity and a random-effects meta-analysis (S6); how far can the calibration slope move when
   only the variances or the mean accuracy of a family differ (S7); and what are the error rates of the
   tolerance rule for the calibration slope (S8)?

## Common design

Data are generated for one participant j and one item i of a family as

    logit P(correct) = intercept + slope x g(measure_i) + d_i + u_j,

with item residuals d ~ N(0, item residual SD) and participant effects u ~ N(0, participant SD). The item
residual stands for everything that makes items differ in difficulty and that the measure does not capture.
Slopes are in logits per standard deviation of the measure: 0.25 (weak), 0.5 (medium), 1 (strong). The sign is
chosen so that a higher measure means a harder item; all slopes are reported as magnitudes.

**Base case.** Four item families (one held out, three for training), one sample per family, 48 items and 40
participants per family (every participant responds to every item), measure standard normal, slope 0.5, item
residual SD 0.5, participant SD 0.8, intercept 1 (mean accuracy about .70). In the base case the measure
accounts for half of the true variance of item difficulty on the logit scale.

**Analysis.** Each simulated data set is analysed with the functions of the package `itemtransfer` that
`transfer()` itself calls, for the one designated held-out family (families are exchangeable unless a study
makes the held-out family different, so one fold per data set suffices and keeps replications independent).
Intervals are 95% percentile intervals of the two-way bootstrap (participants within samples, items within
families) with 500 resamples; the prediction criterion uses 100 item splits for the estimate and 10 inside each
resample. `sim00_validate.py` confirms that this engine returns exactly the numbers of the public `transfer()`
and `diagnose()` on the same data (largest difference 3e-17), and that `check_intervals()` on the equivalent
package `Design` gives the same operating characteristics (coverage .977 against .997, detection .997 against
.993, 300 data sets each).

**Large-sample targets.** For every cell the value of each statistic for very many items and participants was
computed explicitly: 120,000 items per family (60,000 for ten families), the participant distribution
integrated out by Gauss-Hermite quadrature (61 nodes), three independent item sets. The targets are saved in
`results/*_targets.csv` with their standard deviation over item sets (calibration slope in the base case:
1.0007, SD 0.003; log-loss reduction: 0.0299, SD 0.0001). The log-loss reduction is a trial-level quantity, so
its target does not depend on the number of trials per item. The ordering correlation does: its large-sample
value is the correlation with error-free item accuracies, which no finite sample attains (see S2c and S5).

**Number of bootstrap resamples.** For 150 base-case data sets, intervals from 250, 500, 1,000 and 2,000
resamples were compared with intervals from 4,000 resamples. With 500 resamples an end point moves by 4.3% of
the interval width (root mean square; 3.6% for the log-loss reduction), and the question "does the interval
contain the target" changed its answer in 2 of 150 data sets (`results/sim00_bootstrap_size.csv`). This noise
is small against the effects reported below, so 500 resamples were used throughout.

**Performance measures.** Coverage (share of intervals that contain the target), detection rate (share of
intervals that exclude 0 for the calibration slope, or lie above 0 for the log-loss reduction and the ordering
correlation), false-positive rate (the same for a measure without relation), median interval width, and the mean
or median of the estimates. Monte Carlo standard errors of rates are sqrt(p(1 - p) / n). With 1,000
replications the standard error of a coverage near .95 is .007 and that of a rate near .50 is .016.

### Design table

| Study | Varied | Fixed | Cells | Replications per cell | Bootstrap |
|---|---|---|---|---|---|
| S1 Separation of the criteria | held-out slope as a multiple of the training slope (-1, 0, 0.25, 0.5, 1, 2); null measure; proxy measure correlated .7 with the true measure in the training families only, in the held-out family only, or everywhere; training slope 0, 0.05, 0.125, 0.25 with held-out slope 0.5 | base case | 10 | 1,000 (2,000 in the common-slope cell) | two-way, 500 |
| S2a Level structure | measure in the held-out family continuous, four levels or two levels; true relation graded or a step; 48 items and 40 participants, or 96 and 80 | 4 families, training measure continuous, effect SD 0.5 | 12 | 1,000 (500 for the larger design) | two-way, 500 |
| S2b Range mismatch | relation linear, logarithmic or saturating in the measure; held-out range 1 to 4 (as training), 2 to 8, 1 to 8 | 4 families, 48 items, 40 participants, effect SD 0.5 in training | 9 | 1,000 | two-way, 500 |
| S2c Reliability | participants 10, 20, 40, 80; item residual SD 0, 0.5, 1 | 4 families, 48 items, slope 0.5 | 12 | 2,000 | none |
| S3 Operating characteristics | one factor at a time: families 3, 4, 6, 10; items 24, 48, 96, 192; participants 20, 40, 80; slope 0.25, 0.5, 1; item residual SD 0, 0.5, 1; participant SD 0, 0.8, 1.6. Factorial: items (24, 96) x slope (0.25, 1) x item residual SD (0, 1). Two small designs. Slope differing between families (4 cells) | base case | 29 | 1,000 | two-way, 500; in 15 cells also participants-only and items-only |
| S4 Fit and transfer | two measures whose validities are fixed per family, random per family, or equal with a family-specific unit; 3, 4, 6, 10 families | 48 items, 40 participants (two cells 96 and 80), latent slope 1, item residual SD 0.5 | 28 | 2,000 | none |
| S6 Comparison with other analyses | nine scenarios (common slope; held-out intercept 2 or 0; held-out slope x 0.5 or x 2; step relation with two-level held-out family; saturating relation with shifted range; no relation with item residual SD 0.5 or 1) | base case | 9 | 1,000 | two-way, 500 |
| S7 Non-collapsibility | held-out family only: participant SD 0, 0.8, 1.6, 2.4; item residual SD 0, 0.5, 1, 1.5; intercept -0.5, 0, 1, 2, 3 | base case, identical conditional slope | 13 | large-sample values; 500 data sets for two cells | two-way, 500 |
| S8 Tolerance rule | true calibration slope 0.5 to 2 (seven values); held-out items 48, 192, 768; all families 192 or 768 items | 4 families, 40 participants | 27 | 1,000 (48 or 192 held-out items), 300 otherwise | two-way and items-only, 500, 95% and 90% |
| S5 Ordering interval | items 48, 192, 768, 3,072; participants 20, 40, 80; item residual SD 0 or 0.5; slope 0.5 or 1 | 4 families | 8 | 500 (48 and 192 items), 300 or 200 (768 and 3,072 items) | two-way and items-only, 500, no prediction criterion |

The full table with scripts and outputs is `results/tables/design_table.md` (and `.csv`).

## S1. The criteria respond to different things

**Design.** Base case. (a) The same slope in all families. (b) The slope in the held-out family is the
training slope times -1, 0, 0.25, 0.5 or 2. (c) A null measure. (d) A proxy measure with no effect of its own
that correlates .7 with the true measure in all families, only in the training families, or only in the
held-out family. (e) A training slope of 0, 0.05, 0.125 or 0.25 with a held-out slope of 0.5.

**Results (Figure 1; `results/tables/s1_separation.md`).**

| Condition | Ordering, mean | Calibration slope, median (5% to 95%) | Log-loss reduction, mean | Slope interval excludes 0 | Log-loss interval above 0 | below 0 |
|---|---|---|---|---|---|---|
| same slope | .596 (.002) | 1.01 (0.66 to 1.40) | .0308 (.0003) | .993 (.002) | .482 (.011) | .000 |
| held-out slope x 2 | .823 (.002) | 2.03 (1.57 to 2.61) | .0832 (.0006) | 1.000 | 1.000 | .000 |
| held-out slope x 0.5 | .348 (.004) | 0.49 (0.20 to 0.85) | -.0007 (.0004) | .543 (.016) | .006 (.002) | .006 (.002) |
| held-out slope x 0.25 | .190 (.004) | 0.25 (-0.05 to 0.59) | -.0160 (.0004) | .144 (.011) | .000 | .092 (.009) |
| held-out slope 0 | -.004 (.005) | -0.01 (-0.32 to 0.33) | -.0341 (.0005) | .024 (.005) | .000 | .500 (.016) |
| held-out slope reversed | -.595 (.003) | -1.01 (-1.42 to -0.68) | -.0964 (.0009) | .989 (.003) | .000 | 1.000 |
| null measure | -.005 (.003) | -0.10 (-10.8 to 11.0) | -.0007 (.0001) | .001 (.001) | .000 | .003 (.001) |
| proxy, r = .7 everywhere | .419 (.003) | 1.02 (0.48 to 1.78) | .0147 (.0002) | .804 (.009) | .201 (.009) | .000 |
| proxy, r = .7 in training only | .003 (.003) | 0.02 (-0.56 to 0.59) | -.0158 (.0003) | .025 (.004) | .000 | .176 (.009) |
| proxy, r = .7 in held-out only | -.017 (.010) | -2.14 (-43.0 to 43.3) | -.0008 (.0001) | .013 (.003) | .001 (.001) | .011 (.002) |

1. With a common slope the three criteria agree in expectation (calibration slope 1.01, target 1.00), but not in
   their verdicts: the interval of the calibration slope excluded 0 in 99.3% (0.2) of the data sets and the
   interval of the ordering correlation lay above 0 in 97.7% (0.3), whereas the interval of the log-loss
   reduction lay above 0 in only 48.2% (1.1). A medium relation that transfers perfectly improves trial-level
   prediction by about 3%, and the base design cannot reliably tell 3% from 0.
2. The calibration slope recovers the ratio of the held-out slope to the training slope (medians 2.03, 0.49,
   0.25, -0.01 and -1.01 for ratios 2, 0.5, 0.25, 0 and -1; coverage of the large-sample target between .976
   and .991). Ordering does not show the ratio: it only becomes weaker or stronger because the same residual
   noise meets a smaller or larger signal (.35 at ratio 0.5, .82 at ratio 2).
3. The prediction criterion is not a monotone companion of the other two. Its large-sample value is 0 when
   the held-out slope is half the training slope, and negative below that (-.015 at ratio 0.25, -.031 at ratio
   0): a transferred slope that is more than twice too steep predicts worse than no measure at all, although
   the measure still orders the held-out items (ordering .19 to .35). To a first approximation the gain is
   proportional to 2c - 1, where c is the calibration slope. Reported next to a calibration slope below 0.5, a
   negative log-loss reduction is therefore a consequence of the scale, not separate evidence against the
   measure.
4. A null measure fails all three criteria, and the false-positive rates are far below nominal: 0.1% (0.1) for
   the calibration slope, 0.0% for the log-loss reduction, 0.0% for ordering. Its calibration slope is
   arbitrary (5th to 95th percentile -10.8 to 11.0) and the weak-training flag was raised in 97.4% (0.4) of the
   data sets.
5. Collinearity by design. A proxy that correlates .7 with the true measure everywhere appears to transfer:
   training slope -0.29, calibration slope 1.02, interval excluding 0 in 80.4% (0.9). Where the correlation
   exists only in the training families the same proxy has a clear training slope (-0.30, flagged in 0.1% of the data sets) and
   fails in the held-out family on all three criteria (calibration slope 0.02; log-loss interval below 0 in
   17.6% (0.9)). Where it exists only in the held-out family there is nothing to transfer (flag in 98.1%). The
   procedure reports where a correlation with the effective measure exists; it cannot say which measure is
   the effective one. Only a family in which the two measures are uncorrelated separates them.
6. Weak training relation. With a true training slope of 0.05 and a held-out slope of 0.5 the large-sample
   calibration slope is 9.95, the median estimate 6.5, the 5th to 95th percentile -42.9 to 49.9, and 80% of
   the estimates exceed 5 in absolute value; ordering drops to .38 (target .69) because the sign of the
   trained slope is wrong in part of the data sets. The flag (interval of the training slope includes 0) was
   raised in 94.0% (0.8) of these data sets, in 59.1% (1.6) at a training slope of 0.125 and in 2.3% (0.5) at
   0.25. Among flagged data sets 85% (slope 0.05) and 57% (slope 0.125) of the calibration slopes exceeded 5 in
   absolute value; among unflagged ones 5% and 1%. The flag removes the wild values. It also selects: the
   unflagged data sets are those in which the training slope happened to be overestimated, so their
   calibration slopes are too small (median 3.2 against a target of 9.95 at slope 0.05).

**What a user should take from this.** Read the three criteria as answers to three questions and expect
disagreement of two kinds: a clear ordering with a prediction interval that includes 0 (low power of the
prediction criterion), and a clear ordering with a negative log-loss reduction (calibration slope below about
0.5). Do not interpret a calibration slope when the weak-training flag is raised. Do not read transfer of a
measure as evidence that this measure, rather than a correlate, drives difficulty.

**Limitations.** One design size; proxy correlation .7 only; slopes differ only in the held-out family; the
measure is normal and the relation linear.

## S2. Design features of the held-out family

### S2a. Designed levels

**Design.** Training families have a continuous measure. In the held-out family the measure is continuous,
takes four designed levels or takes two designed levels (same standard deviation; items within a level differ
slightly, as in real designs). The true relation is graded (linear in the measure) or a step (items above the
middle of the range are harder by a fixed amount, with no graded effect), with the same effect standard
deviation of 0.5 logits. The level-indicator baseline of `diagnose()` fits one probability per level in the
calibration half of the held-out items.

**Results (Figure 2A and 2B; `results/tables/s2a_levels.md`).**

| True relation | Held-out measure | Ordering, measure | Ordering, level indicator | Ordering within levels | Calibration slope, median | Indicator minus measure, log loss (48 / 40) | (96 / 80) | Indicator better, rate (96 / 80) |
|---|---|---|---|---|---|---|---|---|
| graded | continuous | .618 (.003) | .543 (.003) | .355 (.004) | 1.01 | -.0103 (.0002) | -.0089 (.0002) | .012 (.005) |
| graded | four levels | .620 (.003) | .630 (.003) | .056 (.005) | 1.00 | -.0074 (.0001) | -.0026 (.0001) | .048 (.010) |
| graded | two levels | .574 (.003) | .642 (.003) | .047 (.005) | 1.00 | -.0019 (.0001) | -.0008 (.0000) | .154 (.016) |
| step | continuous | .552 (.003) | .575 (.003) | .109 (.005) | 1.03 | -.0003 (.0002) | .0024 (.0002) | .690 (.021) |
| step | four levels | .557 (.003) | .576 (.003) | -.000 (.005) | 1.03 | -.0001 (.0002) | .0039 (.0002) | .892 (.014) |
| step | two levels | .560 (.003) | .646 (.003) | -.001 (.005) | 1.14 | -.0012 (.0001) | -.0002 (.0001) | .346 (.021) |

(For the continuous measure the two halves of a median split serve as levels.)

1. In a two-level family the ordering criterion "succeeds" equally under both truths: .574 (graded) and .560
   (step), with the interval above 0 in 97.7% and 98.4% of the data sets. The whole correlation is carried by
   the contrast between the levels: the level indicator orders the items better than the measure (.642 and
   .646), and within the levels the measure hardly orders them even when the true relation is graded (.047),
   because the range within a level is too small.
2. A two-level family cannot distinguish a graded relation from a step by any output of the procedure. The
   difference in log-loss reduction between indicator and measure is -.002 under the graded truth and -.001
   under the step truth with 48 items, and -.0008 against -.0002 with 96 items and 80 participants. The one
   trace of the step is a calibration slope above 1 (large-sample value 1.15, median 1.14), which a user would
   read as "effect somewhat stronger here", and whose interval included 1 in 96.3% (0.6) of the data sets.
3. With four levels or a continuous measure the comparison becomes informative, but only with enough data.
   Under a step truth the level indicator predicts better than the measure in 89.2% (1.4) of the data sets
   with four levels at 96 items and 80 participants, against 44.9% (1.6) at 48 and 40; under a graded truth it
   does so in 4.8% (1.0) and 3.6% (0.6). Within-level correlations of a continuous measure are .36 under the
   graded and .11 under the step truth.
4. The level indicator is at a disadvantage that should be kept in mind: it estimates one parameter per level
   on half of the held-out items, which costs .007 in log-loss reduction with four levels and 48 items even
   when the measure is exactly right.

**What a user should take from this.** A held-out family with two designed levels supports "items at the
high level are harder than items at the low level, by about the amount the trained slope predicts" and nothing
about the form of the relation between or within levels. A graded relation needs a family with at least four
levels or a continuous measure, and then a comparison with the level indicator and the within-level
correlations.

**Limitations.** One step location (the middle of the range), equal numbers of items per level, one effect
size.

### S2b. Range of the measure under a non-linear relation

**Design.** The measure is uniform on 1 to 4 in the training families and on 1 to 4, 2 to 8 or 1 to 8 in the
held-out family. The true effect is linear in the measure, in its logarithm, or saturating (1 - exp(-measure /
2)), with the same mechanism and the same coefficients in all families. Three analyses: the measure as given,
all families restricted to the common range, and the logarithm of the measure.

**Results (Figure 2C; `results/tables/s2b_range.md`).** Large-sample calibration slopes, with the share of
intervals that included 1 (48 items, 40 participants) in parentheses:

| True relation | Held-out range | Measure as given | Common range | Logarithm of the measure |
|---|---|---|---|---|
| linear | 1 to 4 | 1.00 (.983) | | 1.00 (.984) |
| linear | 2 to 8 | 1.01 (.988) | 1.00 (.978) | 1.92 (.047) |
| linear | 1 to 8 | 1.01 (.985) | 1.00 (.975) | 1.57 (.279) |
| logarithmic | 1 to 4 | 1.00 (.990) | | 1.00 (.991) |
| logarithmic | 2 to 8 | 0.51 (.251) | 1.00 (.982) | 0.99 (.988) |
| logarithmic | 1 to 8 | 0.60 (.413) | 1.00 (.983) | 1.00 (.986) |
| saturating | 1 to 4 | 1.00 (.984) | | 1.00 (.989) |
| saturating | 2 to 8 | 0.34 (.036) | 1.00 (.989) | 0.69 (.835) |
| saturating | 1 to 8 | 0.47 (.092) | 1.00 (.982) | 0.80 (.895) |

1. With an identical mechanism in all families, a held-out family that covers another range has a
   calibration slope of 0.51 (logarithmic) or 0.34 (saturating), and the interval excluded 1 in 75% and 96%
   of the data sets. A user would conclude that the effect is weaker in the held-out family. Under the
   saturating relation the log-loss reduction is negative as well (-.032; mean estimate -.036 (.001)). Ordering
   is not affected in this way (.60 and .45), which is the pattern "ordering holds, scale fails".
2. Restricting all families to the common range restores a calibration slope of 1.00 in every case, for any
   form of the relation, but at a price: with ranges 1 to 4 and 2 to 8, a third of the items remain (16 of 48
   held-out items on average) and the median interval width grows from about 0.6 to about 5.1; with a
   held-out range of 1 to 8, 43% of the held-out items remain (20.6 of 48) and the width grows from about 0.6
   to about 1.7.
3. A transformed measure restores a slope of 1.00 only when the transformation is the right one (the logarithm
   under the logarithmic relation); under the saturating relation the logarithm gives 0.69 and 0.80, and under
   a linear relation it creates a mismatch that was not there (1.92 and 1.57).
4. When both ranges agree, none of this matters: all calibration slopes are 1.00.

**What a user should take from this.** A calibration slope far from 1 in a family with a different range of
the measure is evidence about the scale of the measure as much as about the family. Report the calibration
slope on the common range next to the unrestricted one, expect a wide interval there, and try the candidate
transformations that theory suggests; if no range is shared, the two explanations cannot be separated.

**Limitations.** Two non-linear forms; uniform measure; the common-range remedy was applied with the true
overlap.

### S2c. Reliability of item difficulty

**Design.** Base case with 10, 20, 40 or 80 participants (trials per item) and item residual SD 0, 0.5 or 1.
For every data set the ordering criterion was also computed against the error-free accuracies of the same
items, and the split-half reliability of item difficulty of the held-out sample (step 2 of the procedure, rank
scale, Spearman-Brown corrected, 200 splits) was used to correct the observed ordering.

**Results (Figure 2D; `results/tables/s2c_reliability.md`).**

| Participants | Item residual SD | Reliability | Ordering observed | Without response noise | Observed / noise-free | Mean sqrt(reliability) | Corrected |
|---|---|---|---|---|---|---|---|
| 10 | 0 | .281 (.004) | .531 (.002) | 1.000 | .53 | .54 | 1.128 (.018) |
| 20 | 0 | .451 (.003) | .664 (.002) | 1.000 | .66 | .67 | 1.034 (.010) |
| 40 | 0 | .618 (.002) | .780 (.001) | 1.000 | .78 | .78 | 0.998 (.002) |
| 80 | 0 | .761 (.001) | .865 (.001) | 1.000 | .87 | .87 | 0.992 (.001) |
| 10 | 0.5 | .445 (.003) | .464 (.003) | .679 (.002) | .68 | .66 | 0.721 (.005) |
| 20 | 0.5 | .613 (.002) | .535 (.002) | .675 (.002) | .79 | .78 | 0.686 (.003) |
| 40 | 0.5 | .758 (.001) | .594 (.002) | .677 (.002) | .88 | .87 | 0.682 (.002) |
| 80 | 0.5 | .862 (.001) | .633 (.002) | .679 (.002) | .93 | .93 | 0.682 (.002) |
| 10 | 1 | .654 (.002) | .342 (.003) | .415 (.003) | .82 | .81 | 0.423 (.004) |
| 20 | 1 | .787 (.001) | .373 (.003) | .416 (.003) | .90 | .89 | 0.420 (.003) |
| 40 | 1 | .881 (.001) | .399 (.003) | .423 (.003) | .94 | .94 | 0.425 (.003) |
| 80 | 1 | .934 (.000) | .413 (.003) | .427 (.003) | .97 | .97 | 0.427 (.003) |

1. The ordering criterion is attenuated by response noise exactly as classical test theory says: the ratio of
   the observed to the noise-free ordering equals the mean square root of the reliability to within .023 in all
   twelve cells (the largest difference, .684 against .661, is at 10 participants and item residual SD 0.5) (for example .53 against .54 with 10 participants and a measure that explains all true
   variance, .88 against .87 in the base case).
2. A measure that is the only source of difficulty (item residual SD 0) reaches an ordering of only .53 with
   10 participants and .78 with 40. Without the reliability ceiling this would be read as a mediocre measure.
3. Dividing by the square root of the reliability recovers the noise-free value on average when the
   reliability is at least about .6 (.682 against .677 in the base case; .998 against 1.000). With low
   reliability the correction overshoots and becomes erratic: 1.13 on average with 10 participants and item
   residual SD 0, reliability not positive in 6% of the data sets, and corrected values above 1 in 43%.
4. With many participants the ordering criterion is limited by the item residual, not by noise: .43 at item
   residual SD 1 however many participants respond. More participants cannot raise an ordering that is low
   because items differ for reasons the measure does not capture.

**What a user should take from this.** Report the ordering criterion with the reliability of the held-out
sample, and the corrected value when the reliability is above about .6. Below that, the right conclusion is
that the sample cannot test the measure.

**Limitations.** All participants respond to all items; reliability was computed in the held-out sample
only; no differences between participants in the effect of the measure.

## S3. Operating characteristics of the intervals

**Design.** Base case, one factor at a time (families 3, 4, 6, 10; items 24, 48, 96, 192; participants 20,
40, 80; slope 0.25, 0.5, 1; item residual SD 0, 0.5, 1; participant SD 0, 0.8, 1.6), a factorial of items (24,
96), slope (0.25, 1) and item residual SD (0, 1), two small designs (3 families, 24 items, 20 participants, item
residual SD 1), and four cells in which the true slope of every family is the base slope times a log-normal
factor. Every data set contains the true measure and a null measure. In 15 cells the two-way bootstrap of the
procedure was compared, on the same data sets, with a bootstrap that resamples participants only and one that
resamples items only (helpers in `simcore.py`; the package itself offers the two-way bootstrap). 1,000 data sets
per cell, 500 resamples.

**Results (Figures 3 and 4; `results/tables/s3_true_measure.md`, `s3_bootstrap_comparison.md`,
`s3_null_measure.md`, `s3_slope_differs.md`).**

Two-way bootstrap, true measure, one factor at a time (base case in bold):

| Varied | Value | Slope: coverage | Slope: median width | Width justified by the spread | Slope: detection | Log loss: coverage | Log loss: detection | Ordering: detection |
|---|---|---|---|---|---|---|---|---|
| **base** | | .988 (.003) | 1.18 | 0.86 | .988 (.003) | .985 (.004) | .458 (.016) | .982 (.004) |
| families | 3 | .981 (.004) | 1.32 | 0.98 | .992 (.003) | .978 (.005) | .454 (.016) | .979 (.005) |
| families | 6 | .985 (.004) | 1.11 | 0.81 | .992 (.003) | .982 (.004) | .496 (.016) | .980 (.004) |
| families | 10 | .989 (.003) | 1.04 | 0.78 | .998 (.001) | .984 (.004) | .504 (.016) | .987 (.004) |
| items | 24 | .981 (.004) | 1.86 | 1.40 | .838 (.012) | .986 (.004) | .194 (.013) | .732 (.014) |
| items | 96 | .985 (.004) | 0.81 | 0.62 | 1.000 | .984 (.004) | .855 (.011) | 1.000 |
| items | 192 | .985 (.004) | 0.57 | 0.45 | 1.000 | .980 (.004) | .990 (.003) | 1.000 |
| participants | 20 | .998 (.001) | 1.57 | 1.11 | .954 (.007) | .986 (.004) | .272 (.014) | .913 (.009) |
| participants | 80 | .971 (.005) | 0.96 | 0.83 | .999 (.001) | .976 (.005) | .654 (.015) | .998 (.001) |
| slope | 0.25 | .989 (.003) | 2.79 | 1.99 | .551 (.016) | .986 (.004) | .094 (.009) | .436 (.016) |
| slope | 1 | .990 (.003) | 0.64 | 0.47 | 1.000 | .980 (.004) | .985 (.004) | 1.000 |
| item residual SD | 0 | .997 (.002) | 0.92 | 0.58 | 1.000 | .995 (.002) | .744 (.014) | 1.000 |
| item residual SD | 1 | .967 (.006) | 1.90 | 1.65 | .799 (.013) | .965 (.006) | .245 (.014) | .736 (.014) |
| participant SD | 0 | .991 (.003) | 1.17 | 0.92 | .994 (.002) | .983 (.004) | .494 (.016) | .977 (.005) |
| participant SD | 1.6 | .983 (.004) | 1.28 | 1.02 | .986 (.004) | .987 (.004) | .428 (.016) | .972 (.005) |

("Width justified by the spread" is the range of the central 95% of the estimates over the 1,000 data sets.)

The three ways of resampling, on the same data sets:

| Items / slope / item residual SD | Slope coverage: two-way | participants only | items only | Null measure, slope interval excludes 0: two-way | participants only | items only | Log-loss detection: two-way | items only |
|---|---|---|---|---|---|---|---|---|
| 48 / 0.5 / 0 | .997 (.002) | .926 (.008) | .910 (.009) | .000 | .061 (.008) | .003 (.002) | .744 (.014) | .976 (.005) |
| 48 / 0.5 / 0.5 (base) | .988 (.003) | .781 (.013) | .952 (.007) | .000 | .137 (.011) | .001 (.001) | .458 (.016) | .690 (.015) |
| 48 / 0.5 / 1 | .967 (.006) | .508 (.016) | .941 (.007) | .002 (.001) | .311 (.015) | .004 (.002) | .245 (.014) | .314 (.015) |
| 24 / 1 / 1 | .969 (.005) | .578 (.016) | .942 (.007) | .001 (.001) | .362 (.015) | .004 (.002) | .387 (.015) | .484 (.016) |
| 96 / 0.25 / 1 | .974 (.005) | .529 (.016) | .953 (.007) | .001 (.001) | .259 (.014) | .003 (.002) | .101 (.010) | .170 (.012) |
| 96 / 1 / 0 | .998 (.001) | .936 (.008) | .907 (.009) | .000 | .210 (.011) | .001 (.001) | 1.000 | 1.000 |
| 96 / 1 / 1 | .965 (.006) | .583 (.016) | .932 (.008) | .001 (.001) | .366 (.015) | .003 (.002) | .967 (.006) | .978 (.005) |
| small design (3 families, 24 items, 20 participants, 0.5 / 1) | .992 (.003) | .660 (.015) | .962 (.006) | .001 (.001) | .169 (.012) | .004 (.002) | .025 (.005) | .079 (.009) |

1. The two-way bootstrap never undercovered. Coverage of the calibration slope was between .965 (.006) and
   1.000 in all 25 common-slope cells, and coverage of the log-loss reduction between .965 (.006) and .998.
   The intervals are conservative: the median width is 1.1 to 2.1 times the width that the spread of the
   estimates would justify (1.18 against 0.86 in the base case, 0.92 against 0.58 without item residual, 1.90
   against 1.65 with item residual SD 1). Resampling participants and items at once counts the response noise
   twice.
2. The price is power, most of all for the prediction criterion. In the base case a medium relation that
   transfers perfectly is detected by the calibration slope in 98.8% (0.3) and by ordering in 98.2% (0.4) of
   the data sets, but by the log-loss reduction in only 45.8% (1.6). The prediction criterion reaches 85%
   with 96 items and 99% with 192 items or a strong slope; it stays at 9.4% (0.9) for a weak slope and at
   24.5% (1.4) when the item residual SD is 1. An interval of the log-loss reduction that includes 0 is
   therefore the expected result for a valid measure of medium strength in designs of ordinary size, and must
   not be read as failed transfer.
3. What limits precision is the number of items of the held-out family and the strength of the relation, not
   the number of families. From 3 to 10 families the median width of the slope interval falls from 1.32 to
   1.04; from 24 to 192 items it falls from 1.86 to 0.57. Even in the base case a width of 1.18 means that a
   calibration slope of 1 cannot be told from 0.5 or 1.6. With a weak slope (0.25) the width is 2.8 and the
   relation is detected in 55.1% (1.6) of the data sets.
4. Small designs are uninformative, and the simulation shows this plainly. With 3 families, 24 items, 20
   participants and item residual SD 1, the median width of the slope interval is 5.5 for a medium slope
   (detection 23.0% (1.3); log-loss detection 2.5% (0.5)) and 22 for a weak slope (detection 1.0% (0.3)).
   The coverage is correct (.992, .990), but an interval from about -2 to 4 says nothing. The limiting factors
   here are the 24 items and the item residual; with 3 families and the base numbers of items and participants
   the procedure works as in the base case (width 1.32, detection .992).
5. Item residual variance decides which resampling is valid. A bootstrap of participants only treats the
   items as fixed and is anticonservative as soon as items differ for reasons that the measure does not
   capture: coverage of the calibration slope .781 (.013) in the base case and .508 (.016) at item residual SD
   1, coverage of the log-loss reduction .695 (.015) and .493 (.016), and a null measure is declared related
   to accuracy in 13.7% (1.1) and 31.1% (1.5) of the data sets (up to 36.6% (1.5) in the factorial). Even
   without any item residual its coverage is below nominal (.926 (.008)), because the items are still a sample
   of values of the measure. More participants make this worse, not better, since the interval shrinks while
   the item-to-item variation stays.
6. A bootstrap of items only is close to nominal: coverage of the calibration slope .907 to .971 (.932 to
   .971 when the item residual SD is at least 0.5 and the participant SD at most 0.8; .907 to .936 when the
   item residual SD is 0), its median width equals the
   width justified by the spread (0.88 against 0.86 in the base case, 1.65 against 1.65 at item residual SD 1),
   the false-positive rate for the null measure stays at or below 0.5%, and the prediction criterion detects
   the base-case relation in 69.0% (1.5) instead of 45.8% of the data sets. It undercovers mildly where
   participants are the main source of error (no item residual, or participant SD 1.6: .916 (.009)).
7. False positives are not a concern with the two-way bootstrap. For the null measure the interval of the
   calibration slope excluded 0 in at most 0.2% of the data sets in every cell, the interval of the log-loss
   reduction lay above 0 in at most 0.1%, and the weak-training flag was raised in 94.6% to 99.5%.
8. When true slopes differ between families, the interval covers the calibration slope of the families at
   hand (coverage .979 to .987 against the value specific to each draw), not a value for families in general.
   With a log-normal SD of 0.4 the large-sample calibration slope of a draw ranges from 0.43 to 2.27 (5th to
   95th percentile, 3 families), and the interval still included 1 in 70.1% (1.4) of the data sets, and in
   50.3% (2.1) of those whose large-sample value was below 0.75 or above 1.33. "The interval includes 1" is
   weak evidence that the trained effect size holds.
9. The percentile interval of the ordering correlation behaves differently from the other two and is treated
   in S5.

**What a user should take from this.** The intervals of the procedure can be trusted not to produce false
claims of transfer; they are too wide, by a factor of about 1.2 to 2. Treat "interval excludes 0" as strong
evidence and "interval includes 0" or "includes 1" as uninformative unless the design is large (roughly 100 or
more held-out items for a medium relation). Never resample participants only. Before collecting data, more
items in the family to be held out buy more than more families or more participants.

**Limitations.** One sample per family and complete data; families of equal size; normal measure; intervals
are percentile intervals with 500 resamples; the items-only bootstrap was studied as a comparison and is not
part of the package; coverage with slopes that differ between families was assessed against the value for the
families at hand only.


## S4. Does within-family fit rank measures the same way as transfer?

**Design.** Difficulty in every family is driven by a latent variable (slope 1 logit per SD, item residual
SD 0.5). Two measures A and B are noisy versions of it; the validity of a measure in a family is its
correlation with the latent variable, so a measure with validity .6 carries 0.6 logits per SD. Three scenarios:
(i) fixed validities: A is the true measure (validity 1) or has validity .6 everywhere, B has one validity in
the training families and another in the held-out family; (ii) random validities: the validity of each measure
in each family is drawn around a mean (Fisher z scale, between-family SD 0 to 0.5), so that no family is
special; (iii) unstable unit: B is more valid than A in every family (.8 against .5), but its unit differs
between families by a log-normal factor. "Fit within the training families" is the deviance explained by the
training model of the procedure (sample intercepts, common slope); the variant with separate slopes per
family gave the same rates to within .02 everywhere. The outcome is whether the measure with the better fit
has the lower log-loss reduction (or ordering) in the held-out family. 2,000 data sets per cell, no bootstrap.

**Results (Figure 5; `results/tables/s4_ranking.md`).**

| Scenario | Validity of A | Validity of B (training / held-out) | Fit winner transfers worse: ordering | log loss | worse by more than .01 in log-loss reduction |
|---|---|---|---|---|---|
| true measure against proxy | 1 | .9 / .9 | .024 (.003) | .023 (.003) | .002 (.001) |
| true measure against proxy | 1 | .9 / 0 | .000 | .000 | .000 |
| constant against family-dependent | .6 | .8 / .8 | .089 (.006) | .078 (.006) | .030 (.004) |
| constant against family-dependent | .6 | .7 / .5 | .647 (.011) | .692 (.010) | .558 (.011) |
| constant against family-dependent | .6 | .8 / .5 | .707 (.010) | .802 (.009) | .673 (.010) |
| constant against family-dependent | .6 | .8 / .3 | .913 (.006) | .963 (.004) | .925 (.006) |
| constant against family-dependent | .6 | .8 / 0 | .986 (.003) | .991 (.002) | .988 (.002) |
| random, means .70 and .50 | SD 0 | | .141 (.008) | .123 (.007) | .058 (.005) |
| random, means .70 and .50 | SD 0.15 | | .213 (.009) | .208 (.009) | .127 (.007) |
| random, means .70 and .50 | SD 0.3 | | .343 (.011) | .327 (.010) | .249 (.010) |
| random, means .70 and .50 | SD 0.5 | | .383 (.011) | .366 (.011) | .299 (.010) |
| random, means .65 and .55 | SD 0 | | .338 (.011) | .335 (.011) | .200 (.009) |
| random, means .65 and .55 | SD 0.15 | | .415 (.011) | .410 (.011) | .263 (.010) |
| random, means .65 and .55 | SD 0.3 | | .451 (.011) | .430 (.011) | .331 (.011) |
| random, means .65 and .55 | SD 0.5 | | .465 (.011) | .436 (.011) | .363 (.011) |
| random, means .65 and .55, 96 items and 80 participants | SD 0 | | .219 (.009) | .208 (.009) | .077 (.006) |
| random, means .65 and .55, 96 items and 80 participants | SD 0.3 | | .447 (.011) | .418 (.011) | .317 (.010) |
| unstable unit of B | .5 | .8 / .8, unit SD 0 | .033 (.004) | .020 (.003) | .009 (.002) |
| unstable unit of B | .5 | .8 / .8, unit SD 0.35 | .028 (.004) | .096 (.007) | .065 (.005) |
| unstable unit of B | .5 | .8 / .8, unit SD 0.7 | .057 (.005) | .262 (.010) | .185 (.009) |

1. The answer depends entirely on whether validity is a property of the measure or of the measure in a
   family. When the true measure is among the candidates, or when validities are the same in all families and
   clearly different (.7 against .5), the measure with the better fit transfers worse in 0% to 14% of the data
   sets, and materially worse (by more than .01 in log-loss reduction) in at most 6%. In these conditions
   within-family fit is a sound guide and the procedure adds little to the ranking.
2. When the validity of a measure depends on the family, within-family fit picks the wrong measure for the
   held-out family most of the time, and no amount of data in the training families helps. A measure with
   validity .8 in three training families and .5 in the held-out family beats a measure with validity .6
   everywhere on fit in 99.6% of the data sets and loses to it in the held-out family in 80.2% (0.9) (log
   loss) or 70.7% (1.0) (ordering); with a held-out validity of .3 the rates are 96.3% and 91.3%, and the
   transferred predictor of the better-fitting measure is then worse than no measure (log-loss reduction
   -.020 against .037 for the other measure).
3. When no family is special but validities vary between families, the two rankings disagree in 33% to 44%
   of the data sets for measures whose mean validities are .65 and .55, and in 12% to 37% for .70 and .50,
   rising with the between-family standard deviation. A between-family SD of 0.3 on the Fisher z scale means
   that a measure with mean validity .65 has validities between about .19 and .88 in 95% of families. Part of
   this disagreement is sampling error (33.5% (1.1) at SD 0 with 48 items and 40 participants, 20.8% (0.9)
   with 96 and 80) and part is real: at SD 0.3 the true rankings in training and held-out family differ in
   42% of the draws, and a larger sample does not change the rate (43.0% against 41.8%).
4. More training families help only slowly. With mean validities .65 and .55 and SD 0.3, the rate at which
   the better-fitting measure transfers worse is 45.2% (1.1) with three families, 43.0% (1.1) with four,
   43.8% (1.1) with six and 39.6% (1.1) with ten: the training side becomes more accurate about the average
   family, while the held-out family remains one draw.
5. Ordering and prediction can rank the measures differently from each other. When the more valid measure has
   a unit that differs between families (unit SD 0.7), it wins on fit in 97.4% of the data sets and on
   ordering in 96.8%, yet has the lower log-loss reduction in 24.8% (the fit winner transfers worse on log
   loss in 26.2% (1.0)), and its mean log-loss reduction falls to that of the less valid measure (.026 against
   .025). Ordering is blind to the unit; prediction and the calibration slope (median 1.38) are not.
6. An honest negative result: selecting the measure by leave-one-family-out transfer among the training
   families did no better than selecting it by fit. The mean log-loss reduction of the selected measure in the
   held-out family was the same to within .001 for the two rules in all random-validity cells (for example
   .0338 against .0340 at SD 0.3), and slightly lower for transfer-based selection when the unit was unstable
   (.021 against .025). The disagreement between fit and transfer is not a defect of the fit statistic that a
   cleverer statistic applied to the same families would repair. It reflects that a family not yet seen can
   differ from the families seen.

**What a user should take from this.** A ranking of measures obtained within families is a ranking for those
families. Whether it carries over is an empirical property of the measures, and the simulation shows that it
fails precisely when validity varies between families, which cannot be known without holding families out.
The value of the procedure is therefore in the held-out result itself, family by family, and not in a better
selection rule. With two measures of similar validity (difference about .1) even a perfectly stable pair is
ranked inconsistently in a third of data sets of the base size, so small differences between measures in a
single held-out family should not be interpreted.

**Limitations.** Two measures only; validities of the two measures are independent across families; the
latent driver is the same in all families; only one held-out family is scored per data set.

## S5. Percentile or basic interval for the ordering criterion?

**Why this was added.** In an application with thousands of items the percentile interval of the ordering
correlation excluded its own estimate. The two-way bootstrap resamples participants, which adds noise to the
item accuracies, and items, which adds ties; both pull the resampled correlations towards zero, so the
percentile interval is centred below the estimate. A basic (reflected) interval, 2 x estimate minus the
percentiles, was proposed as a remedy. The saved replications of S3 allow both intervals to be computed (the
basic interval follows from the estimate and the two percentiles), and `sim05_ordering_interval.py` extends
the range to 768 and 3,072 items, with an items-only bootstrap for comparison. Two targets are distinguished:
the expected ordering at the same numbers of items and participants (the mean of the estimates over the
simulated data sets), and the large-sample ordering (error-free item accuracies).

**Results (`results/tables/ordering_interval.md`).** Slope 0.5 and item residual SD 0.5 unless noted;
S3 cells have 1,000 data sets, S5 cells 500, 300 or 200 (see the table file).

| Items | Participants | Expected ordering | Shift of the interval centre | Median width | Percentile interval excludes its own estimate | Coverage of the expected ordering: two-way percentile | two-way basic | items-only percentile | Coverage of the large-sample ordering: two-way basic | Null measure, interval excludes 0: two-way percentile | two-way basic |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 24 | 40 | .585 | -.130 | .71 | .000 | .990 (.003) | .853 (.011) | | .948 (.007) | .000 | .125 (.010) |
| 48 | 20 | .541 | -.111 | .54 | .000 | .978 (.005) | .856 (.011) | | .961 (.006) | .000 | .108 (.010) |
| 48 | 40 | .592 | -.094 | .48 | .000 | .977 (.005) | .847 (.011) | .945 (.007) | .955 (.007) | .000 | .113 (.010) |
| 48 | 80 | .634 | -.074 | .43 | .000 | .980 (.004) | .871 (.011) | | .955 (.007) | .002 (.001) | .104 (.010) |
| 96 | 40 | .604 | -.077 | .33 | .000 | .963 (.006) | .838 (.012) | | .980 (.004) | .000 | .091 (.009) |
| 192 | 40 | .602 | -.067 | .24 | .000 | .914 (.009) | .812 (.012) | .944 (.010) | .969 (.005) | .000 | .078 (.008) |
| 768 | 20 | .545 | -.079 | .15 | .730 (.031) | .410 (.035) | .430 (.035) | .950 (.015) | .600 (.035) | .000 | .070 (.018) |
| 768 | 40 | .605 | -.060 | .12 | .410 (.028) | .543 (.029) | .533 (.029) | .950 (.013) | .937 (.014) | .000 | .057 (.013) |
| 768 | 80 | .644 | -.040 | .11 | .000 | .730 (.031) | .675 (.033) | .940 (.017) | .970 (.012) | .000 | .075 (.019) |
| 3,072 | 40 | .606 | -.060 | .07 | 1.000 | .055 (.016) | .015 (.009) | .940 (.017) | .750 (.031) | | |
| 48 | 40, item residual SD 0 | .776 | -.159 | .42 | .026 (.005) | .917 (.009) | .691 (.015) | .946 (.007) | .990 (.003) | .000 | .096 (.009) |
| 768 | 40, item residual SD 0 | .788 | -.119 | .13 | 1.000 | .000 | .000 | .905 (.021) | .040 (.014) | .000 | .100 (.021) |
| 768 | 40, slope 1 | .832 | -.046 | .07 | 1.000 | .205 (.029) | .210 (.029) | .960 (.014) | 1.000 | .000 | .065 (.017) |

(The items-only percentile interval was computed in the cells where a value is shown; the null measure was
not run with 3,072 items.)

1. The finding is confirmed and it is general. The centre of the two-way percentile interval lies .04 to .16
   below the estimate in every cell. The shift hardly depends on the number of items, whereas the width of the
   interval shrinks with it (.48 with 48 items, .07 with 3,072). With up to about 100 items the shift is hidden
   inside a wide interval and the percentile interval is conservative for the expected ordering (.96 to .99).
   From about 200 items it undercovers (.914 (.009) at 192 items), and with 768 or more items it fails: .54 at
   768 items, .06 at 3,072 items, where it excluded its own estimate in every data set. A high reliability
   ceiling makes it worse (item residual SD 0: .917 with 48 items, .000 with 768).
2. The basic interval does not repair this for the expected ordering. It undercovers at every design size:
   .83 to .87 with 24 to 96 items in the base configuration (.69 to .90 over all cells with 48 items), .81 at
   192, .53 at 768 and .02 at 3,072. The reflection moves the interval
   up by the amount of the shift, but the estimate itself is not biased downwards relative to its own
   expectation, so the reflected interval sits too high (in the base case it lay entirely above the expected
   ordering in 15% of the data sets).
3. What the basic interval does cover, in small and medium designs, is the large-sample ordering, the
   correlation that error-free item accuracies would give: .93 to .99 for 24 to 768 items with 40 or 80
   participants. The reason is that the estimate is attenuated relative to that value by response noise, and
   the bootstrap adds a similar dose of noise. This is not dependable: it fails with 20 participants at 768
   items (.60), with 3,072 items (.75) and without item residual at 768 items (.04).
4. For a measure without relation the basic interval is anticonservative: it excluded 0 in 6% to 13% of the
   data sets, against 0.0% to 0.2% for the percentile interval. With a training slope near zero the sign of
   the transferred predictor flips between resamples, the resampled correlations straddle zero, and reflecting
   them pushes the interval away from zero.
5. A percentile interval from a bootstrap of items only (participants kept as they are) covered the expected
   ordering at .905 to .960 in all eleven cells of the table in which it was computed, from 48 to 3,072 items
   (and at .941 to .987 in the twelve further cells of S3), and excluded 0 for the null measure in at most 0.5%
   of the data sets. It does not add resampling noise to the
   item accuracies, which removes the source of the shift.

**Recommendation for the package.** (Status: this recommendation was adopted after this section was written. Since version 0.2.0 the package computes the ordering interval from an items-only bootstrap by default, `ordering_boot="items"`.) For the ordering
criterion neither the percentile nor the basic interval of the two-way bootstrap should be the reported
interval. The percentile interval is acceptable (conservative) up to about 100 held-out items and wrong beyond
a few hundred; the basic interval undercovers its stated target at every size and produces false positives
for null measures, so it should not become the default. The interval that held its level across the whole
range is the percentile interval of an items-only bootstrap, and that is what the package should use for
ordering. If only the two existing options are available, use the percentile interval with fewer than about
100 held-out items and report no interval for ordering with more. The calibration slope and the log-loss
reduction are not affected: their two-way percentile intervals were conservative in every cell of S3.

**Limitations.** The items-only interval ignores the sampling of participants and undercovered mildly where
participants are the main source of error (.905 (.021) without item residual). Coverage was assessed for
complete designs; with 200 to 300 data sets in the large cells the Monte Carlo standard errors are .01 to
.035. The null measure was not run with 3,072 items.


## S6. The procedure next to the analyses a researcher would otherwise run

**Design.** Base case, nine scenarios, 1,000 data sets each, the same data analysed four ways.
(a) Grouped cross-validation as in scikit-learn (leave one group out): one logistic model with a single
intercept and the measure, fitted to the trials of the training families; the log loss of the held-out family
is compared with a baseline that predicts the training base rate; the score is the relative reduction; the
intercept is not recalibrated; one number per held-out family, no interval.
(b) A logistic regression per family and Cochran's Q test of slope heterogeneity at .05 (equivalent to a
measure-by-family interaction), once with model-based standard errors (trial-level logistic regression, items
treated as fixed) and once with item-cluster-robust (sandwich) standard errors. An item bootstrap was not run
in addition, to save time.
(c) A random-effects meta-analysis of the four per-family slopes (DerSimonian-Laird, item-robust standard
errors, prediction interval with t on 2 degrees of freedom).
(d) The procedure: three criteria with two-way bootstrap intervals, weak-training flag, and the tolerance
reading of the calibration slope (band 0.80 to 1.25).

**Results (`results/tables/s6_comparators.md`, `results/sim06_summary.csv`).**

| Scenario | Procedure: calibration slope, median | slope interval excludes 0 | reading outside tolerance | log-loss interval above 0 | Grouped CV: mean score | score positive | Q test rejects: model-based SE | item-robust SE | Random effects: tau = 0 | prediction interval, median width | excludes 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 common slope | 1.00 | .991 (.003) | .002 (.001) | .474 (.016) | .0300 (.0004) | .987 (.004) | .310 (.015) | .075 (.008) | .590 (.016) | 0.36 | .878 (.010) |
| 2 common slope, held-out family easier (intercept 2 against 1) | 1.03 | .978 (.005) | .000 | .363 (.015) | .0211 (.0007) | .843 (.012) | .318 (.015) | .087 (.009) | .569 (.016) | 0.37 | .858 (.011) |
| 2 common slope, held-out family harder (intercept 0) | 0.99 | .998 (.001) | .001 (.001) | .506 (.016) | .0231 (.0006) | .860 (.011) | .364 (.015) | .078 (.008) | .560 (.016) | 0.36 | .873 (.011) |
| 3 held-out slope half the training slope | 0.51 | .568 (.016) | .153 (.011) | .003 (.002) | -.0000 (.0004) | .522 (.016) | .844 (.011) | .541 (.016) | .115 (.010) | 1.06 | .288 (.014) |
| 4 held-out slope twice the training slope | 2.01 | 1.000 | .701 (.014) | 1.000 | .0811 (.0006) | 1.000 | .997 (.002) | .970 (.005) | .002 (.001) | 2.00 | .037 (.006) |
| 5 step relation, two-level held-out family | 1.16 | .995 (.002) | .001 (.001) | .640 (.015) | .0303 (.0003) | .998 (.001) | .454 (.016) | .105 (.010) | .500 (.016) | 0.38 | .775 (.013) |
| 6 saturating relation, held-out range 2 to 8 | 0.34 | .822 (.012) | .823 (.012) | .000 (below 0: .144 (.011)) | -.0142 (.0022) | .434 (.016) | .999 (.001) | .975 (.005) | .002 (.001) | 1.86 | .007 (.003) |
| 7 no relation, item residual SD 0.5 | 0.00 | .000 | .000 | .000 | -.0003 (.0000) | .413 (.016) | .363 (.015) | .085 (.009) | .553 (.016) | 0.35 | .000 |
| 7 no relation, item residual SD 1 | 0.06 | .000 | .001 (.001) | .000 | -.0007 (.0001) | .437 (.016) | .721 (.014) | .066 (.008) | .586 (.016) | 0.55 | .000 |

(The mean slope of a family is about 0.43; prediction-interval widths are on that scale. The reading "within
tolerance" did not occur in any of the 9,000 data sets with 48 held-out items; see S8.)

**The algebraic relation.** The calibration slope is the slope of a logistic regression of the held-out trials
on (training slope x measure) with a free intercept. That model is a reparametrisation of the logistic
regression of the held-out trials on the measure itself, so by the invariance of maximum likelihood the
calibration slope equals the held-out family's own slope divided by the training slope, exactly. Numerically,
over the 1,000 data sets of each scenario the correlation between the two is 1.000000 and the largest absolute
difference is 1e-14 (the two no-relation scenarios were restricted to the 660 and 794 data sets with a
training slope above 0.02 in absolute value, where the ratio is numerically stable). The scale criterion is
therefore a comparison of per-family slopes, as in (b), and contains no information beyond the two slopes.

1. A heterogeneity test with model-based standard errors is not valid when items differ for reasons the
   measure does not capture. With one common slope in all four families it rejected homogeneity in 31.0% (1.5)
   of the data sets, with a mean shift in the held-out family in 31.8% and 36.4%, and for a measure without
   any relation in 36.3% (1.5) at item residual SD 0.5 and 72.1% (1.4) at SD 1. The model-based standard error
   of a family's slope is too small by a factor of 1.47 at item residual SD 0.5 and 2.38 at SD 1. A researcher
   who fits a measure-by-family interaction in a plain logistic regression of trials will find "the slopes
   differ" in a third or more of the data sets in which they do not.
2. With item-robust standard errors the same test is close to its level (6.6% to 8.7% in the five scenarios
   with equal slopes, mildly liberal with 48 items per family) and it is the more powerful way to detect a
   slope difference: it rejected in 54.1% (1.6) of the data sets when the held-out slope was half the training
   slope and in 97.0% (0.5) when it was twice, where the tolerance reading "outside" occurred in 15.3% (1.1)
   and 70.1% (1.4) and the slope interval excluded 1 in 41.9% and 96.5%. Where the question is only "do the
   slopes differ", a correctly specified heterogeneity test does as well as the procedure or better, and the
   paper should say so. It does not say which family differs, in which direction or by how much, and it uses
   all families symmetrically.
3. Grouped cross-validation without recalibration confounds the mean accuracy of the held-out family with the
   measure. With an identical slope, its mean score fell from .0300 to .0211 (held-out family easier) and
   .0231 (harder), and the score was negative in 15.7% and 14.0% of the data sets against 1.3% without a mean
   shift. The recalibrated log-loss reduction of the procedure was .0311, .0292 and .0310 in the same three
   scenarios. Without a mean shift the two scores agree (.0300 against .0311), so the recalibration matters
   exactly when families differ in overall accuracy, which is the usual case.
4. Grouped cross-validation gives one number without an interval. For a measure without relation the score
   was positive in 41.3% (1.6) and 43.7% (1.6) of the data sets (5th to 95th percentile -.003 to .002), and a
   user has no means of telling such a value from a small true gain. The interval of the procedure lay above
   0 in none of these data sets. The price is the low power documented in S3: for the common slope the
   score was positive in 98.7% of the data sets while the interval of the procedure lay above 0 in 47.4%.
5. A random-effects meta-analysis of four slopes cannot estimate the between-family variance. With a common
   slope the estimate of tau was exactly 0 in 59.0% (1.6) of the data sets, and equally often (55% to 59%)
   when there was no relation at all. When one of the four families truly differed, the prediction interval
   (t with 2 degrees of freedom) became so wide that it said nothing: median width 1.06 (slope halved) and 2.00
   (slope doubled) for a mean slope near 0.4, and it excluded 0 in 28.8% and 3.7% of the data sets although
   every family had a clear relation. Treating families as random is the right model for "a new family", but
   three to ten families do not support it; this is the reason the procedure treats the families at hand as
   fixed and reports each held-out result separately.
6. None of the three comparators flags the two design problems of scenarios 5 and 6. In the two-level family
   with a step relation all methods report a transferring measure (grouped CV score .0303, item-robust Q test
   rejecting in 10.5%). Under a saturating relation with a shifted range the heterogeneity test rejects in
   97.5% and grouped CV gives a negative mean score, which a user would read as "the measure works differently
   in this family", the wrong conclusion (S2b). The three criteria of the procedure give the same misleading
   numbers (calibration slope 0.34, reading outside tolerance in 82.3%); what differs is that its diagnostics
   (levels, range overlap, common-range slope) point to the cause.

**What the procedure adds, given that its scale criterion is a ratio of two slopes.** (i) Uncertainty that
treats items as a sample, which a plain per-family GLM lacks and which matters by a factor of 1.5 to 2.4 in
the standard error. (ii) The prediction criterion with recalibrated intercept, which separates a difference in
mean accuracy from a failure of the measure. (iii) Direction and size per held-out family with an interval,
instead of one omnibus test. (iv) The design diagnostics, which no comparator has. (v) The reliability
ceiling for the ordering criterion. It does not add power for detecting a slope difference: an item-robust
heterogeneity test is at least as sensitive.

**What a user should take from this.** If per-family slopes are compared, never with model-based standard
errors from a trial-level logistic regression. If grouped cross-validation is used, recalibrate the intercept
in the held-out family and attach an interval. Do not fit a random-effects model to a handful of families
and read its prediction interval.

**Limitations.** The sandwich standard errors cluster on items and ignore participants; an item bootstrap and
a mixed-effects logistic model with crossed random effects (which would be the standard psycholinguistic
analysis) were not run. (Status: a mixed model was added afterwards in R and is reported in Table 6 of the article and in the section on final methods and results of this supplement.) Grouped cross-validation was scored for the designated held-out family only. Four
families; the heterogeneity test has more power with more families.

## S7. Family differences that are not differences in the slope

**Design.** The analysis model has no random effects, so the training slope and the held-out slope are
marginal slopes (averaged over participants and over the item residual), and the calibration slope is their
ratio. A marginal logistic slope is smaller than the conditional slope by a factor of about
1 / sqrt(1 + 0.346 x variance), where the variance is that of the participant effects plus the item residuals.
The conditional slope (0.5) was kept identical in all families, and the held-out family differed from the
training families (participant SD 0.8, item residual SD 0.5, intercept 1) in one respect. Large-sample
calibration slopes were computed for all 13 cells; 500 data sets were run for the two cells that deviate most
from 1 (fewer than the 1,000 planned, for run time).

**Results (`results/tables/s7_noncollapsibility.md`, `s7_finite_sample.md`, `results/sim07_targets.csv`).**

| Held-out family differs in | Value | Large-sample calibration slope | Approximation | Outside 0.80 to 1.25 |
|---|---|---|---|---|
| participant SD (training 0.8) | 0 | 1.112 | 1.097 | no |
| | 0.8 | 0.997 | 1.000 | no |
| | 1.6 | 0.796 | 0.814 | yes (just) |
| | 2.4 | 0.630 | 0.652 | yes |
| item residual SD (training 0.5) | 0 | 1.041 | 1.035 | no |
| | 0.5 | 1.002 | 1.000 | no |
| | 1 | 0.903 | 0.913 | no |
| | 1.5 | 0.783 | 0.809 | yes |
| intercept (training 1) | -0.5 | 0.988 | 1.000 | no |
| | 0 | 0.987 | 1.000 | no |
| | 1 | 0.999 | 1.000 | no |
| | 2 | 1.041 | 1.000 | no |
| | 3 | 1.085 | 1.000 | no |

(The standard deviation of a large-sample value over item sets is at most 0.005.)

1. With an identical conditional mechanism, the large-sample calibration slope ranges from 0.63 to 1.11. A
   held-out sample whose participants are twice as heterogeneous as the training samples (SD 1.6 against 0.8)
   gives 0.80, three times as heterogeneous 0.63; a held-out family whose items carry three times the
   unexplained difficulty (SD 1.5 against 0.5) gives 0.78; a homogeneous held-out sample (SD 0) gives 1.11.
2. The approximation 1 / sqrt(1 + 0.346 x variance), applied to each family, predicts the values of the eight
   variance cells to within 0.03 (largest difference -0.025), so a user can anticipate the size of the effect from the spread of
   participant accuracies and the item residuals.
3. A difference in mean accuracy alone has little effect: 0.99 for a harder held-out family (intercept 0 or
   -0.5), 1.04 and 1.09 for easier ones (intercept 2 and 3; accuracy about .86 and .94). The approximation
   does not capture this (it predicts 1), but the deviation stays inside the band.
4. The large-sample value leaves the band 0.80 to 1.25 only for participant SD 1.6 or more (0.796 and 0.630)
   and item residual SD 1.5 (0.783). Deviations of 10% to 20% from 1 therefore need no difference in the
   mechanism; deviations beyond 25% require a difference in variance that would be visible in the data
   (participant SD doubled or item residual SD tripled).
5. In samples of the base size these deviations are not detectable. For participant SD 2.4 (large-sample
   value 0.63) the median estimate was 0.63, the interval included 1 in 72.8% (2.0) of 500 data sets and the
   reading was "outside tolerance" in 5.4% (1.0); for item residual SD 1.5 (0.78) the interval included 1 in
   93.8% (1.1). Coverage of the large-sample value was .986 (.005) and .958 (.009).
6. The ordering criterion is unaffected by the participant SD (large-sample value .69 throughout) and falls
   with the item residual (.43 at SD 1, .30 at SD 1.5); the log-loss reduction falls with both (.030 to .008
   at participant SD 2.4), because more unexplained variance leaves less to predict.

**What a user should take from this.** A calibration slope is a statement about marginal slopes. Before
reading a deviation from 1 as a weaker or stronger effect, compare the spread of participant accuracies and
the reliability-corrected residual item variance between the held-out family and the training families;
differences in these produce calibration slopes between about 0.6 and 1.1 by themselves. This is a real
limitation of the marginal model of the procedure, and a reason for the tolerance band to be no narrower
than it is.

**Limitations.** One factor at a time, in the held-out family only; normal participant and item effects;
slope 0.5 (the attenuation depends little on the slope in this range, which was not examined further).

## S8. Error rates of the tolerance rule

**Design.** The rule reads a calibration slope as "within tolerance" when its whole 95% interval lies inside
0.80 to 1.25, "outside tolerance" when the whole interval lies outside, and "undetermined" otherwise. True
calibration slopes of 0.5, 0.8, 0.9, 1, 1.11, 1.25 and 2 were produced by the held-out slope. In one arm only
the held-out family had 48, 192 or 768 items (training families 48 each); in a second arm all four families
had 192 or 768 items (true slopes 0.8, 1 and 1.25). 40 participants. Intervals: two-way 95% (the rule of the
package), two-way 90%, and items-only 95% and 90%. 1,000 data sets per cell with 48 or 192 held-out items and
300 in all other cells (cut for run time; Monte Carlo standard errors up to .029 there).

**Results (Figure 6; `results/tables/s8_tolerance.md`, `results/sim08_summary.csv`).** Share of data sets read
as within / outside tolerance:

| Items | True slope | Two-way 95%: within | outside | Two-way 90%: within | outside | Items-only 95%: within | outside | Median width, two-way 95% |
|---|---|---|---|---|---|---|---|---|
| held-out 48 | 0.5 | .000 | .141 (.011) | .000 | .244 | .000 | .315 (.015) | 1.04 |
| held-out 48 | 0.8 | .000 | .005 (.002) | .000 | .020 | .000 | .035 (.006) | 1.14 |
| held-out 48 | 1 | .000 | .000 | .000 | .002 | .000 | .005 (.002) | 1.19 |
| held-out 48 | 1.25 | .000 | .005 (.002) | .000 | .021 | .000 | .026 (.005) | 1.28 |
| held-out 48 | 2 | .000 | .688 (.015) | .000 | .808 | .000 | .864 (.011) | 1.66 |
| held-out 192 | 0.5 | .000 | .422 (.016) | .000 | .593 | .000 | .674 (.015) | 0.57 |
| held-out 192 | 0.8 | .000 | .005 (.002) | .000 | .011 | .000 | .021 (.005) | 0.69 |
| held-out 192 | 1 | .000 | .000 | .000 | .000 | .000 | .000 | 0.78 |
| held-out 192 | 1.25 | .000 | .007 (.003) | .000 | .017 | .004 (.002) | .033 (.006) | 0.90 |
| held-out 192 | 2 | .000 | .944 (.007) | .000 | .968 | .000 | .982 (.004) | 1.32 |
| held-out 768 | 0.5 | .000 | .660 (.027) | .000 | .790 | .000 | .850 (.021) | 0.39 |
| held-out 768 | 0.8 | .000 | .007 (.005) | .000 | .017 | .000 | .020 (.008) | 0.53 |
| held-out 768 | 1 | .000 | .000 | .003 | .000 | .043 (.012) | .000 | 0.64 |
| held-out 768 | 1.25 | .000 | .007 (.005) | .003 | .020 | .033 (.010) | .037 (.011) | 0.77 |
| held-out 768 | 2 | .000 | .990 (.006) | .000 | 1.000 | .000 | 1.000 | 1.25 |
| all families 192 | 0.8 | .000 | .023 (.009) | .000 | .047 | .017 (.007) | .060 (.014) | 0.53 |
| all families 192 | 1 | .000 | .000 | .010 | .000 | .107 (.018) | .000 | 0.57 |
| all families 192 | 1.25 | .000 | .007 (.005) | .010 | .017 | .027 (.009) | .023 (.009) | 0.62 |
| all families 768 | 0.8 | .010 (.006) | .007 (.005) | .023 | .017 | .040 (.011) | .037 (.011) | 0.27 |
| all families 768 | 1 | .807 (.023) | .000 | .900 | .000 | .930 (.015) | .000 | 0.29 |
| all families 768 | 1.25 | .017 (.007) | .003 (.003) | .023 | .013 | .060 (.014) | .030 (.010) | 0.32 |

(True slopes 0.9 and 1.11 are in the table file.)

1. The rule controls its errors. With the two-way 95% interval, a true slope at an edge of the band (0.8 or
   1.25) was read as "within" in at most 1.7% (0.7) of the data sets and as "outside" in at most 2.3% (0.9), in
   every cell; a true slope of 1 was never read as "outside". The rule behaves as two one-sided tests at 2.5%
   or less.
2. The reading "within tolerance" is out of reach for ordinary designs. It requires an interval narrower than
   0.45, and the two-way 95% interval has a median width of 1.19 with 48 held-out items, 0.78 with 192 and
   0.64 with 768 when the training families have 48 items each. At a true slope of exactly 1 the reading was
   "within" in 0.0% of the data sets at all three sizes, and "undetermined" in 100%. Enlarging the held-out
   family alone cannot help, because the uncertainty of the training slope remains: only when all four
   families had 768 items (width 0.29) was a true slope of 1 read as "within" in 80.7% (2.3) of the data sets;
   with 192 items in all families it was 0.0%.
3. The same holds across the designs of S3 (`results/tables/s3_classification_bias_rmse.md`): at a true slope
   of 1 the reading was "within" in 0.0% of the data sets in 24 of 25 cells, and in 48.1% (1.6) in the one cell
   with 96 items, a strong slope and no item residual. It was "outside" in at most 0.8%.
4. "Outside tolerance" has useful power only for large deviations: a true slope of 0.5 was read as "outside"
   in 14.1% (1.1), 42.2% (1.6) and 66.0% (2.7) of the data sets with 48, 192 and 768 held-out items, a true
   slope of 2 in 68.8% (1.5), 94.4% (0.7) and 99.0% (0.6).
5. A 90% two-way interval changes little (within at true 1: 0.0%, 0.0%, 0.3% for the three held-out sizes;
   90.0% when all families have 768 items), and keeps the false "within" rate at the edges at or below 2.3%.
   Because the two-way interval is conservative, its 90% version still covered the large-sample value in 94%
   to 98% of the data sets.
6. An items-only 95% interval is narrower (0.87 against 1.19 with 48 items) and gives "within" more often
   (10.7% (1.8) with 192 items in all families, 93.0% (1.5) with 768), but its error rates at the edges exceed
   2.5%: false "within" 4.0% (1.1) and 6.0% (1.4) with 768 items in all families, false "outside" up to 6.0%
   (1.4). Its coverage here was .91 to .96.

**Bias and RMSE (added to the S3 results).** `results/tables/s3_classification_bias_rmse.md` gives, for every
common-slope cell of S3, the bias and RMSE of the calibration slope and of the log-loss reduction against
their large-sample values. In the base case the calibration slope has a mean bias of 0.012 (0.007), a median
bias of -0.005 and an RMSE of 0.224; the log-loss reduction has a bias of 0.0005 (0.0004) and an RMSE of 0.0128
(target 0.0299). The calibration slope is a ratio and is biased upwards on average where the training slope
is imprecise (0.044 (0.011) with 24 items, 0.061 (0.016) with a weak slope), while its median stays within
0.02 of the target in every cell except three (24 items with a weak slope and item residual SD 1, and the two
small designs); with 24 items, a weak slope and item residual SD
1 its mean and RMSE are dominated by a few extreme ratios (RMSE 39) and only the median is meaningful. The
log-loss reduction is slightly biased upwards for strong slopes with few items (0.0085 (0.0011) at 24 items,
slope 1, no item residual, target 0.111) and otherwise unbiased to within 0.004.

**What a user should take from this.** The tolerance rule is honest: it almost never declares agreement or
disagreement wrongly. In designs of the size studied here its usual answer is "undetermined", and "within
tolerance" should be expected only with several hundred items in every family. It should be presented as a
guard against over-reading, not as a test that designs of ordinary size can pass. The asymmetry matters for
reporting: "undetermined" is not weak evidence of agreement.

**Limitations.** One band; 40 participants; item residual SD 0.5; 300 data sets in the large cells; true
slopes at the edges are nominal (the large-sample values were 0.796 to 0.802 and 1.241 to 1.257).

## Summary

The simulation separates what the procedure establishes from what it is easily taken to establish.

- **The three criteria are three questions.** Ordering responds to whether the measure ranks the held-out
  items, scale to the ratio of held-out to trained effect size, prediction to both: its large-sample value is
  zero at a calibration slope of 0.5 and negative below. A clear ordering with a negative log-loss reduction,
  or with a log-loss interval that includes 0, is an expected pattern and not a contradiction (S1).
- **Transfer is evidence about a relation, not about a mechanism.** A proxy correlated .7 with the effective
  measure transfers wherever that correlation holds and fails where it does not; a two-level family gives the
  same results for a graded relation and for a step; a held-out family with another range of the measure gives
  calibration slopes of 0.3 to 0.6 under a non-linear relation that is identical in all families (S1, S2).
- **The reliability ceiling is quantitative.** The ordering criterion is attenuated by the square root of the
  split-half reliability of item difficulty to within .023, and can be corrected when that reliability is above
  about .6 (S2c).
- **The intervals are safe and wide.** Two-way bootstrap intervals of the calibration slope and the log-loss
  reduction covered their large-sample targets in 96.5% to 100% of the data sets in every design, and a null
  measure was almost never declared related to accuracy (at most 0.2%). They are 1.1 to 2.1 times wider than
  necessary. The prediction criterion detects a perfectly transferring medium relation in under half of the
  data sets with 48 held-out items; designs with 24 items and a noisy family are uninformative on every
  criterion. Resampling participants only gives coverage as low as 51% and false-positive rates up to 37%
  (S3).
- **The ordering interval needs a different bootstrap.** Its two-way percentile interval is centred too low and
  fails with several hundred items or more; the basic interval is no remedy; an items-only percentile interval
  held its level from 48 to 3,072 items (S5).
- **The scale criterion is a ratio of two per-family slopes, and that is all it is.** What the procedure adds
  to a comparison of slopes is uncertainty that treats items as a sample (a heterogeneity test with model-based
  standard errors rejected a true common slope in 31% of the data sets, and in 72% for an unrelated measure
  with item residual SD 1), a prediction criterion that is not confounded with the mean accuracy of the family
  (un-recalibrated grouped cross-validation lost a quarter of its score to a pure intercept shift), and the
  design diagnostics. It does not add power: an item-robust heterogeneity test detects a slope difference
  more often (S6).
- **A calibration slope between about 0.6 and 1.1 can arise with an identical conditional mechanism** when
  families differ in the spread of participants or in residual item variance; a difference in mean accuracy
  alone moves it by less than 0.1 (S7).
- **The tolerance rule is safe and rarely decisive.** False readings at the edges of the band stayed below
  2.5%, but a true slope of 1 was read as "within tolerance" in 0% of the data sets unless every family had
  several hundred items (S8).
- **Within-family fit ranks measures for the families it was computed in.** If validity does not depend on the
  family, fit and transfer agree and the procedure adds little to the ranking. If it does, the better-fitting
  measure transfers worse in a third to nearly all of the data sets, and no selection rule applied to the training
  families, including transfer among them, does better. Only the held-out family shows it (S4).


## Limitations of the simulation as a whole

- The generating model is the model of the analysis plus item and participant effects. Not varied: several
  samples per family, incomplete designs in which participants respond to a subset of the items, families of
  unequal size, intercepts that differ between families, floor and ceiling accuracy, guessing, non-normal
  measures other than the uniform and level designs of S2, differences between participants in the effect of
  the measure, and item residuals that correlate with the measure.
- Only one held-out family is scored per data set, and families are exchangeable except where a study makes
  the held-out family different. Nothing is said about combining the folds of one data set.
- Single-measure models only; the combined model of the package and the weighting diagnostic were not
  examined. The level-indicator baseline and the common-range remedy were examined in one scenario each.
- All intervals are 95% percentile intervals with 500 resamples and 10 item splits inside each resample (100
  for the estimate, against the package default of 500). The bias-corrected interval was not examined.
- Monte Carlo error: 1,000 data sets per cell for all coverage and detection rates of S1 to S3 (2,000 in the
  common-slope cell of S1 and in S2c and S4). Fewer were used in three places, because of run time: 500 for
  the larger design of S2a (which serves means and one rate), and 200 to 500 in S5, where the effects are
  tens of percentage points.
- Slopes are expressed per standard deviation of the measure within a family. A measure whose spread differs
  between families changes the meaning of "the same slope"; S2b covers the range, not the spread.
- The run shared its two cores with another job for the first two hours, and two runs were stopped by a time
  limit and resumed from saved chunks; results do not depend on this (seeds are fixed per cell and
  replication), but the recorded wall times do. While the study ran, the package received an unrelated
  addition (a basic interval type); the test suite passed afterwards (73 tests at that time, version 0.1.0; the released version 0.2.0 has 78 tests) and the agreement between the
  simulation engine and the public `transfer()` and `diagnose()` was confirmed again at the end
  (`results/sim00_public_api_agreement_after_runs.csv`).


## Reproduction

`./run_all.sh` in this directory runs everything (resume-safe: finished chunks in `results/raw/` are skipped).
Seeds: `numpy.random.default_rng([study seed, cell number, chunk x 1000 + replication])`, study seeds 2601 to
2608. Run times, core count and package versions are in `results/run_info.json` and `results/*_run_info.json`
(S1 to S5 about 5.0 hours of wall time on two cores, part of it shared with another job; S6 to S8 about
1.0 hour). No change was made to
the package `itemtransfer` for this study.

Reference: Morris, T. P., White, I. R., & Crowther, M. J. (2019). Using simulation studies to evaluate
statistical methods. *Statistics in Medicine, 38*(11), 2074-2102. https://doi.org/10.1002/sim.8086
