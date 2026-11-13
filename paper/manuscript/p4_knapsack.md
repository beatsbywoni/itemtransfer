## Worked example 2: Measures of computational hardness in knapsack decisions

The second example is a small design of the kind that most laboratories can assemble from public data: three families with 72 to 120 items each. It shows what the procedure can and cannot conclude at this size, and it shows the level and range diagnostics at work.

### Task, measures and data

In the knapsack decision task, a participant sees a set of objects, each with a value and a weight. The participant decides whether some subset of the objects has a total weight at or below a given capacity and a total value at or above a given target. Several measures have been proposed to describe how hard a single instance of this task is for a person (Franco et al., 2021, 2022).

Four measures were examined. *Instance complexity* is the distance between the target and the best total value that any admissible subset can reach, divided by the total value of all objects (Franco et al., 2021). Despite its name, a larger value should make the decision easier, because the answer is then further from the borderline. *Typical-case complexity* runs from 0 to 1 and depends only on the capacity and the target, each expressed as a share of the totals. It is 1 when half of all randomly generated instances with that capacity and target have a solution, and 0 when nearly all or nearly none do (Yadav, Murawski, et al., 2018). Higher values should make the decision harder. *Sahni-k* refers to a simple rule that adds objects in order of their value per unit of weight for as long as they fit. Sahni-k is the smallest number of objects that have to be placed in the subset beforehand for this rule to find the best subset (Sahni, 1975). *Solver effort* is the logarithm of the number of inference steps that a general-purpose constraint solver needs to decide the instance.

The data come from four published studies of one research group (Table 9). The 264 items form three families that share no item, and each family is named after the study that generated its items. Table 9 gives the role of each sample. When a family is held out, none of its samples enters the training fit. The Franco family is evaluated on the Franco et al. (2021) sample, which answered all 72 items; the Franco et al. (2024a) sample answered 56 of them and serves as a training sample for the other two families. This choice was fixed in the analysis plan of an earlier analysis of these data, before the results were seen. The pilot sample of the Lu family was used for the reliability ceiling only. The four samples of the transfer analysis comprise 118 participants and 11,450 responses, of which 10,330 belong to the three evaluation samples. An item that two samples share is one unit in the resampling of items. The families differ in design. The Franco items cover instance complexity continuously, whereas the Doroc and Lu items were built at two levels of it. The Doroc items contain eight objects and the other items six. Only the Franco studies limited the viewing time.

**Table 9.** Samples of the knapsack example and the reliability of item difficulty (step 2).

| Family | Sample | Setting | Participants | Items | Responses | Role in the transfer analysis | Split-half reliability |
|---|---|---|---|---|---|---|---|
| Franco | Franco et al. (2021) | Laboratory, fixed viewing time | 20 | 72 | 1,427 | Training; evaluation of the Franco family | .78 [.71, .84] |
| Franco | Franco et al. (2024a) | Scanner, fixed viewing time | 20 | 56 | 1,120 | Training only | .61 [.46, .74] |
| Doroc | Doroc, Yadav, and Murawski (2025) | Laboratory, two sessions, self-paced | 42 | 72 | 6,029 | Training; evaluation of the Doroc family | .86 [.79, .91] |
| Lu | Lu et al. (2025), main | Online, self-paced | 36 | 120 | 2,874 | Training; evaluation of the Lu family | .82 [.77, .86] |
| Lu | Lu et al. (2025), pilot | In person, self-paced | 17 | 120 | 1,359 | None (reliability only) | .70 [.62, .77] |

*Note.* Reliability is on the logit scale with the Spearman-Brown correction; brackets give the 2.5th and 97.5th percentiles over 1,000 random splits of the participants, which describe the dependence on the split and are not confidence intervals. "Training" means that the sample enters the fit when another family is held out. In the Doroc sample every participant answered every item in two sessions; both responses are used.

### Steps 1 and 2: Recomputed measures and reliability ceiling

All measures were recomputed from the weights and values of the objects. The recomputed values agreed with the published ones except for one item and for solver effort, whose counts depend on the version of the solver; details are in the supplementary material.

Item difficulty was measured with reliabilities between .61 and .86 (Table 9). Samples that answered the same items agreed as far as their reliability allowed: the corrected correlation was .93, 95% CI [.69, 1.15], between the two Franco samples and .95 [.86, 1.03] between the two Lu samples. Corrected correlations can exceed 1 by sampling error. With reliabilities near .8, a perfect measure could reach an ordering correlation of about .9, the square root of the reliability.

### Step 3: Transfer

Instance complexity ordered the items of every held-out family, with correlations between .62 and .70 (Table 10, Figure 6). It was also the only measure whose reduction in log loss was positive in every family, although the interval for the Franco items included 0. Typical-case complexity ordered the Franco and Lu items and gave no evidence of a relation for the Doroc items. Sahni-k and solver effort showed no transfer: their ordering intervals included 0 in every family, and their reductions in log loss were near 0 or negative.

The scale could not be established for the two informative measures. All six of their calibration-slope intervals crossed a limit of the tolerance, and the intervals were between 1.0 and 3.9 wide. This is what the simulation leads one to expect with 72 to 120 held-out items. The design can show that a relation is present and has the right direction. It cannot show that the effect size is the same.

**Table 10.** Transfer of four measures to each held-out family of the knapsack example (step 3).

| Held-out family | Measure | Slope trained / fitted in the family | Ordering | Calibration slope | Reduction in log loss |
|---|---|---|---|---|---|
| Franco | Instance complexity | 13.6 / 8.7 | .70 [.52, .84] | 0.64 [0.27, 1.27] | .083 [−.092, .209] |
| | Typical-case complexity | −0.84 / −1.48 | .44 [.27, .58] | 1.76 [0.76, 4.65] | .043 [.010, .081] |
| | Sahni-k | −0.09 / −0.01 | −.03 [−.27, .24] | weak training relation | .000 [−.016, .010] |
| | Solver effort | −0.12 / −0.48 | .31 [−.01, .51] | weak training relation | .011 [−.002, .029] |
| Doroc | Instance complexity | 9.2 / 17.5 | .65 [.51, .75] | 1.90 [1.21, 2.89] | .044 [.027, .065] |
| | Typical-case complexity | −1.33 / −0.51 | .25 [−.01, .48] | 0.38 [−0.14, 0.95] | −.006 [−.038, .019] |
| | Sahni-k | 0.09 / −0.22 | −.21 [−.40, .34] | weak training relation | −.003 [−.030, .005] |
| | Solver effort | −0.11 / −0.24 | .31 [−.24, .51] | weak training relation | .005 [−.003, .015] |
| Lu | Instance complexity | 10.6 / 11.3 | .62 [.51, .71] | 1.07 [0.66, 1.75] | .100 [.044, .149] |
| | Typical-case complexity | −0.86 / −1.31 | .37 [.21, .51] | 1.52 [0.65, 3.42] | .030 [.005, .057] |
| | Sahni-k | −0.19 / 0.40 | −.19 [−.35, .18] | weak training relation | −.008 [−.027, .001] |
| | Solver effort | −0.29 / 0.02 | −.11 [−.28, .05] | −0.06 [−0.89, 0.64] | −.021 [−.070, .002] |

*Note.* Slopes are in logits per unit of the measure. Brackets give 95% bootstrap intervals from 2,000 resamples: items only for ordering, participants and items for the other two criteria. A positive ordering means that the measure ranks the items in the direction found in the training families. Ordering intervals of measures with a weak training relation are wide because the sign of the trained slope changes between resamples.

*Figure 6 about here.*

### Step 4: Design diagnostics

The diagnostics qualified the result for instance complexity in three ways.

*Level structure.* In the Doroc and Lu families, instance complexity takes two tight clusters of values. A level indicator fitted in the family reduced log loss by about as much as the transferred measure in point estimate: by .055 against .044 for the Doroc items, and by .097 against .100 for the Lu items. Within the levels, the correlations between instance complexity and accuracy lay between −.14 and .25. These two families therefore show that items far from the borderline are easier than items close to it. They do not show that difficulty changes gradually with the distance. Only the Franco family, with its continuous values, bears on that question (Figure 6A).

*Range.* Only 53% of the Franco items lay inside the range of instance complexity that the training families cover. All families were then restricted to the range that they share. The calibration slopes became 1.43 [0.85, 2.47] for the Franco items, 1.47 [1.01, 2.12] for the Doroc items and 0.71 [0.47, 1.03] for the Lu items, against 0.64, 1.90 and 1.07 on the full range. The restriction thus moved every slope, and it did not bring them into agreement. The low unrestricted value for the Franco items is consistent with a relation that flattens at high values of the measure, where accuracy approaches its maximum, which is the pattern that the simulation produced for a saturating relation. With intervals this wide, that reading remains a hypothesis.

*Weighting.* The calibration slope for the Lu items rose from 1.07 to 1.42 when every training sample received equal weight, because the largest training sample, with its two close levels, then counted less.

Two diagnostics concerned the other measures. The training relation was weak for Sahni-k in all three analyses and for solver effort in two. Sahni-k is 0 for 201 of the 264 items, so these item sets say little about it. Instance complexity and typical-case complexity were strongly correlated in the Franco family (Spearman correlation −.72) and moderately in the Lu family (−.55), and almost uncorrelated in the Doroc family (−.09), whose design fixed the capacity. Typical-case complexity thus showed a relation with accuracy where it was correlated with instance complexity and none where it was not. The model with all four measures predicted no better than instance complexity alone in any family (supplementary material). This pattern is the one that the simulation produced for a proxy. One family is not enough to establish it, since the interval of the calibration slope for the Doroc items, [−0.14, 0.95], does not exclude a sizeable effect.

A logistic mixed model with crossed random intercepts for participants and items led to the same reading of instance complexity. Its ratios of the held-out slope to the slope of the other two families were 0.53, 2.03 and 1.44 for the Franco, Doroc and Lu families, and a likelihood-ratio test rejected equal slopes in the three families, χ²(2) = 25.2, *p* < .001. For typical-case complexity the test did not reject equal slopes, χ²(2) = 3.9, *p* = .14.

When the Franco family was evaluated on the Franco et al. (2024a) sample instead, a sensitivity analysis foreseen in the original plan, instance complexity gave an ordering of .68 [.48, .82], a calibration slope of 0.43 [0.18, 0.89] and a reduction in log loss of −.009 [−.173, .133]. The reading is the same: the direction transfers, and the trained effect is too large for this family.

### Step 5: Uncertainty

The simulation check generated 200 data sets with the design of this example and one common, linear slope for instance complexity. The intervals of the calibration slope contained the true value in 94.5% to 99% of the data sets, and a measure without relation was declared related in at most 0.5%. The check also showed what the design cannot do. For the Doroc family, whose two levels of instance complexity lie close together, a perfectly transferring relation was detected by the prediction criterion in only 43% of the simulated data sets.

### What the example shows

At this size, the procedure supports a bounded conclusion. Instance complexity carries information about item difficulty to new families of knapsack items, in the right direction and with predictive value in two of three families. Whether its effect has a constant size, and whether it is graded, cannot be decided from these item sets. The diagnostics give the reasons: two families have two levels, the third covers a wider range than the others, and the result depends on how the training samples are weighted. A report of the three ordering correlations alone, all between .62 and .70, would have suggested a more uniform result than the data contain. The four samples come from one research group, so the example illustrates the procedure and is not a general assessment of these measures.
