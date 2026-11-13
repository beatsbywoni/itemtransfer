import numpy as np
import pandas as pd
import pytest

import itemtransfer as it
from itemtransfer._data import prepare
from itemtransfer.simulate import _simulate_data, _to_frames

from conftest import make_design


def test_simulate_shapes_and_seed():
    design = it.example_design()
    trials, items = it.simulate(design, seed=3)
    t2, i2 = it.simulate(design, seed=3)
    pd.testing.assert_frame_equal(trials, t2)
    pd.testing.assert_frame_equal(items, i2)
    assert list(trials.columns) == ["participant", "item", "family", "sample", "correct"]
    assert list(items.columns) == ["item", "family", "x", "x2", "x_null"]
    assert len(items) == 168 and len(trials) == 30 * 60 + 25 * 40 + 40 * 48 + 35 * 40
    # sample A2 sees the first 40 items of family A; each C1 participant sees 40 of 60 items
    assert trials[trials["sample"] == "A2"]["item"].nunique() == 40
    per = trials[trials["sample"] == "C1"].groupby("participant")["item"].nunique()
    assert (per == 40).all() and trials[trials["sample"] == "C1"]["item"].nunique() == 60
    # two designed levels in family C
    xc = items.loc[items["family"] == "C", "x"]
    assert ((xc - 0.2).abs() < 0.031).sum() == 30 and ((xc - 0.8).abs() < 0.031).sum() == 30
    assert abs(np.corrcoef(items["x2"], items["x_null"])[0, 1]) < 0.25


def test_frames_round_trip_to_internal_counts():
    design = make_design(second_measure=0.4)
    design.families[0].samples[0].repeats = 3
    data = _simulate_data(design, np.random.default_rng(1))
    trials, items = _to_frames(data)
    back = prepare(trials, items, design.measures())
    for name, smp in data.samples.items():
        assert np.array_equal(smp.N, back.samples[name].N) and np.array_equal(smp.S, back.samples[name].S)
    for f in data.families:
        assert np.allclose(data.X[f], back.X[f])


def test_second_measure_correlation_and_values():
    d = it.Design([it.FamilyDesign("A", 0, ("values", np.linspace(1, 2, 400)), [it.SampleDesign("A1", 5)]),
                   it.FamilyDesign("B", 300, ("normal", 0.0, 1.0), [it.SampleDesign("B1", 5)])],
                  second_measure=0.7, null_measure=False)
    _, items = it.simulate(d, seed=2)
    a = items[items["family"] == "A"]
    assert np.allclose(np.sort(a["x"]), np.linspace(1, 2, 400))
    assert abs(np.corrcoef(a["x"], a["x2"])[0, 1] - 0.7) < 0.08


def test_design_errors():
    with pytest.raises(ValueError, match="at least two"):
        it.simulate(it.Design([it.FamilyDesign("A", 10, samples=[it.SampleDesign("A1", 5)])]))
    with pytest.raises(ValueError, match="link"):
        it.simulate(make_design(link="probit"))
    d = make_design(link="log")  # uniform(-1, 1) is not positive
    with pytest.raises(ValueError, match="positive"):
        it.simulate(d)
    with pytest.raises(ValueError, match="no sample"):
        it.simulate(it.Design([it.FamilyDesign("A", 10), it.FamilyDesign("B", 10)]))
    with pytest.raises(TypeError):
        it.simulate({"families": []})


def test_check_intervals_small_run_and_parallel_equivalence():
    design = make_design(n_items=40, n_participants=25)
    a = it.check_intervals(design, n_sim=12, n_boot=60, seed=4, target_scale=(10, 4), target_reps=3)
    b = it.check_intervals(design, n_sim=12, n_boot=60, seed=4, target_scale=(10, 4), target_reps=3, n_jobs=2)
    pd.testing.assert_frame_equal(a, b)
    assert list(a["measure"].unique()) == ["x", "x_null"] and len(a) == 6
    x = a[a["measure"] == "x"]
    assert np.allclose(x["target"], 1.0, atol=0.12)
    assert (x["coverage"] >= 0.6).all() and (x["rate_excludes_0"] == 1.0).all()
    nl = a[a["measure"] == "x_null"]
    assert nl["target"].isna().all() and (nl["rate_excludes_0"] <= 0.25).all()
    assert (nl["rate_weak_training"] >= 0.6).all()


def test_check_intervals_target_is_ratio_for_family_slopes_and_log_link():
    design = make_design(slopes={"C": 1.0}, n_items=40, n_participants=25, participant_sd=0.0, item_sd=0.0,
                         null_measure=False)
    out = it.check_intervals(design, n_sim=4, n_boot=40, seed=1, target_scale=(10, 5), target_reps=2)
    assert abs(out.set_index("family").at["C", "target"] - 0.5) < 0.05
    # effect linear in log(x): a family with small values has a steeper slope per unit
    log_design = it.Design(
        families=[it.FamilyDesign("A", 40, ("uniform", 0.5, 1.0), [it.SampleDesign("A1", 25)]),
                  it.FamilyDesign("B", 40, ("uniform", 0.5, 1.0), [it.SampleDesign("B1", 25)]),
                  it.FamilyDesign("C", 40, ("uniform", 0.02, 0.2), [it.SampleDesign("C1", 25)])],
        slope=1.0, link="log", participant_sd=0.0, item_sd=0.0, null_measure=False)
    out = it.check_intervals(log_design, n_sim=4, n_boot=40, seed=1, target_scale=(10, 5), target_reps=2)
    assert out.set_index("family").at["C", "target"] > 3


def test_check_intervals_prediction_columns():
    design = make_design(n_items=30, n_participants=20)
    out = it.check_intervals(design, n_sim=4, n_boot=40, seed=2, prediction=True, target_scale=(5, 3), target_reps=2,
                             n_splits=20)
    assert {"logloss_target", "logloss_mean", "logloss_coverage", "logloss_rate_above_0"} <= set(out.columns)
    assert (out.loc[out["measure"] == "x", "logloss_target"] > 0.02).all()


def test_design_from_data(example):
    trials, items = example
    design = it.design_from_data(trials, items, "x", seed=1)
    truth = it.example_design()
    assert [f.name for f in design.families] == ["A", "B", "C"]
    for fam, ref in zip(design.families, truth.families):
        assert fam.measure[0] == "values" and len(fam.measure[1]) == ref.n_items
        for s, r in zip(fam.samples, ref.samples):
            assert (s.name, s.n_participants, s.repeats) == (r.name, r.n_participants, r.repeats)
            assert s.items_per_participant == r.items_per_participant
            assert abs(s.intercept - r.intercept) < 0.6
    assert design.families[0].samples[1].items == list(range(40))
    assert abs(design.slope - (-3.0)) < 0.6
    assert 0.5 < design.participant_sd < 1.1 and 0.25 < design.item_sd < 0.8
    assert design.measures() == ["x", "x_null"]
    # calibration moves the slope away from the attenuated marginal estimate
    raw = it.design_from_data(trials, items, "x", calibrate=0)
    assert abs(design.slope) > abs(raw.slope)
    # the design can be simulated and analysed
    t2, i2 = it.simulate(design, seed=2)
    assert abs(len(t2) - len(trials)) < 50 and len(i2) == len(items)
    own = it.design_from_data(trials, items, "x", common_slope=False, calibrate=1)
    assert all(f.slope is not None and f.slope < 0 for f in own.families)
