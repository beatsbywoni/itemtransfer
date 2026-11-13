"""Small statistical helpers shared by the modules."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm, rankdata


def elogit(n, s):
    """Empirical logit of ``s`` correct responses out of ``n`` trials."""
    return np.log((s + 0.5) / (n - s + 0.5))


def spearman_brown(r):
    """Spearman-Brown correction of a correlation between two halves."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return 2 * r / (1 + r)


def pearson(x, y):
    """Pearson correlation; NaN with fewer than three points or no variance."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    xc, yc = x - x.mean(), y - y.mean()
    return float(np.sum(xc * yc) / np.sqrt(np.sum(xc ** 2) * np.sum(yc ** 2)))


def spearman(x, y):
    """Spearman rank correlation (average ranks for ties)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return np.nan
    return pearson(rankdata(x), rankdata(y))


def weighted_ranks(v, w):
    """Average ranks of ``v`` when each value is repeated ``w`` times."""
    u, inv = np.unique(v, return_inverse=True)
    cw = np.bincount(inv, weights=w, minlength=len(u))
    cum = np.cumsum(cw)
    return (cum - cw / 2 + 0.5)[inv]


def wpearson(x, y, w):
    """Pearson correlation with frequency weights ``w``."""
    m = w > 0
    x, y, w = x[m], y[m], w[m]
    tot = w.sum()
    if tot < 3 or len(x) < 2:
        return np.nan
    mx, my = np.sum(w * x) / tot, np.sum(w * y) / tot
    xc, yc = x - mx, y - my
    vx, vy = np.sum(w * xc ** 2), np.sum(w * yc ** 2)
    if vx <= 0 or vy <= 0:
        return np.nan
    return float(np.sum(w * xc * yc) / np.sqrt(vx * vy))


def wspearman(x, y, w):
    """Spearman correlation with frequency weights (items repeated ``w`` times)."""
    m = (w > 0) & np.isfinite(x) & np.isfinite(y)
    x, y, w = x[m], y[m], w[m]
    if len(x) < 2:
        return np.nan
    return wpearson(weighted_ranks(x, w), weighted_ranks(y, w), w)


def corr_rows(X, Y, W=None):
    """Row-wise Pearson correlation of two (k, items) arrays.

    With ``W`` of shape (b, items), returns a (b, k) array of weighted
    correlations (frequency weights); otherwise a (k,) array.
    """
    if W is None:
        Xc = X - X.mean(axis=1, keepdims=True)
        Yc = Y - Y.mean(axis=1, keepdims=True)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.sum(Xc * Yc, axis=1) / np.sqrt(np.sum(Xc ** 2, axis=1) * np.sum(Yc ** 2, axis=1))
    Ws = W / W.sum(axis=1, keepdims=True)
    mx, my = Ws @ X.T, Ws @ Y.T
    xx = Ws @ (X ** 2).T - mx ** 2
    yy = Ws @ (Y ** 2).T - my ** 2
    xy = Ws @ (X * Y).T - mx * my
    with np.errstate(invalid="ignore", divide="ignore"):
        return xy / np.sqrt(xx * yy)


def percentile_interval(boot, level=0.95):
    """Percentile interval of the finite bootstrap values."""
    b = np.asarray(boot, dtype=float)
    b = b[np.isfinite(b)]
    if len(b) < 2:
        return (np.nan, np.nan)
    a = 100 * (1 - level) / 2
    return (float(np.percentile(b, a)), float(np.percentile(b, 100 - a)))


def bc_interval(point, boot, level=0.95):
    """Bias-corrected percentile interval (Efron)."""
    b = np.asarray(boot, dtype=float)
    b = b[np.isfinite(b)]
    if len(b) < 10 or not np.isfinite(point):
        return (np.nan, np.nan)
    frac = np.mean(b < point)
    frac = min(max(frac, 0.5 / len(b)), 1 - 0.5 / len(b))
    z0 = norm.ppf(frac)
    a = (1 - level) / 2
    a1, a2 = norm.cdf(2 * z0 + norm.ppf(a)), norm.cdf(2 * z0 + norm.ppf(1 - a))
    return (float(np.percentile(b, 100 * a1)), float(np.percentile(b, 100 * a2)))


def basic_interval(point, boot, level=0.95):
    """Basic (reflected) bootstrap interval: ``2 * point`` minus the upper and lower percentiles.

    Offered for completeness. In simulations it was not a remedy for the downward shift of two-way resampled
    ordering correlations: it undercovered and produced false positives for measures without relation. For
    the ordering correlation use the items-only bootstrap (the default of :func:`itemtransfer.transfer`).
    """
    lo, hi = percentile_interval(boot, level)
    if not (np.isfinite(point) and np.isfinite(lo) and np.isfinite(hi)):
        return (np.nan, np.nan)
    return (float(2 * point - hi), float(2 * point - lo))


def interval(point, boot, kind="percentile", level=0.95):
    """Bootstrap interval of the requested kind."""
    if kind == "percentile":
        return percentile_interval(boot, level)
    if kind == "bc":
        return bc_interval(point, boot, level)
    if kind == "basic":
        return basic_interval(point, boot, level)
    raise ValueError("`interval` must be 'percentile', 'bc' or 'basic'.")


def bootstrap_counts(rng, size, n_boot):
    """Multinomial resampling counts: (n_boot, size) array, each row sums to ``size``."""
    return rng.multinomial(size, np.full(size, 1.0 / size), size=n_boot).astype(float)


def as_rng(seed):
    """Return a numpy Generator from a seed or pass a Generator through."""
    return seed if isinstance(seed, np.random.Generator) else np.random.default_rng(seed)


def child_rng(seed, k):
    """Independent generator number ``k`` derived from ``seed`` (a Generator is used as is)."""
    if isinstance(seed, np.random.Generator):
        return seed
    if seed is None:
        return np.random.default_rng()
    return np.random.default_rng([int(seed), int(k)])
