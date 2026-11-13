# Second worked example: data provenance (original authors' releases)

Compiled 2026-11-13. Every file listed under "Obtained" was downloaded on 2026-11-13 from the original authors'
OSF projects, and its SHA-256 equals the hash that the OSF API reports for that file, the hash of the copy on the
Mac, and the hash of the copy in this container (three-way match for the 20 data and licence files; `sha256sum -c MANIFEST.sha256` passes for all 21 entries in the container, the 21st being the saved OSF API listing). Statements that could not be
verified are marked **not verified**. Nothing here comes from the PsychLing-101 mirror.

## How the files were obtained (and what did not work)

- The cloud container and the Mac shell (`device_bash`) both sit behind a proxy allowlist that refuses
  `osf.io`, `api.osf.io`, `files.osf.io`, `crr.ugent.be`, `elexicon.wustl.edu`, `zenodo.org` and `lexique.org`
  (HTTP 403 from the proxy). WebFetch is refused by `api.osf.io` (robots). The proxy was not bypassed.
- Route used: the user's Chrome (Claude in Chrome), one new tab, no existing tab touched, no login, no
  credentials, no form submitted. File lists, hashes, licences and wiki texts were read from the public OSF API
  (`https://api.osf.io/v2/nodes/<id>/...`). Files were downloaded from the OSF file server with the URL pattern
  `https://files.osf.io/v1/resources/<node>/providers/osfstorage/<file id>?direct`
  (`files.de-1.osf.io` for projects stored in Germany). The plain `https://osf.io/download/<guid>/` links redirect
  to an object-storage host that did not resolve on the user's network; `?direct` makes OSF stream the file itself.
- Chrome saved the files to `~/Downloads`; they were copied (not moved) into
  `03_knapsack-ipd-meta/data_raw_lex/` and then staged into this container. **The originals are still in
  `~/Downloads`** (deleting is disabled); the user can remove them: `ldt_raw.zip`, `ELP_Trial_Level_Data_Key.txt`,
  `ldt.patch`, `data.zip`, `blp-*.txt.zip` (3), `dlp-*.txt.zip` (4), `license.txt`,
  `By trials Auditory & Visual-MEGALEX.zip`, `vw.ParItems.DVandIV.txt`, `vp.essais_ElTec&Seuils.txt`, three
  `SUBTLEX-*.xlsx`, `lexdl_osf_listing_1.json`.
- Nothing else in the repository was touched; no git command was run; nothing was deleted.

Locations:
- Author's computer: a folder `data_raw_lex/` outside this repository, with `MANIFEST.md` and `MANIFEST.sha256`.
- Analysis machine: `paper/second_example/original/` (same tree, plus `MANIFEST.sha256`).

## Obtained: files, sizes, hashes

OSF file version is 1 unless stated. "Modified" is the OSF `date_modified` of the file.

### English Lexicon Project (ELP), folder `elp/`
Repository: https://osf.io/n63s2/ "English Lexicon Project (trial-level data)", created 2019-02-12, last modified
2024-10-24, contributors David Balota, Melvin Yap, Douglas Bates. No DOI is registered for the project.

| File | Bytes | SHA-256 | OSF guid, modified |
|---|---|---|---|
| `ldt_raw.zip` (820 raw `.LDT` files, lexical decision, words and nonwords) | 36,537,458 | f57f793896d38ccec369f25157685c9879c14c81bed513b7e0a510552614b210 | eu5ca, version 2, 2021-11-20 |
| `ELP_Trial_Level_Data_Key.txt` (format key) | 1,510 | 81343116f673e103f753e351658118b67de8d3f1b054132c4caaf2443c4163c4 | rd632, 2019-02-12 |
| `ldt.patch` (diff between the 2019 and 2021 raw files) | 35,750 | 16bd0e7e29a1ef11afae9812e4a68976510dbb870782717d25827814239afff3 | u2mkb, 2021-11-20 |
| `dataark/data.zip` (older copy in the Data Ark project https://osf.io/879jw/, 2018-02-15; kept for reference only, not used by the loader) | 55,157,211 | c8ed1456e966ea99b024a5f12ab80213248fbde44a56a9ee5e20413664167fe3 | 8xs6h |

Not downloaded from the same project: `nmg_raw.zip` (naming task) and `nmg.patch`.

Licence: **none stated.** The OSF project has no licence field and no licence file. The Data Ark copy says only
that the data were shared with the authors' permission. The project website elexicon.wustl.edu could not be read
in the browser (site permission refused); WebFetch reported that its front page restricts generated word lists to
non-commercial research and forbids use for speech technology, and shows a Washington University copyright
notice (second-hand report from the fetch tool, **not verified** by direct reading).
Redistribution of derived item-level tables: **not explicitly allowed anywhere.** Treat as not permitted without
asking; publish code that fetches the raw file and rebuilds the tables.

Citation: Balota, D. A., Yap, M. J., Cortese, M. J., Hutchison, K. A., Kessler, B., Loftis, B., Neely, J. H.,
Nelson, D. L., Simpson, G. B., & Treiman, R. (2007). The English Lexicon Project. *Behavior Research Methods,
39*(3), 445-459. https://doi.org/10.3758/BF03193014

#### Addition of 2026-11-13: item-level file from the project website (obtained by the user)

The user ran the website query for the complete ELP lexicon on 2026-11-13
(https://elexicon.wustl.edu/query13/query13.html); the result was delivered by e-mail and placed in `elp/`.

| File | Bytes | SHA-256 |
|---|---|---|
| `elexicon_items.csv` (79,672 rows: 40,481 words and the nonwords; columns Word, Length, Freq_HAL, Log_Freq_HAL, SUBTLWF, LgSUBTLWF, Ortho_N, OLD, OLDF, NSyll, NMorph, I_Mean_RT, I_SD, Obs, I_Mean_Accuracy; numbers are quoted strings with thousands separators, "#" marks a missing value) | 7,235,335 | 6d9825d242a740c8373e273393020d964103231550b28804cac27fe448135020 |
| `elexicon_neighborhood.csv` (126,152 word and orthographic neighbour pairs; not used by any script) | 2,148,580 | 4489e61182f91fae61bb45c5b2bc84b998abc6a590a0cd33c46dfa64a7f321b0 |

Both hashes were recomputed in the container on 2026-11-13 and equal the values supplied with the files. The two
files are not listed in `MANIFEST.sha256` (that file is read-only and predates them). They are treated as
untrusted data (read with `python3 -I`, as text, nothing executed).
Terms: the website restricts generated word lists to non-commercial research. Neither file, nor any table derived
row by row from them, may be redistributed.
Use: `step1_elp_published.py` reads `elexicon_items.csv` for the recompute-and-compare step only (length, OLD,
two frequency norms, item accuracy). All 40,481 ELP words of the raw trial files are found in it by exact string.
No measure of the transfer analysis depends on it. This replaces item 1 under "Not obtained" below and the
statement that the mirror `elp_bates/Items.csv.gz` is the only copy of these values; the mirror is not used.

### British Lexicon Project (BLP), folder `blp/`
Repository: https://osf.io/b5sdk/ "British Lexicon Project", created 2024-02-18, modified 2024-05-07, contributor
Marc Brysbaert. No DOI registered. The paper's own address (crr.ugent.be/blp) was not reachable from any route.

| File | Bytes | SHA-256 | OSF guid, modified |
|---|---|---|---|
| `blp-trials.txt.zip` (trial level, words and nonwords; 195,665,024 bytes unzipped) | 67,116,996 | 60aca4cd6c11d34c7e0623836a04b200286bfaae767a66cac8bd23cab04c5d9a | 84efq, 2024-02-18 |
| `blp-items.txt.zip` (item means) | 2,157,390 | adab4e0c1daf7bc830c7cb2ece538c941c2e5ce39837c8fdd198bb65b0c10c00 | 6tdnz |
| `blp-stimuli.txt.zip` (stimulus characteristics: Coltheart N, OLD20, letters, CELEX, BNC and SUBTLEX frequency) | 1,588,745 | d553532bbe82b89eed3216dac184ab33e179770510ddfae82bac442c0aea1d52 | tge67 |
| `license.txt` | 471 | 1c96df5fcc840ebf7e2147ea7f13820fcda223ef78eb55cb505972dfed43248b | 5jmgt, 2024-05-07 |

Not downloaded: `.Rdata` and `.xls` versions of the same tables, `blp-pseudoword-syllables.txt.zip`, the article
PDF, `BLP summary data words.xls`.

Licence: OSF licence field "Other", pointing to `license.txt`, which names "CC BY-NC-SA 4.0" (Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International). Paraphrase: reuse, redistribution and adaptation are
allowed with credit, for non-commercial purposes, and adapted material must carry the same licence.
Redistribution of derived item-level tables: **allowed**, with attribution, non-commercially, under CC BY-NC-SA 4.0
(so such tables cannot be placed under the package's MIT licence; give them their own licence note).

Citation: Keuleers, E., Lacey, P., Rastle, K., & Brysbaert, M. (2012). The British Lexicon Project: Lexical
decision data for 28,730 monosyllabic and disyllabic English words. *Behavior Research Methods, 44*(1), 287-304.
https://doi.org/10.3758/s13428-011-0118-4

The mirror copy used in the feasibility probe was byte-identical (same SHA-256 prefix `60aca4cd6c11d34c`).

### Dutch Lexicon Project (DLP), folder `dlp/`
Repository: https://osf.io/uw7t6/ "Dutch Lexicon Project 1", created 2024-02-16, modified 2024-05-07, contributor
Marc Brysbaert; the project wiki says it exists because the link in the article no longer works. No DOI registered.

| File | Bytes | SHA-256 | OSF guid, modified |
|---|---|---|---|
| `dlp-trials.txt.zip` (trial level, words and nonwords, without block 50; 112,106,643 bytes unzipped) | 40,086,781 | 6ef7a4f18a478a1a60b0b6d0d1de8723dbabb83ba282a23caef8af457f7b1b6b | zjdbn, 2024-02-16 |
| `dlp-trials-block-50.txt.zip` (the repeated block; not used by the loader) | 713,630 | 3fcf6611debebd288f8be20243cb59247430d6a8e5efe404778ac73ac5c200ae | 5qa4s |
| `dlp-items.txt.zip` (item means) | 1,634,437 | c187a423bf585f69d614b4b06343c6deaa5027ad9e7bcd1ab11a0c053878ed52 | ujvk6 |
| `dlp-stimuli.txt.zip` (Coltheart N, OLD20, CELEX and SUBTLEX-NL frequency, nchar, nsyl) | 1,069,395 | b81a926b3353a48a3ba023a88b339befd221d3104c82bd34025491b2df8a97db | jt2ue |
| `license.txt` (identical to the BLP file) | 471 | 1c96df5fcc840ebf7e2147ea7f13820fcda223ef78eb55cb505972dfed43248b | etx4r, 2024-05-07 |

Licence and redistribution: same as BLP (CC BY-NC-SA 4.0 through `license.txt`).
The mirror copy used in the feasibility probe was byte-identical (prefix `6ef7a4f18a478a1a`).
Dutch Lexicon Project 2 (https://osf.io/jfkvw/, same licence file, trial files of 81 MB and 83 MB) exists and was
not downloaded; it is a different study and is not one of the four families.

Citation: Keuleers, E., Diependaele, K., & Brysbaert, M. (2010). Practice effects in large-scale visual word
recognition studies: A lexical decision study on 14,000 Dutch mono- and disyllabic words and nonwords. *Frontiers
in Psychology, 1*, 174. https://doi.org/10.3389/fpsyg.2010.00174

### MEGALEX (visual lexical decision), folder `megalex/`
Repository: https://osf.io/7z6th/ "MEGALEX", created 2018-10-19, last modified 2026-03-26, contributor Ludovic
Ferrand. No DOI registered.

| File | Bytes | SHA-256 | OSF guid, modified |
|---|---|---|---|
| `By trials Auditory & Visual-MEGALEX.zip` (word and pseudoword trials; members `Visual.WpuispW.essais_ElTec.txt` 138,110,510 bytes, `Auditory.WpuispW.essais_ElTec.txt`, and a short note on variable labels) | 68,427,326 | d1aa18efb1491aa62e62cab942f78d7965221689ad188f4a49e035bce398f6ba | uq2yb, 2026-03-26 |
| `vw.ParItems.DVandIV.txt` (item level, visual words: RT, accuracy, letters, OLD20, three frequency columns) | 3,095,603 | 852d45d38e6a70bb1970b19137c1b5b503eb1a4ab3c21329acadfe25a0354d4b | fndvw, 2018-10-19 |
| `vp.essais_ElTec&Seuils.txt` (visual pseudoword trials after the authors' cleaning; not used by the loader) | 56,007,501 | 49a551de85de1adf0be051b6bdd81f308a72a14a3422c1fd0e6931f3ca8dbecc | uk9sn, 2026-03-26 |

Note the date: the trial-by-trial archive was added to the project in March 2026 (members dated February and
March 2026). It is the authors' own release, but it is recent; cite the access date.
Not downloaded: auditory item and pseudoword files, the 691 MB archive of auditory pseudoword recordings. The
folder "BRM article" is empty.

Licence: **none stated** (no licence field, no licence file). The project description says only that the data
are "freely available". Redistribution of derived item-level tables: **not explicitly allowed**; treat as not
permitted without asking the authors; publish code that fetches the files.

Citation: Ferrand, L., Méot, A., Spinelli, E., New, B., Pallier, C., Bonin, P., Dufau, S., Mathôt, S., & Grainger,
J. (2018). MEGALEX: A megastudy of visual and auditory word recognition. *Behavior Research Methods, 50*(3),
1285-1307. https://doi.org/10.3758/s13428-017-0943-1

### Frequency norms recommended by the megastudy authors, folder `frequency/`
All three are Marc Brysbaert's OSF projects with the same `license.txt` (CC BY-NC-SA 4.0), each under 50 MB.
They are downloaded but not yet read by any script.

| File | Bytes | SHA-256 | Repository |
|---|---|---|---|
| `SUBTLEX-US frequency list with PoS and Zipf information.xlsx` | 10,760,844 | 3a8cb93a4e28988c2ce722a63f6b8d394acdc42ebe2ab6e1f0e484ee0d4167a7 | https://osf.io/djpqz/ (guid 7wx25, file dated 2015-08-19) |
| `SUBTLEX-UK.xlsx` | 24,956,289 | 838b534a2fc162b8875e8c0bb1ae272073004148cd29aa90f65c454da748be17 | https://osf.io/zq49t/ (guid d3jbg, 2015-08-19) |
| `SUBTLEX-NL with pos and Zipf cd minimally 2.xlsx` | 12,941,041 | 74a67cf88cf8f4245701e679b13e28ccdc45b836a131e72f34e377a8200129bc | https://osf.io/3d8cx/ (guid e8y5b, 2020-08-25) |
| `license_subtlex_osf.txt` | 471 | 1c96df5fcc840ebf7e2147ea7f13820fcda223ef78eb55cb505972dfed43248b | same file in all three projects |

References named on those OSF pages: Brysbaert and New (2009) for SUBTLEX-US; van Heuven, Mandera, Keuleers and
Brysbaert (2014), *Quarterly Journal of Experimental Psychology, 67*, 1176-1190, for SUBTLEX-UK and the Zipf
scale; Keuleers, Brysbaert and New (2010), *Behavior Research Methods, 42*, 643-650, for SUBTLEX-NL. DOIs were
not seen in a tool result and are therefore not given here. The SUBTLEX-NL page gives the Zipf formula
log10((frequency + 1) / 44.106) + 3. The SUBTLEX-US page warns that the entries "don" and "haven" are unreliable.
The full SUBTLEX-NL list (37.7 MB, guid 2dcvs) was not downloaded.

French: **not downloaded.** Lexique 4 is at https://osf.io/arjcz/ (no licence field; `Lexique4.xlsx` 36.4 MB,
`Lexique3.xlsx` 13.0 MB) and at lexique.org (`https://www.lexique.org/databases/Lexique410/Lexique4.1.zip`).
The lexique.org front page states a Creative Commons Attribution-ShareAlike 4.0 licence in its text, but the fetch
tool reported that the attached link points to a BY-NC licence. Because of this inconsistency and the missing
licence on OSF, the licence is **not verified** and the file was left alone. The MEGALEX item file already carries
the authors' own frequency columns (`fb`, `ff`, `ft`: per the MEGALEX article, book-based, subtitle-based and
their combination; the column meaning is inferred from the article, **not verified** against a codebook, since
the archive's variable note covers only the trial file).

What the megastudy authors themselves used: BLP ships BNC, CELEX and SUBTLEX-US counts and the DLP ships CELEX
and SUBTLEX-NL in their stimulus files; the DLP article reports using SUBTLEX because it correlated best with the
behavioural data; the MEGALEX article reports that the average of subtitle and book frequency worked best. The
ELP website offers HAL, Kučera-Francis and SUBTLEX-US. A per-language norm is therefore well justified as a
comparison, while a single implementation across families (wordfreq) remains the transferred measure.

### wordfreq (Python package)
- PyPI: https://pypi.org/project/wordfreq/ , version 3.1.1 (released 2023-11-21), licence metadata Apache-2.0.
  Source: https://github.com/rspeer/wordfreq . The README carries a sunset notice: the data are a snapshot up to
  about 2021 and will not be updated.
- Code: Apache licence. Bundled data: the README says the data files may be redistributed under
  "a Creative Commons Attribution-ShareAlike 4.0 license" (CC BY-SA 4.0).
- Attribution the README asks for: Google Books Ngrams (acknowledge the source), Leeds Internet Corpus, Wikipedia
  and ParaCrawl (Creative Commons, credit them), OPUS OpenSubtitles 2018 (attribution to OpenSubtitles), SUBTLEX
  lists for US, UK, Chinese, German and Dutch (used with Marc Brysbaert's permission; credit the SUBTLEX authors
  and keep it clear that SUBTLEX is free data), and Twitter-derived counts (collected under Twitter's developer
  terms; no content republished).
- Consequence: Zipf values computed with wordfreq may be shared in derived tables under CC BY-SA 4.0 with those
  credits. Note that for English and Dutch wordfreq already contains SUBTLEX, so "wordfreq versus SUBTLEX" is not
  a comparison of independent sources.
- The README's licence section was read through WebFetch summaries (PyPI page and GitHub page agree); the exact
  wording should be re-read once before it is quoted in the paper.

## Not obtained, and why

1. **ELP item-level file from elexicon.wustl.edu** (the authors' own Length, Ortho_N, OLD, frequency and
   I_Mean_Accuracy values). Chrome refused to read that site ("Permission denied for reading page content on this
   domain"), and the shell and WebFetch cannot reach its query pages. No login was attempted. **User action:**
   either allow the Claude in Chrome extension on `https://elexicon.wustl.edu/` and ask again, or open
   `https://elexicon.wustl.edu/` by hand, use the query that generates a list of all words with their lexical
   characteristics and behavioural lexical decision values, and save the CSV as
   `data_raw_lex/elp/elexicon_items.csv`. Whether that page asks for an e-mail address or a login is **not
   verified**. Until then the only copy of these values in the project is the third-party mirror
   `elp_bates/Items.csv.gz` (GitHub `dmbates/EnglishLexicon.jl`, no licence file; its author is a contributor of
   the OSF project). The loader takes it only through an explicit argument, and it must not be the source of a
   paper number.
2. **crr.ugent.be pages for BLP and DLP**: unreachable from every route that was allowed; the OSF projects by the
   same author hold the same files and state the licence, so nothing is missing.
3. **Lexique (French frequency)**: licence not verified, see above.
4. **DOIs of the SUBTLEX papers**: not seen in a tool result.
5. **OSF project DOIs**: none of the four projects has a registered identifier (the API returned empty lists), so
   the projects must be cited by URL and access date.

## Loader and counts

- `load_lexical.py`: `load_elp`, `load_blp`, `load_dlp`, `load_megalex`, `load_all`. Each returns
  `trials` (participant, item, family, sample, correct), `items` (item, family, length, published columns with
  the prefix `pub_`) and a log of counts. The complete list of exclusions is in the module docstring.
- `summarise_lexical.py` writes `summary_lexical.csv` and `summary_lexical.json` (run time 23 s; Python, numpy and
  pandas versions are recorded in the JSON). Run as
  `python3 -I summarise_lexical.py --elp-items elp_bates/Items.csv.gz` (the argument is optional and only adds the
  comparison with the mirror's published ELP values).

| Family | Participants | Words | Word trials | Responses per word (median, min, max) | Mean accuracy (trials) | Stated in the paper or project page | Feasibility probe |
|---|---|---|---|---|---|---|---|
| ELP | 814 | 40,481 | 1,372,240 | 34, 30, 37 | 0.8391 | 816 participants, 40,481 words | 814; 40,481; 1,372,240; 34, 30; 0.839 |
| BLP | 78 | 28,730 | 1,120,470 | 39, 38, 40 | 0.7569 | 78 participants, 28,730 words | 78; 28,728; 1,120,470; 39, 38; 0.757 |
| DLP | 39 | 14,089 | 549,471 | 39, 39, 39 | 0.8413 | 39 participants, 14,089 words, word accuracy 84% | identical |
| MEGALEX | 96 | 28,466 | 1,311,740 | 46, 37, 74 | 0.8895 | 96 participants, 28,466 words, 2,596,095 trials before cleaning | identical |

No participant saw the same word twice in any family after the exclusions (0 duplicate participant-item rows).

Exclusions, with counts:
- **ELP**: the zip holds 820 files. Six are dropped because the depositors list them in the OSF wiki as redundant
  or questionable (`9999.LDT`, `793DATA.LDT`, `Data999.LDT`, `Data1000.LDT`, `Data1010.LDT`, `Data1016.LDT`); each
  repeats the subject number of another file. This leaves 814 files and 2,745,952 trials; 1,372,990 nonword trials
  are dropped; of 1,372,962 word trials, 722 have an accuracy field that is neither 0 nor 1 (it holds a key code,
  most often 46) and are dropped.
- **BLP**: 2,240,940 trials, 1,120,470 nonword trials dropped, no word trial dropped (11 word trials with
  response code "O" are kept with the authors' accuracy score).
- **DLP**: 1,098,942 trials in the main file, 549,471 nonword trials dropped, no word trial dropped (624 time-outs,
  code "T", stay as errors, as the authors scored them). Block 50 (19,500 trials, of which 9,769 word trials; a
  repetition of block 1) is in a separate file and is not loaded.
- **MEGALEX**: 2,596,095 visual trials (the number the article gives after removal of 3,939 technical failures),
  1,284,263 pseudoword trials dropped, 92 word trials flagged as repetitions dropped.

Differences explained:
- **ELP, 814 against 816 participants.** The article and the OSF wiki say 816; the 2021 release holds 820 files, of
  which the depositors tell users to skip six. The raw files do not say which files made up the article's 816,
  so the two-participant gap cannot be resolved from the deposit. 814 is the number to report, with this reason.
- **BLP, 28,730 against the probe's 28,728 words.** The probe read the table with default missing-value handling
  and lost the words "null" and "nan". The loader keeps them; the count now equals the article's.
- **Accuracy against published item values.** BLP and DLP: recomputed word accuracy equals the published
  item-file value for every word (maximum absolute difference 0). MEGALEX: published values exist for 25,776 of
  28,466 words (the authors left out words below 67% accuracy); correlation with the recomputed values is 0.991,
  69% within 0.005, largest difference 0.088, because the published means were computed after the authors removed
  three participants below 80% accuracy, eight low-accuracy blocks and response-time outliers, none of which is
  removed here. ELP (mirror of the website table, comparison only): correlation 0.996, 65% within 0.005, largest
  difference 0.249; the website's screening rules were not available, so the cause is **not verified**.
- **Length against published values.** Equal for every word in ELP (mirror), BLP and MEGALEX. In the DLP the
  published `nchar` is missing for 146 words and differs for 61 of the remaining 13,943: all inspected cases are
  words with an accented letter (for example "café" has 4 letters and a published value of 6), so the published
  count treats an accented letter as three characters. This is a real finding for the "recompute and compare"
  step.
- **Published neighbourhood distance**: `pub_OLD20` is present for all 28,730 BLP words and all 14,089 DLP words,
  `pub_old20` for 25,776 MEGALEX words; for ELP only through the mirror (`OLD`).

Reading details that matter for anyone re-implementing the loader: read every table with default missing-value
detection switched off; the MEGALEX files are UTF-8, semicolon separated, and their data rows have one more
column (a row number) than the header; the ELP raw files are Latin-1 with two sessions per file and demographic
blocks between and after the trial lines.

## For the Open Practices Statement
- Two of the four sources (BLP, DLP) permit non-commercial redistribution with attribution under the same
  licence; two (ELP, MEGALEX) state no licence. The safe plan is unchanged: do not redistribute raw or derived
  word-level tables; publish the loader, the manifest with hashes and the download addresses.
- The public code cannot download from OSF behind this proxy, but it can anywhere else with the `?direct`
  addresses above or the ordinary `https://osf.io/download/<guid>/` links.
