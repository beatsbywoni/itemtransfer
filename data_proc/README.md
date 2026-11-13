# data_proc/

Tables of the knapsack example, derived from the original authors' repositories by the scripts in `code/`
(`01_osf_download.py`, `02_unpack_raw.py`, `03_extract_datasets.py`, `03b_extract_k8.py`, `08_solver_effort.py`,
`09_instance_metrics.py`, `10_harmonize_trials.py`; `run_3a_download.sh`, `run_3a2.sh` and `run_3a3.sh` call them
in order). The scripts write the raw files to `data_raw/`, which is not part of this repository.

Dataset codes: K2 = Franco et al. (2021), K4 = Franco et al. (2024), K5 = Doroc et al. (2025),
K7 = Lu et al. (2025), K8 = optimisation-task data that the article does not use.

| File | Content |
|---|---|
| `trials_harmonized.csv` | one row per response, with the measures of the instance attached. **The rows of K7 are removed**, because the K7 data carry no licence. Running the scripts restores them; `examples/knapsack.py` needs the complete table |
| `instances.csv` | weights, values, capacity and target of every instance (K7 removed for the same reason) |
| `instance_metrics.csv` | recomputed measures per instance, all datasets (no item lists) |
| `solver_effort_gecode.csv` | Gecode statistics per instance (MiniZinc 2.9.3, Gecode 6.3.0) |
| `instances_K8.csv` | instances of K8 |
