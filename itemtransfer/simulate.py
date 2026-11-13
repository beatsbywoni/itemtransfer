"""Step 5 of the procedure: simulation of data like the user's own design.

A :class:`Design` describes item families, their samples and the
generating model. :func:`simulate` draws one data set from it,
:func:`check_intervals` repeats this to report how often the bootstrap
interval of the calibration slope covers its large-sample target and how
often a relation is detected, and :func:`design_from_data` builds a design
from an existing data set.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Optional, Sequence, Union

import numpy as np
import pandas as pd

from ._data import Data, Sample, prepare
from ._fit import fit_logit
from ._stats import elogit, percentile_interval
from .transfer import (_bootstrap_fold, _draw, _point_fold, _prediction, _reductions, _resolve_evaluate,
                       _split_masks)

__all__ = ["SampleDesign", "FamilyDesign", "Design", "simulate", "check_intervals", "design_from_data"]


@dataclass
class SampleDesign:
    """One sample of participants responding to items of one family.

    Parameters
    ----------
    name : str
        Sample label.
    n_participants : int
        Number of participants.
    items_per_participant : int, optional
        Number of items each participant responds to, drawn at random from
        the items of the sample. Default: all of them.
    repeats : int
        Number of trials per participant and item.
    intercept : float
        Sample intercept on the logit scale.
    items : int or sequence of int, optional
        Items of the family presented to this sample: the first ``k`` items
        (int) or explicit positions. Default: all items of the family.
    """

    name: str
    n_participants: int
    items_per_participant: Optional[int] = None
    repeats: int = 1
    intercept: float = 0.0
    items: Union[int, Sequence[int], None] = None


@dataclass
class FamilyDesign:
    """One item family.

    Parameters
    ----------
    name : str
        Family label.
    n_items : int
        Number of items.
    measure : tuple
        Distribution of the measure ``x`` over the items of the family:

        - ``("uniform", low, high)``: continuous range;
        - ``("normal", mean, sd)``;
        - ``("levels", [v1, v2, ...], jitter)``: designed levels, items
          divided evenly over the levels, each value perturbed uniformly by
          at most ``jitter`` (``jitter`` may be omitted);
        - ``("values", array)``: fixed values (``n_items`` is then their
          number).
    samples : list of SampleDesign
        The samples that responded to this family.
    slope : float, optional
        True slope of ``x`` in this family. Default: the slope of the
        design.
    """

    name: str
    n_items: int
    measure: tuple = ("uniform", 0.0, 1.0)
    samples: list = field(default_factory=list)
    slope: Optional[float] = None


@dataclass
class Design:
    """Generating model for :func:`simulate`.

    The probability of a correct response of participant ``j`` to item
    ``i`` in sample ``s`` of family ``f`` is ::

        logit p = intercept_s + slope_f * g(x_i) + second_slope * x2_i + d_i + u_j

    with item effects ``d_i ~ N(0, item_sd)`` shared by all samples of the
    family and participant effects ``u_j ~ N(0, participant_sd)``.

    Parameters
    ----------
    families : list of FamilyDesign
        At least two families.
    slope : float
        True slope of the measure ``x`` (families can override it).
    link : {"linear", "log"}
        ``g(x) = x`` or ``g(x) = log(x)``. With ``"log"`` the effect is
        linear in the logarithm of the measure while the analysis uses the
        measure itself, which makes the slope per unit depend on the range.
    participant_sd, item_sd : float
        Standard deviations of the random effects on the logit scale.
    second_measure : float, optional
        If given, a second measure ``x2`` is generated with this
        correlation with ``x`` within each family (standard normal
        scale).
    second_slope : float
        True effect of ``x2``.
    null_measure : bool
        Also generate ``x_null``, a standard normal measure that is
        independent of everything and has no effect.
    """

    families: list
    slope: float = 1.0
    link: str = "linear"
    participant_sd: float = 0.8
    item_sd: float = 0.6
    second_measure: Optional[float] = None
    second_slope: float = 0.0
    null_measure: bool = True

    def measures(self):
        """Names of the measure columns that :func:`simulate` produces."""
        return ["x"] + (["x2"] if self.second_measure is not None else []) + (["x_null"] if self.null_measure else [])


def _check_design(design):
    if not isinstance(design, Design):
        raise TypeError("`design` must be an itemtransfer.Design.")
    if len(design.families) < 2:
        raise ValueError("A design needs at least two item families.")
    if design.link not in ("linear", "log"):
        raise ValueError("`link` must be 'linear' or 'log'.")
    names = [f.name for f in design.families]
    if len(set(names)) != len(names):
        raise ValueError("Family names must be unique.")
    snames = [s.name for f in design.families for s in f.samples]
    if len(set(snames)) != len(snames):
        raise ValueError("Sample names must be unique across families.")
    for f in design.families:
        if not f.samples:
            raise ValueError(f"Family '{f.name}' has no sample.")
        if f.measure[0] not in ("uniform", "normal", "levels", "values"):
            raise ValueError(f"Unknown measure distribution {f.measure[0]!r} in family '{f.name}'.")
    if design.second_measure is not None and not -1 < design.second_measure < 1:
        raise ValueError("`second_measure` must be a correlation strictly between -1 and 1.")


def _draw_measure(fam, rng, scale):
    kind = fam.measure[0]
    n = fam.n_items * scale
    if kind == "uniform":
        return rng.uniform(fam.measure[1], fam.measure[2], n)
    if kind == "normal":
        return rng.normal(fam.measure[1], fam.measure[2], n)
    if kind == "levels":
        values = np.asarray(fam.measure[1], dtype=float)
        jitter = fam.measure[2] if len(fam.measure) > 2 else 0.0
        lev = np.sort(np.arange(n) % len(values))
        return values[lev] + (rng.uniform(-jitter, jitter, n) if jitter else 0.0)
    return np.tile(np.asarray(fam.measure[1], dtype=float), scale)


def _sample_items(smp, n_items, scale):
    """Positions (on the scaled item axis) of the items presented to a sample."""
    if smp.items is None:
        return np.arange(n_items * scale)
    if isinstance(smp.items, (int, np.integer)):
        return np.arange(int(smp.items) * scale)
    idx = np.asarray(smp.items, dtype=int)
    return np.concatenate([idx + k * n_items for k in range(scale)])


def _simulate_data(design, rng, scale_items=1, scale_participants=1):
    """Draw one data set and return it in the internal count representation."""
    measures = design.measures()
    data = Data(families=[f.name for f in design.families], measures=measures, items={}, X={})
    for fam in design.families:
        n_items = fam.n_items if fam.measure[0] != "values" else len(fam.measure[1])
        I = n_items * scale_items
        x = _draw_measure(fam, rng, scale_items)
        if design.link == "log" and np.any(x <= 0):
            raise ValueError(f"link='log' needs a positive measure, but family '{fam.name}' has values <= 0.")
        cols = [x]
        lin = (design.slope if fam.slope is None else fam.slope) * (np.log(x) if design.link == "log" else x)
        if design.second_measure is not None:
            sd = x.std()
            z = (x - x.mean()) / sd if sd > 0 else np.zeros(I)
            r = design.second_measure
            x2 = r * z + np.sqrt(1 - r ** 2) * rng.normal(0, 1, I)
            cols.append(x2)
            lin = lin + design.second_slope * x2
        if design.null_measure:
            cols.append(rng.normal(0, 1, I))
        delta = rng.normal(0, design.item_sd, I)
        width = max(4, len(str(I - 1)))
        data.items[fam.name] = np.array([f"{fam.name}_{i:0{width}d}" for i in range(I)])
        data.X[fam.name] = np.column_stack(cols)
        data.family_samples[fam.name] = []
        for smp in fam.samples:
            idx = _sample_items(smp, n_items, scale_items)
            P = smp.n_participants * scale_participants
            u = rng.normal(0, design.participant_sd, P)
            N = np.zeros((P, I))
            if smp.items_per_participant is None or smp.items_per_participant * scale_items >= len(idx):
                N[:, idx] = smp.repeats
            else:
                k = smp.items_per_participant * scale_items
                pick = np.argsort(rng.random((P, len(idx))), axis=1)[:, :k]
                np.put_along_axis(N, idx[pick], smp.repeats, axis=1)
            eta = smp.intercept + lin[None, :] + delta[None, :] + u[:, None]
            S = rng.binomial(N.astype(int), 1 / (1 + np.exp(-eta))).astype(float)
            pw = max(3, len(str(P - 1)))
            data.samples[smp.name] = Sample(name=smp.name, family=fam.name,
                                            participants=np.array([f"{smp.name}_p{j:0{pw}d}" for j in range(P)]),
                                            N=N, S=S)
            data.family_samples[fam.name].append(smp.name)
    return data


def _to_frames(data):
    """Convert the internal representation to the long trials table and the items table."""
    frames = []
    for name, smp in data.samples.items():
        pj, ii = np.nonzero(smp.N)
        n = smp.N[pj, ii].astype(int)
        s = smp.S[pj, ii].astype(int)
        rep_p, rep_i = np.repeat(pj, n), np.repeat(ii, n)
        within = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
        correct = (within < np.repeat(s, n)).astype(int)
        frames.append(pd.DataFrame(dict(participant=smp.participants[rep_p], item=data.items[smp.family][rep_i],
                                        family=smp.family, sample=name, correct=correct)))
    trials = pd.concat(frames, ignore_index=True)
    items = pd.concat([pd.DataFrame(data.X[f], columns=data.measures).assign(item=data.items[f], family=f)
                       for f in data.families], ignore_index=True)
    return trials, items[["item", "family"] + data.measures]


def simulate(design, seed=0):
    """Draw one data set from a design.

    Parameters
    ----------
    design : Design
        The generating model.
    seed : int or numpy.random.Generator
        Seed.

    Returns
    -------
    trials : pandas.DataFrame
        Columns ``participant``, ``item``, ``family``, ``sample``,
        ``correct``.
    items : pandas.DataFrame
        Columns ``item``, ``family``, ``x`` and, depending on the design,
        ``x2`` and ``x_null``.

    Notes
    -----
    Within a participant-by-item cell with several trials, the correct
    responses are listed first; trial order carries no information.

    Examples
    --------
    >>> import itemtransfer as it
    >>> design = it.Design(
    ...     families=[
    ...         it.FamilyDesign("A", 60, ("uniform", 0.0, 1.0), [it.SampleDesign("A1", 30)]),
    ...         it.FamilyDesign("B", 60, ("levels", [0.2, 0.8], 0.02), [it.SampleDesign("B1", 30)]),
    ...     ],
    ...     slope=-2.0,
    ... )
    >>> trials, items = it.simulate(design, seed=1)
    """
    _check_design(design)
    rng = seed if isinstance(seed, np.random.Generator) else np.random.default_rng(seed)
    return _to_frames(_simulate_data(design, rng))


def _one_simulation(args):
    design, seed_seq, measures, n_boot, weights, evaluate, prediction, level, n_splits, n_splits_boot = args
    rng = np.random.default_rng(seed_seq)
    data = _simulate_data(design, rng)
    ev = _resolve_evaluate(data, evaluate)
    models = {m: [m] for m in measures}
    wp, wi = _draw(data, n_boot, rng)
    rows = []
    for f in data.families:
        pt, n_e, s_e, keep = _point_fold(data, f, ev[f], models, weights)
        bt = _bootstrap_fold(data, f, ev[f], models, weights, wp, wi, rng, ordering=False, prediction=prediction,
                             n_splits_boot=n_splits_boot, heldout=False)
        red = None
        if prediction:
            lins = np.vstack([np.zeros(keep.sum())] + [pt[m]["eta"][keep] for m in measures])
            red, _ = _reductions(*_prediction(lins, n_e[keep], s_e[keep], _split_masks(int(keep.sum()), n_splits, rng)))
            red = red.mean(axis=0)
        for j, m in enumerate(measures):
            lo, hi = percentile_interval(bt[m]["calibration_slope"], level)
            tlo, thi = percentile_interval(bt[m]["train_slope"], level)
            row = dict(family=f, measure=m, estimate=pt[m]["calibration_slope"], lo=lo, hi=hi,
                       train_slope=pt[m]["b"][0], train_lo=tlo, train_hi=thi)
            if prediction:
                plo, phi = percentile_interval(bt[m]["logloss_reduction"], level)
                row.update(logloss=red[j + 1], logloss_lo=plo, logloss_hi=phi)
            rows.append(row)
    return rows


def _targets(design, measures, weights, evaluate, scale, reps, seed_seq, prediction):
    rng = np.random.default_rng(seed_seq)
    acc = {}
    for _ in range(reps):
        data = _simulate_data(design, rng, scale_items=scale[0], scale_participants=scale[1])
        ev = _resolve_evaluate(data, evaluate)
        for f in data.families:
            pt, n_e, s_e, keep = _point_fold(data, f, ev[f], {m: [m] for m in measures}, weights)
            if prediction:
                lins = np.vstack([np.zeros(keep.sum())] + [pt[m]["eta"][keep] for m in measures])
                red, _ = _reductions(*_prediction(lins, n_e[keep], s_e[keep], _split_masks(int(keep.sum()), 20, rng)))
                red = red.mean(axis=0)
            for j, m in enumerate(measures):
                acc.setdefault((f, m), []).append(
                    (pt[m]["calibration_slope"], pt[m]["b"][0], red[j + 1] if prediction else np.nan))
    return {k: np.mean(np.array(v), axis=0) for k, v in acc.items()}


def check_intervals(design, n_sim=200, n_boot=200, weights="trials", evaluate=None, prediction=False, level=0.95,
                    target_scale=(25, 10), target_reps=10, n_splits=100, n_splits_boot=10, n_jobs=1, seed=0):
    """Coverage of the calibration-slope interval and detection rates for a design.

    ``n_sim`` data sets are drawn from the design. In each, the
    leave-one-family-out calibration slope of every measure is computed
    with its two-way bootstrap interval, exactly as in
    :func:`itemtransfer.transfer`. The intervals are compared with the
    large-sample value of the calibration slope, which is obtained
    numerically from data sets with many more items and participants.

    Parameters
    ----------
    design : Design
        The generating model, written by hand or built with
        :func:`design_from_data`.
    n_sim : int
        Number of simulated data sets.
    n_boot : int
        Bootstrap resamples per data set.
    weights, evaluate
        As in :func:`itemtransfer.transfer`.
    prediction : bool
        Also check the bootstrap interval of the log-loss reduction
        (slower).
    level : float
        Confidence level.
    target_scale : tuple of int
        Factors by which the number of items and of participants are
        multiplied for the large-sample target.
    target_reps : int
        Number of large data sets averaged for the target.
    n_splits, n_splits_boot : int
        Item splits for the prediction criterion (point estimate, and
        inside the bootstrap).
    n_jobs : int
        Number of worker processes. Results do not depend on it.
    seed : int
        Seed.

    Returns
    -------
    pandas.DataFrame
        One row per held-out family and measure with

        - ``target``: large-sample calibration slope (not defined for the
          ``x_null`` measure, whose training slope is 0 in the limit);
        - ``mean_estimate``, ``median_estimate``, ``sd_estimate``;
        - ``coverage`` of the target with its Monte Carlo standard error
          ``coverage_se``;
        - ``mean_width`` and ``median_width`` of the interval;
        - ``rate_excludes_0``: share of data sets in which the interval
          excludes 0 (detection rate for a measure with an effect, false
          detection rate for the null measure) with ``rate_excludes_0_se``;
        - ``rate_includes_1``: share of intervals that include 1;
        - ``rate_weak_training``: share of data sets in which the interval
          of the training slope includes 0;
        - with ``prediction=True``: ``logloss_target``, ``logloss_mean``,
          ``logloss_coverage`` and ``logloss_rate_above_0`` (interval
          entirely above 0).

    Notes
    -----
    The target is the limit for the simulated design with the same
    distribution of the measure, not the value 1: when true slopes differ
    between families, or when the link is not linear, the large-sample
    calibration slope differs from 1 and the table shows by how much.

    Coverage far below the nominal level means that labels based on the
    interval should not be trusted for a design of this size.

    Examples
    --------
    >>> import itemtransfer as it
    >>> trials, items = it.load_example()
    >>> design = it.design_from_data(trials, items, "x")
    >>> it.check_intervals(design, n_sim=50, n_boot=100, seed=1)  # doctest: +SKIP
    """
    _check_design(design)
    measures = design.measures()
    ss = np.random.SeedSequence(seed)
    children = ss.spawn(n_sim + 1)
    tg = _targets(design, measures, weights, evaluate, target_scale, target_reps, children[0], prediction)
    jobs = [(design, c, measures, n_boot, weights, evaluate, prediction, level, n_splits, n_splits_boot)
            for c in children[1:]]
    if n_jobs and n_jobs > 1:
        with ProcessPoolExecutor(max_workers=n_jobs) as ex:
            results = list(ex.map(_one_simulation, jobs, chunksize=max(1, n_sim // (4 * n_jobs))))
    else:
        results = [_one_simulation(j) for j in jobs]
    sims = pd.DataFrame([r for res in results for r in res])
    rows = []

    def se(p):
        return float(np.sqrt(max(p * (1 - p), 0.0) / n_sim))

    for (f, m), g in sims.groupby(["family", "measure"], sort=False):
        t_slope, t_train, t_ll = tg[(f, m)]
        is_null = m == "x_null"
        target = np.nan if is_null else float(t_slope)
        excl = float(np.mean((g["lo"] > 0) | (g["hi"] < 0)))
        row = dict(family=f, measure=m, target=target, train_slope_target=0.0 if is_null else float(t_train),
                   mean_estimate=float(g["estimate"].mean()), median_estimate=float(g["estimate"].median()),
                   sd_estimate=float(g["estimate"].std(ddof=1)) if len(g) > 1 else np.nan,
                   coverage=np.nan, coverage_se=np.nan,
                   mean_width=float((g["hi"] - g["lo"]).mean()), median_width=float((g["hi"] - g["lo"]).median()),
                   rate_excludes_0=excl, rate_excludes_0_se=se(excl),
                   rate_includes_1=float(np.mean((g["lo"] <= 1) & (g["hi"] >= 1))),
                   rate_weak_training=float(np.mean((g["train_lo"] <= 0) & (g["train_hi"] >= 0))),
                   n_sim=n_sim, n_boot=n_boot)
        if not is_null:
            cov = float(np.mean((g["lo"] <= target) & (target <= g["hi"])))
            row.update(coverage=cov, coverage_se=se(cov))
        if prediction:
            cov = float(np.mean((g["logloss_lo"] <= t_ll) & (t_ll <= g["logloss_hi"])))
            row.update(logloss_target=float(t_ll), logloss_mean=float(g["logloss"].mean()), logloss_coverage=cov,
                       logloss_coverage_se=se(cov), logloss_rate_above_0=float(np.mean(g["logloss_lo"] > 0)))
        rows.append(row)
    return pd.DataFrame(rows)


def _design_stats(data, common_slope, link):
    """Statistics of a data set that a simulation design should reproduce (first measure column)."""

    def g(x):
        if link == "log":
            if np.any(x <= 0):
                raise ValueError("link='log' needs a positive measure.")
            return np.log(x)
        return x

    names = list(data.samples)
    blocks, n, s = [], [], []
    for j, name in enumerate(names):
        smp = data.samples[name]
        nn, ss_ = smp.counts()
        ind = np.zeros((len(nn), len(names)))
        ind[:, j] = 1
        blocks.append(np.column_stack([ind, g(data.X[smp.family][:, 0])]))
        n.append(nn)
        s.append(ss_)
    fit = fit_logit(np.vstack(blocks), np.concatenate(n), np.concatenate(s))
    common = float(fit.coef[-1])
    intercepts = {name: float(a) for name, a in zip(names, fit.coef[:-1])}
    fam_slopes = {}
    p_var, i_var = [], []
    for f in data.families:
        fn = data.family_samples[f]
        Xf = np.vstack([np.column_stack([np.eye(len(fn))[[k] * data.n_items(f)], g(data.X[f][:, 0])])
                        for k in range(len(fn))])
        nf = np.concatenate([data.samples[k].counts()[0] for k in fn])
        sf = np.concatenate([data.samples[k].counts()[1] for k in fn])
        ff = fit_logit(Xf, nf, sf)
        fam_slopes[f] = float(ff.coef[-1]) if np.isfinite(ff.coef[-1]) else common
        b = common if common_slope else fam_slopes[f]
        for k, name in enumerate(fn):
            smp = data.samples[name]
            if not common_slope and np.isfinite(ff.coef[k]):
                intercepts[name] = float(ff.coef[k])
            pn, ps = smp.N.sum(axis=1), smp.S.sum(axis=1)
            ok = pn > 0
            p_var.append((elogit(pn[ok], ps[ok]).var(ddof=1) if ok.sum() > 1 else 0.0, ok.sum()))
            nn, ss_ = smp.counts()
            ok = nn > 0
            res = elogit(nn[ok], ss_[ok]) - (intercepts[name] + b * g(data.X[f][ok, 0]))
            i_var.append((res.var(ddof=1) if ok.sum() > 1 else 0.0, ok.sum()))

    def pooled(v):
        w = np.array([k for _, k in v], dtype=float)
        return float(np.sum(np.array([a for a, _ in v]) * w) / w.sum())

    return dict(slope=common, fam_slopes=fam_slopes, intercepts=intercepts, p_var=pooled(p_var), i_var=pooled(i_var))


def design_from_data(trials, items, measure, common_slope=True, second_measure=None, null_measure=True, link="linear",
                     calibrate=5, n_calibration=20, seed=0, columns=None):
    """Build a simulation design that resembles an existing data set.

    Parameters
    ----------
    trials, items
        As in :func:`itemtransfer.transfer`.
    measure : str
        The measure that plays the role of ``x`` in the design. Its
        observed values are kept for every family.
    common_slope : bool
        If True (default), the same slope (estimated on all families
        together) generates all families, so the design represents
        successful transfer. If False, each family gets the slope estimated
        in that family.
    second_measure : float, optional
        Correlation of an additional simulated measure ``x2`` with ``x``.
    null_measure : bool
        Add a measure without effect.
    link : {"linear", "log"}
        Link of the generating model. With ``"log"`` the slopes are
        estimated for ``log(measure)``.
    calibrate : int
        Number of calibration rounds (0 switches calibration off). In each
        round, ``n_calibration`` data sets are simulated from the current
        design and its parameters are adjusted so that the simulated data
        reproduce, on average, the observed slope(s), sample intercepts,
        spread of participant accuracies and spread of item accuracies
        around the fitted relation.
    n_calibration : int
        Simulated data sets per calibration round.
    seed : int
        Seed of the calibration.
    columns : dict, optional
        Mapping from the standard column names to the names in the tables.

    Returns
    -------
    Design
        Families with the observed measure values, samples with the
        observed numbers of participants, items per participant and trials
        per cell, and calibrated intercepts, slope(s) and standard
        deviations of participant and item effects.

    Notes
    -----
    The slope and intercepts estimated by :func:`itemtransfer.transfer`
    describe accuracy averaged over participants and items, whereas the
    generating model is written for one participant and one item, where
    effects are larger. The calibration corrects for this difference by
    matching summary statistics. The result is a design of the right size
    and shape, not a fitted model of the data. Inspect and edit the
    returned object where you know better.
    """
    data = prepare(trials, items, [measure], columns)
    if link not in ("linear", "log"):
        raise ValueError("`link` must be 'linear' or 'log'.")
    obs = _design_stats(data, common_slope, link)
    families = []
    for f in data.families:
        samples = []
        for name in data.family_samples[f]:
            smp = data.samples[name]
            seen = np.flatnonzero(smp.N.sum(axis=0) > 0)
            per_p = (smp.N > 0).sum(axis=1)
            k = int(np.median(per_p))
            rep = int(max(1, round(float(np.median(smp.N[smp.N > 0])))))
            samples.append(SampleDesign(name=str(name), n_participants=smp.n_participants,
                                        items_per_participant=None if k >= len(seen) else k, repeats=rep,
                                        intercept=obs["intercepts"][name],
                                        items=None if len(seen) == data.n_items(f) else [int(i) for i in seen]))
        families.append(FamilyDesign(name=str(f), n_items=data.n_items(f), measure=("values", data.X[f][:, 0].copy()),
                                     samples=samples, slope=None if common_slope else obs["fam_slopes"][f]))
    design = Design(families=families, slope=obs["slope"], link=link, participant_sd=float(np.sqrt(obs["p_var"])),
                    item_sd=float(np.sqrt(obs["i_var"])), second_measure=None, null_measure=False)
    rng = np.random.default_rng(seed)
    orig = {str(k): k for k in data.samples}
    forig = {str(k): k for k in data.families}
    for _ in range(int(calibrate)):
        sims = [_design_stats(_simulate_data(design, rng), common_slope, link) for _ in range(n_calibration)]
        mean = lambda key: float(np.mean([x[key] for x in sims]))  # noqa: E731

        def ratio(o, m):
            return float(np.clip(o / m, 0.5, 2.0)) if (m != 0 and o / m > 0) else 1.0

        design.participant_sd *= np.sqrt(ratio(obs["p_var"], mean("p_var")))
        design.item_sd *= np.sqrt(ratio(obs["i_var"], mean("i_var")))
        if common_slope:
            design.slope *= ratio(obs["slope"], mean("slope"))
        for fam in design.families:
            if not common_slope:
                m = float(np.mean([x["fam_slopes"][fam.name] for x in sims]))
                fam.slope *= ratio(obs["fam_slopes"][forig[fam.name]], m)
            for smp in fam.samples:
                m = float(np.mean([x["intercepts"][smp.name] for x in sims]))
                smp.intercept += obs["intercepts"][orig[smp.name]] - m
    design.second_measure = second_measure
    design.null_measure = null_measure
    return design
