# Second worked example: word accuracy in visual lexical decision across four megastudies

Compiled 2026-11-13. Every number below is in a CSV or JSON file in this directory; the file is named in
brackets. Scripts (in `paper/second_example/`): `cache_trials.py`, `prep_measures.py`, `step1_elp_published.py`,
`run_lexical.py`, `finish_lexical.py`, `posthoc_shared_words.py`, `figures_lexical.py`. The pre-specification is
`PLAN.md` (written before step 3, with a dated list of deviations). Vocabulary as in `DESIGN.md`.

## Design in one paragraph

Item: one word of one language. Item family: one megastudy. Sample: the participants of that megastudy. Four
families: English Lexicon Project (ELP, American English), British Lexicon Project (BLP), Dutch Lexicon Project
(DLP), MEGALEX visual lexical decision (French). Outcome: a correct "word" response (0/1); 4,353,921 word
trials after the loader's exclusions [run_info.json]. Three measures: word frequency on the Zipf scale (wordfreq
3.1.1), word length in letters, and OLD20 (mean Levenshtein distance to the 20 nearest words of the megastudy's
own word list; rapidfuzz 3.14.6). Items are language-specific: a Dutch or French word form that is spelled like
an English word is a different item (identifiers carry the language). ELP and BLP share 18,978 word forms (matched
on the lower-cased string). These are used for between-sample agreement in step 2. For transfer, each shared word
was assigned at random (seed 20261113) to one of the two families, which gives 30,992 ELP words, 19,241 BLP
words, 14,089 DLP words and 28,466 MEGALEX words (3,662,112 trials) and families that share no item
[run_info.json, step3].

## Step 1. Recompute and compare

What was done. All three measures were recomputed for all 111,766 megastudy words with one implementation and
compared with the values in the authors' item files (BLP, DLP, MEGALEX stimulus files; the ELP item file from
the project website, obtained on 2026-11-13, see PROVENANCE.md) and with the SUBTLEX-US, SUBTLEX-UK and
SUBTLEX-NL lists [step1_recompute_vs_published.csv, step1_measure_counts.csv, step1_frequency_coverage.csv].

What was found.
- Length. Recomputed length equals the published value for every word that consists of letters only. All
  differences come from how non-letters and accented letters are counted. ELP: the published Length counts the
  apostrophe (1,099 words differ by the number of apostrophes; the number of characters equals the published
  value for all 40,481 words). BLP: 2 words contain a full stop. MEGALEX: identical for all 25,776 words with a
  published value (9,349 of the 28,466 words contain an accented letter). DLP: the published `nchar` is missing
  for 146 words; among the other 13,943 it differs from the number of characters for 61 words, and these are
  exactly the 61 words with a non-ASCII letter; in every one of them the published value equals the number of
  characters plus 2 for each accented letter (an accented letter was counted as three characters). A further 150
  DLP words contain an apostrophe, which the published value counts and the letter count used here does not
  (209 differences from the letter count in all, every one explained by these two rules)
  [step1_dlp_length_discrepancies.csv, run_info.json step1.dlp_length]. The discrepancy reported in
  PROVENANCE.md is therefore confirmed and fully explained.
- OLD20. Against each megastudy's own word list, the recomputed values correlate with the published ones at
  r = .999 in ELP (93.1% of 39,382 values identical; the published value is missing for the 1,099 words with an
  apostrophe), .987 in BLP (44.7% identical, mean difference +0.08), .919 in DLP (mean difference +0.40) and
  .890 in MEGALEX (mean difference +0.37). The ELP authors evidently used the ELP list itself as reference
  lexicon; the other authors used larger lexicons, so the values recomputed against the smaller megastudy lists
  are higher. In ELP the largest differences are for the longest words (for example a published value of 2.0
  against 9.4 recomputed for an 18-letter word), where the published value appears to rest on fewer than 20
  neighbours. OLD20 is not on a common scale across families: its median is 2.75, 1.95, 1.90 and 2.35 with
  reference lexicons of 40,481, 28,730, 14,089 and 28,466 words. With a random 14,089-word reference lexicon in
  every family the medians are 3.25, 2.35, 1.90 and 2.70, so lexicon size alone moves the scale by 0.35 to 0.5.
- Frequency. wordfreq does not know 963 (2.4%), 666 (2.3%), 521 (3.7%) and 844 (3.0%) of the words of the four
  megastudies; these receive the package minimum of 0 (the lowest known value is 1.01, so there is a gap).
  Correlations of the Zipf values with the norms that the megastudy authors used or recommend: ELP .94 with log
  HAL and .86 with log SUBTLEX-US (35,515 words); BLP .91 with SUBTLEX-UK Zipf (27,296 words), .90 with log BNC
  and .86 with the log SUBTLEX count in the stimulus file; DLP .88 with SUBTLEX-NL (12,673 words) and .83 with log
  CELEX; MEGALEX Spearman .69, .82 and .79 with the three frequency columns of the item file (these columns are
  not on a log scale, so only the rank correlation is meaningful). wordfreq contains SUBTLEX for English and
  Dutch, so these are not comparisons of independent sources.
- Outcome. Recomputed word accuracy equals the published BLP and DLP values exactly (PROVENANCE.md). For ELP it
  correlates .996 with the website's I_Mean_Accuracy (97.4% within .05, largest difference .249); the website
  reports a median of 26 observations per word against 34 raw responses, so its values rest on screened data
  [step1_elp_accuracy_vs_published.csv].

## Step 2. Reliability ceiling

What was done. Split-half reliability of word difficulty per megastudy (1,000 random halves of the participants,
logit scale, Spearman-Brown) on all its words and on the family as analysed; agreement between ELP and BLP on the
18,978 shared words, raw and corrected, with an item bootstrap (2,000) [step2_reliability.csv,
step2_agreement_elp_blp.csv, step2_exposure.csv].

Sparse participant by item matrices. In three megastudies a participant saw only part of the list: a median of
1,686 of 40,481 words (4.2%) in ELP, exactly half in BLP, 48% in MEGALEX, and all words in DLP. The package builds
a dense participant by item count matrix and sums it over the participants of each half, so cells without a trial
simply contribute nothing; no imputation is involved, and no word was ever left without a trial in one half
(0 of the word-by-half cells in 200 splits). Trials per word are 34 (30 to 37) in ELP, 39 (38 to 40) in BLP, 39
in DLP and 46 (37 to 74) in MEGALEX, hence about 17, 19.5, 19 and 23 per half. Because the halves are halves of
participants, not of the responses to each word, the split is unbalanced for single words in ELP: the smaller
half of the least-covered word holds a median of 5 responses (minimum 3 over 200 splits). This adds noise to the
half estimates and is one reason for ELP's lower value; it does not bias the Spearman-Brown estimate.

What was found.

| Sample | Participants | Words | Trials per word | Reliability, logit scale (range over splits) | Reliability, rank scale |
|---|---|---|---|---|---|
| ELP | 814 | 40,481 | 34 | .862 (.861 to .864) | .823 |
| BLP | 78 | 28,730 | 39 | .941 (.936 to .943) | .923 |
| DLP | 39 | 14,089 | 39 | .917 (.914 to .919) | .860 |
| MEGALEX | 96 | 28,466 | 46 | .884 (.882 to .886) | .813 |

For the families as analysed the values are .866 (ELP, 30,992 words) and .947 (BLP, 19,241 words). On the rank
scale an ordering correlation cannot exceed about the square root of the rank reliability (.90 to .97).
Agreement between ELP and BLP on the shared words: r = .728 on the logit scale (item bootstrap .721 to .735),
Spearman .682; with reliabilities of .852 and .907 on these words the corrected correlation is .828 (.822 to
.836). The two samples therefore disagree on word difficulty beyond measurement error: about 31% of the
reliable variance is not shared (1 - .828 squared). Dialect, participant populations, the composition of the
lists and the nonwords all differ between the two megastudies, so this is a ceiling for any measure that is
computed from the word alone: it cannot be expected to predict one megastudy better than the other megastudy's
data on the same words would.

## Step 3. Transfer

What was done. `itemtransfer.transfer` on the full data, each family held out in turn, each measure alone and the
three-measure model, every training trial counted once, 1,000 two-way bootstrap resamples (participants within
samples, words within families; processed in batches of 50), 500 item splits for the prediction criterion, seed
20261113 [step3_transfer.csv, step3_bootstrap.csv]. No bootstrap fit failed to converge. The fallback to a sample
of words was not needed.

Frequency (Zipf). Percentile intervals; for ordering see the note below the table.

| Held-out family | Training slope | Held-out family's own slope | Ordering | Calibration slope | Log-loss reduction |
|---|---|---|---|---|---|
| ELP | 0.80 (0.78 to 0.82) | 0.68 (0.66 to 0.70) | .564 | 0.84 (0.81 to 0.88) | .071 (.067 to .076) |
| BLP | 0.70 (0.68 to 0.72) | 1.00 (0.96 to 1.04) | .678 | 1.43 (1.37 to 1.49) | .132 (.127 to .139) |
| DLP | 0.78 (0.76 to 0.80) | 0.70 (0.66 to 0.74) | .536 | 0.89 (0.85 to 0.95) | .097 (.087 to .108) |
| MEGALEX | 0.79 (0.77 to 0.80) | 0.72 (0.68 to 0.75) | .525 | 0.92 (0.87 to 0.96) | .085 (.077 to .093) |

- Ordering transfers everywhere: a slope fitted on three megastudies orders the words of the fourth with a
  Spearman correlation of .52 to .68, across languages as well as within English. (The sign of the slope is all
  that matters for ordering, so this equals the within-family rank correlation.)
- Scale does not transfer exactly anywhere. By the rule fixed in advance, no calibration-slope interval includes
  1. The size differs: the trained effect is 8% to 16% too large for ELP, DLP and MEGALEX and 43% too small for
  BLP. The three smaller deviations are partly a consequence of BLP being among their training families (its
  steeper relation raises the trained slope to about 0.79 while their own slopes are about 0.70).
- Prediction: the transferred frequency relation removes 7% to 13% of the trial-level log loss (Brier 5% to
  15%). The gain is real but modest, as expected for single binary responses with mean accuracies of .76 to .89.

Length. The training slope is positive (longer words are answered more accurately: 0.05 to 0.10 logits per
letter) and its interval excludes 0 in every fold, but the relation is tiny. Ordering in the held-out family is
.06 (BLP), .11 (DLP), .07 (MEGALEX) and -.01 (ELP). The calibration slope ranges from 0.20 (0.11 to 0.28) for ELP
to 2.55 (2.04 to 3.17) for DLP; the log-loss reduction is at most .004 and is negative for ELP (-.005, interval
-.008 to -.004): the trained length relation makes predictions for ELP worse than no measure at all.

OLD20. Training slopes are negative (-0.10 to -0.15 per unit: words with distant neighbours are answered less
accurately). In ELP, BLP and MEGALEX the held-out family's own slope has the same sign (-0.14, -0.13, -0.26);
in DLP it is positive (+0.16, 0.10 to 0.22), so the transferred relation orders Dutch words the wrong way
(ordering -.07, calibration slope -1.02, interval -1.43 to -0.64, log-loss reduction -.006). Elsewhere ordering
is .07 to .13 and the log-loss reduction at most .003.

Three-measure model [step3_three_measure_coefficients.csv, step3_three_measures_minus_frequency.csv].
In the training families the coefficients of length and OLD20 change strongly once both are in the model:
length rises from about 0.05 to 0.36 to 0.51 per letter and OLD20 falls from about -0.10 to -0.50 to -0.63.
Within each family the same pattern holds (length 0.28 to 0.61, OLD20 -0.26 to -0.79, all intervals exclude 0).
The two measures are strongly correlated (step 4) and have opposite signs, so each hides the other when used
alone. Out of family the three-measure model improves on frequency alone in three folds: the log-loss
reduction rises by .042 (BLP, .039 to .045), .030 (DLP, .025 to .034) and .028 (MEGALEX, .025 to .032). In ELP
it does not: the difference is -.0002 (-.005 to .004), ordering falls from .564 to .535, and the calibration
slope of the combined predictor is 0.69 (0.66 to 0.72).

Note on the ordering intervals [step3_interval_check.csv, step5_ordering_shift.csv]. In 8 of the 16 rows the
percentile interval of the ordering correlation does not contain the estimate (for example BLP, frequency:
estimate .678, percentile interval .644 to .669). The resampled correlations lie 0.02 to 0.04 below the estimate.
A check on 1,000 words per family shows that the shift comes entirely from resampling participants (-0.018 to
-0.034 with participants only, between -0.002 and +0.001 with items only): duplicated participants add noise to
word accuracies and attenuate a rank correlation. With tens of thousands of items the interval is narrower than
this shift. The table therefore gives ordering without an interval; the bootstrap standard deviations are 0.005
to 0.010 for frequency, and percentile and basic (reflected) intervals are in the file. The basic interval
(BLP, frequency: .686 to .712) lies above the estimate, which is coherent if it is read as an interval for the
ordering that unlimited participants would give, since the estimate is itself attenuated by participant noise.
Calibration slopes of frequency and of the three-measure model and all log-loss reductions are not affected
(mean shift at most 0.002 and 0.0003; for the unstable calibration slopes of length and OLD20 it reaches 0.04).

## Step 4. Design diagnostics

What was done. `itemtransfer.diagnose` on the result of step 3, with length treated as a set of levels
(`max_levels=25`) and 400 resamples for the common-range intervals; the transfer was also run in full with equal
weights for the training samples [step4_*.csv, step4_warnings.txt, step3_transfer_equal_weights.csv].

- Level structure of length. Length takes 21 values in ELP (1 to 21), 11 in BLP and DLP (2 to 12) and 8 in
  MEGALEX (2 to 9). A level indicator fitted in the held-out family (one probability per length) reduces log
  loss by .003, .006, .000 and .003 (BLP, DLP, ELP, MEGALEX), against .003, .004, -.005 and .002 for the
  transferred slope. Even the best possible function of length, fitted in the family itself, explains almost
  nothing; the weak result is a property of length, not of the linear form. In ELP the relation between length
  and accuracy is flat (.82 to .86 between 3 and 18 letters), while in the other three families accuracy rises
  with length up to about 8 to 10 letters [step4_accuracy_by_length.csv, Figure 1].
- Range overlap. For length, 94% of ELP words lie inside the training range (2 to 12 letters); restricting to
  the common range does not rescue the result (calibration slope 0.19, 0.10 to 0.28). For MEGALEX, restricting
  the training families to 2 to 9 letters moves the calibration slope from 1.84 to 1.24 (0.97 to 1.55): the
  slope per letter depends on the range covered. For frequency the ranges coincide (0 to about 7.7) and nothing
  changes. For OLD20 the upper end differs by family (5.0 to 10.1) because both word length and lexicon size
  differ.
- Weak training relation. No row is flagged: with 60,000 to 80,000 training words every training-slope
  interval excludes 0, including length. The calibration slopes of length (0.20 to 2.55) and OLD20 (-1.02 to
  2.69) are nevertheless unstable ratios. In data of this size the flag "interval includes 0" is not a
  sufficient guard; the size of the training slope and the held-out family's own slope have to be read as well.
- Collinearity. Length and OLD20 correlate (Spearman) .85 in ELP, .75 in BLP, .74 in MEGALEX and .69 in DLP;
  frequency correlates -.24 to -.32 with length and -.23 to -.38 with OLD20. The package warns for the first
  three families. Part of this collinearity is by construction: longer words have fewer close neighbours in any
  lexicon.
- Weighting. After the shared words are divided, ELP no longer dominates the trial counts (1.05, 0.75, 0.55 and
  1.31 million trials), and equal weights barely change the frequency results: calibration slopes 0.84 (0.80 to
  0.87), 1.43 (1.37 to 1.50), 0.86 (0.82 to 0.92) and 0.91 (0.86 to 0.95) for ELP, BLP, DLP and MEGALEX, against
  0.84, 1.43, 0.89 and 0.92 with trial weights. The expected weighting problem did not materialise for
  frequency. It does for OLD20: its training slope falls from -0.096 to -0.054 (ELP held out) and from -0.113
  to -0.073 (BLP held out) with equal weights, and the calibration slopes move from 1.45 to 2.57 and from 1.17
  to 1.81, which the package flags.

Sensitivity [sensitivity_transfer.csv; 200 resamples each].
- Opposite assignment of the shared words: the frequency rows change in the third decimal at most (calibration
  slopes 0.84, 1.43, 0.90, 0.92).
- Shared words dropped from both families: the picture changes. BLP's own frequency slope falls from 1.00 to
  0.71 and its calibration slope from 1.43 to 1.04 (0.97 to 1.11); DLP and MEGALEX move to 1.02 and 1.08, ELP to
  0.88; ordering in BLP falls from .68 to .45. A post hoc analysis (not pre-specified) explains this
  [posthoc_frequency_slope_by_word_set.csv]. On the 18,978 shared words, the same items in both samples, the
  frequency slope is 0.98 (0.95 to 1.01) in ELP and 1.16 (1.14 to 1.19) in BLP. On the words that only one
  megastudy contains it is 0.63 (ELP, 21,503 words) and 0.71 (BLP, 9,752 words, of which 45% have a Zipf value
  below 2 and whose mean accuracy is .58). So the slope per Zipf unit depends more on which words are in the set
  (0.63 against 0.98 within the same ELP participants) than on the sample (0.98 against 1.16 on the same words).
  Figure 1 shows why: the relation between frequency and accuracy is not linear on the logit scale across the
  whole range; it is flat at the top and at the floor value of unknown words.
- Words unknown to wordfreq removed (2.3% to 3.7% per family): training slopes rise to 0.88 to 0.97, the
  calibration slopes become 0.90 (ELP), 1.29 (BLP), 0.86 (DLP) and 0.95 (MEGALEX, 0.88 to 1.01, the only interval
  that includes 1). The floor value flattens the fitted slope but does not create the pattern.
- OLD20 against an equal-sized reference lexicon: training slopes are roughly halved (-0.04 to -0.08), the sign
  reversal in DLP remains, and log-loss reductions stay at or below .001. The weak and inconsistent result for
  OLD20 is not an artefact of unequal lexicon size.

## Step 5. Uncertainty

What was done. The intervals of step 3; `check_intervals` (200 simulated data sets, 200 resamples each) on two
designs built with `design_from_data` from a fixed-seed sample of 1,000 words per family with all their
participants and the observed exposure pattern (ELP participants see a median of 42 of the 1,000 words):
(a) one common slope, (b) family-specific slopes; and the transfer on that 1,000-word sample
[step5_check_intervals.csv, step5_designs.csv, step5_transfer_1000_words.csv]. The large-sample targets used 8
times the items and 4 times the participants, 5 repetitions (the package default of 25 and 10 does not fit in
7 GB for this design).

What was found.
- Coverage of the calibration-slope interval for frequency is 93.5% to 95.5% in the common-slope design and
  93.0% to 94.5% with family-specific slopes (Monte Carlo standard error about 1.7 points); coverage of the
  log-loss interval is 95% to 98%. The interval of a null measure excluded 0 in at most 0.5% of data sets and
  its training relation was flagged as weak in 94.5% to 97%. The intervals can be trusted for a design of this
  shape.
- With 1,000 words per family the interval is about 0.24 to 0.33 wide. In the family-specific design the
  interval for BLP (target 1.38) never included 1, while the intervals for DLP (target 0.89), MEGALEX (0.91) and
  ELP (0.83) still included 1 in 62%, 78% and 25% of data sets. The 1,000-word transfer on the real data agrees:
  BLP 1.40 (1.23 to 1.59), ELP 0.81 (0.69 to 0.95), DLP 0.91 (0.79 to 1.05), MEGALEX 0.89 (0.77 to 1.02). The
  small deviations of DLP and MEGALEX are therefore visible only at megastudy scale.
- A caution that the simulation adds: even when one slope generates all families, the large-sample calibration
  slope is not exactly 1 (targets 0.96, 1.00, 1.01 and 1.05), because the models are marginal over participants
  and items and the families differ in mean accuracy and in the distribution of the measure. Deviations of a
  few per cent from 1 should not be read as a failure of transfer. The observed deviations for DLP and MEGALEX
  (0.89 and 0.92) are not far outside this band; those for ELP (0.84) and BLP (1.43) are.

## What the procedure showed that a within-megastudy analysis would not

1. Ordering, scale and prediction separate cleanly for frequency. Any single megastudy shows that frequency
   predicts accuracy. Only the transfer shows that the rank order carries over to another megastudy and another
   language almost unchanged, while the effect size per Zipf unit does not: between 0.68 and 1.00 across
   families, with calibration slopes from 0.84 to 1.43.
2. The effect size is not a property of the language or the sample alone. The between-language differences
   (Dutch and French against American English: own slopes 0.70, 0.72, 0.68) are smaller than the difference
   between the two English megastudies (0.68 against 1.00), and most of that difference follows the word list:
   on identical words the two English samples differ by 0.98 against 1.16, while within one sample the slope
   differs by 0.63 against 0.98 between word sets. A slope from one megastudy is a statement about its word
   selection as much as about readers.
3. Length adds nothing out of family on its own. Its training relation is detectable (the interval excludes 0)
   and useless (log-loss reduction at most .004, negative for ELP), and its direction (longer words are more
   accurate) holds in three families and is absent in the family with the widest range of lengths.
4. OLD20's simple relation is carried by its correlation with length and is not stable across families: alone
   it has a small negative slope in three families and a positive one in Dutch. Once length is in the model the
   coefficient of OLD20 is negative in all four families and five times larger, and the coefficient of length
   grows as much. The pair of measures, not either one, carries information, and that information transfers
   to three of the four held-out families (log-loss reduction +.03 to +.04 beyond frequency) but not to ELP,
   whose words reach 21 letters and whose OLD20 reaches 10.1, outside what the other families contain.
5. The diagnostics changed the reading of two results that a table of criteria alone would invite: the
   "significant" training slope of length is not a usable relation (level indicator), and the BLP result
   depends on the composition of the family (shared words dropped).

## What is already well known

That word frequency is the strongest single predictor of lexical decision performance, and that the megastudies
agree on this, is established; the megastudy articles themselves report frequency, length and neighbourhood
effects, mostly for response times (Balota et al., 2007, https://doi.org/10.3758/BF03193014; Keuleers et al.,
2010, https://doi.org/10.3389/fpsyg.2010.00174; Keuleers et al., 2012,
https://doi.org/10.3758/s13428-011-0118-4; Ferrand et al., 2018, https://doi.org/10.3758/s13428-017-0943-1).
Analyses that pool several of these megastudies exist (Miller, 2024,
https://doi.org/10.3758/s13428-024-02419-y, for response-time outliers), and generalisation across megastudies
has been named as open (Martínez et al., 2025, https://doi.org/10.3758/s13428-025-02829-6). The contribution of
this example is therefore not the frequency effect. It is the demonstration, on data every reader of the journal
knows, that the procedure recovers the expected result (ordering by frequency), quantifies what is usually left
implicit (the effect size is specific to the word list and procedure), and gives a disciplined negative result
for two familiar measures used alone. Accuracy is the secondary outcome in this literature; response times are
not analysed because the procedure is defined for binary responses.

## What weakens the example (stated plainly)

- The headline contrast (BLP's calibration slope of 1.43) is not robust to the definition of the BLP family: with
  the shared words dropped it is 1.04. The honest summary is that the effect size depends on word selection, and
  the paper should present the BLP result together with the word-set analysis, not as a difference between
  British and American readers.
- With this many words every interval is narrow and every calibration slope "fails" the rule that the interval
  must include 1, although the simulation shows that deviations of up to about 5% arise under a common slope.
  The example needs an explicit statement about practically relevant deviation; the rule alone would mislabel
  DLP and MEGALEX.
- The weak-training flag never fires, and the percentile interval of the ordering correlation excludes its own
  estimate in half of the rows. Both are limitations of the package defaults at this scale (see below).
- The relation between Zipf frequency and logit accuracy is visibly non-linear (Figure 1), so a single slope per
  unit is a coarse summary; no transformation was pre-specified and none was tried.
- The weighting diagnostic, expected to matter because of ELP's 814 participants, is uninformative for
  frequency.

## Limitations

- Language, megastudy, laboratory, procedure, nonword construction and participant population are confounded:
  each language has one megastudy (English has two, with different dialects and lists). No difference between
  families can be attributed to language.
- Participants: 814, 78, 39 and 96. The participant part of the two-way bootstrap rests on 39 participants in
  DLP. ELP has 814 participants but each saw 4% of the list, so its word difficulties are the least reliable.
  The loader keeps 814 ELP participants where the article reports 816 (PROVENANCE.md).
- Ceiling: 35%, 31%, 41% and 57% of the words of the four megastudies have accuracy above .95, and 16% to 24%
  have no error at all [step2_exposure.csv]. Frequent words carry little information about slopes, and the
  logit scale stretches small differences there.
- Frequency comes from one fixed corpus snapshot (wordfreq 3.1.1, data up to about 2021, no longer updated),
  which is decades later than some of the data collections and mixes sources that differ by language. Part of
  any slope difference between languages is measurement of the measure. Unknown words receive a floor of 0.
  Frequency is computed from the item and a fixed external resource, not from the item alone.
- OLD20 depends on the reference lexicon. Using each megastudy's own list makes the definition uniform but the
  scale family-specific; the equal-size variant changes slopes but not conclusions.
- The 18,978 shared English words were split at random; a shared word contributes the responses of one megastudy
  only to the transfer analysis. Results are stable under the opposite assignment and not under dropping the
  shared words.
- The models are marginal logistic regressions on word counts; participants enter through the bootstrap only.
- Licences. ELP (raw files and the website item file) and MEGALEX carry no licence that permits
  redistribution, and the ELP website restricts its lists to non-commercial research; BLP, DLP and the SUBTLEX
  lists are CC BY-NC-SA 4.0. No word-level table derived from ELP or MEGALEX is in `results/`: the word-level
  tables (measures, predictions) are in `cache/` and must not be redistributed. The only word-level file in
  `results/` is `step1_dlp_length_discrepancies.csv` (209 DLP words), which is derived from the Dutch Lexicon
  Project (Keuleers et al., 2010) and may be shared only under CC BY-NC-SA 4.0 with attribution. All other
  files are aggregates. The public release should contain the loader, the manifest with hashes, the scripts and
  the aggregate tables.

## Figures

- `figures/figure_lexical_accuracy_by_measure.png` and `.pdf`: proportion of correct responses against each
  measure, by family (bins of 0.5 Zipf units with unknown words as their own bin at 0, each length, bins of 0.25
  OLD20 units; bins with at least 30 words; data in `figure1_binned_accuracy.csv`).
- `figures/figure_lexical_transfer.png` and `.pdf`: the three criteria for each held-out family and model.
  Vertical lines are 95% percentile bootstrap intervals for calibration slope and log-loss reduction and the
  estimate plus or minus 1.96 bootstrap standard deviations for ordering (see the note in step 3). Dotted
  segments in the ordering panel: square root of the rank-scale reliability of the held-out family. Dashed line:
  calibration slope of 1.

## Run record

Versions: Python 3.13.17, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, matplotlib 3.11.2, wordfreq 3.1.1, rapidfuzz
3.14.6, itemtransfer 0.1.0 (with the changes listed in the hand-over). Seed 20261113 throughout (derived streams
in run_info.json). Machine: 2 cores, 7 GB. Run times (wall clock, stages partly in parallel on two cores, so
they include contention): loading 27 s, step 1 84 s, step 2 158 s, step 3 2,133 s, step 3 with equal weights
3,880 s, step 4 930 s, sensitivity 3,018 s, step 5 4,751 s; a single uncontended run of step 3 takes about
25 minutes; peak memory 2.4 GB [run_info.json].
