## Worked example 1: Word measures in lexical decision across four megastudies

The first example applies the procedure to data that many readers of this journal know: megastudies of visual lexical decision. With tens of thousands of items per family, it shows the procedure at a scale where intervals are narrow and where the reading of the calibration slope against a tolerance matters. The results on word frequency agree with what the field knows, which is the purpose of a first example: a validation procedure should recover known facts before it is trusted with open questions.

### Task, measures and data

In visual lexical decision, a participant sees a string of letters and decides whether it is a word. The example uses the word trials of four megastudies. Two are English: the English Lexicon Project from the United States (Balota et al., 2007), called the American megastudy below, and the British Lexicon Project (Keuleers et al., 2012), the British megastudy. The Dutch megastudy is the Dutch Lexicon Project (Keuleers et al., 2010), and the French megastudy is MEGALEX (Ferrand et al., 2018). Each megastudy is one family with one sample. The outcome is the accuracy of the response. Accuracy is the secondary outcome of these studies, after response time, and for many words it is close to its maximum; it mostly reflects whether participants know a word (Keuleers et al., 2015).

Three familiar measures were examined. Word frequency was expressed on the Zipf scale, the base-10 logarithm of the frequency per billion words (van Heuven et al., 2014), and taken from one multilingual resource for all three languages (Speer, 2022), so that one implementation serves all families. Between 2.3% and 3.7% of the words of a megastudy are absent from this resource and received its lowest value, 0. Word length was counted in letters. Neighbourhood distance is the mean edit distance from a word to its 20 nearest words (Yarkoni et al., 2008), computed here against the word list of the same megastudy. This measure is therefore a function of the word and of a reference list. One implementation gives it one definition, but not one scale: the lists differ in size and composition, and a shared English word takes the value of the megastudy to which it is assigned.

The two English megastudies share 18,978 words, which conflicts with the requirement that families share no item. The shared words were used for the agreement between samples in step 2. For the transfer analysis, each shared word was assigned at random to one of the two megastudies. The consequences of this choice were examined in two further analyses, one with the opposite assignment and one in which the shared words were removed from both megastudies. The main analysis comprises 92,788 words and 3.7 million responses. An analysis plan was written before step 3 was run and is part of the supplementary material, with a list of deviations. The plan was written after a feasibility check that had shown rough correlations and slopes within each megastudy, including a larger frequency slope in the British megastudy, so the example is not a confirmatory test. The supplementary material gives the timeline and the flow of the data, from 4.35 million word responses in the four megastudies to the 3.66 million that remain when each shared word is kept in one megastudy.

### Steps 1 and 2: Recomputed measures and reliability ceiling

Recomputing the measures uncovered differences of definition that a user of the published item files would not see. The published length values of the Dutch megastudy count each accented letter as three characters, and two megastudies count apostrophes. Published values of neighbourhood distance rest on reference word lists of different sizes, which shifts the scale of the measure by 0.35 to 0.5 units between megastudies.

The split-half reliability of word difficulty was between .87 and .95 for the families as analysed (Table 7). The two English megastudies nevertheless disagreed beyond measurement error. On their shared words, the correlation between the two sets of word accuracies was .73, and .83, 95% CI [.82, .84], after correction for unreliability. Part of the reliable variation in word difficulty is therefore specific to a megastudy, whether because of dialect, participants or the composition of the lists (see also Keuleers et al., 2012). A measure computed from the word alone cannot account for that part in both megastudies at once.

### Step 3: Transfer

Word frequency ordered the words of every held-out megastudy, across languages as well as within English (Table 7). The reduction in log loss was 7% to 13%. The calibration slopes of the American, Dutch and French megastudies lay between 0.84 and 0.92, and their intervals lay inside the tolerance of 0.80 to 1.25. For the British megastudy the effect was 1.43 times as large as trained, and the interval lay outside the tolerance.

These conclusions depend on the tolerance, which was chosen after the results were known. Under a narrower tolerance of 0.90 to 1.11, the American and the British megastudy would both differ in scale and the other two would be undetermined. Under a wider tolerance of 0.67 to 1.50, all four would agree. The robust statement is that the frequency effect transferred with a deviation of at most 16% in three megastudies and of 43% in the fourth.

Word length and neighbourhood distance, used alone, contributed almost nothing out of family: their reductions in log loss were at most .004, and the trained relation for neighbourhood distance ordered the Dutch words in the wrong direction. For neighbourhood distance this result concerns the measure together with its reference list. With reference lists of equal size the trained slopes were about half as large and the conclusion was the same (supplementary material), but the lists still differ in language and composition, so the result does not show that a neighbourhood measure on a common scale would fail to transfer. The two measures are strongly correlated and act in opposite directions, so each hides the other when used alone. A model with one slope for each of the three measures improved on frequency alone in the British, Dutch and French megastudies, by .03 to .04 in the reduction in log loss. In the American megastudy it did not: ordering was lower than for frequency alone, and the calibration slope of 0.69 lay outside the tolerance. The American list contains longer words than the other three, so the trained relations for length and neighbourhood distance were applied outside their range.

**Table 7.** Transfer to each held-out megastudy in the lexical decision example (step 3).

| Held-out megastudy | Words | Reliability | Model | Slope trained / fitted in the family | Ordering | Calibration slope | Reduction in log loss |
|---|---|---|---|---|---|---|---|
| English Lexicon Project | 30,992 | .87 | Frequency | 0.80 / 0.68 | .56 [.56, .57] | 0.84 [0.81, 0.88] | .071 [.067, .076] |
| | | | Three measures | | .53 [.53, .54] | 0.69 [0.66, 0.72] | .071 [.064, .078] |
| British Lexicon Project | 19,241 | .95 | Frequency | 0.70 / 1.00 | .68 [.67, .69] | 1.43 [1.37, 1.49] | .132 [.127, .138] |
| | | | Three measures | | .75 [.74, .75] | 1.54 [1.48, 1.61] | .174 [.168, .181] |
| Dutch Lexicon Project | 14,089 | .92 | Frequency | 0.78 / 0.70 | .54 [.52, .55] | 0.89 [0.85, 0.95] | .097 [.087, .108] |
| | | | Three measures | | .58 [.57, .59] | 0.98 [0.93, 1.03] | .127 [.117, .138] |
| MEGALEX | 28,466 | .88 | Frequency | 0.79 / 0.72 | .52 [.52, .53] | 0.92 [0.87, 0.96] | .085 [.077, .093] |
| | | | Three measures | | .59 [.58, .60] | 0.92 [0.88, 0.97] | .114 [.103, .123] |

*Note.* Slopes are in logits per Zipf unit. Brackets give 95% bootstrap intervals from 1,000 resamples: items only for ordering, participants and items for the other criteria. The results for length and neighbourhood distance alone are in the supplementary material.

### Step 4: Design diagnostics and sensitivity analyses

None of the five diagnostics explained the larger effect in the British megastudy, and the explanation had to be sought outside them. Frequency covers the same range in all four megastudies, the training relation was strong, and equal weighting of the training samples changed no calibration slope of frequency by more than 0.03. The only flag concerned length and neighbourhood distance, whose Spearman correlation was between .69 and .85.

Four sensitivity analyses narrowed the explanation down (Table 8). The opposite assignment of the shared words changed nothing. Removing the shared words from both English megastudies brought the British calibration slope to 1.04 and, because the British megastudy is among their training families, raised the slopes of the Dutch and French megastudies to 1.02 and 1.08. Removing the words that the frequency resource does not know reduced it to 1.28. A cubic function of frequency, which was not planned and was added to test whether a non-linear relation is responsible, left it at 1.33. The mismatch in scale is therefore tied to which words a list contains, and a more flexible function of frequency does not remove it.

A follow-up analysis, also unplanned, compared slopes on fixed word sets. On the shared words the frequency slope was 0.98 logits per Zipf unit in the American sample and 1.16 in the British sample, a ratio of 1.19. Within the American sample alone, it was 0.98 on the shared words and 0.62 on the remaining words. The choice of words thus mattered more than the sample. This agrees with earlier findings that the size of the frequency effect depends on the range of words and on the vocabulary of the participants (Brysbaert et al., 2018; Keuleers et al., 2015). The procedure cannot say which property of the word sets is responsible. Language, laboratory, nonwords and list composition are confounded across megastudies. Figure 5 shows accuracy as a function of each measure in the four megastudies.

**Table 8.** Calibration slope of word frequency under five variants of the lexical decision analysis.

| Analysis | English Lexicon Project | British Lexicon Project | Dutch Lexicon Project | MEGALEX |
|---|---|---|---|---|
| Main analysis | 0.84 [0.81, 0.88] | 1.43 [1.37, 1.49] | 0.89 [0.85, 0.95] | 0.92 [0.87, 0.96] |
| Shared English words assigned the other way | 0.84 [0.81, 0.88] | 1.43 [1.37, 1.49] | 0.90 [0.85, 0.95] | 0.92 [0.86, 0.96] |
| Shared English words removed | 0.88 [0.84, 0.92] | 1.04 [0.97, 1.11] | 1.02 [0.97, 1.09] | 1.08 [1.01, 1.13] |
| Words unknown to the frequency resource removed | 0.90 [0.86, 0.95] | 1.28 [1.23, 1.34] | 0.86 [0.81, 0.91] | 0.95 [0.88, 1.00] |
| As the previous row, with a cubic function of frequency | 0.90 [0.86, 0.95] | 1.33 [1.27, 1.39] | 0.84 [0.79, 0.90] | 0.95 [0.87, 1.00] |

*Note.* Brackets give 95% bootstrap intervals; the variants used 200 resamples. The last two rows were not part of the analysis plan.

*Figure 5 about here.*

### Step 5: Uncertainty

The simulation check of step 5 was applied to a design with 1,000 words per family and the observed pattern of missing responses. The intervals of the calibration slope contained the true value in 93% to 96% of 200 simulated data sets, and a measure without relation was declared related to accuracy in at most 0.5%. The check covers a smaller design than the data. It also showed that the calibration slopes of the four megastudies would lie between 0.96 and 1.05 if one slope held everywhere, which matches the effect of differences in overall accuracy in the simulation study.

### What the example shows

The procedure recovered three known facts about word frequency: it orders words by difficulty in every megastudy and language, its effect size varies between word lists, and length and neighbourhood distance add to it only in combination. It expressed them in a form that a correlation within one megastudy does not provide, namely how far a relation estimated elsewhere can be relied on for a new list. The example also shows a limit of one diagnostic at this scale. No training relation was flagged as weak, although the calibration slopes of length and neighbourhood distance were unstable (between −1.02 and 2.69; supplementary material). With more than 60,000 training words, the interval of even a negligible slope excludes 0.
