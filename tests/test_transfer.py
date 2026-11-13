import numpy as np
import pandas as pd
import pytest

import itemtransfer as it
from itemtransfer._data import Data, Sample, prepare
from itemtransfer.transfer import (_boot_prediction, _bootstrap_fold, _point_fold, _prediction, _reductions,
                                   _split_masks)

from conftest import make_design


def test_known_slope_recovery_and_calibration_one():
    # no random effects: the marginal model is the generating model
    design = make_design(slope=2.0, n_items=300, n_participants=150, participant_sd=0.0, item_sd=0.0,
                         null_measure=False)
    trials, items = it.simulate(design, seed=1)
    tab = it.transfer(trials, items, ["x"], n_boot=0, n_splits=50).table
    assert np.allclose(tab["train_slope"], 2.0, atol=0.06)
    assert np.allclose(tab["heldout_slope"], 2.0, atol=0.1)
    assert np.allclose(tab["calibration_slope"], 1.0, atol=0.06)
    assert (tab["ordering"] > 0.9).all()
    assert (tab["logloss_reduction"] > 0.1).all()
    assert tab["train_converged"].all() and tab["calibration_converged"].all()


def test_calibration_slope_is_ratio_when_slopes_differ():
    design = make_design(slope=2.0, slopes={"C": 1.0}, n_items=300, n_participants=150, participant_sd=0.0,
                         item_sd=0.0, null_measure=False)
    trials, items = it.simulate(design, seed=2)
    tab = it.transfer(trials, items, ["x"], n_boot=0, n_splits=50).table.set_index("family")
    # held-out C: trained on slope 2, true slope 1
    assert abs(tab.at["C", "calibration_slope"] - 0.5) < 0.04
    assert abs(tab.at["C", "train_slope"] - 2.0) < 0.06
    # held-out A: trained on B (2) and C (1) -> slope between 1 and 2, calibration slope above 1
    assert 1.2 < tab.at["A", "train_slope"] < 1.8
    assert abs(tab.at["A", "calibration_slope"] - 2.0 / tab.at["A", "train_slope"]) < 0.1


def test_calibration_slope_equals_heldout_over_training_slope(small):
    trials, items = small
    tab = it.transfer(trials, items, ["x", "x2", "x_null"], n_boot=0, n_splits=20).table
    single = tab[tab["model"] != "combined"]
    assert np.allclose(single["calibration_slope"], single["heldout_slope"] / single["train_slope"], rtol=1e-6)


def test_intervals_cover_one_for_common_slope_and_null_measure_is_flagged(small):
    trials, items = small
    res = it.transfer(trials, items, ["x", "x_null"], n_boot=400, n_splits=100, seed=5)
    tab = res.table.set_index(["family", "model"])
    for f in "ABC":
        assert tab.at[(f, "x"), "calibration_slope_lo"] < 1 < tab.at[(f, "x"), "calibration_slope_hi"]
        assert tab.at[(f, "x"), "calibration_slope_lo"] > 0
        assert tab.at[(f, "x"), "train_slope_lo"] > 0
        assert tab.at[(f, "x"), "logloss_reduction_lo"] > 0
        # the null measure: no training relation, no ordering, no predictive gain
        assert tab.at[(f, "x_null"), "train_slope_lo"] < 0 < tab.at[(f, "x_null"), "train_slope_hi"]
        assert tab.at[(f, "x_null"), "ordering_lo"] < 0 < tab.at[(f, "x_null"), "ordering_hi"]
        assert tab.at[(f, "x_null"), "logloss_reduction_lo"] < 0.005
        assert abs(tab.at[(f, "x_null"), "logloss_reduction"]) < 0.01
    assert set(res.bootstrap[("A", "x")].columns) >= {"train_slope", "ordering", "calibration_slope",
                                                      "logloss_reduction", "brier_reduction", "heldout_slope"}
    assert len(res.bootstrap[("A", "x")]) == 400


def test_seed_reproducibility_and_generator(small):
    trials, items = small
    a = it.transfer(trials, items, ["x"], n_boot=50, n_splits=20, seed=9).table
    b = it.transfer(trials, items, ["x"], n_boot=50, n_splits=20, seed=9).table
    c = it.transfer(trials, items, ["x"], n_boot=50, n_splits=20, seed=10).table
    pd.testing.assert_frame_equal(a, b)
    assert not np.allclose(a["calibration_slope_lo"], c["calibration_slope_lo"])
    assert np.allclose(a["calibration_slope"], c["calibration_slope"])
    g = it.transfer(trials, items, ["x"], n_boot=0, n_splits=20, seed=np.random.default_rng(9)).table
    assert np.allclose(g["logloss_reduction"], a["logloss_reduction"])


def test_row_order_does_not_matter(small):
    trials, items = small
    a = it.transfer(trials, items, ["x", "x_null"], n_boot=0, n_splits=20, seed=1).table
    b = it.transfer(trials.sample(frac=1, random_state=0), items.sample(frac=1, random_state=0), ["x", "x_null"],
                    n_boot=0, n_splits=20, seed=1).table
    num = a.select_dtypes("number").columns
    a, b = a.sort_values(["family", "model"]), b.sort_values(["family", "model"])
    assert np.allclose(a[num], b[num], equal_nan=True, rtol=1e-8, atol=1e-10)


def test_combined_model_and_single_measure(small):
    trials, items = small
    tab = it.transfer(trials, items, ["x", "x2"], n_boot=0, n_splits=20).table
    assert list(tab["model"].unique()) == ["x", "x2", "combined"]
    assert tab.loc[tab["model"] == "combined", "train_slope"].isna().all()
    tab1 = it.transfer(trials, items, "x", n_boot=0, n_splits=20).table
    assert list(tab1["model"].unique()) == ["x"]
    tab2 = it.transfer(trials, items, ["x", "x2"], combined=False, n_boot=0, n_splits=20).table
    assert "combined" not in set(tab2["model"])


def test_weights_and_evaluation_samples(example):
    trials, items = example
    tr = it.transfer(trials, items, ["x"], weights="trials", n_boot=0, n_splits=20).table.set_index("family")
    eq = it.transfer(trials, items, ["x"], weights="equal", n_boot=0, n_splits=20).table.set_index("family")
    # held-out A is trained on one sample per family, B and C: weights change the fit
    assert not np.isclose(tr.at["A", "train_slope"], eq.at["A", "train_slope"])
    # evaluation on one sample of family A
    one = it.transfer(trials, items, ["x"], evaluate={"A": "A2"}, n_boot=0, n_splits=20).table.set_index("family")
    assert one.at["A", "n_items"] == 40 and tr.at["A", "n_items"] == 60
    assert one.at["A", "eval_samples"] == "A2" and tr.at["A", "eval_samples"] == "A1+A2"
    assert np.isclose(one.at["A", "train_slope"], tr.at["A", "train_slope"])
    assert np.isclose(one.at["B", "calibration_slope"], tr.at["B", "calibration_slope"])
    # hold out one family only
    h = it.transfer(trials, items, ["x"], holdout=["C"], n_boot=0, n_splits=20).table
    assert list(h["family"]) == ["C"] and np.isclose(h["train_slope"].iloc[0], tr.at["C", "train_slope"])


def test_equal_weights_with_one_training_sample_changes_nothing(small):
    trials, items = small
    sub_t, sub_i = trials[trials["family"] != "C"], items[items["family"] != "C"]
    a = it.transfer(sub_t, sub_i, ["x"], weights="trials", n_boot=0, n_splits=20).table
    b = it.transfer(sub_t, sub_i, ["x"], weights="equal", n_boot=0, n_splits=20).table
    assert np.allclose(a["calibration_slope"], b["calibration_slope"])


def _expanded(data, wp, wi):
    """Data set in which participants and items are physically repeated according to the weights."""
    out = Data(families=list(data.families), measures=list(data.measures), items={}, X={})
    for f in data.families:
        rep = np.repeat(np.arange(data.n_items(f)), wi[f].astype(int))
        out.items[f] = np.arange(len(rep))
        out.X[f] = data.X[f][rep]
        out.family_samples[f] = list(data.family_samples[f])
        for s in data.family_samples[f]:
            smp = data.samples[s]
            pr = np.repeat(np.arange(smp.n_participants), wp[s].astype(int))
            out.samples[s] = Sample(s, f, np.arange(len(pr)), smp.N[pr][:, rep], smp.S[pr][:, rep])
    return out


@pytest.mark.parametrize("weights", ["trials", "equal"])
def test_bootstrap_weights_equal_physically_resampled_data(example, weights, rng):
    trials, items = example
    data = prepare(trials, items, ["x", "x2"])
    models = {"x": ["x"], "x2": ["x2"], "combined": ["x", "x2"]}
    from itemtransfer.transfer import _draw
    wp, wi = _draw(data, 3, rng)
    ev = {"A": ["A1", "A2"], "B": ["B1"], "C": ["C1"]}
    for f in data.families:
        bt = _bootstrap_fold(data, f, ev[f], models, weights, wp, wi, rng, prediction=False)
        for b in range(3):
            exp = _expanded(data, {k: v[b] for k, v in wp.items()}, {k: v[b] for k, v in wi.items()})
            pt, _, _, _ = _point_fold(exp, f, ev[f], models, weights)
            for m in models:
                assert np.isclose(bt[m]["calibration_slope"][b], pt[m]["calibration_slope"], rtol=1e-4, atol=1e-5)
                assert np.isclose(bt[m]["ordering"][b], pt[m]["ordering"], atol=1e-9)
                if m != "combined":
                    assert np.isclose(bt[m]["train_slope"][b], pt[m]["b"][0], rtol=1e-5)
                    assert np.isclose(bt[m]["heldout_slope"][b], pt[m]["heldout_slope"], rtol=1e-4, atol=1e-5)


def test_prediction_against_explicit_loop(rng):
    from itemtransfer._fit import fit_logit
    I = 30
    x = rng.normal(size=I)
    n = rng.integers(5, 30, I).astype(float)
    s = rng.binomial(n.astype(int), 1 / (1 + np.exp(-(0.3 + 0.8 * x)))).astype(float)
    lins = np.vstack([np.zeros(I), 1.3 * x])
    masks = _split_masks(I, 7, np.random.default_rng(0))
    ll, br = _prediction(lins, n, s, masks)
    for r in range(7):
        tot = np.zeros(2)
        for cal, ev in [(masks[r] > 0, masks[r] == 0), (masks[r] == 0, masks[r] > 0)]:
            for j in range(2):
                # intercept by brute force: one-parameter fit with the predictor as offset
                grid_a = np.linspace(-3, 3, 60001)
                p = 1 / (1 + np.exp(-(grid_a[:, None] + lins[j][cal][None, :])))
                score = (s[cal] - n[cal] * p).sum(axis=1)
                a = grid_a[np.argmin(np.abs(score))]
                pe = 1 / (1 + np.exp(-(a + lins[j][ev])))
                tot[j] += -np.sum(s[ev] * np.log(pe) + (n[ev] - s[ev]) * np.log(1 - pe)) / n[ev].sum() / 2
        assert np.allclose(ll[r], tot, atol=2e-4)
    red, _ = _reductions(ll, br)
    assert np.allclose(red[:, 0], 0)


def test_level_indicator_baseline_matches_logistic_fit(rng):
    from itemtransfer._fit import fit_logit
    I = 40
    levels = (np.arange(I) % 2).astype(int)
    n = np.full(I, 20.0)
    s = rng.binomial(20, np.where(levels == 1, 0.8, 0.5)).astype(float)
    masks = _split_masks(I, 5, np.random.default_rng(1))
    ll, _ = _prediction(np.zeros((1, I)), n, s, masks, levels=levels)
    for r in range(5):
        tot = 0.0
        for cal, ev in [(masks[r] > 0, masks[r] == 0), (masks[r] == 0, masks[r] > 0)]:
            fit = fit_logit(np.column_stack([np.ones(cal.sum()), levels[cal]]), n[cal], s[cal])
            p = 1 / (1 + np.exp(-(fit.coef[0] + fit.coef[1] * levels[ev])))
            tot += -np.sum(s[ev] * np.log(p) + (n[ev] - s[ev]) * np.log(1 - p)) / n[ev].sum() / 2
        assert np.isclose(ll[r, 1], tot, rtol=1e-7)


def test_bootstrap_prediction_with_unit_weights_matches_point_estimate(rng):
    I = 50
    x = rng.normal(size=I)
    n = np.full(I, 30.0)
    s = rng.binomial(30, 1 / (1 + np.exp(-(0.3 + 1.0 * x)))).astype(float)
    lins = np.vstack([np.zeros(I), 1.0 * x])
    ll, br = _prediction(lins, n, s, _split_masks(I, 2000, np.random.default_rng(0)))
    point = _reductions(ll, br)[0][:, 1].mean()
    B = 40
    bl, _ = _boot_prediction(np.tile(lins, (B, 1, 1)), np.tile(n, (B, 1)), np.tile(s, (B, 1)), np.ones((B, I)), 50,
                             np.random.default_rng(1))
    assert abs(bl[:, 1].mean() - point) < 0.003
    # multiplying all weights by a constant changes nothing; items with weight 0 are ignored
    w = np.ones((B, I))
    w[:, 40:] = 0
    b1, _ = _boot_prediction(np.tile(lins, (B, 1, 1)), np.tile(n, (B, 1)), np.tile(s, (B, 1)), w, 50,
                             np.random.default_rng(2))
    b2, _ = _boot_prediction(np.tile(lins, (B, 1, 1)), np.tile(n, (B, 1)), np.tile(s, (B, 1)), 3 * w, 50,
                             np.random.default_rng(2))
    assert np.allclose(b1, b2)
    ll40, br40 = _prediction(lins[:, :40], n[:40], s[:40], _split_masks(40, 2000, np.random.default_rng(0)))
    assert abs(b1[:, 1].mean() - _reductions(ll40, br40)[0][:, 1].mean()) < 0.003


def test_predictions_table(small):
    trials, items = small
    res = it.transfer(trials, items, ["x"], n_boot=0, n_splits=20)
    p = res.predictions
    assert set(p.columns) == {"family", "model", "item", "linear_predictor", "n_trials", "n_correct", "accuracy"}
    assert len(p) == 180
    merged = p.merge(items, on="item")
    slope = res.table.set_index("family")["train_slope"]
    assert np.allclose(merged["linear_predictor"], merged["family_x"].map(slope) * merged["x"])
    assert "TransferResult" in repr(res)


def test_measure_name_reserved(small):
    trials, items = small
    with pytest.raises(ValueError, match="cannot be called"):
        it.transfer(trials, items.rename(columns={"x": "combined"}), ["combined"], n_boot=0)


def test_bias_corrected_interval_option(small):
    trials, items = small
    a = it.transfer(trials, items, ["x"], n_boot=200, n_splits=20, seed=3).table
    b = it.transfer(trials, items, ["x"], n_boot=200, n_splits=20, seed=3, interval_type="bc", level=0.9).table
    assert np.allclose(a["calibration_slope"], b["calibration_slope"])
    assert not np.allclose(a["calibration_slope_lo"], b["calibration_slope_lo"])
    assert (b["calibration_slope_lo"] < b["calibration_slope"]).all()
    with pytest.raises(ValueError, match="interval_type"):
        it.transfer(trials, items, ["x"], interval_type="normal")


def test_boot_batch_single_batch_is_identical_and_small_batches_agree(example):
    """`boot_batch` bounds memory; one batch reproduces the default run, small batches give the same point
    estimates, the same number of resamples and intervals that differ only by Monte Carlo error."""
    trials, items = example
    kw = dict(n_boot=120, n_splits=40, seed=3)
    ref = it.transfer(trials, items, ["x", "x_null"], **kw)
    one = it.transfer(trials, items, ["x", "x_null"], boot_batch=120, **kw)
    pd.testing.assert_frame_equal(ref.table, one.table)
    small = it.transfer(trials, items, ["x", "x_null"], boot_batch=50, **kw)
    assert small.settings["boot_batch"] == 50 and ref.settings["boot_batch"] is None
    point = ["train_slope", "ordering", "calibration_slope", "heldout_slope", "logloss_reduction"]
    pd.testing.assert_frame_equal(ref.table[point], small.table[point])
    assert all(len(b) == 120 for b in small.bootstrap.values())
    rx, sx = ref.table[ref.table["model"] == "x"], small.table[small.table["model"] == "x"]
    assert np.allclose(rx["calibration_slope_lo"], sx["calibration_slope_lo"], atol=0.25)
    assert np.allclose(rx["calibration_slope_hi"], sx["calibration_slope_hi"], atol=0.25)
    with pytest.raises(ValueError, match="boot_batch"):
        it.transfer(trials, items, ["x"], n_boot=10, boot_batch=0)


def test_prediction_does_not_depend_on_chunking():
    from itemtransfer.transfer import _prediction, _split_masks
    rng = np.random.default_rng(5)
    I = 37
    n = rng.integers(5, 30, I).astype(float)
    x = rng.normal(0, 1, I)
    s = rng.binomial(n.astype(int), 1 / (1 + np.exp(-(0.5 + x)))).astype(float)
    lins = np.vstack([np.zeros(I), x, 0.3 * x])
    masks = _split_masks(I, 23, np.random.default_rng(1))
    levels = (x > 0).astype(int)
    for lev in (None, levels):
        a = _prediction(lins, n, s, masks, levels=lev)
        b = _prediction(lins, n, s, masks, levels=lev, chunk_elems=1)      # one split at a time
        c = _prediction(lins, n, s, masks, levels=lev, chunk_elems=2000)   # a few splits at a time
        for u, v, w in zip(a, b, c):
            assert u.shape == v.shape == w.shape
            assert np.allclose(u, v, rtol=0, atol=1e-10) and np.allclose(u, w, rtol=0, atol=1e-10)


def test_basic_interval_reflects_the_percentiles(example):
    from itemtransfer._stats import basic_interval, interval, percentile_interval
    boot = np.random.default_rng(0).normal(0.4, 0.05, 500)       # resampled values centred below the estimate
    lo, hi = percentile_interval(boot)
    blo, bhi = basic_interval(0.5, boot)
    assert np.isclose(blo, 1.0 - hi) and np.isclose(bhi, 1.0 - lo)
    assert hi < 0.5 and blo > hi and bhi > hi          # shifted against the downward bias
    assert interval(0.5, boot, "basic") == (blo, bhi)
    assert all(np.isnan(basic_interval(np.nan, boot)))
    trials, items = example
    kw = dict(n_boot=80, n_splits=20, seed=4)
    a = it.transfer(trials, items, ["x"], **kw).table.iloc[0]
    b = it.transfer(trials, items, ["x"], interval_type="basic", **kw).table.iloc[0]
    assert np.isclose(b["ordering_lo"], 2 * a["ordering"] - a["ordering_hi"])
    assert np.isclose(b["calibration_slope_hi"], 2 * a["calibration_slope"] - a["calibration_slope_lo"])
    with pytest.raises(ValueError, match="basic"):
        it.transfer(trials, items, ["x"], n_boot=10, interval_type="other")


def test_ordering_interval_items_only_contains_estimate_and_differs_from_two_way(example):
    trials, items = example
    a = it.transfer(trials, items, ["x"], n_boot=300, n_splits=20, seed=3)
    b = it.transfer(trials, items, ["x"], n_boot=300, n_splits=20, seed=3, ordering_boot="two-way")
    assert a.settings["ordering_boot"] == "items"
    # all other statistics are untouched by the choice
    for col in ["calibration_slope_lo", "calibration_slope_hi", "logloss_reduction_lo", "train_slope_hi"]:
        assert np.allclose(a.table[col], b.table[col])
    assert (a.table["ordering_lo"] <= a.table["ordering"]).all() and (a.table["ordering"] <= a.table["ordering_hi"]).all()
    # the two-way resamples are centred lower than the items-only resamples
    for key in a.bootstrap:
        assert a.bootstrap[key]["ordering"].mean() > b.bootstrap[key]["ordering"].mean()
    with pytest.raises(ValueError):
        it.transfer(trials, items, ["x"], n_boot=0, ordering_boot="participants")


def test_scale_reading_follows_the_tolerance(example):
    trials, items = example
    wide = it.transfer(trials, items, ["x"], n_boot=200, n_splits=20, seed=3, tolerance=(-100, 100)).table
    assert (wide["scale_reading"] == "within tolerance").all()
    narrow = it.transfer(trials, items, ["x"], n_boot=200, n_splits=20, seed=3, tolerance=(50, 60)).table
    assert (narrow["scale_reading"] == "outside tolerance").all()
    t = it.transfer(trials, items, ["x"], n_boot=200, n_splits=20, seed=3, tolerance=(0.999, 1.001)).table
    assert set(t["scale_reading"]) <= {"undetermined", "outside tolerance"}
    assert it.transfer(trials, items, ["x"], n_boot=200, n_splits=20, seed=3, tolerance=None).table["scale_reading"].isna().all()
    assert it.transfer(trials, items, ["x"], n_boot=0, n_splits=20).table["scale_reading"].isna().all()
    with pytest.raises(ValueError):
        it.transfer(trials, items, ["x"], n_boot=0, tolerance=(1.2, 0.8))


def test_measures_without_variation_are_reported_as_missing(example):
    trials, items = example
    fams = list(pd.unique(items["family"]))
    flat = items.assign(flat=1.0)
    with pytest.warns(UserWarning, match="constant within every training family"):
        t = it.transfer(trials, flat, ["flat"], n_boot=50, n_splits=10).table
    assert t["calibration_slope"].isna().all() and (t["scale_reading"] == "not applicable").all()
    one = items.assign(partly=np.where(items["family"] == fams[0], 0.0, items["x"]))
    with pytest.warns(UserWarning, match="constant in the held-out family"):
        t = it.transfer(trials, one, ["partly"], n_boot=50, n_splits=10).table.set_index("family")
    assert np.isnan(t.at[fams[0], "calibration_slope"]) and t.at[fams[0], "scale_reading"] == "not applicable"
    assert np.isfinite(t.at[fams[1], "calibration_slope"])


def test_weak_training_relation_is_named_in_the_scale_reading(example):
    trials, items = example
    t = it.transfer(trials, items, ["x_null"], n_boot=300, n_splits=10, seed=2).table
    assert (t["scale_reading"] == "weak training relation").any()


def test_items_without_responses_are_announced(example):
    trials, items = example
    extra = pd.concat([items, items.iloc[[0]].assign(item="never shown")], ignore_index=True)
    with pytest.warns(UserWarning, match="have no response"):
        it.transfer(trials, extra, ["x"], n_boot=0, n_splits=10)
