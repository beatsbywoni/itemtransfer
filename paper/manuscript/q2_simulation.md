## Simulation study

The simulation study has five aims. The first is to show which property of the data each criterion responds to. The second is to show how the design of the held-out family changes what a criterion can show. The third is to establish when the intervals can be trusted. The fourth is to compare the procedure with the analyses that a researcher would otherwise run. The fifth is to examine the tolerance rule and the consequences of a model without random effects. None of the aims depends on a particular task. The report follows Morris et al. (2019).

### Data generation, conditions and analysis

Responses were generated from the model of step 3 with two additions on the logit scale. Each item received a residual, which stands for everything that makes items differ in difficulty and that the measure does not capture. Each participant received an ability. Both were normally distributed. In the base condition there were four families, of which one was held out. Each family had 48 items and one sample of 40 participants, and every participant responded to every item. The measure was standard normal. Its slope was 0.5 logits per standard deviation in every family, which is called a relation of medium size below. Item residuals had a standard deviation of 0.5 logits, so that the measure and the residual contributed equally to the true variance of item difficulty. Abilities had a standard deviation of 0.8 logits, and mean accuracy was about .70.

Each aim varied this condition: the slope in the held-out family, the number of levels and the range of the measure, the form of the relation, and the numbers of families, items and participants. The conditions are named where their results are reported, and the supplementary material lists them all, with bias and root mean squared error. Every data set was analysed with the `itemtransfer` package. Intervals were 95% percentile intervals from 500 resamples. The true values of the calibration slope and of the reduction in log loss were computed from a data set large enough to remove sampling error, with 120,000 items per family. For ordering, the target is the mean of the observed correlation over data sets with the same numbers of items and participants (Table 4). Performance is summarised by three rates. Coverage is the share of intervals that contain the true value or, for ordering, the target. The detection rate is the share of intervals that exclude 0 in the expected direction. The false-positive rate is the same share for a measure that has no relation with accuracy. Rates are based on 1,000 data sets unless noted, which gives Monte Carlo standard errors of at most 1.6 percentage points.

### The three criteria respond to different properties

With the same slope in all families, the criteria agreed on average and differed in power (Figure 2A to 2C). The median calibration slope was 1.01. The intervals of the calibration slope and of ordering excluded 0 in 99% and 98% of the data sets, the interval of the reduction in log loss in only 48%. A perfectly transferring relation of medium size reduces log loss by about 3%, and a design of this size cannot reliably distinguish 3% from nothing.

The calibration slope recovered the ratio of the held-out slope to the training slope: its medians were 2.03, 0.49, 0.25 and −1.01 for ratios of 2, 0.5, 0.25 and −1. Ordering weakened with a smaller held-out slope and stayed positive on average. Prediction followed the approximation of step 3 in this condition, whose effect is of medium size. In very large samples the reduction in log loss was 0 to three decimal places when the held-out effect was half the trained effect, and negative below that. A reduction in log loss near 0 or below, next to a calibration slope of about 0.5 or less, is therefore a consequence of the mismatch in scale and not additional evidence against the measure.

Transfer is evidence about a relation and not about its cause. A proxy, that is, a measure without an effect of its own that correlated .7 with the true measure, appeared to transfer when the correlation held in every family, with a median calibration slope of 1.02. It failed on all three criteria when the correlation held in the training families only, and it was flagged as a weak training relation when the correlation held in the held-out family only.

A weak training relation made the calibration slope meaningless (Figure 2D). With a training slope of 0.05 and a held-out slope of 0.5, the central 90% of the estimates ran from −43 to 50. The flag of step 4 was raised in 94% of these data sets.

*Figure 2 about here.*

### The design of the held-out family limits the conclusion

A family with two levels of the measure could not distinguish a graded relation from a step, in which all items above the middle of the range are harder by a fixed amount (Figure 3A and 3B). Ordering was .57 under the graded relation and .56 under the step, and both were detected in 98% of the data sets. The level indicator ordered the items better than the measure in both cases, and within the levels the measure hardly ordered the items even when the true relation was graded. With four levels, 96 items and 80 participants the comparison became informative: under a step, the indicator predicted better than the measure in 89% of the data sets.

A different range of the measure changed the calibration slope when the relation was not linear, although the mechanism was identical (Figure 3C). The measure ranged from 1 to 4 in the training families and, in the condition reported here, from 2 to 8 in the held-out family. When accuracy depended on the logarithm of the measure, the calibration slope was 0.51 in very large samples. When the effect levelled off at high values, a saturating relation, it was 0.34, and the reduction in log loss was negative. Restricting all families to their common range restored a calibration slope of 1.00 in every case, at the price of precision, because a third of the items remained. Transforming the measure helped only when the transformation was the correct one.

Ordering was attenuated by response noise as classical test theory predicts (Figure 3D). The ratio of the observed ordering to the ordering against error-free accuracies equalled the square root of the split-half reliability to within .03 in all twelve conditions, so the classical relation was a good approximation for rank correlations here. A measure that was the only source of item difficulty reached an ordering of only .53 with 10 participants. Dividing the observed ordering by the square root of the reliability recovered the error-free value when the reliability was about .6 or higher. Below that, the corrected value overshot.

*Figure 3 about here.*

### Intervals depend on what is resampled

The intervals of the calibration slope and of the reduction in log loss from the bootstrap over participants and items contained the true value at least as often as they should (Figure 4). Coverage lay between 96.5% and 100% in all 25 conditions with a common slope, and a measure without relation was declared related in at most 0.2% of the data sets. The intervals were 1.1 to 2.1 times wider than the actual spread of the estimates across data sets. Resampling adds new sampling error on top of the error that the observed accuracies already contain. The price is power, above all for prediction. In this set of runs its detection rate was 46% in the base condition, 86% with 96 items and 99% with 192 items.

Precision depended on the held-out items far more than on the number of families. The median width of the calibration-slope interval fell from 1.32 to 1.04 between 3 and 10 families, and from 1.86 to 0.57 between 24 and 192 items.

Resampling participants only, which treats the items as fixed, failed (Table 3). Coverage was as low as 51%, and a measure without relation was declared related in up to 37% of the data sets. More participants make this worse, because the interval shrinks while the variation between items remains. Resampling items only gave coverage between 91% and 97% across all conditions examined. That stimuli must be treated as a sample has long been established for significance tests (Clark, 1973); these results show the size of the error for transfer statistics.

**Table 3.** Calibration slope: coverage of the 95% interval, and false-positive rate for a measure without relation, when participants and items, participants only or items only are resampled.

| Items per family | Slope | Item residual | Coverage: both | Coverage: participants | Coverage: items | False positives: both | False positives: participants | False positives: items |
|---|---|---|---|---|---|---|---|---|
| 48 | 0.5 | 0 | .997 | .926 | .910 | .000 | .061 | .003 |
| 48 | 0.5 | 0.5 | .988 | .781 | .952 | .000 | .137 | .001 |
| 48 | 0.5 | 1 | .967 | .508 | .941 | .002 | .311 | .004 |
| 96 | 0.25 | 1 | .974 | .529 | .953 | .001 | .259 | .003 |
| 96 | 1 | 1 | .965 | .583 | .932 | .001 | .366 | .003 |

*Note.* 1,000 data sets per row. The second row is the base condition.

The interval of the ordering correlation needed a different treatment (Table 4). In the bootstrap over participants and items, the resampled correlations lay .04 to .16 below the estimate in every condition. With 48 items the shift was hidden inside a wide interval. With 768 items the interval contained the target in only 54% of the data sets, and with 3,072 items it excluded its own estimate in every data set. A second kind of bootstrap interval that corrects for such a shift, the basic interval, did not help, and it declared a measure without relation related in 6% to 13% of the data sets. When only items were resampled, 93% to 95% of the intervals contained the target at every number of items in the base condition. Across all 23 conditions examined, the share lay between 90.5% and 99%. The lowest values occurred where participants are the main source of error, that is, with few participants or without item residuals, because this interval does not resample participants. The target here is the average ordering correlation for samples of the given size. It is not the correlation with error-free item difficulty, which no finite sample attains; the reliability of step 2 shows how much higher that would be. The items-only interval is the one that the procedure uses.

**Table 4.** Interval of the ordering correlation: share of 95% intervals that contain the target, by number of held-out items and bootstrap.

| Items per family | Participants and items, percentile | Participants and items, basic | Items only, percentile | Percentile interval of participants and items excludes its own estimate |
|---|---|---|---|---|
| 48 | .97 | .83 | .93 | .00 |
| 192 | .90 | .77 | .94 | .00 |
| 768 | .54 | .53 | .95 | .41 |
| 3,072 | .06 | .02 | .94 | 1.00 |

*Note.* Base condition with 40 participants; 500 data sets for 48 and 192 items, 300 for 768 and 200 for 3,072. The target is the mean ordering correlation over data sets of the same size.

*Figure 4 about here.*

### Comparison with alternative analyses

Nine scenarios were analysed by the procedure and by two alternatives that need no special software (Table 5). The first was grouped cross-validation in its common default form, without recalibration and with a point score. One model with a single intercept is fitted on the training families. Its log loss on the held-out family is compared with that of a model that predicts the mean accuracy of the training data. The share of log loss removed is the score. The second was a test of whether the slopes of the four families differ. It was run once with the standard errors of an ordinary logistic regression and once with standard errors that treat the responses to one item as a cluster, called item-based below.

The test of slope differences needed item-based standard errors, and even then it rejected somewhat too often. With ordinary standard errors it rejected equal slopes in 31% of the data sets in which the slopes were equal, and in 72% for a measure without relation and large item residuals. With item-based standard errors the rejection rate under equal slopes was 7% to 9%, moderately above the nominal 5%. This test detected a difference in slope more often than the procedure did. When the held-out slope was half the training slope, it rejected in 54% of the data sets, whereas the interval of the calibration slope excluded 1 in 42%. For the question whether slopes differ, the test is the more sensitive tool, and the scale criterion of the procedure, which for a single measure is a ratio of two slopes, should be read together with it.

Grouped cross-validation was distorted by differences in mean accuracy. With equal slopes, the mean score was .030 when all families were equally hard, .021 when the held-out family was easier and .023 when it was harder. The score was negative in 1%, 16% and 14% of the data sets, respectively. The mean of the prediction criterion of the procedure, which re-estimates the intercept, stayed between .029 and .031. The score is a point estimate. For a measure without relation it was positive in 41% to 44% of the data sets, as a statistic centred near 0 will be, whereas the interval of the prediction criterion never lay above 0. The two columns of Table 5 therefore apply different rules, a sign and an interval, and the comparison shows what the default use of grouped cross-validation leaves out. It does not show that grouped cross-validation with recalibration and resampled intervals would perform worse; that analysis is in effect the prediction criterion of the procedure.

The two design problems were invisible in the main output of every method. With a step relation and a two-level family, all methods indicated successful transfer. With a saturating relation and a shifted range, all methods indicated a much weaker effect in the held-out family. Only the diagnostics of step 4 pointed to the level structure and to the range.

**Table 5.** The procedure and two alternative analyses in nine simulated scenarios.

| Scenario | Calibration slope, median | Prediction: interval above 0 | Grouped cross-validation: score above 0 | Slopes differ, ordinary SE | Slopes differ, item-based SE |
|---|---|---|---|---|---|
| Same slope in all families | 1.00 | .47 | .99 | .31 | .08 |
| Same slope, held-out family easier | 1.03 | .36 | .84 | .32 | .09 |
| Same slope, held-out family harder | 0.99 | .51 | .86 | .36 | .08 |
| Held-out slope half the training slope | 0.51 | .00 | .52 | .84 | .54 |
| Held-out slope twice the training slope | 2.01 | 1.00 | 1.00 | 1.00 | .97 |
| Step relation, two levels in the held-out family | 1.16 | .64 | 1.00 | .45 | .11 |
| Saturating relation, shifted range | 0.34 | .00 | .43 | 1.00 | .98 |
| No relation, item residual 0.5 | 0.00 | .00 | .41 | .36 | .09 |
| No relation, item residual 1 | 0.06 | .00 | .44 | .72 | .07 |

*Note.* Entries other than the calibration slope are shares of 1,000 newly generated data sets per scenario. The prediction column counts 95% intervals above 0; the grouped cross-validation column counts positive point scores, without recalibration of the intercept. The data sets were newly generated, so the first row differs slightly from the base condition reported above. "Slopes differ" is the rejection rate at the .05 level of a test of equal slopes in the four families. SE = standard error.

A logistic mixed model with crossed random intercepts for participants and items is the analysis that many readers would choose, and it was added as a third alternative in six scenarios (Table 6). Its likelihood-ratio test of equal slopes in the training families and the held-out family rejected equal slopes in 7% of the data sets with equal slopes, and it detected a held-out slope of half the training slope in 61%, more often than either the item-based test above or the procedure. Its ratio of slopes was also unaffected by differences between participants: when abilities varied twice as much in the held-out family, the median ratio was 0.98, against 0.83 for the slopes without random effects. The mixed model was not immune to differences between families. When the item residuals were twice as large in the held-out family, which violates its assumption of one item variance, it rejected equal slopes in 13% of the data sets. For the question whether slopes differ, a mixed model is therefore the best of the analyses compared here, and the scale criterion should be read together with it where it can be fitted.

**Table 6.** A logistic mixed model with crossed random intercepts compared with a logistic regression without random effects: ratio of the held-out slope to the training slope, and rejection of equal slopes.

| Scenario | Ratio of slopes, mixed model | Ratio of slopes, no random effects | Equal slopes rejected, mixed model | Equal slopes rejected, no random effects |
|---|---|---|---|---|
| Same slope in all families | 1.02 | 1.01 | .07 | .19 |
| Held-out slope half the training slope | 0.51 | 0.51 | .61 | .85 |
| Held-out slope twice the training slope | 1.98 | 1.99 | 1.00 | 1.00 |
| Same slope, abilities vary twice as much in the held-out family | 0.98 | 0.83 | .03 | .35 |
| Same slope, item residuals twice as large in the held-out family | 0.95 | 0.90 | .13 | .41 |
| No relation, item residual 1 | | | .06 | .46 |

*Note.* 200 data sets per scenario, generated as in the base condition. Ratios are medians. Rejection rates are for likelihood-ratio tests at the .05 level; Monte Carlo standard errors are at most .035. The mixed models were fitted with the R package lme4 (Bates et al., 2015).

A random-effects meta-analysis of the four slopes, reported in the supplementary material, estimated the variation between families as exactly zero in more than half of the data sets with a common slope.

### The tolerance rule and the model without random effects

The tolerance rule made few errors and was rarely decisive. When the true calibration slope was exactly 0.80 or 1.25, the rule returned "within tolerance" in at most 1.7% of the data sets and "outside tolerance" in at most 2.3%. The rule can return "within tolerance" only if the interval is narrower than 0.45, the width of the tolerance. With 48 items in each training family, the median width was 1.19 with 48 held-out items and 0.64 with 768, because the training slope stays uncertain. A true slope of 1 was therefore almost always "undetermined". Only when every family had 768 items was it classified as within tolerance in 81% of the data sets. In designs of ordinary size the rule can show that an effect size differs, and it will otherwise return "undetermined".

Because the model has no random effects, families can differ in calibration slope although the measure acts identically in each. More variation between participants, or between items beyond the measure, flattens the slope that the model estimates. With the same generating slope everywhere, the calibration slope in very large samples was 0.80 when the standard deviation of abilities in the held-out family was twice that in the training families. It was 0.90 when the item residuals were twice as large. Differences in mean accuracy changed it by at most 0.09. Deviations of 10% to 20% from 1 can thus arise without any difference in how the measure acts, which is a reason for a tolerance and against a test of the value 1.

### Summary and limits of the simulation study

The simulation supports the procedure in three respects and limits it in two. The three criteria answer different questions. The level and range diagnostics identify held-out families that cannot support a conclusion about the form or the size of a relation. The intervals for scale and prediction from the bootstrap over participants and items were conservative in the conditions with a common slope. The items-only interval for ordering was far better calibrated than the interval from participants and items; its coverage lay between 90.5% and 99% in complete designs and is not established for sparse or unbalanced designs, several samples per family or combined predictors. On the other side, about 100 held-out items were needed before all three criteria detected a relation of medium size in most data sets. Agreement in effect size could be shown only with several hundred items in every family.

The data were generated from the model of the analysis with item and participant effects added, mostly for complete designs with one sample per family and families of equal size. The simulation check of step 5 exists so that users can repeat the check of the scale and prediction intervals for their own design.
