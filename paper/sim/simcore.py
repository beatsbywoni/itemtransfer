"""Shared helpers of the design-agnostic simulation study.

The analysis of every simulated data set is done by the package
``itemtransfer`` (the functions behind ``transfer``, ``diagnose``,
``reliability`` and ``check_intervals``). This module adds what the
package's ``Design`` does not offer and what the study needs:

* a generator with family-specific generating relations (saturating and
  step relations, measures whose correlation with the true driver of
  difficulty differs between families);
* large-sample targets, computed from very large item sets with the
  participant distribution integrated out by Gauss-Hermite quadrature;
* a resume-safe runner that writes one tidy CSV file per cell and chunk.

Vocabulary: item, item family, sample, measure, held-out family, training
families (see the simulation report).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from dataclasses import dataclass, field, replace  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import itemtransfer as it  # noqa: E402
from itemtransfer._data import Data, Sample, restrict  # noqa: E402
from itemtransfer._fit import fit_logit  # noqa: E402
from itemtransfer._stats import pearson, percentile_interval, spearman  # noqa: E402
from itemtransfer.diagnose import detect_levels  # noqa: E402
from itemtransfer.reliability import _half_masks, _split_half  # noqa: E402
from itemtransfer.transfer import (_bootstrap_fold, _draw, _point_fold, _prediction, _reductions,  # noqa: E402
                                   _split_masks)

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
FIGURES = HERE / "figures"
N_CORES = os.cpu_count() or 1

if Path(it.__file__).resolve().parent.parent.name != "itemtransfer":  # pragma: no cover
    raise RuntimeError("itemtransfer was imported from an unexpected place: " + it.__file__)


# --------------------------------------------------------------------------
# generating model
# --------------------------------------------------------------------------
@dataclass
class Fam:
    """One item family with one sample.

    logit P(correct) = intercept + slope * g(t_i) + d_i + u_j, with the driver
    of difficulty ``t`` drawn from ``driver``, item residuals d ~ N(0, item_sd)
    and participant effects u ~ N(0, part_sd).

    driver : ("normal", mean, sd) | ("uniform", low, high) | ("levels", values, jitter)
    effect : ("linear",) | ("log",) | ("sat", c) [g = 1 - exp(-t / c)] | ("step", threshold) [g = sign(t - thr)]
    measures : name -> ("driver",)            the driver itself
                       ("corr", r)            standard normal measure with correlation r with the driver
                       ("null",)              independent standard normal measure
                       ("log",)               log of the driver
    """

    name: str
    n_items: int = 48
    n_part: int = 40
    slope: float = -0.5
    intercept: float = 1.0
    driver: tuple = ("normal", 0.0, 1.0)
    effect: tuple = ("linear",)
    measures: dict = field(default_factory=lambda: {"x": ("driver",)})
    item_sd: float = 0.5
    part_sd: float = 0.8


def families(n_fam=4, held=None, **common):
    """``n_fam`` exchangeable families H, T1, T2, ...; ``held`` overrides fields of the held-out family H."""
    fams = [Fam(name="H", **common)] + [Fam(name=f"T{k}", **common) for k in range(1, n_fam)]
    if held:
        fams[0] = replace(fams[0], **held)
    return fams


def _driver(fam, n, rng):
    kind = fam.driver[0]
    if kind == "normal":
        return rng.normal(fam.driver[1], fam.driver[2], n)
    if kind == "uniform":
        return rng.uniform(fam.driver[1], fam.driver[2], n)
    if kind == "levels":
        values = np.asarray(fam.driver[1], dtype=float)
        jitter = fam.driver[2] if len(fam.driver) > 2 else 0.0
        lev = np.sort(np.arange(n) % len(values))
        return values[lev] + (rng.uniform(-jitter, jitter, n) if jitter else 0.0)
    raise ValueError(kind)


def _effect(fam, t):
    kind = fam.effect[0]
    if kind == "linear":
        return t
    if kind == "log":
        return np.log(t)
    if kind == "sat":
        return 1.0 - np.exp(-t / fam.effect[1])
    if kind == "step":
        return np.sign(t - fam.effect[1])
    raise ValueError(kind)


def _items(fam, n, rng):
    """Driver, measure matrix and item-level logit (without participant effect) of ``n`` items."""
    t = _driver(fam, n, rng)
    sd = t.std()
    z = (t - t.mean()) / sd if sd > 0 else np.zeros(n)
    cols = []
    for spec in fam.measures.values():
        if spec[0] == "driver":
            cols.append(t)
        elif spec[0] == "corr":
            cols.append(spec[1] * z + np.sqrt(1 - spec[1] ** 2) * rng.normal(0, 1, n))
        elif spec[0] == "null":
            cols.append(rng.normal(0, 1, n))
        elif spec[0] == "log":
            cols.append(np.log(t))
        else:
            raise ValueError(spec[0])
    eta = fam.intercept + fam.slope * _effect(fam, t) + rng.normal(0, fam.item_sd, n)
    return t, np.column_stack(cols), eta


def generate(fams, rng, return_truth=False):
    """Draw one data set in the count representation of the package."""
    names = list(fams[0].measures)
    data = Data(families=[f.name for f in fams], measures=names, items={}, X={})
    truth = {}
    for fam in fams:
        if list(fam.measures) != names:
            raise ValueError("All families need the same measures.")
        t, X, eta = _items(fam, fam.n_items, rng)
        u = rng.normal(0, fam.part_sd, fam.n_part)
        N = np.ones((fam.n_part, fam.n_items))
        S = rng.binomial(1, 1 / (1 + np.exp(-(eta[None, :] + u[:, None])))).astype(float)
        data.items[fam.name] = np.array([f"{fam.name}_{i:04d}" for i in range(fam.n_items)])
        data.X[fam.name] = X
        sname = fam.name + "1"
        data.samples[sname] = Sample(name=sname, family=fam.name,
                                     participants=np.array([f"{sname}_p{j:03d}" for j in range(fam.n_part)]), N=N, S=S)
        data.family_samples[fam.name] = [sname]
        truth[fam.name] = dict(t=t, eta=eta, p=marginal_p(eta, fam.part_sd))
    return (data, truth) if return_truth else data


_GH = np.polynomial.hermite_e.hermegauss(61)


def marginal_p(eta, part_sd):
    """P(correct) of each item averaged over participants (Gauss-Hermite quadrature)."""
    if part_sd == 0:
        return 1 / (1 + np.exp(-eta))
    nodes, w = _GH
    w = w / w.sum()
    out = np.zeros_like(eta)
    for x, ww in zip(nodes, w):
        out += ww / (1 + np.exp(-(eta + part_sd * x)))
    return out


def expected_data(fams, rng, scale):
    """Data set with ``scale`` times the items and infinitely many participants (expected counts)."""
    names = list(fams[0].measures)
    data = Data(families=[f.name for f in fams], measures=names, items={}, X={})
    for fam in fams:
        n = fam.n_items * scale
        _, X, eta = _items(fam, n, rng)
        p = marginal_p(eta, fam.part_sd)
        data.items[fam.name] = np.arange(n)
        data.X[fam.name] = X
        sname = fam.name + "1"
        data.samples[sname] = Sample(name=sname, family=fam.name, participants=np.array(["all"]),
                                     N=np.full((1, n), float(fam.n_part)), S=(fam.n_part * p)[None, :])
        data.family_samples[fam.name] = [sname]
    return data


def large_sample_targets(fams, measures=None, held="H", items_total=120_000, reps=3, seed=0, limits=None):
    """Large-sample value of every statistic for the held-out family.

    Items: ``items_total`` per family (rounded to a multiple of the design);
    participants: integrated out. Returns the mean over ``reps`` independent
    item sets and the standard deviation between them (target noise).
    ``limits = {measure: (low, high)}`` restricts all families to a range of
    one measure before the analysis (common-range remedy).
    """
    rng = np.random.default_rng([987, seed])
    measures = measures or list(fams[0].measures)
    rows = []
    for _ in range(reps):
        scale = max(1, items_total // max(f.n_items for f in fams))
        data = expected_data(fams, rng, scale)
        if limits:
            data = restrict_range(data, limits)
        pt, n_e, s_e, keep = _point_fold(data, held, data.family_samples[held], {m: [m] for m in measures}, "trials")
        lins = np.vstack([np.zeros(keep.sum())] + [pt[m]["eta"][keep] for m in measures])
        red, redb = _reductions(*_prediction(lins, n_e[keep], s_e[keep], _split_masks(int(keep.sum()), 4, rng)))
        for j, m in enumerate(measures):
            rows.append(dict(measure=m, train_slope=pt[m]["b"][0], heldout_slope=pt[m]["heldout_slope"],
                             ordering=pt[m]["ordering"], calibration_slope=pt[m]["calibration_slope"],
                             logloss_reduction=red[:, j + 1].mean(), brier_reduction=redb[:, j + 1].mean()))
    df = pd.DataFrame(rows)
    mean = df.groupby("measure", sort=False).mean()
    sd = df.groupby("measure", sort=False).std(ddof=1).add_suffix("_sd")
    return mean.join(sd).reset_index()


def restrict_range(data, limits):
    """Keep only items inside ``limits[measure] = (low, high)`` in every family."""
    keep = {}
    for f in data.families:
        m = np.ones(data.n_items(f), dtype=bool)
        for name, (lo, hi) in limits.items():
            x = data.X[f][:, data.measures.index(name)]
            m &= (x >= lo) & (x <= hi)
        keep[f] = m
    return restrict(data, keep)


# --------------------------------------------------------------------------
# analysis of one held-out family (the code path of itemtransfer.transfer)
# --------------------------------------------------------------------------
def analyse(data, measures, rng, held="H", n_boot=500, n_splits=100, n_splits_boot=10, boot_ordering=True,
            participants_only=False, items_only=False, prediction=True, level=0.95, prefix=""):
    """Three criteria for the held-out family with two-way bootstrap intervals.

    Returns one dict per measure. With ``participants_only=True`` the
    intervals of a bootstrap that resamples participants but keeps the items
    fixed are added (suffix ``_po``); with ``items_only=True`` those of a
    bootstrap that resamples items but keeps the participants fixed (suffix
    ``_io``). Both are comparisons made for the study, not part of the
    procedure.
    """
    models = {m: [m] for m in measures}
    ev = data.family_samples[held]
    pt, n_e, s_e, keep = _point_fold(data, held, ev, models, "trials")
    k = int(keep.sum())
    lins = np.vstack([np.zeros(k)] + [pt[m]["eta"][keep] for m in measures])
    if prediction and np.all(np.isfinite(lins)):
        red, redb = _reductions(*_prediction(lins, n_e[keep], s_e[keep], _split_masks(k, n_splits, rng)))
        red, redb = red.mean(axis=0), redb.mean(axis=0)
    else:
        red = redb = np.full(len(measures) + 1, np.nan)
    rows = {}
    for j, m in enumerate(measures):
        r = pt[m]
        rows[m] = {"measure": prefix + m, "train_slope": r["b"][0], "heldout_slope": r["heldout_slope"],
                   "ordering": r["ordering"], "calibration_slope": r["calibration_slope"],
                   "logloss_reduction": red[j + 1], "brier_reduction": redb[j + 1],
                   "converged": bool(r["train_converged"] and r["calibration_converged"])}
    if n_boot:
        kinds = [""] + (["_po"] if participants_only else []) + (["_io"] if items_only else [])
        for suffix in kinds:
            wp, wi = _draw(data, n_boot, rng, two_way=(suffix != "_po"))
            if suffix == "_io":
                wp = {name: np.ones_like(w) for name, w in wp.items()}
            bt = _bootstrap_fold(data, held, ev, models, "trials", wp, wi, rng, ordering=boot_ordering,
                                 prediction=prediction, n_splits_boot=n_splits_boot, heldout=False)
            for m in measures:
                stats = ["train_slope", "calibration_slope"] + (["ordering"] if boot_ordering else []) + \
                        (["logloss_reduction"] if prediction else [])
                for st in stats:
                    lo, hi = percentile_interval(bt[m][st], level)
                    rows[m][f"{st}_lo{suffix}"], rows[m][f"{st}_hi{suffix}"] = lo, hi
                rows[m][f"boot_failed{suffix}"] = int((~(bt[m]["train_converged"] & bt[m]["calibration_converged"])).sum())
    return [rows[m] for m in measures]


def training_fit(data, measure, held="H"):
    """Deviance explained by a measure within the training families.

    ``pooled``: sample intercepts plus one common slope (the training model of
    the procedure). ``separate``: one intercept and one slope per family (fit
    within each family, deviances added). Both relative to the model with
    sample intercepts only.
    """
    j = data.measures.index(measure)
    d0 = d_sep = 0.0
    Xs, ns, ss, inds = [], [], [], []
    train = [f for f in data.families if f != held]
    for k, f in enumerate(train):
        n, s = data.samples[data.family_samples[f][0]].counts()
        x = data.X[f][:, j]
        f0 = fit_logit(np.ones((len(n), 1)), n, s)
        f1 = fit_logit(np.column_stack([np.ones(len(n)), x]), n, s)
        d0 += f0.deviance
        d_sep += f1.deviance
        ind = np.zeros((len(n), len(train)))
        ind[:, k] = 1
        Xs.append(np.column_stack([ind, x]))
        ns.append(n)
        ss.append(s)
    fp = fit_logit(np.vstack(Xs), np.concatenate(ns), np.concatenate(ss))
    return dict(dev_pooled=(d0 - fp.deviance) / d0, dev_separate=(d0 - d_sep) / d0)


def level_baseline(data, measure, rng, held="H", n_splits=100, levels=None):
    """Level-indicator baseline of the package's ``diagnose`` for one measure in the held-out family.

    ``levels`` can be supplied (for example a median split of a continuous
    measure); otherwise ``itemtransfer.detect_levels`` is used.
    """
    ev = data.family_samples[held]
    pt, n_e, s_e, keep = _point_fold(data, held, ev, {measure: [measure]}, "trials")
    x = data.X[held][keep, data.measures.index(measure)]
    n_k, s_k = n_e[keep], s_e[keep]
    acc = s_k / n_k
    detected = True
    if levels is None:
        levels, info = detect_levels(x)
        if levels is None:
            return dict(n_levels=0)
    else:
        detected = False
    K = int(levels.max()) + 1
    lins = np.vstack([np.zeros(len(x)), pt[measure]["eta"][keep]])
    red, _ = _reductions(*_prediction(lins, n_k, s_k, _split_masks(len(x), n_splits, rng), levels=levels))
    b = pt[measure]["b"][0]
    within = [spearman(np.sign(b) * x[levels == k], acc[levels == k]) for k in range(K)]
    level_mean = np.array([acc[levels == k].mean() for k in range(K)])
    return dict(n_levels=K, detected=detected, ordering_measure=pt[measure]["ordering"],
                ordering_levels=spearman(np.sign(b) * levels, acc), level_accuracy_r=pearson(level_mean[levels], acc),
                logloss_measure=float(red[:, 1].mean()), logloss_levels=float(red[:, 2].mean()),
                ordering_within=float(np.nanmean(within)))


def split_half_reliability(data, held="H", n_splits=200, rng=None):
    """Median Spearman-Brown corrected split-half reliability of item difficulty (logit and rank scale)."""
    smp = data.samples[data.family_samples[held][0]]
    sb, _ = _split_half(smp.N, smp.S, _half_masks(smp.n_participants, n_splits, rng))
    return float(np.nanmedian(sb[:, 0])), float(np.nanmedian(sb[:, 1]))


# --------------------------------------------------------------------------
# runner: cells x chunks, resume-safe
# --------------------------------------------------------------------------
def _run_chunk(args):
    study, func, cell_id, cell, chunk, n_rep, study_seed, out = args
    path = out / f"{cell_id}__{chunk:03d}.csv"
    if path.exists():
        return 0.0
    t0 = time.time()
    rows = []
    for r in range(n_rep):
        rep = chunk * 1000 + r
        rng = np.random.default_rng([study_seed, cell["seed"], rep])
        for row in func(cell, rng):
            rows.append(dict(cell=cell_id, rep=rep, **row))
    tmp = path.with_suffix(".tmp")
    pd.DataFrame(rows).to_csv(tmp, index=False)
    os.replace(tmp, path)
    return time.time() - t0


def run_study(study, func, cells, n_rep, chunk_size, study_seed, n_jobs=None, max_chunks=None):
    """Run ``func(cell, rng) -> list of row dicts`` for every cell, ``n_rep`` times, in chunks.

    ``cells``: dict cell_id -> dict with at least ``seed`` (int) and
    optionally ``n_rep`` (overrides the default). Chunks are written to
    results/raw/<study>/ and skipped when present, so an interrupted run can
    be restarted. Chunk c of every cell is run before chunk c + 1 of any.
    """
    out = RESULTS / "raw" / study
    out.mkdir(parents=True, exist_ok=True)
    tasks = []
    n_chunks = {cid: -(-int(c.get("n_rep", n_rep)) // chunk_size) for cid, c in cells.items()}
    for chunk in range(max(n_chunks.values())):
        if max_chunks is not None and chunk >= max_chunks:
            break
        for cid, c in cells.items():
            if chunk < n_chunks[cid]:
                size = min(chunk_size, int(c.get("n_rep", n_rep)) - chunk * chunk_size)
                tasks.append((study, func, cid, c, chunk, size, study_seed, out))
    t0 = time.time()
    with Pool(n_jobs or N_CORES) as pool:
        cpu = 0.0
        for k, sec in enumerate(pool.imap_unordered(_run_chunk, tasks), 1):
            cpu += sec
            if k % max(1, len(tasks) // 20) == 0:
                print(f"[{study}] {k}/{len(tasks)} chunks, {time.time() - t0:.0f} s", flush=True)
    wall = time.time() - t0
    info_path = RESULTS / f"{study}_run_info.json"
    info = json.loads(info_path.read_text()) if info_path.exists() else dict(study=study, runs=[])
    info["runs"].append(dict(wall_seconds=round(wall, 1), cpu_seconds=round(cpu, 1), chunks=len(tasks),
                             finished=time.strftime("%Y-%m-%d %H:%M:%S"), n_jobs=n_jobs or N_CORES))
    info.update(study_seed=study_seed, default_n_rep=n_rep, chunk_size=chunk_size, versions=versions(),
                seed_rule="numpy.random.default_rng([study_seed, cell_seed, chunk * 1000 + replication])")
    info_path.write_text(json.dumps(info, indent=1))
    return collect(study)


def collect(study):
    """Concatenate all chunk files of a study."""
    files = sorted((RESULTS / "raw" / study).glob("*.csv"))
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def versions():
    import matplotlib
    import scipy
    return dict(python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__,
                matplotlib=matplotlib.__version__, itemtransfer=it.__version__, platform=platform.platform(),
                cores=N_CORES)


# --------------------------------------------------------------------------
# summaries with Monte Carlo standard errors
# --------------------------------------------------------------------------
def rate(x):
    """Share of True values among the finite entries, its Monte Carlo SE and n."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return np.nan, np.nan, 0
    p = float(x.mean())
    return p, float(np.sqrt(p * (1 - p) / n)), n


def mean_se(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return np.nan, np.nan
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x)))


def summarise(df, target=None, null=False):
    """Operating characteristics of one cell and measure (data frame of replications)."""
    out = dict(n_rep=len(df))
    for st in ("train_slope", "ordering", "calibration_slope", "logloss_reduction"):
        out[st + "_mean"], out[st + "_mcse"] = mean_se(df[st])
        out[st + "_median"] = float(np.nanmedian(df[st]))
        out[st + "_sd"] = float(np.nanstd(df[st], ddof=1))
    out["calibration_slope_q05"], out["calibration_slope_q95"] = np.nanpercentile(df["calibration_slope"], [5, 95])
    if "train_slope_lo" not in df:
        return out
    weak = (df["train_slope_lo"] <= 0) & (df["train_slope_hi"] >= 0)
    out["weak_rate"], out["weak_rate_mcse"], _ = rate(weak)
    # width that the spread of the estimates would justify: range of their central 95% (robust to wild ratios)
    out["cal_width_nominal"] = float(np.subtract(*np.nanpercentile(df["calibration_slope"], [97.5, 2.5])))
    out["ll_width_nominal"] = float(np.subtract(*np.nanpercentile(df["logloss_reduction"], [97.5, 2.5]))) \
        if df["logloss_reduction"].notna().any() else np.nan
    full = df
    for suffix in ("", "_po", "_io"):
        if "calibration_slope_lo" + suffix not in full or full["calibration_slope_lo" + suffix].isna().all():
            continue
        df = full[full["calibration_slope_lo" + suffix].notna()]
        weak = (df["train_slope_lo"] <= 0) & (df["train_slope_hi"] >= 0)
        lo, hi = df["calibration_slope_lo" + suffix], df["calibration_slope_hi" + suffix]
        ex0 = (lo > 0) | (hi < 0)
        out["cal_excl0" + suffix], out["cal_excl0_mcse" + suffix], _ = rate(ex0)
        out["cal_pos" + suffix], out["cal_pos_mcse" + suffix], _ = rate(lo > 0)
        out["cal_incl1" + suffix], out["cal_incl1_mcse" + suffix], _ = rate((lo <= 1) & (hi >= 1))
        out["cal_width_median" + suffix] = float(np.nanmedian(hi - lo))
        out["cal_lo_median" + suffix], out["cal_hi_median" + suffix] = float(np.nanmedian(lo)), float(np.nanmedian(hi))
        if suffix == "":
            out["cal_excl0_notweak"], out["cal_excl0_notweak_mcse"], _ = rate(ex0 & ~weak)
        if "logloss_reduction_lo" + suffix in df:
            llo, lhi = df["logloss_reduction_lo" + suffix], df["logloss_reduction_hi" + suffix]
        else:  # prediction criterion not computed
            llo = lhi = pd.Series(np.nan, index=df.index)
        out["ll_pos" + suffix], out["ll_pos_mcse" + suffix], _ = rate(llo > 0)
        out["ll_neg" + suffix], out["ll_neg_mcse" + suffix], _ = rate(lhi < 0)
        out["ll_width_median" + suffix] = float(np.nanmedian(lhi - llo))
        if "ordering_lo" + suffix in df:
            olo, ohi = df["ordering_lo" + suffix], df["ordering_hi" + suffix]
            out["ord_pos" + suffix], out["ord_pos_mcse" + suffix], _ = rate(olo > 0)
            out["ord_excl0" + suffix], out["ord_excl0_mcse" + suffix], _ = rate((olo > 0) | (ohi < 0))
            # basic (reflected) interval, computed from the percentile end points: 2 * estimate - percentiles
            blo, bhi = 2 * df["ordering"] - ohi, 2 * df["ordering"] - olo
            out["ord_pos_basic" + suffix], out["ord_pos_basic_mcse" + suffix], _ = rate(blo > 0)
            out["ord_excl0_basic" + suffix], out["ord_excl0_basic_mcse" + suffix], _ = rate((blo > 0) | (bhi < 0))
            out["ord_excludes_own_estimate" + suffix], out["ord_excludes_own_estimate_mcse" + suffix], _ = \
                rate((df["ordering"] < olo) | (df["ordering"] > ohi))
            out["ord_centre_shift" + suffix], out["ord_centre_shift_mcse" + suffix] = \
                mean_se(np.sign(df["ordering"]) * ((olo + ohi) / 2 - df["ordering"]))
            out["ord_width_median" + suffix] = float(np.nanmedian(ohi - olo))
            eo_ = float(np.nanmean(df["ordering"]))
            out["ord_expected"] = eo_
            for nm, (a_, b_) in (("percentile", (olo, ohi)), ("basic", (blo, bhi))):
                out[f"ord_cov_expected_{nm}{suffix}"], out[f"ord_cov_expected_{nm}_mcse{suffix}"], _ = \
                    rate((a_ <= eo_) & (eo_ <= b_))
                out[f"ord_miss_below_{nm}{suffix}"], _, _ = rate(b_ < eo_)   # interval entirely below the expected value
                out[f"ord_miss_above_{nm}{suffix}"], _, _ = rate(a_ > eo_)
                if target is not None and not null and np.isfinite(target.get("ordering", np.nan)):
                    t_ = target["ordering"]  # value with infinitely many items and participants
                    out[f"ord_cov_large_sample_{nm}{suffix}"], out[f"ord_cov_large_sample_{nm}_mcse{suffix}"], _ = \
                        rate((a_ <= t_) & (t_ <= b_))
        if target is not None and not null:
            c = target.get("calibration_slope", np.nan)
            out["cal_target"] = c
            out["cal_coverage" + suffix], out["cal_coverage_mcse" + suffix], _ = rate((lo <= c) & (c <= hi))
            out["cal_miss_low" + suffix], _, _ = rate(hi < c)
            out["cal_miss_high" + suffix], _, _ = rate(lo > c)
            g = target.get("logloss_reduction", np.nan)
            out["ll_target"] = g
            out["ll_coverage" + suffix], out["ll_coverage_mcse" + suffix], _ = rate((llo <= g) & (g <= lhi))
            e = float(np.nanmean(df["logloss_reduction"]))  # expectation of the estimator in this design
            out["ll_coverage_expect" + suffix], out["ll_coverage_expect_mcse" + suffix], _ = rate((llo <= e) & (e <= lhi))
            if "ordering_lo" + suffix in df:
                o = target.get("ordering", np.nan)
                out["ord_target"] = o
                out["ord_coverage" + suffix], out["ord_coverage_mcse" + suffix], _ = rate((olo <= o) & (o <= ohi))
                eo = float(np.nanmean(df["ordering"]))
                out["ord_coverage_expect" + suffix], out["ord_coverage_expect_mcse" + suffix], _ = \
                    rate((olo <= eo) & (eo <= ohi))
    return out


def save_json(name, obj):
    (RESULTS / name).write_text(json.dumps(obj, indent=1, default=float))
