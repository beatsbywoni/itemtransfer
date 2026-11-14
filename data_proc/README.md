# data_proc/

Tables of the knapsack example, derived from the original authors' repositories by the scripts in `code/`.
To rebuild them, run from the repository root (bash on Linux, macOS or WSL; Python 3.9+ with pandas and numpy):

```
bash code/run_3a_download.sh     # once, needs internet: downloads the repositories into data_raw/
bash code/run_prep.sh            # steps 02, 03, 03b (optional), 08 (only if MiniZinc is installed), 09, 10
```

`data_raw/` is not part of this repository. Checked on 14 November 2026: with the downloaded files, `run_prep.sh`
without MiniZinc reproduces the complete `trials_harmonized.csv` of the article (16,122 rows) in every column except
`k5_responder`. That column is filled only when the optional steps `02b_convert_rds.py` (needs pyreadr) and
`04_validate_against_authors.py` have been run; the article does not use it.

Dataset codes: K2 = Franco et al. (2021), K4 = Franco et al. (2024), K5 = Doroc et al. (2025),
K7 = Lu et al. (2025), K8 = optimisation-task data that the article does not use.
The K5 files come from the OSF project y7m3s, whose components are nc94u (data), cusk9 (code) and hjq8z.

| File | Content |
|---|---|
| `trials_harmonized.csv` | one row per response, with the measures of the instance attached. **The rows of K7 are removed**, because the K7 data carry no licence. Running the scripts restores them; `examples/knapsack.py` needs the complete table |
| `instances.csv` | weights, values, capacity and target of every instance (K7 removed for the same reason) |
| `instance_metrics.csv` | recomputed measures per instance, all datasets (no item lists) |
| `solver_effort_gecode.csv` | Gecode statistics per instance (MiniZinc 2.9.3, Gecode 6.3.0) |
| `instances_K8.csv` | instances of K8 |
