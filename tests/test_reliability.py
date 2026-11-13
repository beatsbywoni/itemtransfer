import numpy as np
import pandas as pd
import pytest

import itemtransfer as it
from itemtransfer._data import sample_matrices, validate_trials
from itemtransfer._stats import elogit, spearman_brown
from itemtransfer.reliability import _half_masks, _split_half
from scipy.stats import pearsonr, spearmanr


def test_split_half_matches_reference_loop(small):
    trials, _ = small
    t = validate_trials(trials)
    _, _, N, S = sample_matrices(t, "A1")
    masks = _half_masks(N.shape[0], 30, np.random.default_rng(5))
    res, dropped = _split_half(N, S, masks)
    assert (dropped == 0).all()
    for k in range(30):
        a, b = masks[k] > 0, masks[k] == 0
        nA, sA, nB, sB = N[a].sum(0), S[a].sum(0), N[b].sum(0), S[b].sum(0)
        r1 = pearsonr(elogit(nA, sA), elogit(nB, sB))[0]
        r2 = spearmanr(sA / nA, sB / nB).correlation
        assert np.isclose(res[k, 0], spearman_brown(r1))
        assert np.isclose(res[k, 1], spearman_brown(r2))


def test_split_half_with_incomplete_exposure(example):
    trials, _ = example
    out = it.reliability(trials, samples=["C1"], n_splits=100, seed=1)
    assert out["n_splits"].iloc[0] == 100
    assert 0.3 < out["logit_sb"].iloc[0] < 1.0
    assert out["trials_per_item_min"].iloc[0] < 35


def test_reliability_table_and_seed(small):
    trials, _ = small
    a = it.reliability(trials, n_splits=200, seed=4)
    b = it.reliability(trials, n_splits=200, seed=4)
    pd.testing.assert_frame_equal(a, b)
    assert list(a["sample"]) == ["A1", "B1", "C1"]
    assert (a["logit_sb_lo"] <= a["logit_sb"]).all() and (a["logit_sb"] <= a["logit_sb_hi"]).all()
    assert (a["n_participants"] == 40).all() and (a["n_items"] == 60).all()
    assert (a["trials_per_item_median"] == 40).all()


def test_reliability_grows_with_participants():
    def rel(n):
        d = it.Design([it.FamilyDesign("A", 80, ("uniform", -1, 1), [it.SampleDesign("A1", n)]),
                       it.FamilyDesign("B", 10, ("uniform", -1, 1), [it.SampleDesign("B1", 5)])], slope=1.5)
        trials, _ = it.simulate(d, seed=2)
        return it.reliability(trials, samples=["A1"], n_splits=200)["logit_sb"].iloc[0]
    assert rel(12) < rel(48) < rel(200)
    assert rel(200) > 0.9


def test_agreement_of_two_samples_with_the_same_item_difficulties():
    d = it.Design([it.FamilyDesign("A", 100, ("uniform", -1, 1),
                                   [it.SampleDesign("A1", 40, intercept=0.5), it.SampleDesign("A2", 40, intercept=0.0)]),
                   it.FamilyDesign("B", 10, ("uniform", -1, 1), [it.SampleDesign("B1", 5)])], slope=1.5, item_sd=0.6)
    trials, _ = it.simulate(d, seed=3)
    ag = it.agreement(trials, "A1", "A2", n_boot=300, n_splits=200, seed=1).iloc[0]
    assert ag["n_shared"] == 100 and not ag["same_participants"]
    assert 0.5 < ag["r_logit"] < ag["r_corrected"]
    assert 0.85 < ag["r_corrected"] < 1.15
    assert ag["r_logit_lo"] < ag["r_logit"] < ag["r_logit_hi"]
    assert ag["r_corrected_lo"] < ag["r_corrected"] < ag["r_corrected_hi"]
    assert "r_disjoint" not in ag.index


def test_agreement_same_participants(small):
    trials, _ = small
    t = trials[trials["sample"] == "A1"].copy()
    half = t.groupby(["participant"]).cumcount() % 2
    t["sample"] = np.where(half == 0, "s1", "s2")  # every participant in both, different items -> no shared items
    with pytest.raises(ValueError, match="share 0 item"):
        it.agreement(t, "s1", "s2")
    # two sessions on the same items by the same participants
    d = it.Design([it.FamilyDesign("A", 60, ("uniform", -1, 1), [it.SampleDesign("A1", 30, repeats=2)]),
                   it.FamilyDesign("B", 10, ("uniform", -1, 1), [it.SampleDesign("B1", 5)])], slope=1.5)
    tr, _ = it.simulate(d, seed=4)
    a = tr[tr["sample"] == "A1"].copy()
    a["sample"] = np.where(a.groupby(["participant", "item"]).cumcount() == 0, "session 1", "session 2")
    ag = it.agreement(a, "session 1", "session 2", n_boot=100, n_splits=100).iloc[0]
    assert ag["same_participants"]
    assert np.isfinite(ag["r_disjoint"]) and ag["r_disjoint"] < ag["r_corrected"]
    assert 0.7 < ag["r_disjoint_corrected"] < 1.3


def test_agreement_unknown_sample(small):
    trials, _ = small
    with pytest.raises(ValueError, match="has no trials"):
        it.agreement(trials, "A1", "nope")


def test_split_half_does_not_depend_on_chunking(example):
    """Blocks of splits bound memory for samples with many items; the estimates are unchanged."""
    from itemtransfer._data import sample_matrices, validate_trials
    t = validate_trials(example[0])
    _, _, N, S = sample_matrices(t, "C1")          # each participant saw part of the items
    masks = _half_masks(N.shape[0], 57, np.random.default_rng(2))
    a, da = _split_half(N, S, masks)
    b, db = _split_half(N, S, masks, chunk_elems=1)
    c, dc = _split_half(N, S, masks, chunk_elems=10 * N.shape[1])
    assert a.shape == b.shape == c.shape == (57, 2)
    assert np.allclose(a, b, equal_nan=True) and np.allclose(a, c, equal_nan=True)
    assert np.array_equal(da, db) and np.array_equal(da, dc)
