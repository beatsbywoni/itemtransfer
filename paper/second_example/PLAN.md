# Second worked example: pre-specification of the transfer analysis

Written 2026-11-13T10:12:50+0900, after step 1 (recompute and compare) had been run and before any code for
steps 2 to 5 was run on these data. Nothing below was changed after transfer results were seen; later additions,
if any, are listed at the end under "Deviations" with a timestamp.

## What had already been seen when this plan was written (honest record)

- The feasibility probe (FEASIBILITY.md, 2026-11-13) had looked, on mirror copies of the data and with rough
  versions of the measures, at the within-megastudy Spearman correlations between word accuracy and Zipf
  frequency (0.53 to 0.69) and word length (-0.02 to 0.11), at within-megastudy binomial slopes (Zipf about 0.70
  in three megastudies and 1.06 in the British Lexicon Project; length 0.01 to 0.12), at one split-half
  reliability per megastudy, and at the raw agreement between the English and British projects on shared words
  (r = 0.73). So the direction of the main expected result (frequency orders words everywhere, its effect size
  is larger in the British project, length is close to a null measure) was known in outline before this plan.
  No leave-one-family-out quantity (training slope, calibration slope, log-loss reduction, ordering of a
  transferred predictor) had been computed by anyone.
- Step 1 of this run (prep_measures.py) had been completed: distributions of the three measures and their
  agreement with published values were seen. No accuracy value from the original files had been related to any
  measure in this run.

## Data

Original authors' files only (original/, hashes in original/MANIFEST.sha256), read with load_lexical.py; its
exclusions are final and no participant, word or trial is removed on the basis of accuracy or response time.
No published item-level value of the English Lexicon Project is used anywhere.
Outcome: correct response to a word in visual lexical decision (0/1). Item = one word of one language.

## Item families and samples

Four item families, one per megastudy, each with one sample (its participants): English Lexicon Project (ELP),
British Lexicon Project (BLP), Dutch Lexicon Project (DLP), MEGALEX (visual lexical decision).
- Items are language-specific: item identifier = language code + ":" + the NFC-normalised, lower-cased string
  ("en:", "nl:", "fr:"). A Dutch or French word form that is identical to an English string is a different item.
- ELP and BLP are both English and share word forms (matched on the lower-cased string). Shared words are used in
  step 2 for between-sample agreement. For transfer, each shared word is assigned to exactly one of the two
  families: the shared words are sorted, permuted with numpy.random.default_rng(20261113), and the first half
  of the permutation goes to the ELP family, the rest to the BLP family. The responses of the other megastudy to
  an assigned word are not used in the transfer analysis.
- Sensitivity (point estimates; intervals if run time allows): (a) the opposite assignment; (b) shared words
  dropped from both families.

## Measures (fixed here)

1. zipf: word frequency on the Zipf scale, wordfreq.zipf_frequency(word, language) from the Python package
   wordfreq 3.1.1 with its default word list, languages "en" (both English megastudies), "nl", "fr". Words unknown
   to the package get its minimum (0.0); they are counted and kept.
2. length: number of Unicode letters in the NFC-normalised string (an accented letter counts once; apostrophes
   and full stops are not letters).
3. old20: mean Levenshtein distance (unit costs, rapidfuzz 3.14.6) from the lower-cased string to its 20 nearest
   other entries of a reference lexicon. The reference lexicon is defined in the same way for every family: the
   complete word list of the megastudy the item belongs to (40,481, 28,730, 14,089 and 28,466 words). Known
   consequence, to be discussed: lexicon size differs, so the values are not on a common scale across families.
   A shared English word takes the value computed against the lexicon of the family it is assigned to.
   Sensitivity measure (not one of the three, point estimates only): old20 against a fixed-seed random 14,089-word
   subset of each megastudy's list (equal lexicon size).
No null or control measure. No transformation of any measure. Models: each measure alone and the three-measure
model ("combined").

## Steps

Step 2. itemtransfer.reliability per megastudy on all its words (1,000 random halves of the participants, seed
20261113), with trials per word overall and per half (minimum and median over splits) because each participant
saw only part of the list in three of the four megastudies. itemtransfer.agreement between ELP and BLP on all
shared words (raw and corrected, item bootstrap 2,000, seed 20261113). Reliability is also reported for the four
families as analysed.

Step 3. itemtransfer.transfer, every family held out in turn, measures zipf, length, old20 and combined.
Primary weighting: the package default (every training trial counts once). n_boot = 1,000 two-way bootstrap
resamples (boot_batch = 50), n_splits = 500, n_splits_boot = 10, percentile intervals, level 0.95, seed 20261113.
Full data first; if run time or memory is prohibitive, a fixed-seed random sample of 4,000 words per family
(numpy.random.default_rng(20261113), drawn after the shared-word assignment) is used for the bootstrap and the
full-data point estimates are still reported. Reported per held-out family and model: training slope, ordering,
calibration slope, log-loss reduction (and Brier), the held-out family's own slope, all with intervals.

Step 4. itemtransfer.diagnose on the same result: level structure of length (max_levels raised to 25 so that
length is treated as a set of levels in every family; the other settings are defaults), range overlap (interval
of the common-range calibration slope with 400 resamples), weak training relation, correlation between measures
within each family (length and old20 in particular), weighting (trials against equal). Because the number of
participants and trials differs strongly between megastudies (814 participants in ELP), the transfer of step 3
is also run in full with weights="equal" (same seed and settings) and reported beside the primary run.

Step 5. Uncertainty: the intervals of step 3, and itemtransfer.check_intervals on designs built with
itemtransfer.design_from_data from a fixed-seed random sample of 1,000 words per family (same seed), measure
zipf: (a) common slope (transfer holds by construction), (b) family-specific slopes (the observed heterogeneity).
n_sim = 200, n_boot = 200, seed 20261113, null measure included; target_scale reduced to what memory allows and
recorded. The transfer of step 3 is also run on that 1,000-word sample so that its intervals can be set beside
the simulated coverage.

## Reading rules fixed in advance

- A measure "orders" the held-out words if the interval of the ordering correlation excludes 0; its "scale
  transfers" if the calibration-slope interval includes 1 and excludes 0; "prediction" is judged by the interval
  of the log-loss reduction. With tens of thousands of words, intervals will be narrow and almost any deviation
  from 1 will be detectable; the size of the deviation is therefore reported and interpreted, not only whether
  the interval excludes 1.
- All three criteria are reported for every row, including rows that weaken the example.

## Deviations

- 2026-11-13T10:14:29+0900 (before any step 2 to 5 result existed): the item-level file of the English Lexicon Project was obtained
  from the project website by the user (original/elp/elexicon_items.csv, see PROVENANCE.md). Its published
  values (Length, OLD, Log_Freq_HAL, LgSUBTLWF, I_Mean_Accuracy) are now used in step 1 for comparison with the
  recomputed values (step1_elp_published.py). The sentence above that no published ELP item value is used
  therefore holds for the measures and for steps 2 to 5, not for the comparison in step 1. Nothing else changed.
- 2026-11-13T12:09:49+0900 (after the transfer results had been seen). Additions that were not in the plan, all reported as such:
  (1) a sensitivity run with the words unknown to wordfreq removed (written into run_lexical.py before step 3
  results were inspected, but not listed above); (2) coefficients of the three-measure model in the training
  families and within each family, and bootstrap intervals for the difference between the three-measure model
  and frequency alone; (3) check_intervals was run with prediction=True and target_scale=(8, 4), target_reps=5;
  (4) post hoc, prompted by the results: basic (reflected) intervals and a decomposition of the downward shift
  of resampled ordering correlations (finish_lexical.py), and the within-sample frequency slope by word set for
  the two English megastudies (posthoc_shared_words.py). The sensitivity runs used 200 bootstrap resamples.
  No pre-specified analysis was dropped or altered; the 4,000-word fallback was not needed.
