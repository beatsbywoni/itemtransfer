## Software

The Python package `itemtransfer` (version 0.2.1) carries out steps 2 to 5. It depends only on NumPy, pandas and SciPy, is released under the MIT licence, and is installed from its repository with `pip install git+https://github.com/beatsbywoni/itemtransfer`.

The input is the pair of tables described above: one row per response and one row per item. Each step is one function, and a further function runs all steps and writes the tables and a summary in plain language (Box 1). The functions check their input and say in words what has to be changed, for example an item that is listed in two families or a measure that is missing for some items. A measure that does not vary in the training families or in the held-out family is reported as such, and the criteria that need its variation are left empty.

**Box 1.** Steps 2 to 5 with `itemtransfer`.

```python
import itemtransfer as it

# trials: participant, item, sample, correct (0 or 1)
# items:  item, family, and one column per measure
measures = ["frequency", "length"]

# Step 2: reliability ceiling
it.reliability(trials, seed=1)
it.agreement(trials, "sample A", "sample B", seed=1)

# Step 3: transfer by ordering, scale and prediction, with intervals
result = it.transfer(trials, items, measures, tolerance=(0.80, 1.25), seed=1)
result.table

# Step 4: design diagnostics, returned as tables and plain-language warnings
checks = it.diagnose(trials, items, measures, result=result)
print("\n".join(checks["warnings"]))

# Step 5: coverage and detection rates (scale, prediction) for a design like this one
design = it.design_from_data(trials, items, "frequency")
it.check_intervals(design, n_sim=200, prediction=True, seed=1)

# All steps in one call, written to a folder
it.report(trials, items, measures, out_dir="transfer_report", n_sim=200,
          check_prediction=True, seed=1)
```

The table returned by `transfer` has one row per held-out family and model. Next to the three criteria and their intervals it gives the training slope and the slope fitted in the held-out family. A further column reads the calibration slope against the tolerance: "within tolerance", "outside tolerance", "undetermined", or "weak training relation" when the interval of the training slope includes 0. The simulation check reports coverage and detection rates for the calibration slope and, with the option shown in Box 1, for the reduction in log loss. It adds a measure without relation to every simulated data set, so that false-positive rates are reported together with coverage. Every random step takes a seed, and the report records the seed, the settings and the versions of all packages.

The computations work on counts per item, so large data sets are feasible: the transfer analysis of the lexical example, with 3.7 million responses and 1,000 resamples, took about 35 minutes on two processor cores.

The repository contains a tutorial with a small synthetic data set, a suite of 79 tests, the simulation code, and the scripts of both examples. The main results of both examples come from the functions shown in Box 1; the follow-up analyses of the lexical example use additional scripts in the repository.

## Discussion

Difficulty measures are developed on one kind of item and used on others. Leave-one-family-out transfer validation tests that step directly. A relation between a measure and accuracy is estimated on some item families and judged on a family that was held out. The three criteria are read against the reliability of the data and the design of the held-out family. This section states what the procedure adds to existing practice, how it can be used in other paradigms, and where its limits lie.

### What the procedure adds

The findings on inference are warnings for analyses of accuracy by item properties in data where participants are crossed with items. They were obtained under the simulated conditions described above. The uncertainty must take the sampling of items into account, as has long been known for significance tests (Clark, 1973): intervals from resampled participants alone contained their target as rarely as 51% of the time, and a test of slope differences with ordinary standard errors rejected equal slopes six times too often. The percentile interval of the usual bootstrap over participants and items should not be used for the rank correlation between a measure and observed item accuracy, because the resampled correlations are shifted downwards and, with thousands of items, the interval excludes its own estimate. And a score from grouped cross-validation without recalibration mixes differences in mean accuracy with differences in the relation of interest.

The procedure combines three questions that existing analyses answer separately or not at all. A mixed model with crossed random effects, or a test of slope differences with item-based standard errors, is the sensitive tool for the question whether effect sizes differ, and it complements the calibration slope. The prediction criterion says whether a difference in slope matters for single responses. The reliability ceiling says how much there is to predict. The diagnostics say what the design of the held-out family can show, and in the simulated scenarios with two levels or a shifted range they were the only output that pointed to the cause.

The design of the held-out family decides what a positive result means. Stimulus sets in experimental work are often built at a few levels of a measure to increase power. That can serve the comparison of the original study well and still limits validation: two families of the knapsack example could show that two levels differ and nothing about the form of the relation. Range has a similar effect. Under a non-linear relation, a family that covers other values of the measure yields a calibration slope far from 1 although nothing about the mechanism has changed.

The diagnostics do not find every cause. In the lexical example, the larger frequency effect in the British megastudy was traced to the composition of the word lists by sensitivity analyses that lie outside the five diagnostics. Varying the definition of the families, as was done there, is a useful addition whenever families overlap or were assembled by different rules.

### Using the procedure in other paradigms

The procedure needs responses scored as correct or incorrect, a measure defined for every item, and at least two families that share no item. Many paradigms meet these conditions. Reasoning items from different generators or item banks can serve as families, with rule counts or other structural properties as measures (Zorowitz et al., 2024). So can puzzles from different sources, and memory or perception tasks whose stimuli come from different normed sets. Public collections of item responses make such analyses possible without new data (Domingue et al., 2025).

What counts as a family is a substantive decision that should be made before the results are seen. A useful rule is that a family is whatever a later study would replace as a whole: the generator and its settings, the corpus, the item bank. When two resources share items, as the two English megastudies do, the shared items violate the definition. They can be assigned to one family or removed, and the lexical example shows that the two choices can lead to different results. Both should be reported.

For planning, the simulation gives three rules of thumb. More items in the family that will be held out improve precision more than additional families do. About 100 held-out items were needed in the base condition before a relation of medium size was detected by all three criteria in most data sets. A family intended for validation should cover the measure continuously or in more than two levels, with enough items per level, and its range should overlap with that of the training families. In the simulated scenario, four levels with 96 items were informative. The simulation check gives the coverage and detection rates of the scale and prediction criteria for a specific design before data are collected. It follows the approach of simulation-based planning tools for item effects and for model estimation (Beeckmans et al., 2024; Buchanan et al., 2026).

Results should be reported per held-out family: the three criteria with the reliability, the slope fitted in the family, the flags of step 4, and a tolerance for the calibration slope that was fixed in advance. An average over families hides the disagreement that the procedure exists to reveal.

Such a report can guide the selection of stimuli, within limits. A positive ordering in every held-out family supports the use of a measure to rank or stratify candidate items from a comparable design. It does not establish that items matched on the measure are matched in difficulty, because part of item difficulty lies outside the measure. Predicted accuracies for new items need, in addition, an intercept for the new participants and setting, even when the calibration slope lies within the tolerance. If the slope lies outside the tolerance or is undetermined, the size of the effect has to be estimated on the new items as well before item sets are equated in expected accuracy. In the lexical example, frequency gave useful information about the order of the words in every list examined, and the British list shows why the size of its effect should be checked when the composition of a list changes.

### Limitations

First, the procedure handles binary responses only. Response time is the main outcome in several fields, including word recognition. The logic of the five steps carries over, but step 3 would need a model for response times, and the behaviour of the criteria would have to be established again.

Second, the model of step 3 has no random effects, so its slopes are population-averaged. [[LIMITATION-MARGINAL]]

Third, the statements of the procedure are conditional on the families at hand. With three or four families, the variation of a slope across all possible designs cannot be estimated, and each result concerns one held-out family. [[LIMITATION-META]]

Fourth, transfer shows that a relation holds and does not show why. A measure can transfer because it is correlated with the property that drives difficulty. Causal claims need families in which the candidate measures are uncorrelated, or experiments.

Fifth, the effect of the measure is linear on the logit scale. The range diagnostic detects some consequences of non-linearity, and the user can transform the measure or enter several terms. The procedure does not search for the correct form.

Sixth, the tolerance for the calibration slope is an illustrative convention, and the rule returns "undetermined" unless every family has several hundred items. Calibration slopes should therefore always be reported with their intervals.

Seventh, the simulations generated data from the model of the analysis with item and participant effects added, mostly for complete designs. The interval of the ordering correlation was examined in such designs only; for sparse or unbalanced designs, and for small samples of participants, its coverage is not established. The procedure applies no correction for the number of measures, families and criteria that are examined, so the results of the examples are descriptive, family by family.

## Conclusion

A difficulty measure earns general use by holding for items that were built differently from those on which it was developed. Leave-one-family-out transfer validation turns that general claim into three questions for each held-out family: whether the measure preserves the ordering of the items, the size of its effect, and its value for predicting single responses. The simulations show why the answers can disagree and why the intervals must respect the sampling of items. In the examples, word frequency ordered the words of four megastudies while the size of its effect depended on the composition of the lists. Instance complexity ordered the items of three knapsack families, whose small and partly two-level designs left the size of its effect undetermined. The `itemtransfer` package makes the procedure available for tasks with correct and incorrect responses and at least two item families that share no item, and its simulation check shows what a given design can support.

## Declarations

**Funding.** No funding was received for conducting this study.

**Conflicts of interest/Competing interests.** The author has no competing interests to declare that are relevant to the content of this article.

**Ethics approval.** Not applicable. The study analysed public, de-identified data from published studies and collected no new data from human participants.

**Consent to participate.** Not applicable.

**Consent for publication.** Not applicable.

**Availability of data and materials.** No new data were collected. The knapsack data are available from the repositories of the original authors (Doroc, Murawski, & Yadav, 2025; Franco et al., 2024b; Suzuki et al., 2023; Yadav, Bossaerts, et al., 2018). The lexical decision data are available from the sites of the four megastudies (Balota et al., 2007; Ferrand et al., 2018; Keuleers et al., 2010, 2012). The repository of this article lists the source and checksum of every file, gives instructions for obtaining the files, and contains the scripts that prepare them, the item-level and summary tables whose licences permit redistribution, and all result files. Derived tables for the Lu et al. (2025) data, the English Lexicon Project and MEGALEX are not redistributed, because these sources carry no licence that permits it; the scripts rebuild them from the original files.

**Code availability.** The `itemtransfer` package, the simulation code and the analysis code of both examples are available at https://github.com/beatsbywoni/itemtransfer and are archived at https://doi.org/10.5281/zenodo.24210664.

**Authors' contributions.** The sole author conceived the study, developed the procedure and the software, conducted the analyses and wrote the manuscript.

**Use of artificial intelligence.** Claude (Anthropic), a large language model, was used under the author's direction for code scaffolding, analysis scripting, running the simulations and analyses, critical review of drafts, and drafting and language editing of the manuscript. The author reviewed all code, results and text and takes full responsibility for the content.

## Open Practices Statement

The data analysed in this article are public and are available from the sources cited under Availability of data and materials. The code for the software, the simulation study and both examples, together with all result files and the supplementary material, is available at https://github.com/beatsbywoni/itemtransfer. The analysis plan of the lexical decision example was written before its transfer analysis was run and is included with a dated list of deviations; it was not registered with an external registry. The tolerance for the calibration slope, the items-only interval for ordering and the analyses marked as unplanned were introduced after results had been seen. The knapsack example and the simulation study were not preregistered.
