import numpy as np
import pytest

import itemtransfer as it

from conftest import make_design


def test_detect_levels():
    rng = np.random.default_rng(0)
    lev, info = it.detect_levels(rng.uniform(0, 1, 80))
    assert lev is None and info["n_levels"] == 0 and info["kind"] == "none"
    lev, info = it.detect_levels(rng.normal(0, 1, 200))
    assert lev is None
    x = np.concatenate([rng.uniform(0.027, 0.032, 36), rng.uniform(0.089, 0.105, 36)])
    lev, info = it.detect_levels(x)
    assert info["n_levels"] == 2 and info["kind"] == "clustered" and info["gap_ratio"] > 2
    assert (lev[:36] == 0).all() and (lev[36:] == 1).all()
    x3 = np.concatenate([np.full(10, 1.0), np.full(10, 2.0), np.full(10, 5.0)]) + rng.uniform(-0.01, 0.01, 30)
    lev, info = it.detect_levels(x3)
    assert info["n_levels"] == 3 and list(np.bincount(lev)) == [10, 10, 10]
    lev, info = it.detect_levels(np.array([0, 1, 2, 3] * 5))
    assert info["n_levels"] == 4 and info["kind"] == "discrete"
    lev, info = it.detect_levels(np.ones(10))
    assert lev is None and info["kind"] == "constant"


@pytest.fixture(scope="module")
def two_level():
    design = it.Design(
        families=[
            it.FamilyDesign("A", 60, ("uniform", 0.0, 1.0), [it.SampleDesign("A1", 40, intercept=-1.0)]),
            it.FamilyDesign("B", 60, ("uniform", 0.0, 1.0), [it.SampleDesign("B1", 40, intercept=-1.0)]),
            it.FamilyDesign("C", 60, ("levels", [0.2, 0.8], 0.02), [it.SampleDesign("C1", 40, intercept=-1.0)]),
        ],
        slope=3.0, participant_sd=0.5, item_sd=0.4, second_measure=0.9,
    )
    trials, items = it.simulate(design, seed=7)
    return trials, items, it.diagnose(trials, items, ["x", "x2", "x_null"], n_boot=300, n_splits=100, seed=3)


def test_two_level_design_triggers_level_warning(two_level):
    _, _, d = two_level
    lv = d["levels"].set_index(["family", "measure"])
    assert lv.at[("C", "x"), "n_levels"] == 2
    assert lv.at[("A", "x"), "n_levels"] == 0 and lv.at[("C", "x_null"), "n_levels"] == 0
    base = d["level_baseline"]
    assert list(base["family"]) == ["C"] and list(base["measure"]) == ["x"]
    row = base.iloc[0]
    # with two levels and no within-level relation, the indicator predicts about as well as the measure
    assert abs(row["logloss_reduction_levels"] - row["logloss_reduction_measure"]) < 0.03
    assert row["logloss_reduction_levels"] > 0.03
    assert row["ordering_levels"] > 0.5 and row["level_accuracy_r"] > 0.5
    w = d["within_level"]
    assert len(w) == 2 and (w["n_items"] == 30).all()
    assert (w["measure_max"] - w["measure_min"] < 0.05).all()
    assert w["accuracy_mean"].iloc[1] > w["accuracy_mean"].iloc[0]
    msgs = [m for m in d["warnings"] if "takes 2 levels in held-out family 'C'" in m]
    assert len(msgs) == 1 and "'x'" in msgs[0]


def test_level_baseline_uses_the_transfer_splits(two_level):
    _, _, d = two_level
    tab = d["transfer"].table.set_index(["family", "model"])
    assert np.isclose(d["level_baseline"]["logloss_reduction_measure"].iloc[0], tab.at[("C", "x"), "logloss_reduction"])
    wt = d["weighting"].set_index(["family", "model"])
    assert np.isclose(wt.at[("C", "x"), "logloss_reduction_trials"], tab.at[("C", "x"), "logloss_reduction"])
    assert np.isclose(wt.at[("C", "x"), "calibration_slope_trials"], tab.at[("C", "x"), "calibration_slope"])


def test_weak_training_flag_and_collinearity(two_level):
    _, _, d = two_level
    weak = d["weak_training"].set_index(["family", "measure"])
    assert weak.loc[(slice(None), "x_null"), "weak"].all()
    assert not weak.loc[(slice(None), "x"), "weak"].any()
    assert sum("'x_null'" in m and "interval that includes 0" in m for m in d["warnings"]) == 3
    corr = d["measure_correlations"]
    xx2 = corr[(corr["measure_a"] == "x") & (corr["measure_b"] == "x2")]
    assert (xx2["spearman"] > 0.7).all()
    assert sum("strongly correlated" in m for m in d["warnings"]) == 3
    assert not any("'x_null'" in m and "strongly correlated" in m for m in d["warnings"])


def test_range_overlap_warning():
    design = it.Design(
        families=[
            it.FamilyDesign("A", 60, ("uniform", 0.0, 0.3), [it.SampleDesign("A1", 40)]),
            it.FamilyDesign("B", 60, ("uniform", 0.0, 0.3), [it.SampleDesign("B1", 40)]),
            it.FamilyDesign("C", 80, ("uniform", 0.0, 1.0), [it.SampleDesign("C1", 40)]),
        ],
        slope=3.0, participant_sd=0.5, item_sd=0.3, null_measure=False,
    )
    trials, items = it.simulate(design, seed=5)
    d = it.diagnose(trials, items, ["x"], n_boot=100, n_splits=50, seed=1)
    rg = d["range"].set_index("family")
    assert rg.at["C", "share_inside_training"] < 0.5
    assert rg.at["A", "share_inside_training"] > 0.9
    assert rg.at["C", "n_heldout_common"] < 40 and rg.at["C", "common_high"] < 0.31
    assert np.isfinite(rg.at["C", "calibration_slope_common"])
    assert rg.at["C", "calibration_slope_common_lo"] < rg.at["C", "calibration_slope_common"] < rg.at["C", "calibration_slope_common_hi"]
    assert any("of the items of held-out family 'C' lie inside the range" in m for m in d["warnings"])
    # held-out A: the training families cover a wider range; items of C are restricted
    assert rg.at["A", "n_train_common"] < 140
    # explicit limits apply to all families
    d2 = it.diagnose(trials, items, ["x"], range_limits={"x": (None, 0.3)}, n_boot=0, n_splits=50, seed=1)
    r2 = d2["range"].set_index("family")
    assert r2.at["C", "common_high"] == 0.3 and np.isinf(r2.at["C", "common_low"])
    assert np.isclose(r2.at["C", "calibration_slope_common"], rg.at["C", "calibration_slope_common"], rtol=0.2)
    assert any("No bootstrap was run" in m for m in d2["warnings"])


def test_range_check_equals_transfer_on_filtered_data(example):
    trials, items = example
    lim = (0.3, 0.7)
    d = it.diagnose(trials, items, ["x"], range_limits={"x": lim}, n_boot=0, n_splits=20)
    keep = items[(items["x"] >= lim[0]) & (items["x"] <= lim[1])]
    tab = it.transfer(trials[trials["item"].isin(keep["item"])], keep, ["x"], n_boot=0, n_splits=20).table
    rg = d["range"].set_index("family")
    assert list(tab["family"]) == ["A", "B"]  # family C has no item in the range
    assert np.isnan(rg.at["C", "calibration_slope_common"]) and rg.at["C", "n_heldout_common"] == 0
    rg = rg.loc[["A", "B"]]
    assert np.allclose(rg["calibration_slope_common"], tab["calibration_slope"])
    assert np.allclose(rg["ordering_common"], tab["ordering"])
    assert np.allclose(rg["train_slope_common"], tab["train_slope"])


def test_weighting_sensitivity_warning():
    # two training samples of very different size and different slopes
    design = it.Design(
        families=[
            it.FamilyDesign("A", 60, ("uniform", -1, 1), [it.SampleDesign("A1", 200)], slope=3.0),
            it.FamilyDesign("B", 60, ("uniform", -1, 1), [it.SampleDesign("B1", 15)], slope=1.0),
            it.FamilyDesign("C", 60, ("uniform", -1, 1), [it.SampleDesign("C1", 40)], slope=2.0),
        ],
        participant_sd=0.3, item_sd=0.2, null_measure=False,
    )
    trials, items = it.simulate(design, seed=8)
    d = it.diagnose(trials, items, ["x"], n_boot=100, n_splits=50, seed=1)
    wt = d["weighting"].set_index(["family", "model"])
    assert wt.at[("C", "x"), "train_slope_trials"] > wt.at[("C", "x"), "train_slope_equal"] + 0.4
    assert wt.at[("C", "x"), "calibration_slope_trials"] < wt.at[("C", "x"), "calibration_slope_equal"]
    assert any("depends on the weighting" in m and "'C'" in m for m in d["warnings"])


def test_diagnose_accepts_a_transfer_result(small):
    trials, items = small
    res = it.transfer(trials, items, ["x", "x_null"], n_boot=100, n_splits=50, seed=2)
    d1 = it.diagnose(trials, items, ["x", "x_null"], result=res)
    d2 = it.diagnose(trials, items, ["x", "x_null"], n_boot=100, n_splits=50, seed=2)
    assert d1["warnings"] == d2["warnings"]
    assert d1["transfer"] is res
    with pytest.raises(TypeError):
        it.diagnose(trials, items, ["x"], result=res.table)


def test_diagnose_boot_batch(example):
    """`boot_batch` is accepted, reused from the transfer result and does not change point estimates."""
    trials, items = example
    res = it.transfer(trials, items, ["x", "x_null"], n_boot=60, n_splits=30, seed=2, boot_batch=25)
    d1 = it.diagnose(trials, items, ["x", "x_null"], result=res, n_boot=60)
    res0 = it.transfer(trials, items, ["x", "x_null"], n_boot=60, n_splits=30, seed=2)
    d0 = it.diagnose(trials, items, ["x", "x_null"], result=res0, n_boot=60)
    import pandas as pd
    cols = ["family", "measure", "share_inside_training", "ordering_common", "calibration_slope_common",
            "train_slope_common"]
    pd.testing.assert_frame_equal(d0["range"][cols], d1["range"][cols])
    assert d1["range"]["calibration_slope_common_lo"].notna().all()
