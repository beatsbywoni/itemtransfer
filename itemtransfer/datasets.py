"""The small synthetic example data set shipped with the package."""
from __future__ import annotations

from importlib import resources

import pandas as pd

from .simulate import Design, FamilyDesign, SampleDesign, simulate

__all__ = ["example_design", "load_example"]

EXAMPLE_SEED = 2026


def example_design():
    """Design that generated the bundled example data.

    Three item families share one true slope of the measure ``x`` (-3
    logits per unit). Family ``A`` has two samples that share 40 items,
    family ``B`` has a continuous range of ``x``, and family ``C`` has two
    designed levels of ``x`` and participants who each respond to 40 of its
    60 items. ``x2`` is correlated with ``x`` (r = .6) and has no effect of
    its own; ``x_null`` is unrelated to accuracy.

    Returns
    -------
    Design
    """
    return Design(
        families=[
            FamilyDesign("A", 60, ("uniform", 0.1, 1.0),
                         [SampleDesign("A1", 30, intercept=2.3), SampleDesign("A2", 25, intercept=2.0, items=40)]),
            FamilyDesign("B", 48, ("uniform", 0.2, 0.9), [SampleDesign("B1", 40, intercept=2.6)]),
            FamilyDesign("C", 60, ("levels", [0.2, 0.8], 0.03),
                         [SampleDesign("C1", 35, items_per_participant=40, intercept=2.2)]),
        ],
        slope=-3.0, participant_sd=0.8, item_sd=0.5, second_measure=0.6, second_slope=0.0, null_measure=True,
    )


def load_example():
    """Load the bundled synthetic example data.

    Returns
    -------
    trials : pandas.DataFrame
        6,120 responses with the columns ``participant``, ``item``,
        ``family``, ``sample``, ``correct``.
    items : pandas.DataFrame
        168 items with the columns ``item``, ``family``, ``x``, ``x2``,
        ``x_null``.

    Notes
    -----
    The data were generated with ``simulate(example_design(), seed=2026)``.
    """
    base = resources.files("itemtransfer") / "data"
    with resources.as_file(base / "example_trials.csv") as p:
        trials = pd.read_csv(p)
    with resources.as_file(base / "example_items.csv") as p:
        items = pd.read_csv(p)
    return trials, items


def _write_example(directory):
    """Regenerate the bundled CSV files (used when building the package)."""
    trials, items = simulate(example_design(), seed=EXAMPLE_SEED)
    trials.to_csv(f"{directory}/example_trials.csv", index=False)
    items.round(6).to_csv(f"{directory}/example_items.csv", index=False)
