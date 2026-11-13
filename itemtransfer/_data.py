"""Input validation and the internal count representation."""
from __future__ import annotations

import warnings

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

__all__ = ["DEFAULT_COLUMNS", "validate_trials", "validate_items"]

DEFAULT_COLUMNS = {
    "participant": "participant",
    "item": "item",
    "family": "family",
    "sample": "sample",
    "correct": "correct",
}


def _columns(columns):
    cols = dict(DEFAULT_COLUMNS)
    if columns:
        unknown = set(columns) - set(DEFAULT_COLUMNS)
        if unknown:
            raise ValueError(
                f"Unknown keys in `columns`: {sorted(unknown)}. Allowed keys: {sorted(DEFAULT_COLUMNS)}."
            )
        cols.update(columns)
    return cols


def validate_trials(trials, columns=None, require_family=False):
    """Check a trials table and return it with standard column names.

    Parameters
    ----------
    trials : pandas.DataFrame
        One row per response, with a participant, an item, a sample and a
        binary outcome (and optionally the item family).
    columns : dict, optional
        Mapping from the standard names (``participant``, ``item``,
        ``family``, ``sample``, ``correct``) to the column names used in
        ``trials``.
    require_family : bool
        Raise an error when the family column is absent.

    Returns
    -------
    pandas.DataFrame
        A copy with the standard column names, ``correct`` as float 0/1.

    Raises
    ------
    TypeError
        If ``trials`` is not a DataFrame.
    ValueError
        If a column is missing, a value is missing, the outcome is not
        binary, a sample contains items of several families, or an item is
        assigned to several families.
    """
    if not isinstance(trials, pd.DataFrame):
        raise TypeError("`trials` must be a pandas DataFrame with one row per response.")
    cols = _columns(columns)
    needed = ["participant", "item", "sample", "correct"]
    has_family = cols["family"] in trials.columns
    if require_family and not has_family:
        raise ValueError(f"`trials` has no item family column '{cols['family']}'.")
    missing = [cols[k] for k in needed if cols[k] not in trials.columns]
    if missing:
        raise ValueError(
            f"`trials` is missing the column(s) {missing}. Expected columns: "
            f"{[cols[k] for k in needed]} (rename them or pass `columns=`)."
        )
    use = needed + (["family"] if has_family else [])
    dup = [cols[k] for k in use if (trials.columns == cols[k]).sum() > 1]
    if dup:
        raise ValueError(f"`trials` has more than one column named {dup}.")
    t = trials[[cols[k] for k in use]].copy()
    t.columns = use
    if len(t) == 0:
        raise ValueError("`trials` has no rows.")
    na = t.isna().sum()
    if na.any():
        bad = {cols[k]: int(v) for k, v in na.items() if v > 0}
        raise ValueError(
            f"`trials` contains missing values: {bad}. Remove these rows or code them explicitly "
            "(for example a missing response as incorrect) before the analysis."
        )
    y = t["correct"]
    if y.dtype == bool:
        y = y.astype(float)
    try:
        y = y.astype(float)
    except (TypeError, ValueError):
        raise ValueError(f"The outcome column '{cols['correct']}' must be binary (0/1 or boolean).") from None
    if not np.isin(y.to_numpy(), [0.0, 1.0]).all():
        vals = sorted(pd.unique(y))[:6]
        raise ValueError(
            f"The outcome column '{cols['correct']}' must be binary (0/1); found values such as {vals}."
        )
    t["correct"] = y
    if has_family:
        per_item = t.groupby("item", sort=False)["family"].nunique()
        if (per_item > 1).any():
            ex = list(per_item.index[per_item > 1][:5])
            raise ValueError(
                f"Item families must not share items, but {int((per_item > 1).sum())} item(s) occur in more than "
                f"one family (for example {ex}). Give shared items one family, or rename them if they are "
                "different stimuli."
            )
        per_sample = t.groupby("sample", sort=False)["family"].nunique()
        if (per_sample > 1).any():
            ex = list(per_sample.index[per_sample > 1][:5])
            raise ValueError(
                f"Each sample must respond to items of one family only; sample(s) {ex} contain items of "
                "several families. Split such a sample into one sample per family."
            )
    return t


def validate_items(items, measures, columns=None):
    """Check an items table and return it with standard column names.

    Parameters
    ----------
    items : pandas.DataFrame
        One row per item with its family and one column per measure.
    measures : sequence of str
        Names of the measure columns.
    columns : dict, optional
        Column name mapping (see :func:`validate_trials`).

    Returns
    -------
    pandas.DataFrame
        A copy with columns ``item``, ``family`` and the measures.

    Raises
    ------
    TypeError, ValueError
        If the table is malformed: missing columns, duplicated items,
        missing or non-numeric measure values.
    """
    if not isinstance(items, pd.DataFrame):
        raise TypeError("`items` must be a pandas DataFrame with one row per item.")
    if isinstance(measures, str):
        measures = [measures]
    measures = list(measures)
    if len(measures) == 0:
        raise ValueError("`measures` must name at least one measure column of `items`.")
    if len(set(measures)) != len(measures):
        raise ValueError("`measures` contains duplicated names.")
    cols = _columns(columns)
    missing = [c for c in [cols["item"], cols["family"]] + measures if c not in items.columns]
    if missing:
        raise ValueError(f"`items` is missing the column(s) {missing}.")
    it = items[[cols["item"], cols["family"]] + measures].copy()
    it.columns = ["item", "family"] + measures
    if it[["item", "family"]].isna().any().any():
        raise ValueError("`items` contains missing values in the item or family column.")
    dup = it["item"].duplicated()
    if dup.any():
        ex = list(it.loc[dup, "item"].unique()[:5])
        raise ValueError(
            f"`items` must have one row per item and families must not share items; {int(dup.sum())} item(s) "
            f"appear more than once (for example {ex})."
        )
    for m in measures:
        try:
            v = it[m].astype(float)
        except (TypeError, ValueError):
            raise ValueError(f"Measure '{m}' is not numeric.") from None
        n_bad = int((~np.isfinite(v.to_numpy())).sum())
        if n_bad:
            raise ValueError(
                f"Measure '{m}' has {n_bad} missing or non-finite value(s). A measure must be defined for every "
                "item; remove the items for which it is undefined (from `items` and `trials`) or drop the measure."
            )
        it[m] = v
    return it


@dataclass
class Sample:
    """Responses of one sample as participant-by-item count matrices on the item axis of its family."""

    name: str
    family: str
    participants: np.ndarray
    N: np.ndarray  # participants x family items, trials
    S: np.ndarray  # participants x family items, correct responses

    @property
    def n_participants(self):
        return len(self.participants)

    @property
    def n_trials(self):
        return int(self.N.sum())

    def counts(self, wp=None):
        if wp is None:
            return self.N.sum(axis=0), self.S.sum(axis=0)
        return wp @ self.N, wp @ self.S


@dataclass
class Data:
    """Validated data set: families, their items and measures, and their samples."""

    families: list
    measures: list
    items: dict  # family -> array of item labels (sorted)
    X: dict  # family -> items x measures
    samples: dict = field(default_factory=dict)  # sample name -> Sample
    family_samples: dict = field(default_factory=dict)  # family -> list of sample names

    def n_items(self, family):
        return len(self.items[family])


def _count_matrices(t, participants, items):
    pi = pd.Index(participants).get_indexer(t["participant"])
    ii = pd.Index(items).get_indexer(t["item"])
    shape = (len(participants), len(items))
    flat = pi * shape[1] + ii
    N = np.bincount(flat, minlength=shape[0] * shape[1]).astype(float).reshape(shape)
    S = np.bincount(flat, weights=t["correct"].to_numpy(), minlength=shape[0] * shape[1]).reshape(shape)
    return N, S


def _sorted_unique(values):
    """Sorted distinct values (sorted as text when the values cannot be compared)."""
    u = pd.unique(np.asarray(values, dtype=object)) if not isinstance(values, pd.Series) else pd.unique(values)
    try:
        return np.array(sorted(u))
    except TypeError:
        return np.array(sorted(u, key=str), dtype=object)


def prepare(trials, items, measures, columns=None):
    """Validate both tables and build the internal :class:`Data` object."""
    if isinstance(measures, str):
        measures = [measures]
    measures = list(measures)
    it = validate_items(items, measures, columns)
    t = validate_trials(trials, columns)
    fam_of = it.set_index("item")["family"]
    unknown = ~t["item"].isin(fam_of.index)
    if unknown.any():
        ex = list(pd.unique(t.loc[unknown, "item"])[:5])
        raise ValueError(
            f"{int(t.loc[unknown, 'item'].nunique())} item(s) in `trials` are absent from `items` (for example {ex})."
        )
    fam_items = t["item"].map(fam_of)
    if "family" in t.columns:
        differ = fam_items.to_numpy() != t["family"].to_numpy()
        if differ.any():
            ex = list(pd.unique(t.loc[differ, "item"])[:5])
            raise ValueError(
                "The family of an item differs between `trials` and `items` "
                f"(for example items {ex}). Families must not share items."
            )
    t["family"] = fam_items.to_numpy()
    per_sample = t.groupby("sample", sort=False)["family"].nunique()
    if (per_sample > 1).any():
        ex = list(per_sample.index[per_sample > 1][:5])
        raise ValueError(
            f"Each sample must respond to items of one family only; sample(s) {ex} contain items of several "
            "families. Split such a sample into one sample per family."
        )
    answered = it["item"].isin(pd.unique(t["item"]))
    if not answered.all():
        warnings.warn(f"{int((~answered).sum())} item(s) in `items` have no response in `trials` and are left out.",
                      stacklevel=3)
    it = it[answered]
    families = list(_sorted_unique(it["family"]))
    data = Data(families=families, measures=measures, items={}, X={})
    for f in families:
        sub = it[it["family"] == f]
        labels = _sorted_unique(sub["item"])
        data.items[f] = labels
        data.X[f] = sub.set_index("item").loc[labels, measures].to_numpy(dtype=float)
        data.family_samples[f] = []
    groups = dict(tuple(t.groupby("sample", sort=False)))
    for name in _sorted_unique(t["sample"]):
        ts = groups[name]
        f = ts["family"].iloc[0]
        participants = _sorted_unique(ts["participant"])
        N, S = _count_matrices(ts, participants, data.items[f])
        data.samples[name] = Sample(name=name, family=f, participants=participants, N=N, S=S)
        data.family_samples[f].append(name)
    return data


def sample_matrices(t, sample, items=None, participants=None):
    """Count matrices of one sample taken from a validated trials table (used by reliability and agreement)."""
    ts = t[t["sample"] == sample]
    if len(ts) == 0:
        raise ValueError(f"Sample '{sample}' has no trials. Available samples: {list(pd.unique(t['sample']))}.")
    if items is not None:
        ts = ts[ts["item"].isin(items)]
    labels = _sorted_unique(ts["item"]) if items is None else np.asarray(items)
    parts = _sorted_unique(ts["participant"]) if participants is None else np.asarray(participants)
    N, S = _count_matrices(ts, parts, labels)
    return parts, labels, N, S


def restrict(data, keep):
    """Return a copy of ``data`` with only the items flagged in ``keep`` (family -> boolean mask).

    Samples left without trials and families left without items are removed.
    """
    out = Data(families=[], measures=list(data.measures), items={}, X={})
    for f in data.families:
        m = np.asarray(keep.get(f, np.ones(data.n_items(f), dtype=bool)), dtype=bool)
        if not m.any():
            continue
        names = []
        for sname in data.family_samples[f]:
            smp = data.samples[sname]
            N, S = smp.N[:, m], smp.S[:, m]
            if N.sum() == 0:
                continue
            out.samples[sname] = Sample(name=sname, family=f, participants=smp.participants, N=N, S=S)
            names.append(sname)
        if not names:
            continue
        out.families.append(f)
        out.items[f] = data.items[f][m]
        out.X[f] = data.X[f][m]
        out.family_samples[f] = names
    return out
