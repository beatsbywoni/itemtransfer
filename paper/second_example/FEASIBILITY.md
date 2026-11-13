# Second worked example: feasibility search

Compiled 2026-11-13. No manuscript text was written. Every number below was computed in this session from
downloaded files (scripts and raw output in `_probe_scripts/`), or is quoted from a README that was read.
Statements that could not be verified are marked **unverified**.

## Recommendation in one paragraph

**Use visual lexical decision megastudies: word accuracy in four megastudies (English Lexicon Project, British
Lexicon Project, Dutch Lexicon Project, MEGALEX) with word frequency, word length and orthographic neighbourhood
distance as the competing measures.** It meets every requirement, all four trial-level files were downloaded and
read in this container (about 280 MB compressed, 5.4 million word trials), three of the four source papers are in
*Behavior Research Methods*, and a quick probe already shows the pattern the procedure is designed to expose:
frequency orders words similarly in every family, but its slope on the logit scale differs between families
(about 0.70 in three, 1.06 in the British project), length is a near-null measure, and length and neighbourhood
distance are collinear by design. The only real caveats are about provenance (take the files from the original
repositories, not from the GitHub mirror used here) and about wording (frequency is a property of the item that
needs an external corpus, so "computed from the item alone" must be phrased carefully). Matrix reasoning
(MaRs-IB) is the fallback, but it is one item bank and does not give three independent families.

## What was searched and how

- GitHub repository and code search (`gh api search/...`), then blob-less clones to list files, then `curl` from
  `raw.githubusercontent.com` and `media.githubusercontent.com` (Git LFS) for the files themselves.
- OSF, Zenodo, figshare, crr.ugent.be and PubMed Central could not be reached from this container (proxy 403,
  robots block, or a JavaScript shell with no content). Anything said about those hosts comes from READMEs or
  workflow files in GitHub repositories that point to them, and is marked as such.
- Downloaded data were treated as untrusted: each source in its own new directory, nothing executed from them,
  all reading done with `python3 -I` from scripts kept elsewhere.

## Ranked shortlist

### 1. Lexical decision megastudies across lexicon projects (recommended)

**Item** = one word (nonwords are dropped: they have no frequency). **Outcome** = correct "word" response (0/1).

| Family | Language, design as seen in the data | Participants | Words | Word trials | Responses per word (median, min) | Mean accuracy | Split-half reliability of word difficulty (logit, Spearman-Brown, one random split) |
|---|---|---|---|---|---|---|---|
| English Lexicon Project (ELP) | US English, word length 1 to 21, six universities, each participant saw a subset | 814 | 40,481 | 1,372,240 | 34, 30 | 0.839 | 0.864 |
| British Lexicon Project (BLP) | British English, length 2 to 13, each participant saw about half | 78 | 28,728 | 1,120,470 | 39, 38 | 0.757 | 0.939 |
| Dutch Lexicon Project (DLP) | Dutch, length 2 to 12, every participant saw every word (repeated block 50 excluded) | 39 | 14,089 | 549,471 | 39, 39 | 0.841 | 0.916 |
| MEGALEX, visual part | French, length 2 to 9, each participant saw half (repetitions excluded) | 96 | 28,466 | 1,311,740 | 46, 37 | 0.889 | 0.886 |

All words in all four families have at least 20 responses. The share of words below 95% accuracy is 0.65, 0.65,
0.59 and 0.43, so the outcome is not at ceiling; the share below 50% is 0.08, 0.19, 0.10 and 0.05.

**Where the files are.**

| Family | Verified copy used here (GitHub) | Size | Original source named in the README (not reachable from here) |
|---|---|---|---|
| ELP | `https://raw.githubusercontent.com/dmbates/EnglishLexicon.jl/main/arrow/ldt_trial.arrow` (+ `ldt_item.arrow`, `ldt_subj.arrow`, `Items.csv.gz`); commit a9acbeb | 12.6 MB + 1.4 MB + 3.8 MB | `https://osf.io/n63s2/`, trial-level zip `https://osf.io/eu5ca/`; item characteristics from elexicon.wustl.edu |
| BLP | `https://raw.githubusercontent.com/Data-X01/PsychLing-101/main/keuleers2011_britishlexiconproject/original_data/blp-trials.txt.zip` | 67.1 MB (195.7 MB unzipped, tab separated) | `https://osf.io/b5sdk/` (file `84efq`); also `http://crr.ugent.be/blp/txt/blp-trials.txt.zip`, `blp-stimuli.txt.zip`, `blp-items.txt.zip` |
| DLP | same repository, `keuleers2010_DLP1/original_data/dlp-trials.txt.zip`, `dlp-stimuli.txt`, `dlp-items.txt` | 40.1 MB (112.1 MB unzipped) + 3.9 MB + 5.6 MB | `https://osf.io/uw7t6/`; also `http://crr.ugent.be/dlp/txt/dlp-trials.txt.zip` |
| MEGALEX | `https://media.githubusercontent.com/media/Data-X01/PsychLing-101/main/ferrand2018_megalex/processed_data/exp1.csv` (Git LFS; standardised copy of the visual trials) | 155.5 MB | `https://osf.io/7z6th/`, folder "MEGALEX Word data trial-by-trial Visual + Auditory", archive `By trials Auditory & Visual-MEGALEX.zip` |

PsychLing-101 commit 3520318 (2026-10-15). Local copies: `elp_bates/`, `blp/`, `dlp1/`, `megalex/`.

**Column structure (as read).**
- ELP `ldt_trial.arrow`: `subj, seq, acc (True/False/null), rt, item`; 2,745,952 rows including nonwords; 1,370
  null accuracies. `ldt_item.arrow`: `item, Ortho_N, BG_Sum, BG_Mean, BG_Freq_By_Pos, itemno, isword, wrdlen,
  pairno` (80,962 rows). `Items.csv.gz`: 40,481 words by 57 columns including `Length, Freq_KF, Freq_HAL,
  Log_Freq_HAL, SUBTLWF, LgSUBTLWF, SUBTLCD, Ortho_N, OLD, PLD, NSyll, NMorph, I_Mean_Accuracy`. The arrow files
  use dictionary columns with a null category: cast them to plain strings before converting to pandas (see
  `_probe_scripts/elp.py`). `pyarrow` is needed and is not in the base environment.
- BLP `blp-trials.txt`: 2,240,940 rows by 21 columns: `participant, lexicality (W/N), block, environment, order,
  trial, spelling, button, response, accuracy, previous.accuracy, rt, previous.rt, ..., rt.raw`.
- DLP `dlp-trials.txt`: 1,098,942 rows by 21 columns, same layout as BLP plus `zscore`. `dlp-stimuli.txt`: 28,173
  rows by 29 columns including `coltheart.N, OLD20, celex.frequency, subtlex.frequency, subtlex.log10.frequency,
  subtlex.cd, nchar, nsyl`.
- MEGALEX `exp1.csv`: 2,596,095 rows: `participant_id, trial_id, trial_order, phase_id, trial_in_block,
  stimulus_type (word/pseudoword), stimulus, response, accuracy, rt, repetition`.

**Measures (three or four, competing).**
1. Word frequency on the Zipf scale. One implementation for all four languages: the `wordfreq` Python package
   (version 3.1.1 installed from PyPI, Apache-2.0 for the code; its README says the bundled data files carry their
   own terms, **check before redistribution**). Coverage: 96.3% to 97.7% of words have a non-zero value.
2. Word length in letters (computed from the item).
3. Orthographic Levenshtein distance to the 20 nearest words (OLD20), computed from the item and a reference
   lexicon. Published values exist for ELP (`OLD`, 97.3% coverage) and DLP (`OLD20`, 100%), which gives the
   "recompute and compare with published values" step something real to check.
4. Optional fourth: a second frequency norm (ELP ships HAL, Kučera-Francis and SUBTLEX; DLP ships CELEX and
   SUBTLEX-NL). In ELP, `wordfreq` Zipf correlates 0.94 with log HAL and 0.84 with log SUBTLEX (Spearman); in
   DLP 0.87 with log SUBTLEX-NL. This supports step 1, but a per-language norm is not a single implementation
   across families, so keep it as a comparison, not as a transferred measure.

**Probe results (item level, not paper numbers; `_probe_scripts/lex2_output.txt`).**

| Family | Spearman accuracy ~ Zipf | Spearman accuracy ~ length | Spearman Zipf ~ length | Binomial slope on Zipf | Binomial slope on length |
|---|---|---|---|---|---|
| ELP | 0.574 | -0.021 | -0.335 | 0.711 | 0.009 |
| BLP | 0.694 | 0.028 | -0.306 | 1.058 | 0.057 |
| DLP | 0.536 | 0.105 | -0.324 | 0.698 | 0.123 |
| MEGALEX | 0.525 | 0.070 | -0.237 | 0.719 | 0.092 |

Other facts that map onto the five steps of the procedure:
- *Samples that share items*: ELP and BLP share 18,977 words (ELP only 21,504; BLP only 9,751; case-insensitive
  match). Agreement of word difficulty on the shared words is r = 0.733 on the logit scale (Spearman 0.685,
  n = 18,553 exact-case matches), below both split-half values, so there is a genuine between-sample ceiling to
  report. To keep families disjoint, assign shared words to one family for the transfer test and use the other
  project's responses to those words only for the agreement step.
- *Collinearity by design*: length and OLD correlate 0.87 in ELP (all lengths) and 0.63 in DLP (short words only).
- *Range overlap*: word length runs to 21 in ELP but stops at 9 in MEGALEX and 12 to 13 in BLP and DLP.
- *Weak training relation*: length is close to a null predictor of accuracy in every family.
- *Ordering versus scale*: the frequency slope in BLP is about 1.5 times that in the other three families, with
  similar or better ordering. A calibration slope clearly different from 1 with good rank agreement is therefore
  likely when BLP is held out or dominates training. Possible reasons (lower mean accuracy in BLP, British words
  scored against a general English frequency list, design) are for the analysis to sort out, not established here.

**Transfer question it answers.** A relation between word frequency (or length, or neighbourhood distance) and
word-recognition accuracy fitted on some megastudies: does it predict, with correct order, correct size and
useful probabilistic accuracy, in a megastudy built for another language or another word selection? BRM itself
names this as open: the exploration file records that Martínez et al. (2025) leave cross-megastudy generalisation
as future work and that Boeve and Bogaerts (2025) find predictor rankings to be corpus dependent.

**Expected effort.** Low to moderate. Loading and aggregating all four files took under two minutes here. Work
items: a loader per family (four small functions), OLD20 for about 110,000 words against a reference lexicon
(needs a vectorised or compiled Levenshtein, or a random subset of 2,000 to 3,000 words per family, which is
enough and keeps the example compact), the shared-word assignment rule, and the usual run of the package. One
to two days including checks. To keep the example small, a fixed-seed sample of words per family is defensible
and should be stated.

**Risks.**
1. *Provenance and licence.* No licence statement was seen for any of the four original deposits (OSF pages were
   unreachable): **licence unverified**. The copies used here sit in PsychLing-101, whose compilation is
   CC BY-NC-SA 4.0 and whose README asks contributors not to publish analyses "based on PsychLing-101 data" before
   the project paper appears. For the paper, download from the original repositories (URLs above) through the
   user's computer, cite the original articles, and do not redistribute the files; the public code should fetch
   them. The MEGALEX file used here is the mirror's standardised version, so the loader must be rewritten for the
   original archive. The ELP arrow files are a cleaned third-party version (the repository's `Notes.md` lists
   skipped and patched participant files; the repository has no licence file).
2. *"Computed from the item alone."* Frequency needs a corpus. It is response-independent and fixed before the
   data are seen, which is what matters, but the vocabulary sentence in DESIGN.md should allow "computed from the
   item and a fixed external resource".
3. *Familiar territory.* That frequency predicts lexical decision is known to every BRM reader. This is an
   advantage for a second example (readers can judge the procedure against what they already know), but the
   example must lead with what the procedure adds: scale does not transfer although order does.
4. *Cross-language frequency lists* differ in source and quality; part of any slope difference is measurement of
   the measure. Report it as such, and show the within-English contrast (ELP against BLP) beside the cross-language
   ones.
5. *Few participants in DLP (39) and BLP (78)*: participant bootstrap intervals will be wide for those samples,
   though item difficulty is still highly reliable.
6. *Accuracy is the secondary outcome in this literature* (response time is primary). Say so; word accuracy is
   nevertheless what word-difficulty and prevalence work in BRM uses.

**BRM references (DOIs as seen in tool results this session).**
- Balota et al. (2007), The English Lexicon Project, *BRM 39*(3), 445-459, https://doi.org/10.3758/BF03193014
- Keuleers, Lacey, Rastle and Brysbaert (2012), The British Lexicon Project, *BRM 44*(1), 287-304,
  https://doi.org/10.3758/s13428-011-0118-4
- Ferrand et al. (2018), MEGALEX, *BRM 50*(3), 1285-1307, https://doi.org/10.3758/s13428-017-0943-1
- Not BRM: Keuleers, Diependaele and Brysbaert (2010), *Frontiers in Psychology 1*, 174,
  https://doi.org/10.3389/fpsyg.2010.00174 (Dutch Lexicon Project)
- Already in the exploration file: Miller (2024, four megastudies as a case study), Martínez et al. (2025),
  Boeve and Bogaerts (2025), Compton et al. (2026, word difficulty estimates), Brysbaert et al. (2025).
- Possible extra families, same mirror, not downloaded: SPALEX (Spanish, crowdsourced; original
  `https://figshare.com/projects/SPALEX/29722`, doi 10.3389/fpsyg.2018.02156; mirror file `merged.csv.gz` about
  285 MB), Simplified Chinese Lexicon Project (Wang et al., 2025, *BRM 57*, 206,
  https://doi.org/10.3758/s13428-025-02701-7; 29 participants, characters, so length and OLD20 do not apply),
  Catalan prevalence megastudy (Guasch et al., 2023, *BRM 55*, 3198-3217,
  https://doi.org/10.3758/s13428-022-01959-5; 24.6 million rows, too large for a compact example), English
  Crowdsourcing Project (`https://osf.io/v25ek/`, Mandera et al., 2020, https://doi.org/10.3758/s13428-019-01272-8).
  Four families are enough; SPALEX would add a crowdsourced design if a fifth is wanted.

### 2. Matrix reasoning: MaRs-IB (fallback; one item bank)

- **Source.** `https://github.com/ndawlab/mars-irt`, MIT licence, repository about 451 MB because of raw JSON and
  figures; the CSV files needed are about 5 MB (51 MB with model summaries). Commit 04eecda. Released with
  Zorowitz et al. (2024), *BRM 56*(3), 1104-1122, https://doi.org/10.3758/s13428-023-02067-8. Stimuli at
  `https://osf.io/g96f4/` (not checked). Local sparse copy: `mars-irt/repo/`.
- **Structure.** Calibration study `03_Calibration/data/data.csv`: 1,584 participants, 25,344 trials (477 with
  missing accuracy), columns `subject, trial, item_set, item_id, item, dimension, test_form, shape_set, distractor,
  choice, accuracy, rt, ...`; 64 item templates, each in 3 shape sets and 2 distractor types, giving 384 item
  versions with a median of 66 responses (49 to 88) per version and 395 per template; mean accuracy 0.596.
  Further samples: two collaborator datasets (100 participants, 80 templates; 102 participants, 40 templates), two
  pilots (180 and 342 participants; 16 and 12 templates), validation long and short forms (352 and 341
  participants; 28 and 12 templates), and summary statistics only for the original 659-participant study.
- **Measures.** `dimension` (dimensionality score, 2 to 8), `n_rules` (1 to 6), `n_features` or number of elements
  (1 to 4), distractor type. Template level: dimensionality and number of rules correlate 0.92; number of elements
  correlates 0.32 and 0.18 with them; accuracy correlates -0.60, -0.58 and -0.52 with the three.
- **Families.** This is the problem. Every sample uses the same templates. Shape sets are clones of one template
  and distractor types are two versions of it, so neither is a family that "shares no items" in substance. The
  nine Raven-type items in the validation study have no computed features. Splitting the 64 templates by layout
  type would be an invented family structure with about 20 items each.
- **What it could still do.** A clone-transfer illustration (fit on two shape sets, test on the third; or fit on
  one distractor type, test on the other), which speaks to Zorowitz et al.'s point that clones are not
  interchangeable, plus a good reliability-ceiling illustration across seven samples that share items.
- **A real multi-family version would need other banks.** Open Matrices Item Bank (Koch et al., 2022, *Journal
  of Intelligence*; 220 items built from six rules with 1 to 5 rules per item, N about 2,561, item properties
  tabulated, repository `https://osf.io/4km79/`): the article's data statement names no repository and the OSF
  page could not be opened, so **availability of item-level responses is unverified**. No third bank with public
  trial data and rule annotations was found.
- **Effort.** One day for the clone-transfer version. **Risk**: reviewers will say the "families" are not
  families; two of three measures are nearly the same variable.

### 3. H-ARC (human performance on the Abstraction and Reasoning Corpus)

- **Source.** Code `https://github.com/Le-Gris/h-arc`; data on OSF `https://osf.io/bh8yq` (not reachable here;
  licence and size unverified). LeGris et al. (2025), *Scientific Data 12*, 1380,
  https://doi.org/10.1038/s41597-025-05687-1. The repository holds only task lists and analysis code.
- **Structure (from `data/readme.md`).** Action-level rows with `task_type` (training or evaluation set),
  `hashed_id`, `task_name`, `attempt_number`, `solved`, grid sizes.
- **Families.** Two (training set and evaluation set; task counts not checked here); a third would have to come
  from another dataset.
- **Measures.** Computable from task files (grid size, number of colours, number of changed cells), but none is
  an established difficulty measure.
- **Why it ranks low.** Two families; responses per task could not be checked and are expected to be low
  (**unverified**); not a BRM domain; measures would be ad hoc.

### 4. Considered and set aside

- **Item Response Warehouse** (Domingue et al., 2025, BRM; `https://github.com/datapages/irw`, MIT, website and
  metadata): many public item-response tables, but items come without content from which a difficulty measure
  could be computed. Useful as a citation, not as an example.
- **Syllogisms, Tower of London, Rush Hour, arithmetic, Sudoku**: GitHub searches returned no dataset with three
  disjoint item families, trial-level accuracy and computable measures. One Rush Hour replication repository
  (`fangzefunny/rush_hour`, no licence) covers a single puzzle set. Not pursued further.
- **Four-in-a-row and Lichess**: excluded as instructed.

## Recommendation

1. **Adopt the lexical decision example** with four families and three measures (Zipf frequency, length, OLD20),
   on a fixed-seed sample of words per family if compactness matters. It is a second domain that is central to
   BRM, with source papers in BRM, large reliable item-level outcomes, shared items between two samples, and a
   visible disagreement between ordering and scale.
2. **Before any paper number is produced**: fetch the four datasets from their original repositories through the
   user's computer (OSF `n63s2`/`eu5ca`, `b5sdk`, `uw7t6`, `7z6th`, or the crr.ugent.be zip files), record
   licence statements, and confirm that the BLP and DLP zips match the copies used here (SHA-256 prefixes:
   BLP `60aca4cd6c11d34c`, DLP `6ef7a4f18a478a1a`). The files in this directory are for feasibility only.
3. **Do not** present MaRs-IB shape sets or distractor types as item families. If a third domain is wanted
   later, MaRs-IB works only as a clearly labelled clone-transfer side note.

## Files in this directory

- `elp_bates/`, `blp/`, `dlp1/`, `megalex/`: downloaded data (untrusted, read-only use).
- `mars-irt/repo/`: sparse checkout (CSV, TSV, README, licence, LaTeX sources only).
- `_probe_scripts/`: the scripts used here and their raw output (`lex2_output.txt`, `mars_output.txt`). They
  expect `pyarrow` and `wordfreq` on a path given as an argument; both were installed to a scratch directory
  with `pip --target`, not into the system environment. Versions: numpy 2.5.3, pandas 3.0.5, scipy 1.18.1,
  wordfreq 3.1.1.
