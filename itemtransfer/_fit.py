"""Binomial logistic regression on aggregated counts.

Two fitters are provided. :func:`fit_logit` fits one model and is used for
every point estimate. :func:`fit_logit_batch` fits the same model to many
resamples at once and is used inside the bootstraps. Both use Newton steps
with step halving and report convergence instead of hiding it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["LogitFit", "fit_logit", "fit_logit_batch", "fit_intercepts"]


@dataclass
class LogitFit:
    """Result of :func:`fit_logit`.

    Attributes
    ----------
    coef : numpy.ndarray
        Coefficients on the original scale of the design matrix.
    deviance : float
        Binomial deviance of the fitted model.
    null_deviance : float
        Deviance of the model with one common probability.
    converged : bool
        True when the change in deviance and the Newton step were both
        negligible at the last iteration.
    boundary : bool
        True when a fitted linear predictor exceeds 30 in absolute value,
        which indicates (quasi-)separation.
    n_iter : int
        Number of Newton iterations used.
    """

    coef: np.ndarray
    deviance: float
    null_deviance: float
    converged: bool
    boundary: bool
    n_iter: int


def _xlogy(a, b):
    out = np.zeros_like(a, dtype=float)
    m = a > 0
    out[m] = a[m] * np.log(b[m])
    return out


def _binom_dev(n, s, mu, fw):
    mu = np.clip(mu, 1e-15, 1 - 1e-15)
    return 2 * np.sum(fw * (_xlogy(s, s / n / mu) + _xlogy(n - s, (n - s) / n / (1 - mu))))


def fit_logit(X, n, s, weights=None, max_iter=200, tol=1e-12):
    """Fit a binomial logistic regression to aggregated counts.

    Parameters
    ----------
    X : array_like, shape (rows, p)
        Design matrix. Include the intercept column(s) yourself.
    n : array_like, shape (rows,)
        Number of trials in each row.
    s : array_like, shape (rows,)
        Number of correct responses in each row.
    weights : array_like, shape (rows,), optional
        Frequency weight of each row (default 1). Rows with ``n == 0`` or
        weight 0 are dropped.
    max_iter : int
        Maximum number of Newton iterations.
    tol : float
        Relative tolerance on the change in deviance.

    Returns
    -------
    LogitFit

    Notes
    -----
    Columns that are not 0/1 indicators are scaled to unit standard deviation
    (and centred when a constant lies in the column space), so the fit does
    not depend on the units of the predictors. Coefficients are returned on
    the original scale. Newton steps are halved until the deviance does not
    increase; the coefficients are not bounded. A design with non-finite
    values returns coefficients of NaN and ``converged=False``.
    """
    n = np.asarray(n, dtype=float)
    s = np.asarray(s, dtype=float)
    fw = np.ones_like(n) if weights is None else np.asarray(weights, dtype=float)
    keep = (n > 0) & (fw > 0)
    X, n, s, fw = np.asarray(X, dtype=float)[keep], n[keep], s[keep], fw[keep]
    p = X.shape[1]
    if len(n) == 0:
        return LogitFit(np.full(p, np.nan), np.nan, np.nan, False, False, 0)
    pbar = np.sum(fw * s) / np.sum(fw * n)
    dev0 = _binom_dev(n, s, np.full(len(n), pbar), fw)
    if not np.all(np.isfinite(X)):
        return LogitFit(np.full(p, np.nan), np.nan, dev0, False, False, 0)
    ones = np.ones(len(n))
    is_ind = np.array([np.all(np.isin(np.unique(X[:, j]), [0.0, 1.0])) for j in range(p)])
    sd = X.std(axis=0)
    mu_x = X.mean(axis=0)
    res_const = ones - X @ np.linalg.lstsq(X, ones, rcond=None)[0]
    has_const = float(np.sqrt(np.mean(res_const ** 2))) < 1e-8
    scale = (~is_ind) & (sd > 0)
    centre = np.where(scale & has_const, mu_x, 0.0)
    S = np.where(scale, sd, 1.0)
    Z = (X - centre) / S
    mu0 = (s + 0.5) / (n + 1.0)
    eta0 = np.log(mu0 / (1 - mu0))
    W0 = fw * n * mu0 * (1 - mu0)
    beta = np.linalg.lstsq(Z * np.sqrt(W0)[:, None], eta0 * np.sqrt(W0), rcond=None)[0]
    dev = _binom_dev(n, s, 1 / (1 + np.exp(-(Z @ beta))), fw)
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        eta = Z @ beta
        mu = 1 / (1 + np.exp(-eta))
        W = fw * n * mu * (1 - mu)
        score = Z.T @ (fw * (s - n * mu))
        info = (Z.T * W) @ Z
        try:
            step = np.linalg.solve(info + 1e-12 * np.eye(p), score)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(info, score, rcond=None)[0]
        t = 1.0
        while True:
            cand = beta + t * step
            dev_c = _binom_dev(n, s, 1 / (1 + np.exp(-(Z @ cand))), fw)
            if np.isfinite(dev_c) and dev_c <= dev + 1e-10 * (abs(dev) + 1):
                break
            t /= 2
            if t < 1e-10:
                cand, dev_c = beta, dev
                break
        change = dev - dev_c
        beta, dev = cand, dev_c
        if abs(change) < tol * (abs(dev) + 0.1) and np.max(np.abs(t * step)) < 1e-7:
            converged = True
            break
    eta = Z @ beta
    boundary = bool(np.max(np.abs(eta)) > 30)
    coef = np.linalg.lstsq(X, eta, rcond=None)[0] if np.any(centre != 0) else beta / S
    dev = _binom_dev(n, s, 1 / (1 + np.exp(-eta)), fw)
    return LogitFit(coef, float(dev), float(dev0), converged, boundary, it)


# --------------------------------------------------------------------------
# batched fits for the bootstraps
# --------------------------------------------------------------------------
def _nll(eta, wn, ws):
    # negative log likelihood up to a constant, row-wise over the batch
    return np.sum(wn * np.logaddexp(0.0, eta) - ws * eta, axis=1)


def _solve(A, b):
    p = A.shape[-1]
    A = A + 1e-12 * np.eye(p)
    try:
        return np.linalg.solve(A, b[..., None])[..., 0]
    except np.linalg.LinAlgError:
        out = np.full(b.shape, np.nan)
        for k in range(A.shape[0]):
            try:
                out[k] = np.linalg.solve(A[k], b[k])
            except np.linalg.LinAlgError:
                out[k] = np.linalg.lstsq(A[k], b[k], rcond=None)[0]
        return out


def fit_logit_batch(X, n, s, weights=None, n_indicator=1, max_iter=100, tol=1e-10):
    """Fit one logistic model to many sets of counts at once.

    Parameters
    ----------
    X : numpy.ndarray, shape (rows, p) or (batch, rows, p)
        Design matrix, shared by all batch members or one per member. The
        first ``n_indicator`` columns must be 0/1 indicator columns that sum
        to one in every row (one intercept, or one intercept per sample).
    n, s : numpy.ndarray, shape (batch, rows)
        Trials and correct responses for each batch member.
    weights : numpy.ndarray, shape (batch, rows), optional
        Frequency weights. Rows with zero weight or zero trials are ignored.
    n_indicator : int
        Number of leading indicator columns.
    max_iter, tol : int, float
        Newton iteration limit and relative tolerance.

    Returns
    -------
    coef : numpy.ndarray, shape (batch, p)
        Coefficients on the original scale (NaN where the fit failed).
    converged : numpy.ndarray of bool, shape (batch,)
    """
    n = np.asarray(n, dtype=float)
    s = np.asarray(s, dtype=float)
    w = np.ones_like(n) if weights is None else np.asarray(weights, dtype=float)
    wn, ws = w * n, w * s
    B, R = n.shape
    shared = X.ndim == 2
    p = X.shape[-1]
    k = n_indicator
    active = wn > 0
    # centre and scale the non-indicator columns (numerical conditioning only)
    if shared:
        cen = X[:, k:].mean(axis=0)
        sc = X[:, k:].std(axis=0)
        sc = np.where(sc > 0, sc, 1.0)
        Z = X.copy()
        Z[:, k:] = (X[:, k:] - cen) / sc
        cen = np.broadcast_to(cen, (B, p - k))
        sc = np.broadcast_to(sc, (B, p - k))
    else:
        a = active[:, :, None].astype(float)
        cnt = np.maximum(a.sum(axis=1), 1.0)
        cen = (X[:, :, k:] * a).sum(axis=1) / cnt
        var = (((X[:, :, k:] - cen[:, None, :]) ** 2) * a).sum(axis=1) / cnt
        sc = np.sqrt(var)
        sc = np.where(sc > 0, sc, 1.0)
        Z = X.copy()
        Z[:, :, k:] = (X[:, :, k:] - cen[:, None, :]) / sc[:, None, :]

    def lin(beta, idx):
        if shared:
            return beta @ Z.T
        return np.einsum("brp,bp->br", Z[idx], beta)

    def grad_info(W, r, idx):
        if shared:
            score = r @ Z
            info = np.einsum("br,rp,rq->bpq", W, Z, Z, optimize=True)
        else:
            Zi = Z[idx]
            score = np.einsum("br,brp->bp", r, Zi)
            info = np.einsum("br,brp,brq->bpq", W, Zi, Zi, optimize=True)
        return score, info

    all_idx = np.arange(B)
    mu0 = (s + 0.5) / (n + 1.0)
    eta0 = np.log(mu0 / (1 - mu0))
    W0 = wn * mu0 * (1 - mu0)
    sc0, info0 = grad_info(W0, W0 * eta0, all_idx)
    beta = _solve(info0, sc0)
    beta = np.where(np.isfinite(beta), beta, 0.0)
    nll = _nll(lin(beta, all_idx), wn, ws)
    conv = np.zeros(B, dtype=bool)
    todo = np.ones(B, dtype=bool)
    for _ in range(max_iter):
        idx = np.flatnonzero(todo)
        if len(idx) == 0:
            break
        b = beta[idx]
        eta = lin(b, idx)
        mu = 1 / (1 + np.exp(-eta))
        W = wn[idx] * mu * (1 - mu)
        score, info = grad_info(W, ws[idx] - wn[idx] * mu, idx)
        step = _solve(info, score)
        step = np.where(np.isfinite(step), step, 0.0)
        t = np.ones(len(idx))
        cand = b + step
        nll_c = _nll(lin(cand, idx), wn[idx], ws[idx])
        old = nll[idx]
        bad = ~(np.isfinite(nll_c) & (nll_c <= old + 1e-10 * (np.abs(old) + 1)))
        for _h in range(40):
            if not bad.any():
                break
            t[bad] /= 2
            cand[bad] = b[bad] + t[bad, None] * step[bad]
            nll_c[bad] = _nll(lin(cand[bad], idx[bad]), wn[idx[bad]], ws[idx[bad]])
            bad[bad] = ~(np.isfinite(nll_c[bad]) & (nll_c[bad] <= old[bad] + 1e-10 * (np.abs(old[bad]) + 1)))
        cand[bad] = b[bad]
        nll_c[bad] = old[bad]
        change = old - nll_c
        done = (np.abs(change) < tol * (np.abs(nll_c) + 0.1)) & (np.max(np.abs(t[:, None] * step), axis=1) < 1e-6)
        beta[idx] = cand
        nll[idx] = nll_c
        conv[idx[done]] = True
        todo[idx[done | bad]] = False
    # back to the original scale
    coef = beta.copy()
    coef[:, k:] = beta[:, k:] / sc
    if k == 1:
        coef[:, 0] = beta[:, 0] - np.sum(coef[:, k:] * cen, axis=1)
    else:
        coef[:, :k] = beta[:, :k] - np.sum(coef[:, k:] * cen, axis=1)[:, None]
    empty = ~active.any(axis=1)
    coef[empty] = np.nan
    conv[empty] = False
    return coef, conv


def fit_intercepts(offset, n, s, weights=None, max_iter=100, tol=1e-12):
    """Fit only the intercept of a logistic model with a fixed offset.

    All arrays broadcast against each other; the last axis runs over rows
    (items). Returns the intercept for every leading index.

    Parameters
    ----------
    offset : numpy.ndarray, shape (..., rows)
        Fixed linear predictor.
    n, s : numpy.ndarray, shape (..., rows)
        Trials and correct responses.
    weights : numpy.ndarray, shape (..., rows), optional
        Row weights; rows with weight 0 are ignored.

    Returns
    -------
    numpy.ndarray, shape (...)
    """
    if weights is not None:
        n = n * weights
        s = s * weights
    tot_n = n.sum(axis=-1)
    tot_s = s.sum(axis=-1)
    shape = np.broadcast_shapes(offset.shape, n.shape)[:-1]
    cnt = np.maximum((n > 0).sum(axis=-1), 1)
    mean_off = np.where(n > 0, offset, 0.0).sum(axis=-1) / cnt
    a = np.broadcast_to(np.log((tot_s + 0.5) / (tot_n - tot_s + 0.5)) - mean_off, shape).copy()
    for _ in range(max_iter):
        p = 1 / (1 + np.exp(-(a[..., None] + offset)))
        g = np.sum(s - n * p, axis=-1)
        h = np.sum(n * p * (1 - p), axis=-1)
        with np.errstate(invalid="ignore", divide="ignore"):
            step = np.where(h > 0, g / h, 0.0)
        step = np.clip(step, -5.0, 5.0)
        a += step
        if np.max(np.abs(step)) < tol:
            break
    return a
