# Figure captions (simulation study)

Files: `fig1_separation`, `fig2_design_features`, `fig3_operating_characteristics`, `fig4_bootstrap_comparison`,
`fig5_ranking` (each as 300 dpi PNG and as PDF). All figures are produced by `make_figures.py` from the saved
results. Unless stated otherwise the design is the base case: four item families (one held out, three for
training), 48 items and 40 participants per family, a true slope of 0.5 logits per standard deviation of the
measure, an item residual standard deviation of 0.5 logits and a participant standard deviation of 0.8 logits.

**Figure 1. The three criteria respond to different properties of the data.**
(A) Ordering, (B) scale and (C) prediction for the held-out family in ten conditions. Left of the dotted line the
true measure is analysed and the true slope in the held-out family is the training slope multiplied by the factor
shown ("slope x 2" to "slope 0"; "slope reversed": factor -1). Right of the dotted line the slope is the same in all
families and the measure analysed is a null measure or a proxy measure that has no effect of its own and correlates
.7 with the true measure in all families, in the training families only, or in the held-out family only. Filled
circles are medians over the simulated data sets, bars run from the 5th to the 95th percentile, and open diamonds
are the large-sample values (absent where the large-sample training slope is zero and the value is not defined).
Triangles mark bars that continue beyond the plotted range. Dashed line in B: calibration slope of 1. (D)
Calibration slope when the true slope in the training families is weaker than in the held-out family (0.5). Open
circles: data sets in which the interval of the training slope included 0 (weak training relation flagged);
filled circles: data sets without the flag; groups with fewer than 20 data sets are not drawn. The percentages
give the share of flagged data sets. 2,000 data sets in the condition with the same slope, 1,000 in all others.

**Figure 2. Design features of the held-out family that change what the criteria can show.**
(A) Ordering in the held-out family when its measure is continuous, takes four designed levels or takes two
designed levels, for a graded true relation (circles, left group of each triple) and for a step between the lower
and the upper half of the range with no graded effect (squares, right group). Filled black: the transferred
measure; open: a level indicator; small grey: mean correlation between measure and accuracy within the levels. For the continuous measure, the two halves of a
median split serve as levels. (B) Log-loss reduction of the level indicator minus that of the transferred measure;
values above zero mean that the indicator, which is fitted in the held-out family, predicts better than the
measure. Bars in A and B: 95% Monte Carlo intervals of the mean. (C) Calibration slope when the range of the
measure in the held-out family equals the training range (1 to 4), is shifted (2 to 8) or is wider (1 to 8), for
a relation that is linear, logarithmic or saturating in the measure. Symbols: large-sample values for the measure
as given, for all families restricted to the common range, and for the logarithm of the measure; bars: 5th to
95th percentile of the estimates (48 items, 40 participants). Dashed line: 1. (D) Mean ordering as a function of
the number of participants (trials per item) for three item residual standard deviations: observed, observed
divided by the square root of the split-half reliability of item difficulty, and the value for the same items
without response noise (horizontal marks).

**Figure 3. Operating characteristics of the two-way bootstrap intervals, one design factor at a time.**
Each column varies one factor around the base case. (A) Detection rate: share of data sets in which the 95%
interval of the calibration slope excludes 0 (scale), the interval of the log-loss reduction lies above 0
(prediction) and the interval of the ordering correlation lies above 0 (ordering). (B) Coverage of the 95%
interval: calibration slope and log-loss reduction against their large-sample values, ordering against its
expected value in the design (the ordering correlation has no large-sample value that is independent of the
number of participants). Dashed line: nominal 95%. (C) Median width of the interval of the calibration slope and
the width that the spread of the estimates would justify (the range of the central 95% of the estimates over
the simulated data sets), on a logarithmic axis. 1,000 data sets per cell, 500 bootstrap resamples.

**Figure 4. Which units to resample.**
The two-way bootstrap of the procedure (participants within samples and items within families) compared with
resampling participants only and with resampling items only, in twelve designs labelled by items per family, true
slope and item residual standard deviation ("small design": three families, 24 items, 20 participants, slope 0.5,
item residual standard deviation 1). (A) Coverage of the interval of the calibration slope and (B) of the
log-loss reduction, against the large-sample values. (C) Share of data sets in which the interval of the
calibration slope of a null measure excludes 0 and (D) in which the interval of its log-loss reduction lies above
0. Dashed lines: nominal 95% in A and B, 5% in C and 2.5% in D. Bars: 95% Monte Carlo intervals. 1,000 data sets
per design.

**Figure 5. Fit within the training families and transfer to the held-out family can rank two measures
differently.**
Two measures A and B are noisy versions of the latent driver of difficulty; the validity of a measure in a family
is its correlation with that driver. (A) Rate at which the measure that explains more deviance within the
training families has the smaller log-loss reduction in the held-out family, when the validities are drawn at
random for every family around the two means shown; the horizontal axis is the between-family standard deviation
of validity. (B) The same rate when validities are fixed: A is the true measure (validity 1) or has validity .6
in every family, and B has the validity shown in the training families and in the held-out family. (C) Mean
log-loss reduction in the held-out family of the measure selected by three rules that use the training families
only (deviance explained with a common slope, deviance explained with separate slopes per family, and
leave-one-family-out transfer among the training families), compared with always using the measure that is
better on average (horizontal marks). "Unit SD": measure B is the more valid measure in every family, but its
unit differs between families by a log-normal factor with the standard deviation shown. Dashed lines: 50%.
Bars: 95% Monte Carlo intervals. 2,000 data sets per condition.

**Figure 6. Readings of the tolerance rule for the calibration slope.**
Share of simulated data sets in which the calibration slope was read as within tolerance (whole interval inside
0.80 to 1.25; solid lines, filled symbols) or outside tolerance (whole interval outside; dashed lines, open
symbols), as a function of the true calibration slope, for (A) 48, (B) 192 and (C) 768 items in the held-out
family (48 items in each of the three training families, 40 participants). Black circles: two-way 95% percentile
interval; grey triangles: items-only 95% percentile interval. The remaining data sets were read as undetermined.
Vertical dotted lines: edges of the band; horizontal dashed line: 2.5%. 1,000 data sets per point in A and B,
300 in C.
