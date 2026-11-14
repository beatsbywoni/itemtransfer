import numpy as np
import pandas as pd
import pytest

import itemtransfer as it
from itemtransfer.datasets import EXAMPLE_SEED


def test_example_data_matches_its_design(example):
    trials, items = example
    t2, i2 = it.simulate(it.example_design(), seed=EXAMPLE_SEED)
    assert trials.shape == (6120, 5) and items.shape == (168, 5)
    pd.testing.assert_frame_equal(trials, t2)
    assert np.allclose(items[["x", "x2", "x_null"]], i2[["x", "x2", "x_null"]], atol=1e-6)
    assert list(items["item"]) == list(i2["item"])


def test_report_writes_files(example, tmp_path):
    trials, items = example
    out = it.report(trials, items, ["x", "x2", "x_null"], out_dir=tmp_path, n_boot=100, n_splits=50,
                    n_splits_reliability=100, n_sim=6, n_boot_sim=40, seed=1)
    for key in ["reliability", "agreement", "transfer", "predictions", "levels", "level_baseline", "within_level",
                "range", "weak_training", "measure_correlations", "weighting", "interval_check"]:
        assert isinstance(out[key], pd.DataFrame)
        assert (tmp_path / f"{key}.csv").exists()
    assert (tmp_path / "report.md").read_text() == out["markdown"]
    assert (tmp_path / "run_info.json").exists() and (tmp_path / "warnings.txt").exists()
    assert len(out["reliability"]) == 4 and len(out["agreement"]) == 1
    assert out["agreement"]["n_shared"].iloc[0] == 40
    assert len(out["transfer"]) == 12 and len(out["interval_check"]) == 6
    for heading in ["Step 2. Reliability ceiling", "Step 3. Transfer", "Step 4. Design diagnostics",
                    "Step 5. Interval check by simulation"]:
        assert heading in out["markdown"]
    assert any("fall into 2 tight clusters in held-out family 'C'" in w for w in out["warnings"])
    assert out["run_info"]["version"] == it.__version__ and out["run_info"]["seed"] == 1
    back = pd.read_csv(tmp_path / "transfer.csv")
    assert np.allclose(back["calibration_slope"], out["transfer"]["calibration_slope"])


def test_report_reliability_only_sample(example):
    trials, items = example
    out = it.report(trials, items, ["x"], reliability_only=["A2"], n_boot=0, n_splits=20, n_splits_reliability=50)
    assert "A2" in set(out["reliability"]["sample"]) and len(out["agreement"]) == 1
    assert set(out["transfer"]["eval_samples"]) == {"A1", "B1", "C1"}
    ref = it.transfer(trials[trials["sample"] != "A2"], items, ["x"], n_boot=0, n_splits=20).table
    assert np.allclose(out["transfer"]["calibration_slope"], ref["calibration_slope"])
    with pytest.raises(ValueError, match="unknown samples"):
        it.report(trials, items, ["x"], reliability_only=["zz"], n_boot=0)


def test_plot_transfer(example):
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    trials, items = example
    res = it.transfer(trials, items, ["x"], n_boot=0, n_splits=20)
    fig = it.plot_transfer(res, "x")
    assert len(fig.axes) == 3
    with pytest.raises(ValueError, match="not in the result"):
        it.plot_transfer(res, "nope")
