"""A minimal figure of a transfer result (matplotlib is optional)."""
from __future__ import annotations

import numpy as np

from ._fit import fit_logit

__all__ = ["plot_transfer"]


def plot_transfer(result, model, axes=None):
    """Plot item accuracy against the transferred predictor for each held-out family.

    Each panel shows the held-out items of one family: the transferred
    linear predictor (training slope times measure) on the horizontal axis
    and item accuracy on the vertical axis. The dashed curve keeps the
    trained slope and fits only the intercept (calibration slope fixed at
    1); the solid curve also fits the calibration slope.

    Parameters
    ----------
    result : TransferResult
        Output of :func:`itemtransfer.transfer`.
    model : str
        A measure name or ``"combined"``.
    axes : sequence of matplotlib axes, optional
        One axis per held-out family. By default a new figure is created.

    Returns
    -------
    matplotlib.figure.Figure

    Raises
    ------
    ImportError
        If matplotlib is not installed (``pip install itemtransfer[plot]``).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as err:  # pragma: no cover
        raise ImportError("plot_transfer needs matplotlib: pip install itemtransfer[plot]") from err
    pred = result.predictions[result.predictions["model"] == model]
    if pred.empty:
        raise ValueError(f"Model '{model}' is not in the result; available: {list(result.table['model'].unique())}.")
    fams = list(pred["family"].unique())
    if axes is None:
        fig, axes = plt.subplots(1, len(fams), figsize=(3.6 * len(fams), 3.4), sharey=True, squeeze=False)
        axes = axes[0]
    else:
        axes = np.atleast_1d(axes)
        fig = axes[0].figure
    tab = result.table.set_index(["family", "model"])
    for ax, f in zip(axes, fams):
        d = pred[pred["family"] == f]
        eta = d["linear_predictor"].to_numpy()
        n, s = d["n_trials"].to_numpy(), d["n_correct"].to_numpy()
        ax.scatter(eta, d["accuracy"], s=14, alpha=0.6, color="0.3", linewidths=0)
        grid = np.linspace(eta.min(), eta.max(), 100) if np.ptp(eta) > 0 else np.array([eta.min()])
        fixed = fit_logit(np.ones((len(eta), 1)), n, s)  # start value only
        a = fixed.coef[0]
        for _ in range(50):
            p = 1 / (1 + np.exp(-(a + eta)))
            step = np.sum(s - n * p) / np.sum(n * p * (1 - p))
            a += step
            if abs(step) < 1e-10:
                break
        free = fit_logit(np.column_stack([np.ones(len(eta)), eta]), n, s)
        ax.plot(grid, 1 / (1 + np.exp(-(a + grid))), "--", color="C0", label="trained slope (calibration slope 1)")
        ax.plot(grid, 1 / (1 + np.exp(-(free.coef[0] + free.coef[1] * grid))), "-", color="C1",
                label="fitted calibration slope")
        row = tab.loc[(f, model)]
        ax.set_title(f"held-out family {f}\nslope {row['calibration_slope']:.2f}, ordering {row['ordering']:.2f}",
                     fontsize=9)
        ax.set_xlabel(f"transferred predictor ({model})")
    axes[0].set_ylabel("item accuracy")
    axes[0].legend(fontsize=7, frameon=False, loc="lower right")
    fig.tight_layout()
    return fig
