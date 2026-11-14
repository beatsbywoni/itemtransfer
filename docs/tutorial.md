# Tutorial: the five steps on the bundled example

This tutorial walks through leave-one-family-out transfer validation with the small synthetic data set that ships
with the package. All output shown below was produced with the code as printed (seed 1). Run times refer to a
laptop with two cores.

## Vocabulary

- **item**: one stimulus (a puzzle, a word, a test item).
- **item family**: a set of items produced by one design or generator. Families share no item.
- **sample**: one group of participants who responded to (a subset of) the items of one family.
- **measure**: an item-level difficulty predictor computed from the item alone.
- **held-out family** and **training families**: each family is held out in turn; the others are used for training.

## The example data

```python
import itemtransfer as it

trials, items = it.load_example()
trials.head(3)
```

```
  participant    item family sample  correct
0     A1_p000  A_0000      A     A1        1
1     A1_p000  A_0001      A     A1        0
2     A1_p000  A_0002      A     A1        1
```

```python
items.head(3)
```

```
     item family      x     x2  x_null
0  A_0000      A  0.261 -0.605   0.765
1  A_0001      A  0.676  1.375   0.946
2  A_0002      A  0.521 -0.541   0.461
```

The data contain 6,120 responses to 168 items in three families. They were simulated with
`it.simulate(it.example_design(), seed=2026)`, so the truth is known:

- the measure `x` lowers the logit of a correct response by 3 per unit in every family;
- `x2` is correlated with `x` (r = .6) but has no effect of its own;
- `x_null` is unrelated to accuracy;
- family A has two samples (A1: 30 participants, 60 items; A2: 25 participants, the first 40 of these items);
- family B has one sample (40 participants, 48 items);
- family C has one sample (35 participants who each saw 40 of its 60 items), and `x` takes only two designed
  levels in it (about 0.2 and about 0.8).

Your own data need the same two tables. If your columns have other names, pass for example
`columns={"participant": "subject", "correct": "acc"}` to any function.

## Step 1. Recompute the measures

Compute every measure for every item with one implementation, and compare the values with published ones where
they exist. This step depends on the task and is not part of the package. The result is the `items` table.

## Step 2. Reliability ceiling

A measure cannot be asked to predict what is not reproducible. The first question is therefore how reliable the
item difficulties are.

```python
rel = it.reliability(trials, seed=1)
rel[["sample", "n_participants", "n_items", "trials_per_item_median",
     "logit_sb", "logit_sb_lo", "logit_sb_hi"]].round(2)
```

```
sample  n_participants  n_items  trials_per_item_median  logit_sb  logit_sb_lo  logit_sb_hi
    A1              30       60                    30.0      0.82         0.73         0.88
    A2              25       40                    25.0      0.75         0.61         0.84
    B1              40       48                    40.0      0.78         0.67         0.86
    C1              35       60                    23.0      0.79         0.71         0.86
```

`logit_sb` is the median, over 1,000 random splits of the participants into halves, of the Spearman-Brown corrected
correlation between the item logits of the two halves. The two bounds are the 2.5th and 97.5th percentiles over
the splits. They show how much the estimate depends on the split of this one sample; they are not a confidence
interval. The columns `spearman_sb*` give the same on the rank scale.

Samples A1 and A2 share 40 items, so their agreement can be computed:

```python
ag = it.agreement(trials, "A1", "A2", seed=1)
ag[["n_shared", "r_logit", "r_logit_lo", "r_logit_hi", "rel_a", "rel_b",
    "r_corrected", "r_corrected_lo", "r_corrected_hi"]].round(2)
```

```
 n_shared  r_logit  r_logit_lo  r_logit_hi  rel_a  rel_b  r_corrected  r_corrected_lo  r_corrected_hi
       40     0.76        0.57        0.87   0.82   0.75         0.96            0.82            1.16
```

The raw correlation between the two samples is .76. Divided by the square root of the product of the two
reliabilities (computed on the 40 shared items) it is .96: within the limits set by measurement error, the two
samples agree on which items are hard. The intervals come from resampling items. When the same participants
contribute to both samples (two sessions, say), `agreement` also reports the correlation between disjoint halves
of the participants, which is free of what individual participants carry over from one session to the other.

Read the transfer results against this ceiling. With reliabilities near .8, no measure can reach an ordering
correlation of 1.

## Step 3. Transfer: three criteria that can disagree

```python
res = it.transfer(trials, items, ["x", "x2", "x_null"], n_boot=2000, seed=1)   # about 6 s
cols = ["family", "model", "train_slope", "ordering", "calibration_slope",
        "calibration_slope_lo", "calibration_slope_hi",
        "logloss_reduction", "logloss_reduction_lo", "logloss_reduction_hi"]
res.table[cols].round(2)
```

```
family    model  train_slope  ordering  calibration_slope  calibration_slope_lo  calibration_slope_hi  logloss_reduction  logloss_reduction_lo  logloss_reduction_hi
     A        x        -2.46      0.72               1.06                  0.67                  1.57               0.05                  0.02                  0.10
     A       x2        -0.27      0.47               1.25                  0.54                  3.54               0.02                  0.00                  0.04
     A   x_null         0.11      0.10               0.57                 -5.87                  8.05               0.00                 -0.02                  0.01
     A combined          NaN      0.67               1.01                  0.55                  1.44               0.05                  0.01                  0.09
     B        x        -2.59      0.63               0.88                  0.49                  1.38               0.03                 -0.00                  0.06
     B       x2        -0.35      0.25               0.51                 -0.13                  1.50               0.00                 -0.04                  0.03
     B   x_null         0.11     -0.06              -0.15                 -7.99                  7.97              -0.00                 -0.02                  0.01
     B combined          NaN      0.64               0.89                  0.47                  1.38               0.03                 -0.00                  0.07
     C        x        -2.50      0.71               1.02                  0.66                  1.51               0.10                  0.04                  0.16
     C       x2        -0.28      0.46               1.38                  0.41                  3.40               0.02                 -0.00                  0.05
     C   x_null         0.04      0.20               5.75                -54.21                 57.83               0.00                 -0.01                  0.02
     C combined          NaN      0.66               0.98                  0.61                  1.45               0.10                  0.03                  0.16
```

Each row holds out one family (`family`) and judges one model on it. For the row `A, x`, the model
`logit P(correct) = a_sample + b * x` was fitted to the trials of families B and C, with one intercept per sample.

- **`train_slope`** is `b`. Here it is about -2.5. (The generating slope of -3 applies to one participant and one
  item; averaged over participants and items the relation is flatter. This is expected.)
- **`ordering`** is the Spearman correlation between `b * x` and item accuracy in the held-out family. It asks
  whether the measure puts the held-out items in the right order.
- **`calibration_slope`** asks whether the effect has the right size. The held-out trials are regressed on
  `b * x` with a free intercept. A slope of 1 means that the trained effect holds in the held-out family; 0 means
  no relation; a value between 0 and 1 means that the effect is weaker there than in training; a value above 1
  that it is stronger. For `x` the three slopes are 1.06, 0.88 and 1.02, and all three intervals include 1 and
  exclude 0.
- **`logloss_reduction`** asks how much the transferred relation improves the prediction of single responses.
  The slope stays at its training value. Because overall accuracy differs between families, the intercept is
  fitted on a random half of the held-out items and the predictions are scored on the other half; the halves then
  swap, and this is repeated for 500 random splits. The value is the relative reduction in log loss against a
  model with an intercept only. `brier_reduction` is the same for the Brier score.

The intervals of the calibration slope and of the reductions come from a two-way bootstrap: participants are
resampled within each sample and items within each family, and the training fit is repeated in every resample.
The interval of the ordering correlation comes from the same item resamples with the participants kept as they
are, because resampled participants add noise to item accuracies and pull a rank correlation towards zero. The
column `scale_reading` compares the interval of the calibration slope with the tolerance (default 0.80 to 1.25):
`within tolerance`, `outside tolerance`, or `undetermined` when the interval crosses a limit.

Three things in this table are worth noting.

1. *The criteria measure different things.* In family B the ordering of `x` is clear (.63) and its calibration
   slope is close to 1, but the interval of the log-loss reduction reaches 0: the gain in predicting single
   responses is small even for a measure that works.
2. *A correlated measure can appear to transfer.* `x2` has no effect of its own, yet its training slope is
   negative and its calibration slope interval excludes 0 in families A and C, because it is correlated with `x`.
   The `combined` rows show that it adds nothing to `x`.
3. *The calibration slope of `x_null` is meaningless.* Its training slope is close to 0, so the transferred
   predictor is nearly constant and the calibration slope is a ratio with a denominator near zero (5.75 with an
   interval from -54 to 58 in family C). Step 4 flags this.

Useful options: `weights="equal"` gives every training sample the same total weight instead of letting every
trial count once; `evaluate={"A": "A1"}` computes the criteria for family A on sample A1 only. By default the
samples of a held-out family are pooled: their responses per item are added, and the criteria refer to this pooled
population with one evaluation intercept, whereas the training fit has one intercept per sample. Pooled criteria
are not adjusted for the sample, so evaluate samples one at a time when they differ in overall accuracy and in
which items they answered; `holdout=["C"]` holds out only some families; `combined=False` skips the model
with all measures. `res.predictions` contains the transferred predictor and the accuracy of every held-out item,
and `res.bootstrap[("A", "x")]` the resampled statistics.

```python
fig = it.plot_transfer(res, "x")      # optional, needs matplotlib
```

## Step 4. Design diagnostics

```python
diag = it.diagnose(trials, items, ["x", "x2", "x_null"], result=res)   # about 1.5 s
for w in diag["warnings"]:
    print("-", w)
```

```
- The values of measure 'x' fall into 2 tight clusters in held-out family 'C'. Ordering and prediction in this
  family may be dominated by the contrasts between the clusters; the relations within the clusters are reported
  separately: a level indicator fitted in the family reduces log loss by 0.097, the transferred measure by 0.099.
  Within the levels, the correlations between measure and accuracy are 0.21, -0.05.
- The training slope of 'x_null' for held-out family 'A' has an interval that includes 0 (-0.0783 to 0.287). The
  calibration slope is then a ratio with a denominator near zero and is not informative; read the training slope
  and the held-out slope instead.
- (the same warning for held-out families 'B' and 'C')
```

`diagnose` returns a dictionary of tables and this list of warnings. The tables are:

**`levels`, `level_baseline`, `within_level`: level structure.** In family C the measure `x` takes two designed
levels. A design with two levels can show that the levels differ in difficulty; it cannot show that the measure
is the right scale between or within them. The package therefore compares the measure with a level indicator
(one probability per level, fitted on the calibration half of the held-out items):

```python
diag["level_baseline"].round(3).T
```

```
family                               C
measure                              x
n_levels                             2
kind                         clustered
ordering_measure                 0.706
ordering_levels                  0.835
level_accuracy_r                 0.801
logloss_reduction_measure        0.099
logloss_reduction_levels         0.097
logloss_difference               0.002
logloss_difference_split_lo     -0.001
logloss_difference_split_hi      0.013
```

The level indicator predicts as well as the transferred measure (0.097 against 0.099), and inside the two levels
the measure does not order the items (`within_level` gives correlations of 0.21 and -0.05 over ranges of 0.06).
The result for family C therefore supports "items with high `x` are harder than items with low `x`" and nothing
finer. Note that the ordering correlation of the two-level indicator (.84) is higher than that of the measure
itself (.71): with two levels, small differences in `x` within a level add rank noise.

A measure counts as having few levels when it has at most `max_levels` (6) distinct values, or when its values
form up to 6 groups whose gaps are at least `min_gap_ratio` (2) times as wide as the widest group.

**`range`: range overlap.** For each held-out family, the table gives the range of the measure in the held-out
and in the training families, the share of held-out items inside the training range, and the criteria recomputed
on the common range (all families restricted to the overlap, or to limits you pass as
`range_limits={"x": (low, high)}`). A warning appears when fewer than 80% of the held-out items lie inside the
training range, because the trained slope is then extrapolated. If the effect of a measure is not linear, a slope
per unit depends on the range covered; comparing `calibration_slope` with `calibration_slope_common` shows
whether this matters. To test another scale, add a transformed column (for example the logarithm of the measure)
to `items` and treat it as a further measure.

**`weak_training`: weak training relation.** The calibration slope divides the held-out slope by the training
slope. When the interval of the training slope includes 0, the row is flagged and the table shows the slope
fitted in the held-out family itself (`heldout_slope`), which remains interpretable.

**`measure_correlations`: collinearity by design.** Spearman correlations between the measures within each
family. Here `x` and `x2` correlate between .51 and .61, below the warning threshold of .7 but enough to explain
why `x2` appears to transfer.

**`weighting`: weighting of the training samples.** The criteria with training samples weighted by trials and
equally. In this example the two agree (for `x`: 1.06 and 1.06, 0.88 and 0.89, 1.02 and 1.03). A warning appears
when the calibration slopes differ by more than 0.25 and by more than a quarter of the larger one.

## Step 5. Uncertainty: can the intervals be trusted?

The labels attached to results ("transfers", "does not transfer") rest on bootstrap intervals. Whether such an
interval has the coverage it claims depends on the design: the number of families, items and participants, and
the distribution of the measure. The package lets you check this on data simulated to resemble your own.

```python
design = it.design_from_data(trials, items, "x", seed=1)
round(design.slope, 2), round(design.participant_sd, 2), round(design.item_sd, 2)
```

```
(-3.06, 0.83, 0.55)
```

`design_from_data` keeps the observed values of the measure, the numbers of participants and items and the
pattern of who saw what, and calibrates a generating model so that simulated data reproduce the observed slope,
intercepts and spread of participant and item accuracies. (The values used to generate the example were -3, 0.8
and 0.5.) By default all families share one slope, so the design represents successful transfer.

```python
chk = it.check_intervals(design, n_sim=200, n_boot=200, n_jobs=2, seed=1)   # about 10 s; calibration slope only
chk[["family", "measure", "target", "mean_estimate", "coverage", "coverage_se",
     "mean_width", "rate_excludes_0", "rate_weak_training"]].round(2)
```

```
family measure  target  mean_estimate  coverage  coverage_se  mean_width  rate_excludes_0  rate_weak_training
     A       x    1.01           1.00      0.98         0.01        0.83              1.0                0.00
     A  x_null     NaN          -0.72       NaN          NaN       30.92              0.0                0.96
     B       x    1.00           1.04      0.98         0.01        1.00              1.0                0.00
     B  x_null     NaN          -0.00       NaN          NaN       35.11              0.0                0.96
     C       x    0.99           0.99      1.00         0.00        0.81              1.0                0.00
     C  x_null     NaN          -1.90       NaN          NaN       49.11              0.0                0.96
```

- `target` is the calibration slope that the design yields with very many items and participants. It is 1 here
  because the simulated slope is the same in all families.
- `coverage` is the share of the 200 simulated data sets in which the 95% interval contained the target, with
  its Monte Carlo standard error. In this design the interval is conservative (98% to 100%).
- `rate_excludes_0` is the share of data sets in which the interval excluded 0: the detection rate for `x`
  (100%), and the false detection rate for a measure without effect (`x_null`, 0%).
- `rate_weak_training` is the share in which the training relation was flagged as weak (96% for `x_null`).
- With `prediction=True` the check also covers the interval of the log-loss reduction (columns `logloss_target`,
  `logloss_mean`, `logloss_coverage`, `logloss_coverage_se`, `logloss_rate_above_0`); it then takes longer. The
  interval of the ordering correlation is not part of the check.
- `mean_width` tells you what the design can distinguish: with intervals about 0.8 to 1.0 wide, a calibration
  slope of 1 cannot be told apart from 0.7 or 1.4.

You can also write a design by hand, which is how planned studies and "what if" questions are examined:

```python
design = it.Design(
    families=[
        it.FamilyDesign("A", 60, ("uniform", 0.1, 1.0), [it.SampleDesign("A1", 30, intercept=2.3)]),
        it.FamilyDesign("B", 48, ("uniform", 0.2, 0.9), [it.SampleDesign("B1", 40, intercept=2.6)]),
        it.FamilyDesign("C", 60, ("levels", [0.2, 0.8], 0.03),
                        [it.SampleDesign("C1", 35, items_per_participant=40, intercept=2.2)], slope=-1.5),
    ],
    slope=-3.0,               # families A and B; family C has half the effect
    link="linear",            # "log": the effect is linear in log(x)
    participant_sd=0.8, item_sd=0.5,
    second_measure=0.6,       # x2, correlated with x, with effect second_slope (default 0)
    null_measure=True,
)
trials2, items2 = it.simulate(design, seed=3)
it.check_intervals(design, n_sim=200, n_boot=200, n_jobs=2)
```

With family slopes that differ, the `target` for family C is about 0.5 (half the trained effect), and
`rate_includes_1` shows how often an interval would still include 1.

## Everything in one call

```python
out = it.report(trials, items, ["x", "x2", "x_null"], out_dir="transfer_report",
                n_boot=2000, n_sim=200, n_jobs=2, seed=1)
```

The interval check inside `report` covers the calibration slope; `check_prediction=True` adds the log-loss
reduction.

`report` runs steps 2 to 5 and returns the tables in a dictionary. With `out_dir` it also writes one CSV file per
table, `warnings.txt`, a Markdown summary (`report.md`) and `run_info.json` (seed, settings, package versions,
run time). A sample that should enter the reliability ceiling only, such as a pilot sample, can be named in
`reliability_only=[...]`.

## Reading the results: a short checklist

1. Is item difficulty reliable enough (step 2)? If not, collect more data before judging any measure.
2. Does the training slope differ from 0? If not, stop: there is nothing to transfer.
3. Ordering, scale and prediction: report all three with intervals. Do not summarise them in one word when they
   disagree.
4. For every held-out family, read the warnings of step 4 before interpreting a criterion. A two-level family
   cannot confirm a scale; a family outside the training range tests extrapolation; a correlated measure borrows
   its apparent success.
5. Check the interval for a design like yours (step 5) before attaching a label to it.
