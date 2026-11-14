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

Commands are given from the repository root. The package itself runs on any platform with Python 3.10 or later.
The scripts of the article were run on Linux; the shell scripts need bash (Linux, macOS or WSL).

Environment:

```
pip install ".[plot,test]"               # the package
pip install -r paper/requirements.txt    # pinned versions used for the article (Python 3.13), with openpyxl
```

Further tools are needed only for single steps: R 4.6.2 with lme4 2.1.0 (`paper/glmm/`); MiniZinc 2.9.3 with
Gecode 6.3.0 (solver effort of the knapsack items; optional, the result file is distributed); pandoc, LibreOffice
and python-docx (building the DOCX and PDF files); pyreadr (only for the optional step `code/02b_convert_rds.py`).

Two routes exist. The result files in this folder are complete, so tables and figures can be checked against them
without any raw data (section 1.9 of the supplement names the file behind each table). Rebuilding the results from
the raw data needs the downloads described in steps 4 and 5.

1. Tests: `python -m pytest -q` (79 tests, under a minute; 76 pass and 3 are skipped, because they need the complete
   knapsack data and the result files of an earlier analysis, neither of which is distributed).
2. Tutorial with the synthetic data set: `docs/tutorial.md` (a few minutes).
3. Simulation study: `bash paper/sim/run_all.sh` (about six hours on two cores; resumes from saved chunks), then
   `python paper/sim/make_tables.py`, `python paper/sim/make_figures.py` and `python paper/sim/exact_breakeven.py`.
   Mixed models: `Rscript paper/glmm/glmm_simulation.R` (about 20 minutes).
4. Knapsack example. `data_proc/trials_harmonized.csv` in this repository lacks the rows of Lu et al. (2025),
   whose data carry no licence, so the complete table has to be rebuilt first:
   `bash code/run_3a_download.sh` (once, needs internet; downloads the authors' repositories into `data_raw/`),
   then `bash code/run_prep.sh` (steps 02, 03, 03b, 08 if MiniZinc is installed, 09 and 10; see
   `data_proc/README.md`). Then `python examples/knapsack.py` (a few minutes),
   `python paper/figures/make_knapsack_figure.py` and
   `Rscript paper/glmm/glmm_knapsack.R data_proc/trials_harmonized.csv`. For the same reason
   `paper/knapsack_report/predictions.csv` is given here without the rows of the Lu family; the run restores them.
5. Lexical decision example. Obtain the files listed in `paper/second_example/PROVENANCE.md` (sources, sizes and
   SHA-256 checksums; the item file of the English Lexicon Project is requested from the project website) and
   place them under `paper/second_example/original/`. Then:

   ```
   cd paper/second_example/original && sha256sum -c MANIFEST.sha256 && cd ..
   python cache_trials.py
   python prep_measures.py
   python step1_elp_published.py
   for stage in step2 step3 step3_equal step4 sensitivity step5; do python run_lexical.py $stage; done
   python posthoc_shared_words.py
   python nonlinear_frequency.py
   python finish_lexical.py
   python figures_lexical.py
   ```

   The stages take several hours in total (`step3` alone about 35 minutes on two cores).
6. Article and supplement: `python paper/manuscript/assemble.py`, `python paper/supplement/build_supplement.py`,
   `bash paper/submission/build.sh`.

## Licences

Code: MIT (see `LICENSE`). Result tables derived from the British and Dutch Lexicon Projects and SUBTLEX:
CC BY-NC-SA 4.0, as required by the sources. Word-level tables derived from the English Lexicon Project and
MEGALEX, and item-level tables derived from the Lu et al. (2025) knapsack data, are not redistributed; the
scripts rebuild them from the original files. Frequency values come from the `wordfreq` package (data under
CC BY-SA 4.0).
