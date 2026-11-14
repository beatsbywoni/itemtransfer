"""Step 4 of the procedure: design diagnostics.

The three transfer criteria can disagree. The diagnostics collected here
describe properties of the design that explain such disagreement: few
designed levels of a measure, little overlap in its range, a weak training
relation, measures that are correlated by design, and the weighting of the
training samples.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ._data import prepare, restrict
from ._stats import as_rng, child_rng, pearson, percentile_interval, spearman
from .transfer import (TransferResult, _batch_sizes, _bootstrap_fold, _check_folds, _draw, _model_columns, _point_fold,
                       _prediction, _reductions, _resolve_evaluate, _split_masks, transfer)

__all__ = ["diagnose", "detect_levels"]


def detect_levels(values, max_levels=6, min_gap_ratio=2.0):
    """Detect whether a measure takes a few designed levels.

    Parameters
    ----------
    values : array_like
        Values of one measure for the items of one family.
    max_levels : int
        Largest number of levels that counts as "few".
    min_gap_ratio : float
        For measures with more than ``max_levels`` distinct values: the
        values are cut at their largest gaps into 2 to ``max_levels``
        groups. A grouping counts as a level structure when its smallest
        gap between groups exceeds ``min_gap_ratio`` times the widest range
        within a group and every group has at least two items.

    Returns
    -------
    levels : numpy.ndarray of int or None
        Level index of every item (0 = lowest values), or None when no
        level structure was found.
    info : dict
        ``n_distinct``, ``n_levels`` (0 when none), ``kind`` ("discrete",
        "clustered", "constant" or "none") and ``gap_ratio``.
    """
    x = np.asarray(values, dtype=float)
    u = np.unique(np.round(x, 10))
    info = dict(n_distinct=len(u), n_levels=0, kind="none", gap_ratio=np.nan)
    if len(u) < 2:
        info["kind"] = "constant"
        return None, info
    if len(u) <= max_levels:
        info.update(n_levels=len(u), kind="discrete", gap_ratio=np.inf)
        return np.searchsorted(u, np.round(x, 10)), info
    gaps = np.diff(u)
    order = np.argsort(gaps)[::-1]
    best = None
    for k in range(2, max_levels + 1):
        cuts = np.sort(order[: k - 1])
        bounds = (u[cuts] + u[cuts + 1]) / 2
        lev = np.searchsorted(bounds, x)
        sizes = np.bincount(lev, minlength=k)
        if sizes.min() < 2:
            continue
        width = max(x[lev == j].max() - x[lev == j].min() for j in range(k))
        ratio = np.inf if width == 0 else gaps[cuts].min() / width
        if best is None or ratio > best[0]:
            best = (ratio, k, lev)
    if best is not None:
        info["gap_ratio"] = float(best[0])
        if best[0] > min_gap_ratio:
            info.update(n_levels=best[1], kind="clustered")
            return best[2], info
    return None, info


def _fmt(v):
    return f"{v:.2f}" if np.isfinite(v) else "not defined"


def diagnose(trials, items, measures, result=None, combined=True, weights="trials", evaluate=None, holdout=None,
             range_limits=None, max_levels=6, min_gap_ratio=2.0, collinearity=0.7, n_boot=2000, n_splits=500,
             seed=0, columns=None, boot_batch=None):
    """Design diagnostics that explain disagreement between the transfer criteria.

    Parameters
    ----------
    trials, items, measures
        As in :func:`itemtransfer.transfer`.
    result : TransferResult, optional
        Result of :func:`itemtransfer.transfer` on the same data. When
        given, its settings (weights, evaluation samples, held-out
        families, seed, number of splits) are reused and the transfer is
        not run again. Otherwise the transfer is run with the arguments
        below.
    combined, weights, evaluate, holdout, n_boot, n_splits, seed, columns
        As in :func:`itemtransfer.transfer` (used when ``result`` is None;
        ``n_boot`` is also the number of resamples for the interval of the
        calibration slope on the common range).
    range_limits : dict, optional
        ``{measure: (low, high)}`` with None for an open end. The criteria
        are recomputed with all items outside the limits removed. By
        default the common range of a fold is the overlap between the range
        of the held-out family and the range of its training families.
    max_levels, min_gap_ratio
        Passed to :func:`detect_levels`.
    collinearity : float
        Absolute Spearman correlation between two measures within a family
        from which a warning is issued.
    boot_batch : int, optional
        Number of bootstrap resamples processed at a time (see
        :func:`itemtransfer.transfer`); useful for data with very many
        items. By default the value used for ``result`` is reused.

    Returns
    -------
    dict
        ``levels``
            One row per family and measure: number of items, of distinct
            values and of detected levels.
        ``level_baseline``
            For held-out families in which the measure has few levels:
            ordering and log-loss reduction of the measure next to those of
            a level indicator (one fitted probability per level, estimated
            on the calibration half of the held-out items), and the
            correlation between level means and item accuracy.
        ``within_level``
            One row per level: number of items, range and standard
            deviation of the measure, mean accuracy and the Spearman
            correlation between measure and accuracy inside the level.
        ``range``
            Range of the measure in the held-out and the training families,
            the share of held-out items inside the training range, and
            ordering, calibration slope and training slope recomputed on
            the common range.
        ``weak_training``
            Training slope with its interval and a flag when the interval
            includes 0.
        ``measure_correlations``
            Spearman correlation between every pair of measures within each
            family.
        ``weighting``
            The criteria with training samples weighted by trials and
            equally.
        ``warnings``
            A list of plain-language sentences, one per issue found.
        ``transfer``
            The :class:`TransferResult` used.

    Notes
    -----
    A level indicator uses as many parameters fitted in the held-out family
    as there are levels, against one (the intercept) for a transferred
    measure. When it predicts as well as the measure, the held-out family
    shows that its levels differ in difficulty but cannot show that the
    measure is the right scale.

    Examples
    --------
    >>> import itemtransfer as it
    >>> trials, items = it.load_example()
    >>> diag = it.diagnose(trials, items, ["x", "x_null"], n_boot=200, seed=1)
    >>> print("\\n".join(diag["warnings"]))  # doctest: +SKIP
    """
    if result is None:
        result = transfer(trials, items, measures, combined=combined, weights=weights, evaluate=evaluate,
                          holdout=holdout, n_boot=n_boot, n_splits=n_splits, seed=seed, columns=columns,
                          boot_batch=boot_batch)
    elif not isinstance(result, TransferResult):
        raise TypeError("`result` must be the object returned by itemtransfer.transfer().")
    else:
        st = result.settings
        weights, evaluate, holdout, n_splits = st["weights"], st["evaluate"], st["holdout"], st["n_splits"]
        combined = st["combined"]
        if st.get("seed") is not None:
            seed = st["seed"]
        if boot_batch is None:
            boot_batch = st.get("boot_batch")
    data = prepare(trials, items, measures, columns)
    folds = _check_folds(data, holdout)
    ev = _resolve_evaluate(data, evaluate)
    models = _model_columns(data.measures, combined)
    tab = result.table.set_index(["family", "model"])
    warnings = []

    # ---------------------------------------------------------------- level structure
    lev_rows, base_rows, within_rows = [], [], []
    split_rng = as_rng(seed)
    fold_point, fold_masks = {}, {}
    for f in folds:  # same item splits as transfer() when the seed is the same integer
        fold_point[f] = _point_fold(data, f, ev[f], models, weights)
        k = int(fold_point[f][3].sum())
        fold_masks[f] = _split_masks(k, n_splits, split_rng) if k >= 4 else None
    for f in data.families:
        for j, m in enumerate(data.measures):
            _, info = detect_levels(data.X[f][:, j], max_levels, min_gap_ratio)
            lev_rows.append(dict(family=f, measure=m, n_items=data.n_items(f), **info))
            if info["kind"] == "constant":
                warnings.append(f"Measure '{m}' is constant in family '{f}'; it cannot order the items of that family.")
    for f in folds:
        pt, n_e, s_e, keep = fold_point[f]
        n_k, s_k = n_e[keep], s_e[keep]
        acc = s_k / n_k
        masks = fold_masks[f]
        for j, m in enumerate(data.measures):
            x = data.X[f][keep, j]
            levels, info = detect_levels(x, max_levels, min_gap_ratio)
            if levels is None or masks is None:
                continue
            b = pt[m]["b"][0]
            lins = np.vstack([np.zeros(len(x)), pt[m]["eta"][keep]])
            ll, br = _prediction(lins, n_k, s_k, masks, levels=levels)
            red, _ = _reductions(ll, br)
            diff = red[:, 1] - red[:, 2]
            level_mean = np.array([acc[levels == k].mean() for k in range(info["n_levels"])])
            within = []
            for k in range(info["n_levels"]):
                mk = levels == k
                rw = spearman(x[mk], acc[mk]) if mk.sum() >= 3 else np.nan
                within.append(rw)
                within_rows.append(dict(family=f, measure=m, level=k, n_items=int(mk.sum()),
                                        measure_min=float(x[mk].min()), measure_max=float(x[mk].max()),
                                        measure_sd=float(x[mk].std()), accuracy_mean=float(acc[mk].mean()),
                                        accuracy_sd=float(acc[mk].std()), ordering_within=rw))
            row = dict(family=f, measure=m, n_levels=info["n_levels"], kind=info["kind"],
                       ordering_measure=pt[m]["ordering"],
                       ordering_levels=spearman(np.sign(b) * levels, acc),
                       level_accuracy_r=pearson(level_mean[levels], acc),
                       logloss_reduction_measure=float(red[:, 1].mean()),
                       logloss_reduction_levels=float(red[:, 2].mean()),
                       logloss_difference=float(diff.mean()),
                       logloss_difference_split_lo=float(np.percentile(diff, 2.5)),
                       logloss_difference_split_hi=float(np.percentile(diff, 97.5)))
            base_rows.append(row)
            if info["kind"] == "discrete":
                lead = (f"Measure '{m}' takes {info['n_levels']} distinct values in held-out family '{f}'. "
                        "Ordering and prediction in this family can only reflect contrasts between these values: ")
            else:
                lead = (f"The values of measure '{m}' fall into {info['n_levels']} tight clusters in held-out family "
                        f"'{f}'. Ordering and prediction in this family may be dominated by the contrasts between "
                        "the clusters; the relations within the clusters are reported separately: ")
            txt = (lead + "a level "
                   f"indicator fitted in the family reduces log loss by {row['logloss_reduction_levels']:.3f}, the "
                   f"transferred measure by {row['logloss_reduction_measure']:.3f}.")
            if np.isfinite(within).any():
                txt += (" Within the levels, the correlations between measure and accuracy are "
                        + ", ".join(_fmt(r) for r in within) + ".")
            warnings.append(txt)

    # ---------------------------------------------------------------- weak training relation
    weak_rows = []
    for f in folds:
        for m in data.measures:
            lo, hi = tab.at[(f, m), "train_slope_lo"], tab.at[(f, m), "train_slope_hi"]
            weak = bool(lo <= 0 <= hi) if np.isfinite(lo) and np.isfinite(hi) else np.nan
            weak_rows.append(dict(family=f, measure=m, train_slope=tab.at[(f, m), "train_slope"], train_slope_lo=lo,
                                  train_slope_hi=hi, weak=weak, calibration_slope=tab.at[(f, m), "calibration_slope"],
                                  heldout_slope=tab.at[(f, m), "heldout_slope"],
                                  heldout_slope_lo=tab.at[(f, m), "heldout_slope_lo"],
                                  heldout_slope_hi=tab.at[(f, m), "heldout_slope_hi"]))
            if weak is True:
                warnings.append(
                    f"The training slope of '{m}' for held-out family '{f}' has an interval that includes 0 "
                    f"({lo:.3g} to {hi:.3g}). The calibration slope is then a ratio with a denominator near zero and "
                    "is not informative; read the training slope and the held-out slope instead."
                )
    if not result.settings.get("n_boot"):
        warnings.append("No bootstrap was run (n_boot = 0), so weak training relations could not be flagged.")

    # ---------------------------------------------------------------- range overlap
    range_rows = []
    brng = child_rng(seed, 2)
    for f in folds:
        for j, m in enumerate(data.measures):
            xh = data.X[f][:, j]
            xt = np.concatenate([data.X[g][:, j] for g in data.families if g != f])
            inside = (xh >= xt.min()) & (xh <= xt.max())
            if range_limits and m in range_limits:
                lo, hi = range_limits[m]
                lo = -np.inf if lo is None else lo
                hi = np.inf if hi is None else hi
            else:
                lo, hi = max(xh.min(), xt.min()), min(xh.max(), xt.max())
            keep = {g: (data.X[g][:, j] >= lo) & (data.X[g][:, j] <= hi) for g in data.families}
            row = dict(family=f, measure=m, heldout_min=float(xh.min()), heldout_max=float(xh.max()),
                       train_min=float(xt.min()), train_max=float(xt.max()), share_inside_training=float(inside.mean()),
                       common_low=float(lo), common_high=float(hi), n_heldout_common=int(keep[f].sum()),
                       n_train_common=int(sum(keep[g].sum() for g in data.families if g != f)),
                       ordering=tab.at[(f, m), "ordering"], ordering_common=np.nan,
                       calibration_slope=tab.at[(f, m), "calibration_slope"], calibration_slope_common=np.nan,
                       calibration_slope_common_lo=np.nan, calibration_slope_common_hi=np.nan,
                       train_slope=tab.at[(f, m), "train_slope"], train_slope_common=np.nan)
            changed = any((~keep[g]).any() for g in data.families)
            sub = restrict(data, keep)
            evs = [e for e in ev[f] if e in sub.samples]
            ok = (f in sub.families and len(sub.families) >= 2 and len(evs) > 0 and row["n_heldout_common"] >= 3
                  and np.ptp(np.concatenate([sub.X[g][:, j] for g in sub.families if g != f])) > 0)
            if not changed:
                row.update(ordering_common=row["ordering"], calibration_slope_common=row["calibration_slope"],
                           train_slope_common=row["train_slope"],
                           calibration_slope_common_lo=tab.at[(f, m), "calibration_slope_lo"],
                           calibration_slope_common_hi=tab.at[(f, m), "calibration_slope_hi"])
            elif ok:
                pt, _, _, _ = _point_fold(sub, f, evs, {m: [m]}, weights)
                row.update(ordering_common=pt[m]["ordering"], calibration_slope_common=pt[m]["calibration_slope"],
                           train_slope_common=pt[m]["b"][0])
                if n_boot:
                    cs = []
                    for size in _batch_sizes(n_boot, boot_batch):
                        wp, wi = _draw(sub, size, brng)
                        bt = _bootstrap_fold(sub, f, evs, {m: [m]}, weights, wp, wi, brng, ordering=False,
                                             prediction=False, heldout=False)
                        cs.append(bt[m]["calibration_slope"])
                    lo_b, hi_b = percentile_interval(np.concatenate(cs))
                    row.update(calibration_slope_common_lo=lo_b, calibration_slope_common_hi=hi_b)
            range_rows.append(row)
            is_weak = any(w["family"] == f and w["measure"] == m and w["weak"] is True for w in weak_rows)
            if is_weak:
                if row["share_inside_training"] < 0.8:
                    warnings.append(
                        f"Only {100 * row['share_inside_training']:.0f}% of the items of held-out family '{f}' lie "
                        f"inside the range of '{m}' in the training families ({row['train_min']:.3g} to "
                        f"{row['train_max']:.3g}).")
            elif row["share_inside_training"] < 0.8:
                txt = (f"Only {100 * row['share_inside_training']:.0f}% of the items of held-out family '{f}' lie "
                       f"inside the range of '{m}' in the training families ({row['train_min']:.3g} to "
                       f"{row['train_max']:.3g}); the trained slope is extrapolated.")
                if np.isfinite(row["calibration_slope_common"]):
                    txt += (f" On the common range the calibration slope is {row['calibration_slope_common']:.2f} "
                            f"instead of {row['calibration_slope']:.2f}.")
                warnings.append(txt)
            elif changed and np.isfinite(row["calibration_slope_common"]) and \
                    abs(row["calibration_slope_common"] - row["calibration_slope"]) > 0.25 and row["n_train_common"] < \
                    sum(data.n_items(g) for g in data.families if g != f) * 0.8:
                warnings.append(
                    f"The training families cover a wider range of '{m}' than held-out family '{f}'. With all "
                    f"families restricted to the common range ({lo:.3g} to {hi:.3g}) the calibration slope is "
                    f"{row['calibration_slope_common']:.2f} instead of {row['calibration_slope']:.2f}; the slope per "
                    "unit of the measure depends on the range covered."
                )

    # ---------------------------------------------------------------- correlation between measures
    corr_rows = []
    for f in data.families:
        for a in range(len(data.measures)):
            for c in range(a + 1, len(data.measures)):
                rho = spearman(data.X[f][:, a], data.X[f][:, c])
                corr_rows.append(dict(family=f, measure_a=data.measures[a], measure_b=data.measures[c], spearman=rho,
                                      n_items=data.n_items(f)))
                if np.isfinite(rho) and abs(rho) >= collinearity:
                    warnings.append(
                        f"Measures '{data.measures[a]}' and '{data.measures[c]}' are strongly correlated in family "
                        f"'{f}' (Spearman {rho:.2f}); their separate relations with accuracy are hard to interpret in "
                        "that family, and the coefficients of a joint model may depend strongly on the design. The "
                        "flag is a heuristic and does not mean that the effects cannot be separated in principle."
                    )

    # ---------------------------------------------------------------- weighting of training samples
    weight_rows = []
    for f in folds:
        res = {}
        masks = fold_masks[f]
        for wt in ("trials", "equal"):
            pt, n_e, s_e, keep = fold_point[f] if wt == weights else _point_fold(data, f, ev[f], models, wt)
            lins = np.vstack([np.zeros(keep.sum())] + [pt[m]["eta"][keep] for m in models])
            if masks is not None and np.all(np.isfinite(lins)):
                red, _ = _reductions(*_prediction(lins, n_e[keep], s_e[keep], masks))
                red = red.mean(axis=0)
            else:
                red = np.full(len(models) + 1, np.nan)
            res[wt] = (pt, red)
        n_train = sum(len(data.family_samples[g]) for g in data.families if g != f)
        for k, (name, cols) in enumerate(models.items()):
            row = dict(family=f, model=name, n_training_samples=n_train)
            for wt in ("trials", "equal"):
                pt, red = res[wt]
                row[f"train_slope_{wt}"] = pt[name]["b"][0] if len(cols) == 1 else np.nan
                row[f"ordering_{wt}"] = pt[name]["ordering"]
                row[f"calibration_slope_{wt}"] = pt[name]["calibration_slope"]
                row[f"logloss_reduction_{wt}"] = red[k + 1]
            weight_rows.append(row)
            a, b = row["calibration_slope_trials"], row["calibration_slope_equal"]
            is_weak = any(w["family"] == f and w["measure"] == name and w["weak"] is True for w in weak_rows)
            if not is_weak and np.isfinite(a) and np.isfinite(b) and abs(a - b) > 0.25 and \
                    abs(a - b) > 0.25 * max(abs(a), abs(b)):
                warnings.append(
                    f"The calibration slope of '{name}' for held-out family '{f}' depends on the weighting of the "
                    f"training samples: {a:.2f} with weights by trials, {b:.2f} with equal weights."
                )
    return dict(levels=pd.DataFrame(lev_rows), level_baseline=pd.DataFrame(base_rows),
                within_level=pd.DataFrame(within_rows), range=pd.DataFrame(range_rows),
                weak_training=pd.DataFrame(weak_rows), measure_correlations=pd.DataFrame(corr_rows),
                weighting=pd.DataFrame(weight_rows), warnings=warnings, transfer=result)
