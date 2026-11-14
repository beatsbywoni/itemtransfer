"""One call that runs steps 2 to 5 and writes a summary."""
from __future__ import annotations

import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd

from ._data import prepare, validate_trials
from .diagnose import diagnose
from .reliability import agreement, reliability
from .simulate import check_intervals, design_from_data
from .transfer import transfer

__all__ = ["report"]


def _md_table(df, digits=3):
    if df is None or len(df) == 0:
        return "_none_\n"

    def cell(v):
        if isinstance(v, (bool, np.bool_)):
            return "yes" if v else "no"
        if isinstance(v, (float, np.floating)):
            if not np.isfinite(v):
                return ""
            return f"{v:.{digits}f}"
        return str(v)

    lines = ["| " + " | ".join(str(c) for c in df.columns) + " |", "|" + "|".join("---" for _ in df.columns) + "|"]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines) + "\n"


def _ci(df, stat, digits=2):
    lo, hi = df[stat + "_lo"], df[stat + "_hi"]
    return [f"{v:.{digits}f} [{a:.{digits}f}, {b:.{digits}f}]" if np.isfinite(a) and np.isfinite(b)
            else (f"{v:.{digits}f}" if np.isfinite(v) else "") for v, a, b in zip(df[stat], lo, hi)]


def report(trials, items, measures, out_dir=None, combined=True, weights="trials", evaluate=None, holdout=None,
           range_limits=None, reliability_only=None, n_boot=2000, n_splits=500, n_splits_reliability=1000, n_sim=0, n_boot_sim=200,
           check_measure=None, n_jobs=1, seed=0, columns=None, tolerance=(0.80, 1.25), boot_batch=None,
           check_prediction=False):
    """Run the reliability ceiling, the transfer, the diagnostics and the interval check.

    Parameters
    ----------
    trials, items, measures
        As in :func:`itemtransfer.transfer`.
    out_dir : str or pathlib.Path, optional
        Directory for the output files (created if needed): one CSV file
        per table, ``report.md`` and ``run_info.json``. Nothing is written
        when it is None.
    combined, weights, evaluate, holdout, n_boot, n_splits
        Passed to :func:`itemtransfer.transfer`.
    range_limits
        Passed to :func:`itemtransfer.diagnose`.
    reliability_only : sequence of str, optional
        Samples that enter the reliability ceiling (step 2) only, for
        example a pilot sample. They are removed before steps 3 to 5.
    n_splits_reliability : int
        Random participant splits for the reliabilities.
    n_sim : int
        Number of simulated data sets for the interval check (step 5). The
        default 0 skips the check, because it is the slowest part.
    n_boot_sim : int
        Bootstrap resamples per simulated data set.
    check_measure : str, optional
        Measure on which the simulated design is built (default: the first
        measure).
    tolerance, boot_batch
        Passed to :func:`itemtransfer.transfer`.
    check_prediction : bool
        If True, the interval check also covers the log-loss reduction
        (``check_intervals(..., prediction=True)``), which takes longer. By
        default the check covers the calibration slope only.
    n_jobs : int
        Worker processes for the interval check.
    seed : int
        Seed used by every step.
    columns : dict, optional
        Mapping from the standard column names to the names in the tables.

    Returns
    -------
    dict
        ``reliability``, ``agreement``, ``transfer``, ``predictions``,
        ``levels``, ``level_baseline``, ``within_level``, ``range``,
        ``weak_training``, ``measure_correlations``, ``weighting`` and
        ``interval_check`` (pandas DataFrames; empty when a step does not
        apply), ``warnings`` (list of str), ``markdown`` (the text of the
        report) and ``run_info`` (settings, package versions, run time).

    Examples
    --------
    >>> import itemtransfer as it
    >>> trials, items = it.load_example()
    >>> out = it.report(trials, items, ["x", "x2", "x_null"], n_boot=200, seed=1)
    >>> sorted(out)[:3]
    ['agreement', 'interval_check', 'level_baseline']
    """
    t0 = time.time()
    if isinstance(measures, str):
        measures = [measures]
    t = validate_trials(trials, columns)
    data_all = prepare(trials, items, measures, columns)
    if reliability_only:
        unknown = [s for s in reliability_only if s not in data_all.samples]
        if unknown:
            raise ValueError(f"`reliability_only` names unknown samples: {unknown}.")
        sample_col = (columns or {}).get("sample", "sample")
        trials = trials[~trials[sample_col].isin(list(reliability_only))]
    data = prepare(trials, items, measures, columns)
    out = {}
    out["reliability"] = reliability(t, n_splits=n_splits_reliability, seed=seed)
    pairs = []
    for f in data_all.families:
        names = data_all.family_samples[f]
        for a in range(len(names)):
            for b in range(a + 1, len(names)):
                sa, sb = data_all.samples[names[a]], data_all.samples[names[b]]
                shared = (sa.N.sum(axis=0) > 0) & (sb.N.sum(axis=0) > 0)
                if shared.sum() >= 3:
                    pairs.append(agreement(t, names[a], names[b], n_splits=n_splits_reliability, n_boot=n_boot, seed=seed))
    out["agreement"] = pd.concat(pairs, ignore_index=True) if pairs else pd.DataFrame()
    res = transfer(trials, items, measures, combined=combined, weights=weights, evaluate=evaluate, holdout=holdout,
                   n_boot=n_boot, n_splits=n_splits, seed=seed, columns=columns, tolerance=tolerance,
                   boot_batch=boot_batch)
    out["transfer"] = res.table
    out["predictions"] = res.predictions
    diag = diagnose(trials, items, measures, result=res, range_limits=range_limits, n_boot=n_boot, seed=seed,
                    columns=columns)
    for key in ["levels", "level_baseline", "within_level", "range", "weak_training", "measure_correlations",
                "weighting"]:
        out[key] = diag[key]
    out["warnings"] = list(diag["warnings"])
    out["interval_check"] = pd.DataFrame()
    if n_sim:
        cm = measures[0] if check_measure is None else check_measure
        design = design_from_data(trials, items, cm, seed=seed, columns=columns)
        ev = {str(k): [str(s) for s in v] for k, v in res.settings["evaluate"].items()}
        out["interval_check"] = check_intervals(design, n_sim=n_sim, n_boot=n_boot_sim, weights=weights, evaluate=ev,
                                                prediction=bool(check_prediction), n_jobs=n_jobs, seed=seed)
        for _, r in out["interval_check"].iterrows():
            if r["measure"] == "x" and np.isfinite(r["coverage"]) and r["coverage"] < 0.90 - 2 * r["coverage_se"]:
                out["warnings"].append(
                    f"In data simulated to resemble this design, the interval of the calibration slope of '{cm}' for "
                    f"held-out family '{r['family']}' covered its target in {100 * r['coverage']:.0f}% of data sets "
                    "(nominal 95%). Conclusions that rest on this interval are uncertain."
                )
    import scipy

    from . import __version__

    out["run_info"] = dict(
        package="itemtransfer", version=__version__, python=platform.python_version(), numpy=np.__version__,
        pandas=pd.__version__, scipy=scipy.__version__, seed=seed, n_boot=n_boot, n_splits=n_splits,
        n_splits_reliability=n_splits_reliability, n_sim=n_sim, n_boot_sim=n_boot_sim, weights=weights,
        reliability_only=[str(s) for s in (reliability_only or [])], check_prediction=bool(check_prediction),
        measures=list(measures), evaluate={str(k): [str(s) for s in v] for k, v in res.settings["evaluate"].items()},
        tolerance=None if tolerance is None else list(res.settings["tolerance"]),
        ordering_boot=res.settings["ordering_boot"], interval_type=res.settings["interval_type"],
        level=res.settings["level"], boot_batch=boot_batch, n_jobs=n_jobs, platform=platform.platform(),
        run_time_seconds=None)

    # ------------------------------------------------------------------ markdown summary
    tb = res.table
    main = pd.DataFrame({
        "held-out family": tb["family"], "model": tb["model"], "items": tb["n_items"], "trials": tb["n_trials"],
        "training slope": _ci(tb, "train_slope"), "ordering": _ci(tb, "ordering"),
        "calibration slope": _ci(tb, "calibration_slope"),
        "scale": tb["scale_reading"].fillna(""),
        "log-loss reduction": _ci(tb, "logloss_reduction", 3), "Brier reduction": _ci(tb, "brier_reduction", 3)})
    rel = out["reliability"]
    relm = pd.DataFrame({"sample": rel["sample"], "participants": rel["n_participants"], "items": rel["n_items"],
                         "trials per item (median)": rel["trials_per_item_median"],
                         "reliability, logit scale": _ci(rel, "logit_sb"),
                         "reliability, rank scale": _ci(rel, "spearman_sb")})
    md = ["# Leave-one-family-out transfer validation", "",
          f"Measures: {', '.join(measures)}. Families: {', '.join(str(f) for f in data.families)}. "
          f"Training samples weighted by {'trials' if weights == 'trials' else 'sample (equal weights)'}. "
          f"Seed {seed}; {n_boot} bootstrap resamples; intervals are 95% percentile intervals.", "",
          "## Step 2. Reliability ceiling", "",
          "Split-half reliability of item difficulty within each sample (Spearman-Brown; median and 2.5th to 97.5th "
          "percentile over random splits of the participants).", "", _md_table(relm)]
    if len(out["agreement"]):
        ag = out["agreement"]
        agm = pd.DataFrame({"sample A": ag["sample_a"], "sample B": ag["sample_b"], "shared items": ag["n_shared"],
                            "r (logit)": _ci(ag, "r_logit"), "Spearman": _ci(ag, "rho"),
                            "r corrected for unreliability": _ci(ag, "r_corrected")})
        md += ["Agreement between samples that share items (item bootstrap intervals).", "", _md_table(agm)]
    else:
        md += ["No two samples share items, so agreement between samples was not computed.", ""]
    md += ["## Step 3. Transfer", "",
           "Intervals of the training slope, the calibration slope and the reductions come from the two-way "
           "bootstrap (participants within samples, items within families); the interval of the ordering "
           "correlation comes from a bootstrap of items only. The calibration slope is 1 when the trained effect has "
           "the same size in the held-out family and 0 when there is no relation."
           + ("" if tolerance is None else f" Column 'scale' compares its interval with the tolerance "
              f"{tolerance[0]:g} to {tolerance[1]:g}; where the interval of the training slope includes 0 it reads "
              "'weak training relation' and the calibration slope should not be interpreted."),
           "", _md_table(main)]
    md += ["## Step 4. Design diagnostics", ""]
    if out["warnings"]:
        md += [f"- {w}" for w in out["warnings"]] + [""]
    else:
        md += ["No issue was flagged.", ""]
    md += ["### Level structure", "", _md_table(out["levels"]), "### Level-indicator baseline", "",
           _md_table(out["level_baseline"]), "### Within-level relations", "", _md_table(out["within_level"]),
           "### Range overlap", "", _md_table(out["range"]), "### Training slopes", "",
           _md_table(out["weak_training"]), "### Correlation between measures", "",
           _md_table(out["measure_correlations"]), "### Weighting of training samples", "",
           _md_table(out["weighting"])]
    md += ["## Step 5. Interval check by simulation", ""]
    if n_sim:
        md += [f"Data sets simulated from a design built on the measure '{check_measure or measures[0]}' "
               f"({n_sim} data sets, {n_boot_sim} resamples each). In the simulated design this measure is called x; "
               "x_null is a measure without effect. "
               + ("The check covers the calibration slope and the log-loss reduction." if check_prediction else
                  "The check covers the calibration slope only; `check_prediction=True` adds the log-loss reduction.")
               + " The interval of the ordering correlation is not part of this check.", "", _md_table(out["interval_check"])]
    else:
        md += ["Not run (n_sim = 0). Call `report(..., n_sim=200)` or `check_intervals` to check the coverage of the "
               "calibration-slope interval for a design like this one.", ""]
    out["run_info"]["run_time_seconds"] = round(time.time() - t0, 1)
    md += ["## Run information", "", "```", json.dumps(out["run_info"], indent=1), "```", ""]
    out["markdown"] = "\n".join(md)
    if out_dir is not None:
        d = Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        for key, val in out.items():
            if isinstance(val, pd.DataFrame):
                val.to_csv(d / f"{key}.csv", index=False)
        (d / "warnings.txt").write_text("\n".join(out["warnings"]) + ("\n" if out["warnings"] else ""))
        (d / "report.md").write_text(out["markdown"])
        (d / "run_info.json").write_text(json.dumps(out["run_info"], indent=1))
    return out
