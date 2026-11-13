import numpy as np
import pytest

import itemtransfer as it


def make_design(slope=2.0, slopes=None, n_items=60, n_participants=40, participant_sd=0.5, item_sd=0.3, **kw):
    """Three families with a continuous measure; optional per-family slopes."""
    slopes = slopes or {}
    fams = [
        it.FamilyDesign(name, n_items, ("uniform", -1.0, 1.0),
                        [it.SampleDesign(f"{name}1", n_participants, intercept=a)], slope=slopes.get(name))
        for name, a in [("A", 0.5), ("B", 0.8), ("C", 0.2)]
    ]
    return it.Design(families=fams, slope=slope, participant_sd=participant_sd, item_sd=item_sd, **kw)


@pytest.fixture(scope="session")
def small():
    """A small data set: common slope 2, a correlated second measure and a null measure."""
    design = make_design(second_measure=0.5)
    trials, items = it.simulate(design, seed=11)
    return trials, items


@pytest.fixture(scope="session")
def example():
    return it.load_example()


@pytest.fixture()
def rng():
    return np.random.default_rng(123)
