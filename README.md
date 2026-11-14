# itemtransfer

Leave-one-family-out transfer validation of item-level difficulty measures, for any task with binary item
responses.

A **measure** is an item-level difficulty predictor computed from the item alone (a complexity index of a puzzle,
the frequency of a word, a property of a test item). An **item family** is a set of items produced by one design
or generator. A measure that explains accuracy within one family may fail in another. This package asks whether
the relation between a measure and accuracy, estimated on some families, holds in a family that was held out.

## Installation

```
pip install git+https://github.com/beatsbywoni/itemtransfer     # from the repository; needs numpy, pandas, scipy
pip install .                    # from a clone of the repository
pip install ".[plot]"            # adds matplotlib for the optional figure
```

Python 3.10 or later. Repeated responses of a participant to an item are allowed and count as separate trials.

## Quick start

```python
import itemtransfer as it

# trials: one row per response  -> participant, item, sample, correct (0/1); family is optional
# items:  one row per item      -> item, family, one column per measure
trials, items = it.load_example()          # small synthetic data set shipped with the package
measures = ["x", "x2", "x_null"]

# Step 2. Reliability ceiling: how reproducible is item difficulty?
print(it.reliability(trials))                       # split-half reliability within each sample
print(it.agreement(trials, "A1", "A2"))             # two samples that share items

# Step 3. Transfer: train on the other families, judge on the held-out family
res = it.transfer(trials, items, measures, n_boot=2000, seed=1)
print(res.table[["family", "model", "train_slope", "ordering",
                 "calibration_slope", "calibration_slope_lo", "calibration_slope_hi",
                 "logloss_reduction", "logloss_reduction_lo", "logloss_reduction_hi"]])

# Step 4. Design diagnostics: why might the three criteria disagree?
diag = it.diagnose(trials, items, measures, result=res)
print("\n".join(diag["warnings"]))

# Step 5. Can the intervals be trusted for a design like this one?
design = it.design_from_data(trials, items, "x")
print(it.check_intervals(design, n_sim=200, n_boot=200, prediction=True, n_jobs=2))

# Or everything in one call, with CSV files and a Markdown summary
out = it.report(trials, items, measures, out_dir="transfer_report", n_sim=200, check_prediction=True, n_jobs=2, seed=1)
```

The interval check covers the calibration slope and, with `prediction=True` (in `report`: `check_prediction=True`),
the log-loss reduction. It does not cover the interval of the ordering correlation.

## Options worth knowing

- `tolerance=(0.80, 1.25)` in `transfer` and `report`: the range of calibration slopes that counts as "the
  trained effect size holds". The column `scale_reading` says whether the whole interval lies within it, outside
  it, or crosses a limit (`undetermined`). It reads `weak training relation` when the interval of the training
  slope includes 0, and `not applicable` when the measure does not vary. Choose the range before looking at the
  results.
- `evaluate={family: sample}`: the sample of a held-out family on which the criteria are computed. By default all
  samples of the family are pooled into one evaluation population with one intercept (the training fit has one
  intercept per sample). Evaluate samples one at a time when sample-specific transfer is the question.
- `ordering_boot="items"` (default) or `"two-way"`: resampling used for the interval of the ordering correlation.
- `boot_batch=50`: process the bootstrap resamples in batches. Needed for data with tens of thousands of items;
  memory is about `boot_batch` times the number of items times 100 bytes.
- `interval_type="percentile"` (default), `"bc"` or `"basic"`.

## Data format

| table | required columns | meaning |
|---|---|---|
| `trials` | `participant`, `item`, `sample`, `correct` (and optionally `family`) | one row per response; `correct` is 0/1 |
| `items` | `item`, `family`, one column per measure | one row per item |

A **sample** is one group of participants who responded to (a subset of) the items of one family. Families must
not share items. Column names can be mapped with `columns={"participant": "subject_id", ...}`. Inputs are checked
and errors say what to change: a non-binary outcome, missing values, an item listed in two families, a sample that
spans two families, or a measure that is undefined for some items.

## The procedure

1. **Recompute** every measure for every item with one implementation (outside this package).
2. **Reliability ceiling.** `reliability` gives the split-half reliability of item difficulty within each sample
   (random halves of the participants, logit scale and rank scale, Spearman-Brown). `agreement` gives the
   correlation between two samples that share items, raw and corrected for unreliability, with an item bootstrap
   interval. A measure cannot be asked to predict what is not reproducible.
3. **Transfer, with three criteria that can disagree.** `transfer` fits
   `logit P(correct) = a_sample + b * measure` on the training families and reports, for the held-out family,
   *ordering* (Spearman correlation between `b * measure` and item accuracy), *scale* (calibration slope: 1 means
   that the trained effect size holds, 0 means no relation) and *prediction* (relative reduction in trial-level log
   loss and Brier score against an intercept-only model, with the slope fixed from training and the intercept
   fitted on a random half of the held-out items).
4. **Design diagnostics.** `diagnose` checks whether the measure takes only a few levels in the held-out family
   (and compares it with a level indicator), how far the ranges of the measure overlap, whether the training
   relation is too weak for the calibration slope to mean anything, how strongly the measures are correlated
   within each family, and whether the result depends on the weighting of the training samples. It returns tables
   and a short list of plain-language warnings.
5. **Uncertainty.** Two-way bootstrap intervals (participants within samples, items within families) for the
   calibration slope and the log-loss reduction; an items-only bootstrap interval for the ordering correlation
   (the two-way interval of a rank correlation is centred too low, see `ordering_boot`); item bootstrap for
   agreement between samples; and
   `design_from_data`, `simulate` and `check_intervals` to check coverage and detection rates on data simulated to
   resemble your own design.

## Functions

| function | purpose |
|---|---|
| `reliability(trials)` | split-half reliability of item difficulty per sample |
| `agreement(trials, sample_a, sample_b)` | between-sample correlation on shared items, raw and corrected |
| `transfer(trials, items, measures)` | leave-one-family-out transfer: ordering, scale, prediction, with intervals |
| `diagnose(trials, items, measures)` | design diagnostics and warnings |
| `simulate(design)` | draw a data set from a `Design` (`FamilyDesign`, `SampleDesign`) |
| `design_from_data(trials, items, measure)` | build a `Design` that resembles your data |
| `check_intervals(design)` | coverage of the calibration-slope interval and detection rates; with `prediction=True` also for the log-loss reduction |
| `report(trials, items, measures, out_dir=...)` | steps 2 to 5 in one call; CSV tables and `report.md` |
| `plot_transfer(result, model)` | optional figure (needs matplotlib) |
| `load_example()`, `example_design()` | the bundled synthetic data and the design that generated them |

Every function has a docstring with the full list of arguments and outputs (`help(it.transfer)`). A walk-through
with output and interpretation is in [docs/tutorial.md](docs/tutorial.md). `examples/knapsack.py` runs the full
report on a real data set (knapsack decision problems, three item families, four measures).

## Reproducibility

All random steps take a `seed` and use `numpy.random.Generator`; there is no global state. `report` writes the
seed, the settings, the package versions and the run time to `run_info.json`. The test suite (`pytest`) contains
unit tests on synthetic data and a regression test that compares the package with an earlier analysis of the knapsack data by the same
author (skipped when those data are absent).

## Limitations

- Binary responses only. Response times and graded responses are not handled.
- The models are marginal logistic regressions on item counts; participants enter through the bootstrap, not
  through random effects.
- A calibration slope is a ratio. It is uninformative when the training slope is near zero; `diagnose` flags
  this.
- Bootstrap intervals are percentile intervals (bias-corrected or basic on request). Their coverage depends on the
  design; check it with `check_intervals` before attaching labels to results. In simulations with a common slope, the two-way
  intervals of the calibration slope and the log-loss reduction were conservative (1.1 to 2.1 times wider than
  needed, coverage 96.5% or more). The items-only interval of the ordering correlation had coverage between 90.5%
  and 99% in complete designs; it is not covered by `check_intervals`.
- In very large data the weak-training flag is not raised for slopes that are negligible but estimated precisely.
  Read the size of the training slope and the slope fitted in the held-out family as well.
- The agreement interval resamples items and keeps participants fixed.

## Licence and citation

MIT licence (see `LICENSE`). Citation details are in `CITATION.cff`.


## Repository contents

| Path | Content |
|---|---|
| `itemtransfer/`, `tests/`, `docs/tutorial.md` | The package (version 0.2.1), its 79 tests and a tutorial with a synthetic data set |
| `examples/knapsack.py` | Script of the knapsack example of the article |
| `paper/` | Materials of the article: simulation study, both worked examples, mixed models, figures, manuscript and supplement sources. See `paper/README.md` for the commands that reproduce every table and figure |
| `code/`, `data_proc/` | Preparation of the knapsack data from the original authors' repositories, and the tables that may be redistributed |
| `prereg/` | Analysis plan of the earlier analysis of the knapsack data (26 October 2026), which fixed the evaluation samples |

Tests: `pip install ".[test]"`, then `python -m pytest -q` (under a minute; 76 pass and 3 are skipped in this repository, because
they need the complete knapsack data and the result files of an earlier analysis, neither of which is distributed).

## Citation and licence

See `CITATION.cff`. Code: MIT licence (`LICENSE`). Data tables: see `paper/README.md`.
