"""Step 3 of the procedure: leave-one-family-out transfer of a measure.

For every held-out item family the relation between a measure and accuracy
is estimated on the other families and then judged on the held-out family
by three criteria that can disagree: ordering, scale and prediction.
"""
from __future__ import annotations

import warnings

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ._data import prepare
from ._fit import fit_intercepts, fit_logit, fit_logit_batch
from ._stats import as_rng, bootstrap_counts, child_rng, interval, spearman, wspearman

__all__ = ["transfer", "TransferResult"]


@dataclass
class TransferResult:
    """Result of :func:`transfer`.

    Attributes
    ----------
    table : pandas.DataFrame
        One row per held-out family and model (see :func:`transfer`).
    predictions : pandas.DataFrame
        One row per held-out family, model and item: the transferred linear
        predictor (training slope times measure, without intercept), the
        number of trials and correct responses and the item accuracy in the
        evaluation sample(s).
    bootstrap : dict
        ``(family, model) -> pandas.DataFrame`` with one row per two-way
        bootstrap resample and one column per statistic.
    settings : dict
        The arguments used, including seeds.
    """

    table: pd.DataFrame
    predictions: pd.DataFrame
    bootstrap: dict = field(default_factory=dict, repr=False)
    settings: dict = field(default_factory=dict)

    def __repr__(self):
        cols = ["family", "model", "train_slope", "ordering", "calibration_slope", "logloss_reduction"]
        return "TransferResult\n" + self.table[cols].round(3).to_string(index=False)


# --------------------------------------------------------------------------
# set-up helpers
# --------------------------------------------------------------------------
def _model_columns(measures, combined):
    if "combined" in measures or "constant" in measures:
        raise ValueError("A measure cannot be called 'combined' or 'constant'; rename the column.")
    models = {m: [m] for m in measures}
    if combined and len(measures) > 1:
        models["combined"] = list(measures)
    return models


def _resolve_evaluate(data, evaluate):
    out = {}
    evaluate = evaluate or {}
    unknown = set(evaluate) - set(data.families)
    if unknown:
        raise ValueError(f"`evaluate` names unknown families: {sorted(unknown, key=str)}.")
    for f in data.families:
        ev = evaluate.get(f)
        if ev is None:
            ev = list(data.family_samples[f])
        elif isinstance(ev, str) or not isinstance(ev, (list, tuple)):
            ev = [ev]
        for s in ev:
            if s not in data.family_samples[f]:
                raise ValueError(
                    f"Evaluation sample '{s}' is not a sample of family '{f}' (its samples: {data.family_samples[f]})."
                )
        out[f] = list(ev)
    return out


def _check_folds(data, holdout):
    if len(data.families) < 2:
        raise ValueError(
            f"Leave-one-family-out transfer needs at least two item families; found {len(data.families)}."
        )
    folds = list(data.families) if holdout is None else list(holdout)
    unknown = [f for f in folds if f not in data.families]
    if unknown:
        raise ValueError(f"Unknown held-out families {unknown}; families in the data: {data.families}.")
    return folds


def _training_rows(data, family):
    """Stack the training samples of a fold: design block sizes, measure matrix and sample order."""
    names = [s for f in data.families if f != family for s in data.family_samples[f]]
    X = np.vstack([data.X[data.samples[s].family] for s in names])
    sizes = [data.n_items(data.samples[s].family) for s in names]
    ind = np.zeros((sum(sizes), len(names)))
    start = 0
    for j, k in enumerate(sizes):
        ind[start:start + k, j] = 1.0
        start += k
    return names, sizes, ind, X


def _sample_weight(n_blocks, weights):
    """Row weight factor per training sample: 1 (trials) or inversely proportional to its number of trials."""
    tot = np.array([b.sum() for b in n_blocks], dtype=float)
    if weights == "trials":
        return np.ones(len(tot))
    with np.errstate(divide="ignore"):
        return np.where(tot > 0, tot.mean() / tot, 0.0)


# --------------------------------------------------------------------------
# point estimates
# --------------------------------------------------------------------------
def _point_fold(data, family, eval_samples, models, weights):
    names, sizes, ind, Xtr = _training_rows(data, family)
    blocks = [data.samples[s].counts() for s in names]
    fac = _sample_weight([b[0] for b in blocks], weights)
    n = np.concatenate([b[0] for b in blocks])
    s = np.concatenate([b[1] for b in blocks])
    fw = np.concatenate([np.full(k, c) for k, c in zip(sizes, fac)])
    n_e = sum(data.samples[e].counts()[0] for e in eval_samples)
    s_e = sum(data.samples[e].counts()[1] for e in eval_samples)
    keep = n_e > 0
    acc = np.where(keep, s_e / np.maximum(n_e, 1), np.nan)
    Xh = data.X[family]
    out = {}
    for name, cols in models.items():
        ci = [data.measures.index(m) for m in cols]
        fit = fit_logit(np.hstack([ind, Xtr[:, ci]]), n, s, fw)
        b = fit.coef[len(names):]
        eta = Xh[:, ci] @ b
        rho = spearman(eta[keep], acc[keep])
        cal = fit_logit(np.column_stack([np.ones(keep.sum()), eta[keep]]), n_e[keep], s_e[keep])
        res = dict(b=b, train_converged=fit.converged and not fit.boundary, eta=eta, ordering=rho,
                   calibration_slope=cal.coef[1], calibration_converged=cal.converged and not cal.boundary,
                   heldout_slope=np.nan)
        if len(cols) == 1:
            ho = fit_logit(np.column_stack([np.ones(keep.sum()), Xh[keep][:, ci[0]]]), n_e[keep], s_e[keep])
            res["heldout_slope"] = ho.coef[1]
        out[name] = res
    return out, n_e, s_e, keep


def _split_masks(n_items, n_splits, rng):
    """Random halves of the items: (n_splits, items) 0/1 array marking the first half of a permutation."""
    masks = np.zeros((n_splits, n_items))
    half = n_items // 2
    for r in range(n_splits):
        masks[r, rng.permutation(n_items)[:half]] = 1.0
    return masks


def _losses(lin, n, s, w):
    """Trial-level log loss and Brier score over the last axis, rows weighted by ``w``."""
    p = np.clip(1 / (1 + np.exp(-lin)), 1e-12, 1 - 1e-12)
    wn, ws = w * n, w * s
    tot = wn.sum(axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ll = -np.sum(ws * np.log(p) + (wn - ws) * np.log(1 - p), axis=-1) / tot
        br = np.sum(ws * (1 - p) ** 2 + (wn - ws) * p ** 2, axis=-1) / tot
    return ll, br


def _prediction(lins, n, s, masks, levels=None, tol=1e-12, chunk_elems=8_000_000):
    """Split-half intercept calibration.

    lins : (models, items) transferred linear predictors (a row of zeros is the intercept-only model).
    masks : (splits, items) 0/1, first half of the items of each split.
    levels : optional integer level of each item; adds a level-indicator baseline as the last model.
    chunk_elems : the splits are processed in blocks of at most this many array elements (splits x 2 x models x
        items), which bounds memory for families with many items; the splits are independent, so the result does
        not depend on it.
    Returns log loss and Brier score, each (splits, models [+1]), averaged over the two directions.
    """
    step = max(1, int(chunk_elems // (2 * (lins.shape[0] + 1) * max(lins.shape[1], 1))))
    if len(masks) > step:
        parts = [_prediction(lins, n, s, masks[a:a + step], levels=levels, tol=tol, chunk_elems=chunk_elems)
                 for a in range(0, len(masks), step)]
        return np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts])
    halves = np.stack([masks, 1 - masks], axis=1)  # splits x 2 x items
    cal = halves[:, :, None, :]
    ev = 1 - cal
    a = fit_intercepts(lins[None, None], n * cal, s * cal, tol=tol)  # splits x 2 x models
    ll, br = _losses(a[..., None] + lins[None, None], n, s, ev)
    if levels is not None:
        K = int(levels.max()) + 1
        onehot = (levels[None, :] == np.arange(K)[:, None]).astype(float)  # K x items
        nL = (halves * n) @ onehot.T  # splits x 2 x K
        sL = (halves * s) @ onehot.T
        n_all, s_all = (halves * n).sum(-1, keepdims=True), (halves * s).sum(-1, keepdims=True)
        with np.errstate(invalid="ignore", divide="ignore"):
            pL = np.where(nL > 0, sL / nL, s_all / n_all)
        # a level without errors (or without correct responses) in the calibration half: smoothed estimate
        edge = (pL <= 0) | (pL >= 1)
        pL = np.where(edge, (np.where(nL > 0, sL, s_all) + 0.5) / (np.where(nL > 0, nL, n_all) + 1.0), pL)
        lin_lev = np.log(pL / (1 - pL))[:, :, levels]  # splits x 2 x items
        l2, b2 = _losses(lin_lev, n, s, 1 - halves)
        ll = np.concatenate([ll, l2[..., None]], axis=-1)
        br = np.concatenate([br, b2[..., None]], axis=-1)
    return ll.mean(axis=1), br.mean(axis=1)


def _reductions(ll, br, const=0):
    """Relative reduction of each model against the intercept-only model (column ``const``), per split."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return 1 - ll / ll[:, [const]], 1 - br / br[:, [const]]


# --------------------------------------------------------------------------
# two-way bootstrap
# --------------------------------------------------------------------------
def _draw(data, n_boot, rng, two_way=True):
    """Resampling counts: participants within each sample, items within each family."""
    wp = {name: bootstrap_counts(rng, smp.n_participants, n_boot) for name, smp in data.samples.items()}
    wi = {}
    for f in data.families:
        k = data.n_items(f)
        wi[f] = bootstrap_counts(rng, k, n_boot) if two_way else np.ones((n_boot, k))
    return wp, wi


def _batch_sizes(n_boot, boot_batch):
    """Sizes of the bootstrap batches: one batch of ``n_boot`` unless ``boot_batch`` is given."""
    if boot_batch is None:
        return [int(n_boot)]
    if int(boot_batch) != boot_batch or boot_batch < 1:
        raise ValueError("`boot_batch` must be a positive integer (or None for a single batch).")
    return [int(min(boot_batch, n_boot - a)) for a in range(0, int(n_boot), int(boot_batch))]


def _boot_prediction(lins, n, s, w, n_splits, rng, chunk_elems=3_000_000):
    """Resampled log-loss and Brier reductions. lins: (boot, models, items) incl. the zero row first."""
    B, M, I = lins.shape
    out_ll = np.full((B, M), np.nan)
    out_br = np.full((B, M), np.nan)
    step = max(1, int(chunk_elems // (n_splits * 2 * M * I)))
    for a0 in range(0, B, step):
        sl = slice(a0, min(B, a0 + step))
        C = sl.stop - sl.start
        present = (w[sl] > 0) & (n[sl] > 0)
        u = rng.random((C, n_splits, I))
        u = np.where(present[:, None, :], u, 2.0)
        rank = np.argsort(np.argsort(u, axis=-1), axis=-1)
        half = (present.sum(axis=1) // 2)[:, None, None]
        first = (rank < half) & present[:, None, :]
        second = (~first) & present[:, None, :]
        halves = np.stack([first, second], axis=2).astype(float)  # C x K x 2 x I
        wc = (w[sl][:, None, None, :] * halves)[:, :, :, None, :]  # C x K x 2 x 1 x I
        we = (w[sl][:, None, None, :] * halves[:, :, ::-1, :])[:, :, :, None, :]
        nn = n[sl][:, None, None, None, :]
        ss = s[sl][:, None, None, None, :]
        L = lins[sl][:, None, None, :, :]
        a = fit_intercepts(L, nn * wc, ss * wc, tol=1e-9, max_iter=50)
        ll, br = _losses(a[..., None] + L, nn, ss, we)  # C x K x 2 x M
        ll, br = ll.mean(axis=2), br.mean(axis=2)
        with np.errstate(invalid="ignore", divide="ignore"):
            out_ll[sl] = np.nanmean(1 - ll / ll[:, :, [0]], axis=1)
            out_br[sl] = np.nanmean(1 - br / br[:, :, [0]], axis=1)
    return out_ll, out_br


def _bootstrap_fold(data, family, eval_samples, models, weights, wp, wi, rng, ordering=True, prediction=True,
                    n_splits_boot=10, heldout=True):
    names, sizes, ind, Xtr = _training_rows(data, family)
    k = len(names)
    n_blocks, s_blocks, w_blocks = [], [], []
    for sname in names:
        smp = data.samples[sname]
        n_blocks.append(wp[sname] @ smp.N)
        s_blocks.append(wp[sname] @ smp.S)
        w_blocks.append(wi[smp.family])
    if weights == "equal":
        tot = np.stack([(nb * wb).sum(axis=1) for nb, wb in zip(n_blocks, w_blocks)], axis=1)  # boot x samples
        with np.errstate(divide="ignore", invalid="ignore"):
            fac = np.where(tot > 0, tot.mean(axis=1, keepdims=True) / tot, 0.0)
        w_blocks = [wb * fac[:, [j]] for j, wb in enumerate(w_blocks)]
    n = np.concatenate(n_blocks, axis=1)
    s = np.concatenate(s_blocks, axis=1)
    w = np.concatenate(w_blocks, axis=1)
    n_e = sum(wp[e] @ data.samples[e].N for e in eval_samples)
    s_e = sum(wp[e] @ data.samples[e].S for e in eval_samples)
    w_e = wi[family] * (n_e > 0)
    B = n.shape[0]
    Xh = data.X[family]
    acc = np.where(n_e > 0, s_e / np.maximum(n_e, 1), np.nan)
    out = {}
    lins = [np.zeros((B, Xh.shape[0]))]
    for name, cols in models.items():
        ci = [data.measures.index(m) for m in cols]
        coef, conv = fit_logit_batch(np.hstack([ind, Xtr[:, ci]]), n, s, w, n_indicator=k)
        b = coef[:, k:]
        eta = b @ Xh[:, ci].T
        res = dict(train_slope=b[:, 0] if len(cols) == 1 else np.full(B, np.nan), train_converged=conv)
        Xc = np.stack([np.ones_like(eta), eta], axis=2)
        cal, cconv = fit_logit_batch(Xc, n_e, s_e, w_e, n_indicator=1)
        res["calibration_slope"] = cal[:, 1]
        res["calibration_converged"] = cconv
        if ordering:
            res["ordering"] = np.array([wspearman(eta[j], acc[j], w_e[j]) for j in range(B)])
        if heldout and len(cols) == 1:
            ho, _ = fit_logit_batch(np.column_stack([np.ones(Xh.shape[0]), Xh[:, ci[0]]]), n_e, s_e, w_e, n_indicator=1)
            res["heldout_slope"] = ho[:, 1]
        out[name] = res
        lins.append(np.where(np.isfinite(eta), eta, 0.0))
    if prediction:
        ll, br = _boot_prediction(np.stack(lins, axis=1), n_e, s_e, w_e, n_splits_boot, rng)
        for j, name in enumerate(models):
            out[name]["logloss_reduction"] = ll[:, j + 1]
            out[name]["brier_reduction"] = br[:, j + 1]
    return out


# --------------------------------------------------------------------------
# public function
# --------------------------------------------------------------------------
def transfer(trials, items, measures, combined=True, weights="trials", evaluate=None, holdout=None, n_boot=2000,
             n_splits=500, n_splits_boot=10, interval_type="percentile", level=0.95, seed=0, columns=None,
             boot_batch=None, ordering_boot="items", tolerance=(0.80, 1.25)):
    """Leave-one-family-out transfer of item-level difficulty measures.

    For each held-out family, the model ``logit P(correct) = a_sample +
    b * measure`` is fitted to the trials of all other families (binomial,
    one intercept per training sample). The trained slope ``b`` is then
    judged on the held-out family by three criteria:

    ordering
        Spearman correlation, across held-out items, between the
        transferred predictor ``b * measure`` and item accuracy.
    scale
        Calibration slope: the slope of a binomial regression of the
        held-out trials on ``b * measure`` with a free intercept. A value
        of 1 means that the trained effect has the same size in the
        held-out family, 0 means no relation.
    prediction
        Relative reduction in trial-level log loss (and Brier score)
        against an intercept-only model. The slope is fixed at its training
        value; the intercept is fitted on a random half of the held-out
        items and the loss is computed on the other half; the halves then
        swap roles. The result is the mean over ``n_splits`` random splits.

    Parameters
    ----------
    trials : pandas.DataFrame
        Long table with one row per response: ``participant``, ``item``,
        ``sample``, ``correct`` (0/1) and optionally ``family``.
    items : pandas.DataFrame
        One row per item: ``item``, ``family`` and one column per measure.
    measures : sequence of str
        Measure columns of ``items``. Each is analysed on its own.
    combined : bool
        Also fit the model that contains all measures together (row
        ``combined``); ignored with a single measure.
    weights : {"trials", "equal"}
        Weighting of the training samples. ``"trials"`` lets every trial
        count once; ``"equal"`` gives every training sample the same total
        weight.
    evaluate : dict, optional
        ``{family: sample or list of samples}``: the sample(s) of a
        held-out family on which the criteria are computed. By default all
        samples of the family are pooled: their responses per item are
        added, and ordering, scale and prediction refer to this pooled
        population with a single evaluation intercept. The training fit, in
        contrast, has one intercept per sample. Pooled criteria are not
        estimates of a slope that is adjusted for the sample; when samples
        of a family differ in overall accuracy and in which items they
        answered, evaluate them one at a time.
    holdout : sequence, optional
        Families to hold out in turn (default: every family). All other
        families are always used for training.
    n_boot : int
        Two-way bootstrap resamples (participants within each sample and
        items within each family, both with replacement; the training fit
        is repeated in every resample). 0 switches the intervals off.
    n_splits : int
        Random splits of the held-out items for the prediction criterion.
    n_splits_boot : int
        Random splits used inside each bootstrap resample.
    interval_type : {"percentile", "bc", "basic"}
        Percentile interval (default), bias-corrected percentile interval,
        or basic (reflected) interval ``2 * estimate - percentiles``.
        ``result.bootstrap`` keeps the resampled values, so any interval
        can be recomputed without a new run.
    level : float
        Confidence level of the intervals.
    seed : int or numpy.random.Generator
        Seed. With an integer, the item splits use ``default_rng(seed)``
        and the bootstrap an independent stream derived from it.
    columns : dict, optional
        Mapping from the standard column names to the names in the tables.
    boot_batch : int, optional
        Number of bootstrap resamples processed at a time. By default all
        ``n_boot`` resamples are held in memory at once, which needs about
        ``n_boot`` times the number of items times 100 bytes. For data with
        tens of thousands of items, set for example ``boot_batch=50``. The
        resamples are then drawn batch by batch, so the random numbers (not
        the method) differ from a run without batches.
    ordering_boot : {"items", "two-way"}
        Resampling used for the interval of the ordering correlation.
        ``"items"`` (default) resamples the items of every family and keeps
        the participants as they are. ``"two-way"`` also resamples
        participants; this adds response noise to the resampled item
        accuracies, so the resampled correlations lie below the estimate,
        and with a few hundred items or more the percentile interval is
        centred too low and can exclude the estimate itself. The intervals
        of all other statistics always come from the two-way bootstrap.
    tolerance : tuple of two floats, optional
        Range of calibration slopes that counts as "the trained effect size
        holds" (default 0.80 to 1.25). It should be chosen before the
        results are seen. The column ``scale_reading`` compares the interval
        of the calibration slope with this range. ``None`` omits the column.

    Returns
    -------
    TransferResult
        ``result.table`` has one row per held-out family and model with

        - ``family``, ``model``, ``eval_samples``, ``n_items``, ``n_trials``;
        - ``train_slope`` with ``train_slope_lo``, ``train_slope_hi``
          (single-measure models), ``train_converged``;
        - ``ordering`` with ``ordering_lo``, ``ordering_hi``;
        - ``calibration_slope`` with ``calibration_slope_lo``,
          ``calibration_slope_hi``, ``calibration_converged``;
        - ``scale_reading``: ``"within tolerance"`` (the whole interval of
          the calibration slope lies inside ``tolerance``), ``"outside
          tolerance"`` (the whole interval lies outside),
          ``"undetermined"`` (the interval crosses a limit), ``"weak
          training relation"`` (the interval of the training slope includes
          0, so the calibration slope is not interpretable) or ``"not
          applicable"`` (the measure does not vary);
        - ``heldout_slope`` (slope per unit of the measure fitted in the
          held-out family itself) with interval;
        - ``logloss_reduction`` with ``logloss_reduction_lo``,
          ``logloss_reduction_hi`` (bootstrap interval) and
          ``logloss_split_lo``, ``logloss_split_hi`` (2.5th and 97.5th
          percentiles over the random item splits of the data at hand);
        - ``brier_reduction`` with interval;
        - ``logloss``, ``brier``: mean losses of the model;
        - ``boot_failed``: number of resamples in which a fit for this row
          did not converge (these resamples are kept in the intervals).

    Raises
    ------
    ValueError
        If the inputs are malformed or fewer than two families are present.

    Notes
    -----
    The calibration slope is a ratio (held-out slope over training slope).
    When the training slope is close to zero the ratio is unstable; see
    :func:`itemtransfer.diagnose`. In the combined model the calibration
    slope refers to the whole linear predictor.

    The split range of the prediction criterion shows the dependence on the
    random item split only. The bootstrap interval reflects participants
    and items. Its coverage for a design like yours can be checked with
    :func:`itemtransfer.check_intervals`.

    Examples
    --------
    >>> import itemtransfer as it
    >>> trials, items = it.load_example()
    >>> res = it.transfer(trials, items, ["x", "x_null"], n_boot=200, seed=1)
    >>> res.table[["family", "model", "calibration_slope"]]  # doctest: +SKIP
    """
    if weights not in ("trials", "equal"):
        raise ValueError("`weights` must be 'trials' or 'equal'.")
    if interval_type not in ("percentile", "bc", "basic"):
        raise ValueError("`interval_type` must be 'percentile', 'bc' or 'basic'.")
    if ordering_boot not in ("items", "two-way"):
        raise ValueError("`ordering_boot` must be 'items' or 'two-way'.")
    if tolerance is not None:
        tolerance = tuple(float(t) for t in tolerance)
        if len(tolerance) != 2 or not tolerance[0] < tolerance[1]:
            raise ValueError("`tolerance` must be a pair (lower, upper) with lower < upper, or None.")
    data = prepare(trials, items, measures, columns)
    folds = _check_folds(data, holdout)
    ev = _resolve_evaluate(data, evaluate)
    models = _model_columns(data.measures, combined)
    split_rng = as_rng(seed)
    rows, pred_rows, point = [], [], {}
    for f in folds:
        pt, n_e, s_e, keep = _point_fold(data, f, ev[f], models, weights)
        n_k, s_k = n_e[keep], s_e[keep]
        lins = np.vstack([np.zeros(keep.sum())] + [pt[m]["eta"][keep] for m in models])
        if keep.sum() >= 4 and np.all(np.isfinite(lins)):
            ll, br = _prediction(lins, n_k, s_k, _split_masks(int(keep.sum()), n_splits, split_rng))
            red_ll, red_br = _reductions(ll, br)
        else:
            ll = br = red_ll = red_br = np.full((1, len(models) + 1), np.nan)
        for j, (name, cols) in enumerate(models.items()):
            r = pt[name]
            row = dict(family=f, model=name, eval_samples="+".join(str(e) for e in ev[f]), n_items=int(keep.sum()),
                       n_trials=int(n_e.sum()),
                       train_slope=r["b"][0] if len(cols) == 1 else np.nan, train_converged=bool(r["train_converged"]),
                       ordering=r["ordering"], calibration_slope=r["calibration_slope"],
                       calibration_converged=bool(r["calibration_converged"]), heldout_slope=r["heldout_slope"],
                       logloss_reduction=float(np.mean(red_ll[:, j + 1])),
                       logloss_split_lo=float(np.percentile(red_ll[:, j + 1], 2.5)),
                       logloss_split_hi=float(np.percentile(red_ll[:, j + 1], 97.5)),
                       brier_reduction=float(np.mean(red_br[:, j + 1])),
                       logloss=float(np.mean(ll[:, j + 1])), brier=float(np.mean(br[:, j + 1])),
                       logloss_constant=float(np.mean(ll[:, 0])), brier_constant=float(np.mean(br[:, 0])))
            rows.append(row)
            pred_rows.append(pd.DataFrame(dict(family=f, model=name, item=data.items[f][keep],
                                               linear_predictor=r["eta"][keep], n_trials=n_k, n_correct=s_k,
                                               accuracy=s_k / n_k)))
        point[f] = pt
    table = pd.DataFrame(rows)
    stats = ["train_slope", "ordering", "calibration_slope", "heldout_slope", "logloss_reduction", "brier_reduction"]
    for st in stats:
        table[st + "_lo"] = np.nan
        table[st + "_hi"] = np.nan
    table["boot_failed"] = 0
    boot = {}
    if n_boot:
        brng = child_rng(seed, 1)
        parts = {}
        for size in _batch_sizes(n_boot, boot_batch):
            wp, wi = _draw(data, size, brng)
            for f in folds:
                res = _bootstrap_fold(data, f, ev[f], models, weights, wp, wi, brng, n_splits_boot=n_splits_boot,
                                      ordering=ordering_boot == "two-way")
                if ordering_boot == "items":
                    # same item resamples, participants kept as observed
                    w1 = {name: np.ones_like(v) for name, v in wp.items()}
                    oi = _bootstrap_fold(data, f, ev[f], models, weights, w1, wi, brng, ordering=True,
                                         prediction=False, heldout=False)
                    for name in models:
                        res[name]["ordering"] = oi[name]["ordering"]
                for name in models:
                    parts.setdefault((f, name), []).append(res[name])
        for f in folds:
            for name in models:
                r = {k: np.concatenate([p[k] for p in parts[(f, name)]]) for k in parts[(f, name)][0]}
                idx = table.index[(table["family"] == f) & (table["model"] == name)][0]
                frame = {}
                for st in stats:
                    if st in r:
                        frame[st] = r[st]
                        if np.isfinite(table.at[idx, st]):
                            lo, hi = interval(table.at[idx, st], r[st], interval_type, level)
                            table.at[idx, st + "_lo"], table.at[idx, st + "_hi"] = lo, hi
                table.at[idx, "boot_failed"] = int((~(r["train_converged"] & r["calibration_converged"])).sum())
                boot[(f, name)] = pd.DataFrame(frame)
    # measures without variation: nothing can be estimated or judged, so say so instead of reporting numbers
    degenerate = {}
    for f in folds:
        for name, cols in models.items():
            if len(cols) != 1:
                continue
            ci = data.measures.index(cols[0])
            train_var = any(np.ptp(data.X[g][:, ci]) > 0 for g in data.families if g != f)
            held_var = np.ptp(data.X[f][:, ci]) > 0
            if not train_var:
                degenerate[(f, name)] = "constant within every training family"
            elif not held_var:
                degenerate[(f, name)] = "constant in the held-out family"
    for (f, name), why in degenerate.items():
        idx = table.index[(table["family"] == f) & (table["model"] == name)][0]
        blank = stats if "training" in why else ["ordering", "calibration_slope", "heldout_slope",
                                                 "logloss_reduction", "brier_reduction"]
        for st in blank:
            table.loc[idx, [st, st + "_lo", st + "_hi"]] = np.nan
        warnings.warn(f"Measure '{name}' is {why} (held-out family '{f}'); the transfer criteria that need its "
                      "variation are set to missing.", stacklevel=2)
    table["scale_reading"] = None
    if tolerance is not None and n_boot:
        lo, hi = table["calibration_slope_lo"], table["calibration_slope_hi"]
        inside = (lo >= tolerance[0]) & (hi <= tolerance[1])
        outside = (hi < tolerance[0]) | (lo > tolerance[1])
        reading = np.where(inside, "within tolerance", np.where(outside, "outside tolerance", "undetermined"))
        weak = (table["train_slope_lo"] <= 0) & (table["train_slope_hi"] >= 0)
        reading = np.where(weak, "weak training relation", reading)
        table["scale_reading"] = np.where(lo.notna() & hi.notna(), reading, None)
    for (f, name) in degenerate:
        table.loc[(table["family"] == f) & (table["model"] == name), "scale_reading"] = "not applicable"
    order = ["family", "model", "eval_samples", "n_items", "n_trials",
             "train_slope", "train_slope_lo", "train_slope_hi", "train_converged",
             "ordering", "ordering_lo", "ordering_hi",
             "calibration_slope", "calibration_slope_lo", "calibration_slope_hi", "calibration_converged",
             "scale_reading", "heldout_slope", "heldout_slope_lo", "heldout_slope_hi",
             "logloss_reduction", "logloss_reduction_lo", "logloss_reduction_hi", "logloss_split_lo",
             "logloss_split_hi", "brier_reduction", "brier_reduction_lo", "brier_reduction_hi",
             "logloss", "brier", "logloss_constant", "brier_constant", "boot_failed"]
    settings = dict(measures=list(data.measures), combined=bool(combined), weights=weights, evaluate=ev,
                    holdout=folds, n_boot=int(n_boot), n_splits=int(n_splits), n_splits_boot=int(n_splits_boot),
                    interval_type=interval_type, level=level, boot_batch=boot_batch,
                    ordering_boot=ordering_boot, tolerance=tolerance,
                    seed=None if isinstance(seed, np.random.Generator) else seed)
    return TransferResult(table=table[order], predictions=pd.concat(pred_rows, ignore_index=True), bootstrap=boot,
                          settings=settings)
