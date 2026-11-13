# Article materials

Materials for the article "Do item difficulty measures generalise to new stimulus sets? Leave-one-family-out
validation, its pitfalls, and the itemtransfer package" (H. Jeong).

| Folder | Content |
|---|---|
| `sim/` | Simulation study: code (`simcore.py`, `sim00` to `sim08`, `run_all.sh`, `exact_breakeven.py`), raw results per data set (`results/raw/`), summaries and tables (`results/`), figures, and the dated report `SIMULATION_REPORT.md` |
| `glmm/` | Mixed models in R (`glmm_simulation.R`, `glmm_knapsack.R`), their logs and result tables |
| `second_example/` | Lexical decision example: analysis plan (`PLAN.md`), provenance and checksums of every source file (`PROVENANCE.md`, `original/MANIFEST.sha256`), scripts, result tables (`results/`) and report |
| `knapsack_report/` | Output of `itemtransfer.report` for the knapsack example, and the sensitivity analysis for the Franco family |
| `figures/` | Figures of the article and the scripts for Figures 1 and 6 |
| `manuscript/`, `supplement/`, `submission/` | Sources of the article and the supplementary material, and the build scripts |

Section 1.9 of the supplementary material (`supplement/supplement.md`) maps every table and figure of the article
to its result files and script. Section 1.4 lists versions, seeds and settings.

## Reproducing the results

Environment: Python 3.13 with the packages in `requirements.txt`; R 4.6.2 with lme4 2.1.0 for `glmm/`. Install the
package from the repository root with `pip install ".[plot,test]"`. Commands are given from the repository root.

1. Tests: `python -m pytest -q` (78 tests, under a minute; 3 are skipped without the complete knapsack data).
2. Tutorial with the synthetic data set: `docs/tutorial.md` (a few minutes).
3. Simulation study: `bash paper/sim/run_all.sh` (about six hours on two cores; resumes from saved chunks), then
   `python paper/sim/make_tables.py`, `python paper/sim/make_figures.py` and `python paper/sim/exact_breakeven.py`.
   Mixed models: `Rscript paper/glmm/glmm_simulation.R` (about 20 minutes).
4. Knapsack example: `data_proc/trials_harmonized.csv` in this repository lacks the rows of Lu et al. (2025),
   whose data carry no licence. Rebuild the complete table from the authors' repositories with
   `code/01_osf_download.py`, `code/02_unpack_raw.py`, `code/03_extract_datasets.py`, `code/08_solver_effort.py`,
   `code/09_instance_metrics.py` and `code/10_harmonize_trials.py` (see `data_proc/README.md`). Then
   `python examples/knapsack.py` (about two minutes), `python paper/figures/make_knapsack_figure.py` and
   `Rscript paper/glmm/glmm_knapsack.R data_proc/trials_harmonized.csv`. For the same reason
   `knapsack_report/predictions.csv` is given here without the rows of the Lu family; the run restores them.
5. Lexical decision example: obtain the files listed in `second_example/PROVENANCE.md` (sources, sizes and
   SHA-256 checksums; the item file of the English Lexicon Project is requested from the project website), place
   them under `second_example/original/`, check them with `sha256sum -c MANIFEST.sha256`, then run in
   `second_example/`: `cache_trials.py`, `prep_measures.py`, `step1_elp_published.py`, `run_lexical.py` with the
   stages `step2`, `step3`, `step3_equal`, `step4`, `sensitivity`, `step5` (several hours in total; `step3`
   alone about 35 minutes), `posthoc_shared_words.py`, `nonlinear_frequency.py`, `finish_lexical.py`,
   `figures_lexical.py`.
6. Article and supplement: `python paper/manuscript/assemble.py`, `python paper/supplement/build_supplement.py`,
   `bash paper/submission/build.sh` (needs pandoc, LibreOffice and python-docx).

## Licences

Code: MIT (see `LICENSE`). Result tables derived from the British and Dutch Lexicon Projects and SUBTLEX:
CC BY-NC-SA 4.0, as required by the sources. Word-level tables derived from the English Lexicon Project and
MEGALEX, and item-level tables derived from the Lu et al. (2025) knapsack data, are not redistributed; the
scripts rebuild them from the original files. Frequency values come from the `wordfreq` package (data under
CC BY-SA 4.0).
