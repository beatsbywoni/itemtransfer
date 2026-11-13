import numpy as np
import pandas as pd
import pytest

import itemtransfer as it


def test_missing_column(small):
    trials, items = small
    with pytest.raises(ValueError, match="missing the column"):
        it.transfer(trials.drop(columns=["participant"]), items, ["x"], n_boot=0)
    with pytest.raises(ValueError, match="missing the column"):
        it.transfer(trials, items.drop(columns=["x"]), ["x"], n_boot=0)


def test_not_a_dataframe(small):
    trials, items = small
    with pytest.raises(TypeError):
        it.reliability(trials.to_numpy())
    with pytest.raises(TypeError):
        it.transfer(trials, items.to_dict(), ["x"])


def test_outcome_must_be_binary(small):
    trials, items = small
    bad = trials.copy()
    bad.loc[bad.index[0], "correct"] = 2
    with pytest.raises(ValueError, match="binary"):
        it.transfer(bad, items, ["x"], n_boot=0)
    bad["correct"] = "yes"
    with pytest.raises(ValueError, match="binary"):
        it.reliability(bad)


def test_boolean_outcome_is_accepted(small):
    trials, items = small
    b = trials.assign(correct=trials["correct"].astype(bool))
    r1 = it.transfer(trials, items, ["x"], n_boot=0, n_splits=20).table
    r2 = it.transfer(b, items, ["x"], n_boot=0, n_splits=20).table
    assert np.allclose(r1["calibration_slope"], r2["calibration_slope"])


def test_missing_values(small):
    trials, items = small
    bad = trials.copy().astype({"correct": float})
    bad.loc[bad.index[:3], "correct"] = np.nan
    with pytest.raises(ValueError, match="missing values"):
        it.transfer(bad, items, ["x"], n_boot=0)
    bad_items = items.copy()
    bad_items.loc[bad_items.index[0], "x"] = np.nan
    with pytest.raises(ValueError, match="missing or non-finite"):
        it.transfer(trials, bad_items, ["x"], n_boot=0)


def test_families_must_not_share_items(small):
    trials, items = small
    dup = pd.concat([items, items.iloc[[0]].assign(family="B")])
    with pytest.raises(ValueError, match="must not share items"):
        it.transfer(trials, dup, ["x"], n_boot=0)
    bad = trials.copy()
    first_item = bad["item"].iloc[0]
    rows = bad[bad["item"] == first_item].index[:2]
    bad.loc[rows, "family"] = "B"
    with pytest.raises(ValueError, match="must not share items"):
        it.reliability(bad)


def test_family_conflict_between_tables(small):
    trials, items = small
    wrong = items.copy()
    wrong.loc[wrong.index[0], "family"] = "C"
    with pytest.raises(ValueError, match="differs between"):
        it.transfer(trials, wrong, ["x"], n_boot=0)


def test_sample_spanning_two_families(small):
    trials, items = small
    bad = trials.assign(sample="one")
    with pytest.raises(ValueError, match="one family only"):
        it.transfer(bad, items, ["x"], n_boot=0)


def test_item_absent_from_items_table(small):
    trials, items = small
    with pytest.raises(ValueError, match="absent from `items`"):
        it.transfer(trials, items.iloc[5:], ["x"], n_boot=0)


def test_needs_two_families(small):
    trials, items = small
    with pytest.raises(ValueError, match="at least two item families"):
        it.transfer(trials[trials["family"] == "A"], items[items["family"] == "A"], ["x"], n_boot=0)


def test_bad_options(small):
    trials, items = small
    with pytest.raises(ValueError, match="weights"):
        it.transfer(trials, items, ["x"], weights="participants")
    with pytest.raises(ValueError, match="not a sample of family"):
        it.transfer(trials, items, ["x"], evaluate={"A": "B1"}, n_boot=0)
    with pytest.raises(ValueError, match="Unknown held-out"):
        it.transfer(trials, items, ["x"], holdout=["Z"], n_boot=0)
    with pytest.raises(ValueError, match="Unknown keys"):
        it.transfer(trials, items, ["x"], columns={"subject": "participant"})
    with pytest.raises(ValueError, match="duplicated"):
        it.transfer(trials, items, ["x", "x"], n_boot=0)


def test_column_mapping(small):
    trials, items = small
    t2 = trials.rename(columns={"participant": "pid", "item": "stimulus", "family": "set", "sample": "group",
                                "correct": "acc"})
    i2 = items.rename(columns={"item": "stimulus", "family": "set"})
    cols = {"participant": "pid", "item": "stimulus", "family": "set", "sample": "group", "correct": "acc"}
    a = it.transfer(trials, items, ["x"], n_boot=0, n_splits=20, seed=3).table
    b = it.transfer(t2, i2, ["x"], n_boot=0, n_splits=20, seed=3, columns=cols).table
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(it.reliability(trials, n_splits=50), it.reliability(t2, n_splits=50, columns=cols))


def test_family_column_optional_in_trials(small):
    trials, items = small
    a = it.transfer(trials, items, ["x"], n_boot=0, n_splits=20, seed=3).table
    b = it.transfer(trials.drop(columns=["family"]), items, ["x"], n_boot=0, n_splits=20, seed=3).table
    pd.testing.assert_frame_equal(a, b)
