# Leave-one-family-out transfer validation

Measures: instance_complexity, typical_case_complexity, sahni_k, solver_effort. Families: Doroc, Franco, Lu. Training samples weighted by trials. Seed 20261016; 2000 bootstrap resamples; intervals are 95% percentile intervals.

## Step 2. Reliability ceiling

Split-half reliability of item difficulty within each sample (Spearman-Brown; median and 2.5th to 97.5th percentile over random splits of the participants).

| sample | participants | items | trials per item (median) | reliability, logit scale | reliability, rank scale |
|---|---|---|---|---|---|
| Franco 2021 | 20 | 72 | 20.000 | 0.78 [0.71, 0.84] | 0.76 [0.69, 0.83] |
| Franco 2024 | 20 | 56 | 20.000 | 0.61 [0.46, 0.74] | 0.63 [0.45, 0.76] |
| Doroc 2025 | 42 | 72 | 84.000 | 0.86 [0.79, 0.91] | 0.88 [0.84, 0.92] |
| Lu 2025 main | 36 | 120 | 24.000 | 0.82 [0.77, 0.86] | 0.83 [0.78, 0.87] |
| Lu 2025 pilot | 17 | 120 | 11.000 | 0.70 [0.62, 0.77] | 0.71 [0.62, 0.78] |

Agreement between samples that share items (item bootstrap intervals).

| sample A | sample B | shared items | r (logit) | Spearman | r corrected for unreliability |
|---|---|---|---|---|---|
| Franco 2021 | Franco 2024 | 56 | 0.63 [0.46, 0.76] | 0.64 [0.45, 0.80] | 0.93 [0.69, 1.15] |
| Lu 2025 main | Lu 2025 pilot | 120 | 0.72 [0.64, 0.79] | 0.75 [0.67, 0.81] | 0.95 [0.86, 1.03] |

## Step 3. Transfer

Intervals of the training slope, the calibration slope and the reductions come from the two-way bootstrap (participants within samples, items within families); the interval of the ordering correlation comes from a bootstrap of items only. The calibration slope is 1 when the trained effect has the same size in the held-out family and 0 when there is no relation. Column 'scale' compares its interval with the tolerance 0.8 to 1.25; where the interval of the training slope includes 0 it reads 'weak training relation' and the calibration slope should not be interpreted.

| held-out family | model | items | trials | training slope | ordering | calibration slope | scale | log-loss reduction | Brier reduction |
|---|---|---|---|---|---|---|---|---|---|
| Doroc | instance_complexity | 72 | 6029 | 9.17 [6.52, 12.42] | 0.65 [0.51, 0.75] | 1.90 [1.21, 2.89] | undetermined | 0.044 [0.027, 0.065] | 0.045 [0.028, 0.066] |
| Doroc | typical_case_complexity | 72 | 6029 | -1.33 [-1.78, -0.91] | 0.25 [-0.01, 0.48] | 0.38 [-0.14, 0.95] | undetermined | -0.006 [-0.038, 0.019] | -0.008 [-0.043, 0.018] |
| Doroc | sahni_k | 72 | 6029 | 0.09 [-0.20, 0.45] | -0.21 [-0.40, 0.34] | -2.41 [-17.94, 17.09] | weak training relation | -0.003 [-0.030, 0.005] | -0.003 [-0.025, 0.006] |
| Doroc | solver_effort | 72 | 6029 | -0.11 [-0.26, 0.03] | 0.31 [-0.24, 0.51] | 2.20 [-16.20, 20.12] | weak training relation | 0.005 [-0.003, 0.015] | 0.006 [-0.003, 0.016] |
| Doroc | combined | 72 | 6029 |  | 0.68 [0.49, 0.78] | 1.78 [0.76, 2.53] | undetermined | 0.040 [0.013, 0.060] | 0.040 [0.014, 0.060] |
| Franco | instance_complexity | 72 | 1427 | 13.64 [10.89, 16.77] | 0.70 [0.52, 0.84] | 0.64 [0.27, 1.27] | undetermined | 0.083 [-0.092, 0.209] | 0.133 [0.029, 0.215] |
| Franco | typical_case_complexity | 72 | 1427 | -0.84 [-1.33, -0.35] | 0.44 [0.27, 0.58] | 1.76 [0.76, 4.65] | undetermined | 0.043 [0.010, 0.081] | 0.038 [0.007, 0.070] |
| Franco | sahni_k | 72 | 1427 | -0.09 [-0.31, 0.23] | -0.03 [-0.27, 0.24] | 0.08 [-16.94, 20.68] | weak training relation | -0.000 [-0.016, 0.010] | -0.000 [-0.016, 0.008] |
| Franco | solver_effort | 72 | 1427 | -0.12 [-0.26, 0.01] | 0.31 [-0.01, 0.51] | 3.86 [-12.61, 29.11] | weak training relation | 0.011 [-0.002, 0.029] | 0.009 [-0.002, 0.024] |
| Franco | combined | 72 | 1427 |  | 0.69 [0.51, 0.82] | 0.62 [0.25, 1.20] | undetermined | 0.079 [-0.104, 0.209] | 0.132 [0.016, 0.217] |
| Lu | instance_complexity | 120 | 2874 | 10.64 [7.01, 14.93] | 0.62 [0.51, 0.71] | 1.07 [0.66, 1.75] | undetermined | 0.100 [0.044, 0.149] | 0.098 [0.047, 0.147] |
| Lu | typical_case_complexity | 120 | 2874 | -0.86 [-1.32, -0.42] | 0.37 [0.21, 0.51] | 1.52 [0.65, 3.42] | undetermined | 0.030 [0.005, 0.057] | 0.031 [0.004, 0.059] |
| Lu | sahni_k | 120 | 2874 | -0.19 [-0.40, 0.06] | -0.19 [-0.35, 0.18] | -2.09 [-23.03, 12.64] | weak training relation | -0.008 [-0.027, 0.001] | -0.008 [-0.030, 0.001] |
| Lu | solver_effort | 120 | 2874 | -0.29 [-0.49, -0.12] | -0.11 [-0.28, 0.05] | -0.06 [-0.89, 0.64] | outside tolerance | -0.021 [-0.070, 0.002] | -0.023 [-0.071, 0.002] |
| Lu | combined | 120 | 2874 |  | 0.54 [0.40, 0.71] | 1.09 [0.66, 1.69] | undetermined | 0.098 [0.038, 0.148] | 0.096 [0.038, 0.145] |

## Step 4. Design diagnostics

- Measure 'instance_complexity' takes 2 levels in held-out family 'Doroc'. Ordering and prediction in this family can only reflect differences between these levels: a level indicator fitted in the family reduces log loss by 0.055, the transferred measure by 0.044. Within the levels, the correlations between measure and accuracy are -0.14, -0.02.
- Measure 'sahni_k' takes 4 distinct values in held-out family 'Doroc'. Ordering and prediction in this family can only reflect differences between these levels: a level indicator fitted in the family reduces log loss by -0.002, the transferred measure by -0.003.
- Measure 'sahni_k' takes 3 distinct values in held-out family 'Franco'. Ordering and prediction in this family can only reflect differences between these levels: a level indicator fitted in the family reduces log loss by -0.027, the transferred measure by -0.000.
- Measure 'instance_complexity' takes 2 levels in held-out family 'Lu'. Ordering and prediction in this family can only reflect differences between these levels: a level indicator fitted in the family reduces log loss by 0.097, the transferred measure by 0.100. Within the levels, the correlations between measure and accuracy are 0.25, -0.11.
- Measure 'sahni_k' takes 4 distinct values in held-out family 'Lu'. Ordering and prediction in this family can only reflect differences between these levels: a level indicator fitted in the family reduces log loss by -0.003, the transferred measure by -0.008.
- The training slope of 'sahni_k' for held-out family 'Doroc' has an interval that includes 0 (-0.198 to 0.449). The calibration slope is then a ratio with a denominator near zero and is not informative; read the training slope and the held-out slope instead.
- The training slope of 'solver_effort' for held-out family 'Doroc' has an interval that includes 0 (-0.257 to 0.0288). The calibration slope is then a ratio with a denominator near zero and is not informative; read the training slope and the held-out slope instead.
- The training slope of 'sahni_k' for held-out family 'Franco' has an interval that includes 0 (-0.312 to 0.227). The calibration slope is then a ratio with a denominator near zero and is not informative; read the training slope and the held-out slope instead.
- The training slope of 'solver_effort' for held-out family 'Franco' has an interval that includes 0 (-0.265 to 0.0123). The calibration slope is then a ratio with a denominator near zero and is not informative; read the training slope and the held-out slope instead.
- The training slope of 'sahni_k' for held-out family 'Lu' has an interval that includes 0 (-0.402 to 0.0616). The calibration slope is then a ratio with a denominator near zero and is not informative; read the training slope and the held-out slope instead.
- Only 76% of the items of held-out family 'Doroc' lie inside the range of 'solver_effort' in the training families (0 to 4.81).
- Only 53% of the items of held-out family 'Franco' lie inside the range of 'instance_complexity' in the training families (0.00803 to 0.162); the trained slope is extrapolated. On the common range the calibration slope is 1.43 instead of 0.64.
- Measures 'instance_complexity' and 'typical_case_complexity' are strongly correlated in family 'Franco' (Spearman -0.72); their separate relations with accuracy cannot be told apart in that family.
- The calibration slope of 'typical_case_complexity' for held-out family 'Lu' depends on the weighting of the training samples: 1.52 with weights by trials, 1.14 with equal weights.

### Level structure

| family | measure | n_items | n_distinct | n_levels | kind | gap_ratio |
|---|---|---|---|---|---|---|
| Doroc | instance_complexity | 72 | 58 | 2 | clustered | 3.602 |
| Doroc | typical_case_complexity | 72 | 71 | 0 | none | 0.158 |
| Doroc | sahni_k | 72 | 4 | 4 | discrete |  |
| Doroc | solver_effort | 72 | 33 | 0 | none | 0.324 |
| Franco | instance_complexity | 72 | 72 | 0 | none | 0.231 |
| Franco | typical_case_complexity | 72 | 67 | 0 | none | 1.069 |
| Franco | sahni_k | 72 | 3 | 3 | discrete |  |
| Franco | solver_effort | 72 | 15 | 0 | none | 0.509 |
| Lu | instance_complexity | 120 | 100 | 2 | clustered | 31.751 |
| Lu | typical_case_complexity | 120 | 98 | 0 | none | 0.128 |
| Lu | sahni_k | 120 | 4 | 4 | discrete |  |
| Lu | solver_effort | 120 | 21 | 0 | none | 0.492 |

### Level-indicator baseline

| family | measure | n_levels | kind | ordering_measure | ordering_levels | level_accuracy_r | logloss_reduction_measure | logloss_reduction_levels | logloss_difference | logloss_difference_split_lo | logloss_difference_split_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Doroc | instance_complexity | 2 | clustered | 0.652 | 0.782 | 0.770 | 0.044 | 0.055 | -0.011 | -0.016 | -0.004 |
| Doroc | sahni_k | 4 | discrete | -0.205 | -0.205 | 0.299 | -0.003 | -0.002 | -0.001 | -0.009 | 0.014 |
| Franco | sahni_k | 3 | discrete | -0.031 | -0.031 | 0.153 | -0.000 | -0.027 | 0.027 | -0.005 | 0.107 |
| Lu | instance_complexity | 2 | clustered | 0.617 | 0.673 | 0.656 | 0.100 | 0.097 | 0.003 | 0.000 | 0.013 |
| Lu | sahni_k | 4 | discrete | -0.190 | -0.190 | 0.173 | -0.008 | -0.003 | -0.005 | -0.015 | 0.026 |

### Within-level relations

| family | measure | level | n_items | measure_min | measure_max | measure_sd | accuracy_mean | accuracy_sd | ordering_within |
|---|---|---|---|---|---|---|---|---|---|
| Doroc | instance_complexity | 0 | 36 | 0.027 | 0.032 | 0.001 | 0.691 | 0.094 | -0.142 |
| Doroc | instance_complexity | 1 | 36 | 0.089 | 0.105 | 0.002 | 0.883 | 0.061 | -0.022 |
| Doroc | sahni_k | 0 | 57 | 0.000 | 0.000 | 0.000 | 0.799 | 0.123 |  |
| Doroc | sahni_k | 1 | 11 | 1.000 | 1.000 | 0.000 | 0.732 | 0.117 |  |
| Doroc | sahni_k | 2 | 3 | 2.000 | 2.000 | 0.000 | 0.824 | 0.059 |  |
| Doroc | sahni_k | 3 | 1 | 3.000 | 3.000 | 0.000 | 0.554 | 0.000 |  |
| Franco | sahni_k | 0 | 51 | 0.000 | 0.000 | 0.000 | 0.838 | 0.165 |  |
| Franco | sahni_k | 1 | 14 | 1.000 | 1.000 | 0.000 | 0.781 | 0.219 |  |
| Franco | sahni_k | 2 | 7 | 2.000 | 2.000 | 0.000 | 0.879 | 0.148 |  |
| Lu | instance_complexity | 0 | 60 | 0.008 | 0.012 | 0.001 | 0.655 | 0.195 | 0.251 |
| Lu | instance_complexity | 1 | 60 | 0.158 | 0.162 | 0.001 | 0.915 | 0.081 | -0.114 |
| Lu | sahni_k | 0 | 93 | 0.000 | 0.000 | 0.000 | 0.768 | 0.201 |  |
| Lu | sahni_k | 1 | 24 | 1.000 | 1.000 | 0.000 | 0.839 | 0.181 |  |
| Lu | sahni_k | 2 | 2 | 2.000 | 2.000 | 0.000 | 0.919 | 0.044 |  |
| Lu | sahni_k | 3 | 1 | 3.000 | 3.000 | 0.000 | 0.875 | 0.000 |  |

### Range overlap

| family | measure | heldout_min | heldout_max | train_min | train_max | share_inside_training | common_low | common_high | n_heldout_common | n_train_common | ordering | ordering_common | calibration_slope | calibration_slope_common | calibration_slope_common_lo | calibration_slope_common_hi | train_slope | train_slope_common |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Doroc | instance_complexity | 0.027 | 0.105 | 0.000 | 0.528 | 1.000 |  | 0.170 | 72 | 166 | 0.652 | 0.652 | 1.904 | 1.468 | 1.006 | 2.120 | 9.173 | 11.895 |
| Doroc | typical_case_complexity | 0.000 | 0.993 | 0.000 | 0.996 | 1.000 | 0.000 | 0.993 | 72 | 191 | 0.249 | 0.249 | 0.384 | 0.380 | -0.134 | 0.964 | -1.330 | -1.346 |
| Doroc | sahni_k | 0.000 | 3.000 | 0.000 | 3.000 | 1.000 | 0.000 | 3.000 | 72 | 192 | -0.205 | -0.205 | -2.414 | -2.414 | -17.945 | 17.093 | 0.093 | 0.093 |
| Doroc | solver_effort | 2.000 | 6.087 | 0.000 | 4.807 | 0.764 | 2.000 | 4.807 | 55 | 150 | 0.315 | -0.226 | 2.202 | -1.251 | -17.093 | 11.802 | -0.111 | 0.198 |
| Franco | instance_complexity | 0.000 | 0.528 | 0.008 | 0.162 | 0.528 |  | 0.170 | 46 | 192 | 0.704 | 0.793 | 0.641 | 1.431 | 0.848 | 2.473 | 13.636 | 13.636 |
| Franco | typical_case_complexity | 0.000 | 0.996 | 0.000 | 0.993 | 0.986 | 0.000 | 0.993 | 71 | 171 | 0.445 | 0.438 | 1.764 | 1.891 | 0.761 | 5.754 | -0.836 | -0.796 |
| Franco | sahni_k | 0.000 | 2.000 | 0.000 | 3.000 | 1.000 | 0.000 | 2.000 | 72 | 190 | -0.031 | 0.031 | 0.080 | -0.776 | -23.672 | 23.187 | -0.085 | 0.009 |
| Franco | solver_effort | 1.585 | 4.392 | 0.000 | 6.087 | 1.000 | 1.585 | 4.392 | 72 | 145 | 0.314 | -0.314 | 3.859 | -1.918 | -12.530 | 9.720 | -0.124 | 0.249 |
| Lu | instance_complexity | 0.008 | 0.162 | 0.000 | 0.528 | 1.000 |  | 0.170 | 120 | 118 | 0.617 | 0.617 | 1.066 | 0.706 | 0.466 | 1.026 | 10.643 | 16.063 |
| Lu | typical_case_complexity | 0.000 | 0.989 | 0.000 | 0.996 | 1.000 | 0.000 | 0.989 | 120 | 142 | 0.367 | 0.367 | 1.520 | 1.510 | 0.675 | 3.538 | -0.859 | -0.864 |
| Lu | sahni_k | 0.000 | 3.000 | 0.000 | 3.000 | 1.000 | 0.000 | 3.000 | 120 | 144 | -0.190 | -0.190 | -2.094 | -2.094 | -23.027 | 12.643 | -0.190 | -0.190 |
| Lu | solver_effort | 0.000 | 4.807 | 1.585 | 6.087 | 0.892 | 1.585 | 4.807 | 107 | 127 | -0.111 | -0.207 | -0.056 | -0.897 | -3.977 | -0.002 | -0.292 | -0.341 |

### Training slopes

| family | measure | train_slope | train_slope_lo | train_slope_hi | weak | calibration_slope | heldout_slope | heldout_slope_lo | heldout_slope_hi |
|---|---|---|---|---|---|---|---|---|---|
| Doroc | instance_complexity | 9.173 | 6.515 | 12.420 | no | 1.904 | 17.466 | 12.625 | 22.661 |
| Doroc | typical_case_complexity | -1.330 | -1.781 | -0.906 | no | 0.384 | -0.511 | -1.150 | 0.182 |
| Doroc | sahni_k | 0.093 | -0.198 | 0.449 | yes | -2.414 | -0.223 | -0.492 | 0.102 |
| Doroc | solver_effort | -0.111 | -0.257 | 0.029 | yes | 2.202 | -0.245 | -0.494 | -0.041 |
| Franco | instance_complexity | 13.636 | 10.894 | 16.774 | no | 0.641 | 8.744 | 3.786 | 16.444 |
| Franco | typical_case_complexity | -0.836 | -1.325 | -0.355 | no | 1.764 | -1.475 | -2.330 | -0.727 |
| Franco | sahni_k | -0.085 | -0.312 | 0.227 | yes | 0.080 | -0.007 | -0.528 | 0.571 |
| Franco | solver_effort | -0.124 | -0.265 | 0.012 | yes | 3.859 | -0.478 | -0.901 | -0.121 |
| Lu | instance_complexity | 10.643 | 7.006 | 14.935 | no | 1.066 | 11.346 | 8.275 | 15.158 |
| Lu | typical_case_complexity | -0.859 | -1.324 | -0.416 | no | 1.520 | -1.305 | -1.972 | -0.647 |
| Lu | sahni_k | -0.190 | -0.402 | 0.062 | yes | -2.094 | 0.398 | -0.062 | 1.051 |
| Lu | solver_effort | -0.292 | -0.491 | -0.117 | no | -0.056 | 0.016 | -0.150 | 0.200 |

### Correlation between measures

| family | measure_a | measure_b | spearman | n_items |
|---|---|---|---|---|
| Doroc | instance_complexity | typical_case_complexity | -0.091 | 72 |
| Doroc | instance_complexity | sahni_k | -0.178 | 72 |
| Doroc | instance_complexity | solver_effort | -0.331 | 72 |
| Doroc | typical_case_complexity | sahni_k | -0.114 | 72 |
| Doroc | typical_case_complexity | solver_effort | 0.308 | 72 |
| Doroc | sahni_k | solver_effort | 0.124 | 72 |
| Franco | instance_complexity | typical_case_complexity | -0.718 | 72 |
| Franco | instance_complexity | sahni_k | -0.021 | 72 |
| Franco | instance_complexity | solver_effort | -0.459 | 72 |
| Franco | typical_case_complexity | sahni_k | -0.062 | 72 |
| Franco | typical_case_complexity | solver_effort | 0.316 | 72 |
| Franco | sahni_k | solver_effort | 0.067 | 72 |
| Lu | instance_complexity | typical_case_complexity | -0.551 | 120 |
| Lu | instance_complexity | sahni_k | 0.285 | 120 |
| Lu | instance_complexity | solver_effort | -0.022 | 120 |
| Lu | typical_case_complexity | sahni_k | -0.141 | 120 |
| Lu | typical_case_complexity | solver_effort | 0.223 | 120 |
| Lu | sahni_k | solver_effort | 0.092 | 120 |

### Weighting of training samples

| family | model | n_training_samples | train_slope_trials | ordering_trials | calibration_slope_trials | logloss_reduction_trials | train_slope_equal | ordering_equal | calibration_slope_equal | logloss_reduction_equal |
|---|---|---|---|---|---|---|---|---|---|---|
| Doroc | instance_complexity | 3 | 9.173 | 0.652 | 1.904 | 0.044 | 8.266 | 0.652 | 2.113 | 0.041 |
| Doroc | typical_case_complexity | 3 | -1.330 | 0.249 | 0.384 | -0.006 | -1.330 | 0.249 | 0.384 | -0.006 |
| Doroc | sahni_k | 3 | 0.093 | -0.205 | -2.414 | -0.003 | -0.005 | 0.205 | 47.744 | 0.000 |
| Doroc | solver_effort | 3 | -0.111 | 0.315 | 2.202 | 0.005 | -0.196 | 0.315 | 1.249 | 0.007 |
| Doroc | combined | 3 |  | 0.680 | 1.782 | 0.040 |  | 0.694 | 2.053 | 0.038 |
| Franco | instance_complexity | 2 | 13.636 | 0.704 | 0.641 | 0.083 | 12.677 | 0.704 | 0.690 | 0.089 |
| Franco | typical_case_complexity | 2 | -0.836 | 0.445 | 1.764 | 0.043 | -0.981 | 0.445 | 1.504 | 0.047 |
| Franco | sahni_k | 2 | -0.085 | -0.031 | 0.080 | -0.000 | 0.009 | 0.031 | -0.747 | -0.000 |
| Franco | solver_effort | 2 | -0.124 | 0.314 | 3.859 | 0.011 | -0.076 | 0.314 | 6.290 | 0.007 |
| Franco | combined | 2 |  | 0.688 | 0.622 | 0.079 |  | 0.681 | 0.665 | 0.085 |
| Lu | instance_complexity | 3 | 10.643 | 0.617 | 1.066 | 0.100 | 7.999 | 0.617 | 1.419 | 0.092 |
| Lu | typical_case_complexity | 3 | -0.859 | 0.367 | 1.520 | 0.030 | -1.147 | 0.367 | 1.138 | 0.033 |
| Lu | sahni_k | 3 | -0.190 | -0.190 | -2.094 | -0.008 | -0.157 | -0.190 | -2.541 | -0.006 |
| Lu | solver_effort | 3 | -0.292 | -0.111 | -0.056 | -0.021 | -0.359 | -0.111 | -0.045 | -0.031 |
| Lu | combined | 3 |  | 0.539 | 1.094 | 0.098 |  | 0.539 | 1.448 | 0.090 |

## Step 5. Interval check by simulation

Data sets simulated from a design built on the measure 'instance_complexity' (200 data sets, 200 resamples each). In the simulated design this measure is called x; x_null is a measure without effect.

| family | measure | target | train_slope_target | mean_estimate | median_estimate | sd_estimate | coverage | coverage_se | mean_width | median_width | rate_excludes_0 | rate_excludes_0_se | rate_includes_1 | rate_weak_training | n_sim | n_boot |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Doroc | x | 0.989 | 11.264 | 0.988 | 0.985 | 0.264 | 0.945 | 0.016 | 1.101 | 1.082 | 0.970 | 0.012 | 0.945 | 0.000 | 200 | 200 |
| Doroc | x_null |  | 0.000 | -2.963 | -0.019 | 39.303 |  |  | 29.183 | 25.656 | 0.000 | 0.000 | 0.990 | 0.970 | 200 | 200 |
| Franco | x | 1.021 | 11.185 | 1.060 | 1.050 | 0.194 | 0.975 | 0.011 | 0.956 | 0.909 | 1.000 | 0.000 | 0.970 | 0.000 | 200 | 200 |
| Franco | x_null |  | 0.000 | -2.960 | 0.160 | 25.839 |  |  | 57.685 | 48.802 | 0.000 | 0.000 | 1.000 | 0.945 | 200 | 200 |
| Lu | x | 0.999 | 11.242 | 0.997 | 0.984 | 0.143 | 0.990 | 0.007 | 0.773 | 0.757 | 1.000 | 0.000 | 0.990 | 0.000 | 200 | 200 |
| Lu | x_null |  | 0.000 | -2.670 | -0.023 | 61.214 |  |  | 31.915 | 29.347 | 0.005 | 0.005 | 0.985 | 0.940 | 200 | 200 |

## Run information

```
{
 "package": "itemtransfer",
 "version": "0.2.0",
 "python": "3.13.17",
 "numpy": "2.5.3",
 "pandas": "3.0.5",
 "scipy": "1.18.1",
 "seed": 20261016,
 "n_boot": 2000,
 "n_splits": 500,
 "n_splits_reliability": 1000,
 "n_sim": 200,
 "n_boot_sim": 200,
 "weights": "trials",
 "reliability_only": [
  "Lu 2025 pilot"
 ],
 "measures": [
  "instance_complexity",
  "typical_case_complexity",
  "sahni_k",
  "solver_effort"
 ],
 "evaluate": {
  "Doroc": [
   "Doroc 2025"
  ],
  "Franco": [
   "Franco 2021"
  ],
  "Lu": [
   "Lu 2025 main"
  ]
 },
 "tolerance": [
  0.8,
  1.25
 ],
 "ordering_boot": "items",
 "interval_type": "percentile",
 "level": 0.95,
 "boot_batch": null,
 "n_jobs": 2,
 "platform": "Linux-6.18.44-fc-v445-x86_64-with-glibc2.39",
 "run_time_seconds": 37.1
}
```
