import numpy as np

from itemtransfer._fit import fit_intercepts, fit_logit, fit_logit_batch


def _data(rng, rows=400, n_trials=50, beta=(0.3, -1.2, 0.7)):
    X = np.column_stack([np.ones(rows), rng.normal(size=rows), rng.normal(size=rows) * 100])
    eta = X @ np.array([beta[0], beta[1], beta[2] / 100])
    n = np.full(rows, float(n_trials))
    s = rng.binomial(n_trials, 1 / (1 + np.exp(-eta))).astype(float)
    return X, n, s


def test_recovers_known_coefficients(rng):
    X, n, s = _data(rng, rows=4000)
    fit = fit_logit(X, n, s)
    assert fit.converged and not fit.boundary
    assert np.allclose(fit.coef, [0.3, -1.2, 0.007], atol=0.03, rtol=0.05)
    assert fit.deviance < fit.null_deviance


def test_invariant_to_units(rng):
    X, n, s = _data(rng)
    f1 = fit_logit(X, n, s)
    X2 = X.copy()
    X2[:, 2] *= 1e-6
    f2 = fit_logit(X2, n, s)
    assert np.allclose(f1.coef[:2], f2.coef[:2], rtol=1e-6)
    assert np.isclose(f1.coef[2], f2.coef[2] * 1e-6, rtol=1e-6)


def test_frequency_weights_equal_repeated_rows(rng):
    X, n, s = _data(rng, rows=60)
    w = rng.integers(0, 4, 60).astype(float)
    f1 = fit_logit(X, n, s, w)
    rep = np.repeat(np.arange(60), w.astype(int))
    f2 = fit_logit(X[rep], n[rep], s[rep])
    assert np.allclose(f1.coef, f2.coef, rtol=1e-7, atol=1e-9)


def test_separation_is_reported():
    X = np.column_stack([np.ones(6), np.arange(6.0)])
    n = np.full(6, 10.0)
    s = np.array([0, 0, 0, 10, 10, 10.0])
    fit = fit_logit(X, n, s)
    assert fit.boundary or not fit.converged


def test_non_finite_design_returns_nan():
    X = np.column_stack([np.ones(4), [0.0, 1.0, np.nan, 2.0]])
    fit = fit_logit(X, np.full(4, 5.0), np.array([1.0, 2, 3, 4]))
    assert np.isnan(fit.coef).all() and not fit.converged


def test_batch_matches_scalar_shared_design(rng):
    X, n, s = _data(rng, rows=80, n_trials=20)
    Xd = np.column_stack([np.repeat(np.eye(2), 40, axis=0), X[:, 1:]])
    B = 25
    W = rng.integers(0, 4, (B, 80)).astype(float)
    N = np.tile(n, (B, 1))
    S = rng.binomial(20, 0.5 + 0.3 * np.tanh(X[:, 1]), (B, 80)).astype(float)
    coef, conv = fit_logit_batch(Xd, N, S, W, n_indicator=2)
    assert conv.all()
    for b in range(B):
        ref = fit_logit(Xd, N[b], S[b], W[b])
        assert np.allclose(coef[b], ref.coef, rtol=1e-5, atol=1e-6)


def test_batch_matches_scalar_own_design(rng):
    B, R = 20, 50
    eta = rng.normal(size=(B, R)) * rng.uniform(0.01, 5, (B, 1))
    Xb = np.stack([np.ones((B, R)), eta], axis=2)
    N = np.full((B, R), 30.0)
    S = rng.binomial(30, 1 / (1 + np.exp(-(0.2 + 0.5 * eta / eta.std(axis=1, keepdims=True))))).astype(float)
    W = rng.integers(0, 3, (B, R)).astype(float)
    coef, conv = fit_logit_batch(Xb, N, S, W, n_indicator=1)
    assert conv.all()
    for b in range(B):
        ref = fit_logit(Xb[b], N[b], S[b], W[b])
        assert np.allclose(coef[b], ref.coef, rtol=1e-5, atol=1e-6)


def test_intercept_only_fit_matches_offset_model(rng):
    off = rng.normal(size=40)
    n = np.full(40, 25.0)
    s = rng.binomial(25, 1 / (1 + np.exp(-(0.4 + off)))).astype(float)
    a = fit_intercepts(off, n, s)
    p = 1 / (1 + np.exp(-(a + off)))
    assert abs(np.sum(s - n * p)) < 1e-8  # score equation of the intercept
    a2 = fit_intercepts(np.stack([off, off * 0]), n, s)
    assert np.isclose(a2[0], a) and np.isclose(a2[1], np.log(s.sum() / (n.sum() - s.sum())))
