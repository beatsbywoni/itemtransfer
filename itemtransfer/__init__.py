"""itemtransfer: leave-one-family-out transfer validation of item-level difficulty measures.

The package implements a five-step procedure for any task with binary item
responses:

1. recompute the measures (done by the user, outside this package);
2. reliability ceiling: :func:`reliability`, :func:`agreement`;
3. transfer with three criteria (ordering, scale, prediction): :func:`transfer`;
4. design diagnostics: :func:`diagnose`;
5. uncertainty and interval checks: bootstrap intervals in :func:`transfer`
   and :func:`agreement`, and :func:`simulate`, :func:`design_from_data`,
   :func:`check_intervals`.

:func:`report` runs steps 2 to 5 in one call.
"""
from ._data import validate_items, validate_trials
from ._fit import LogitFit, fit_logit
from .datasets import example_design, load_example
from .diagnose import detect_levels, diagnose
from .plotting import plot_transfer
from .reliability import agreement, reliability
from .report import report
from .simulate import Design, FamilyDesign, SampleDesign, check_intervals, design_from_data, simulate
from .transfer import TransferResult, transfer

__version__ = "0.2.0"

__all__ = [
    "reliability", "agreement", "transfer", "TransferResult", "diagnose", "detect_levels",
    "simulate", "check_intervals", "design_from_data", "Design", "FamilyDesign", "SampleDesign",
    "report", "plot_transfer", "load_example", "example_design", "fit_logit", "LogitFit",
    "validate_trials", "validate_items", "__version__",
]
