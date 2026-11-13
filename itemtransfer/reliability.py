"""Step 2 of the procedure: the reliability ceiling.

:func:`reliability` gives the split-half reliability of item difficulty
within each sample. :func:`agreement` gives the correlation of item
difficulty between two samples that share items, raw and corrected for
unreliability.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from ._data import _sorted_unique, sample_matrices, validate_trials
from ._stats import (as_rng, bootstrap_counts, child_rng, corr_rows, elogit, pearson, percentile_interval, spearman,
                     spearman_brown, weighted_ranks, wpearson)

__all__ = ["reliability", "agreement"]


def _half_masks(n_participants, n_splits, rng):
    """Random halves of the participants: (n_splits, participants) 0/1 array (first half of a permutation)."""
    masks = np.zeros((n_splits, n_participants))
    half = n_participants // 2
    for k in range(n_splits):
        masks[k, rng.permutation(n_participants)[:half]] = 1.0
    return masks


def _split_half(N, S, masks, chunk_elems=4_000_000):
    """Spearman-Brown corrected split-half correlations (logit scale, Spearman scale) for each split.

    The splits are processed in blocks of at most ``chunk_elems`` array elements (splits x items) to bound
    memory for samples with many items; the result does not depend on it.
    """
    step = max(1, int(chunk_elems // max(N.shape[1], 1)))
    if len(masks) > step:
        parts = [_split_half(N, S, masks[a:a + step], chunk_elems) for a in range(0, len(masks), step)]
        return np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts])
    nA, sA = masks @ N, masks @ S
    nB, sB = (1 - masks) @ N, (1 - masks) @ S
    ok = (nA > 0) & (nB > 0)
    k = len(masks)
    out = np.full((k, 2), np.nan)
    full = ok.all(axis=1)
    if full.any() and N.shape[1] >= 3:
        la, lb = elogit(nA[full], sA[full]), elogit(nB[full], sB[full])
        out[full, 0] = corr_rows(la, lb)
        ra = rankdata(sA[full] / nA[full], axis=1)
        rb = rankdata(sB[full] / nB[full], axis=1)
        out[full, 1] = corr_rows(ra, rb)
    for j in np.flatnonzero(~full):
        m = ok[j]
        if m.sum() < 3:
            continue
        out[j, 0] = pearson(elogit(nA[j, m], sA[j, m]), elogit(nB[j, m], sB[j, m]))
        out[j, 1] = spearman(sA[j, m] / nA[j, m], sB[j, m] / nB[j, m])
    return spearman_brown(out), (~ok).sum(axis=1)


def reliability(trials, samples=None, n_splits=1000, seed=0, columns=None):
    """Split-half reliability of item difficulty within each sample.

    The participants of a sample are split at random into two halves. Item
    difficulty is computed in each half, the two halves are correlated
    across items and the correlation is stepped up with the Spearman-Brown
    formula. This is repeated for ``n_splits`` random splits.

    Parameters
    ----------
    trials : pandas.DataFrame
        Long table with one row per response and the columns
        ``participant``, ``item``, ``sample`` and ``correct`` (0/1).
    samples : sequence of str, optional
        Samples to analyse (default: all, in order of appearance).
    n_splits : int
        Number of random splits of the participants.
    seed : int or numpy.random.Generator
        Seed of the splits. With an integer, every sample starts from the
        same seed, so results do not depend on the order of the samples.
    columns : dict, optional
        Mapping from the standard column names to the names in ``trials``.

    Returns
    -------
    pandas.DataFrame
        One row per sample with

        - ``n_participants``, ``n_items``, ``n_trials``;
        - ``trials_per_item_median``, ``trials_per_item_min``;
        - ``logit_sb``, ``logit_sb_lo``, ``logit_sb_hi``: median and 2.5th
          and 97.5th percentiles, over splits, of the reliability on the
          logit scale (Pearson correlation of empirical logits);
        - ``spearman_sb``, ``spearman_sb_lo``, ``spearman_sb_hi``: the same
          on the rank scale (Spearman correlation of item accuracies);
        - ``n_splits``: number of splits with a defined estimate.

    Notes
    -----
    The percentile range describes how much the estimate depends on the
    random split of this one sample. It is not a confidence interval for
    new participants or new items. Items without a trial in one of the
    halves are left out of that split.

    Examples
    --------
    >>> import itemtransfer as it
    >>> trials, items = it.load_example()
    >>> it.reliability(trials, n_splits=200).round(2)  # doctest: +SKIP
    """
    t = validate_trials(trials, columns)
    names = list(pd.unique(t["sample"])) if samples is None else list(samples)
    rows = []
    for name in names:
        parts, labels, N, S = sample_matrices(t, name)
        if len(parts) < 4:
            raise ValueError(f"Sample '{name}' has {len(parts)} participant(s); split-half reliability needs at least 4.")
        rng = as_rng(seed)
        res, _ = _split_half(N, S, _half_masks(len(parts), n_splits, rng))
        per_item = N.sum(axis=0)
        row = dict(sample=name, n_participants=len(parts), n_items=len(labels), n_trials=int(N.sum()),
                   trials_per_item_median=float(np.median(per_item)), trials_per_item_min=int(per_item.min()))
        for j, key in enumerate(["logit_sb", "spearman_sb"]):
            v = res[:, j][np.isfinite(res[:, j])]
            row[key] = float(np.median(v)) if len(v) else np.nan
            row[key + "_lo"], row[key + "_hi"] = percentile_interval(v)
        row["n_splits"] = int(np.isfinite(res[:, 0]).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def agreement(trials, sample_a, sample_b, same_participants=None, n_splits=1000, n_boot=2000, n_splits_boot=10,
              seed=0, columns=None):
    """Agreement of item difficulty between two samples that share items.

    Parameters
    ----------
    trials : pandas.DataFrame
        Long table of responses (see :func:`reliability`).
    sample_a, sample_b : str
        Names of the two samples. They must share at least three items.
    same_participants : bool, optional
        Whether the two samples consist of the same participants (for
        example two sessions). Default: True when the samples share at least
        one participant label. When True, the correlation between disjoint
        halves of the participants is reported as well.
    n_splits : int
        Random splits of the participants for the reliabilities.
    n_boot : int
        Item bootstrap resamples (0 switches the intervals off).
    n_splits_boot : int
        Number of participant splits used for the reliabilities inside each
        bootstrap resample.
    seed : int or numpy.random.Generator
        Seed for the splits and the bootstrap.
    columns : dict, optional
        Mapping from the standard column names to the names in ``trials``.

    Returns
    -------
    pandas.DataFrame
        One row with

        - ``n_shared``: number of shared items;
        - ``r_logit`` (Pearson correlation of empirical logits) and ``rho``
          (Spearman correlation of accuracies), each with ``_lo`` and
          ``_hi`` from the item bootstrap;
        - ``rel_a``, ``rel_b``: split-half reliabilities (logit scale,
          Spearman-Brown, median over splits) computed on the shared items;
        - ``r_corrected``: ``r_logit / sqrt(rel_a * rel_b)`` with an item
          bootstrap interval in which the correlation and both
          reliabilities are recomputed on each resampled item set;
        - for samples of the same participants: ``r_disjoint`` (sample A in
          one half of the participants against sample B in the other half,
          median over splits, with the 2.5th and 97.5th percentiles over
          splits) and ``r_disjoint_corrected`` (divided by the reliabilities
          of the half samples).

    Notes
    -----
    The bootstrap resamples items and keeps the participants fixed. The
    intervals therefore describe uncertainty over items for samples of the
    size at hand. Resampling participants with replacement is not used
    here, because duplicated participants add noise to the item means and
    shift the resampled correlations downwards.

    When the same participants contribute to both samples, their individual
    responses to particular items are shared, which can raise the
    correlation. The disjoint-half correlation removes this at the cost of
    half the sample size.

    The corrected correlation can exceed 1 because the reliabilities are
    estimates.
    """
    t = validate_trials(trials, columns)
    for nm in (sample_a, sample_b):
        if nm not in set(t["sample"]):
            raise ValueError(f"Sample '{nm}' has no trials. Available samples: {list(pd.unique(t['sample']))}.")
    ta, tb = t[t["sample"] == sample_a], t[t["sample"] == sample_b]
    shared = _sorted_unique(np.array(list(set(ta["item"]) & set(tb["item"]))))
    if len(shared) < 3:
        raise ValueError(
            f"Samples '{sample_a}' and '{sample_b}' share {len(shared)} item(s); at least 3 shared items are needed."
        )
    pa, pb = set(ta["participant"]), set(tb["participant"])
    if same_participants is None:
        same_participants = len(pa & pb) > 0
    parts = _sorted_unique(np.array(list(pa | pb))) if same_participants else None
    PA, _, NA, SA = sample_matrices(t, sample_a, items=shared, participants=parts)
    PB, _, NB, SB = sample_matrices(t, sample_b, items=shared, participants=parts)
    nA, sA, nB, sB = NA.sum(0), SA.sum(0), NB.sum(0), SB.sum(0)
    la, lb = elogit(nA, sA), elogit(nB, sB)
    acc_a, acc_b = sA / nA, sB / nB
    r = pearson(la, lb)
    rho = spearman(acc_a, acc_b)
    rng = as_rng(seed)
    mA = _half_masks(len(PA), n_splits, rng)
    mB = _half_masks(len(PB), n_splits, rng)
    relA = float(np.nanmedian(_split_half(NA, SA, mA)[0][:, 0]))
    relB = float(np.nanmedian(_split_half(NB, SB, mB)[0][:, 0]))
    rc = r / np.sqrt(relA * relB) if (relA > 0 and relB > 0) else np.nan
    row = dict(sample_a=sample_a, sample_b=sample_b, same_participants=bool(same_participants), n_shared=len(shared),
               r_logit=r, r_logit_lo=np.nan, r_logit_hi=np.nan, rho=rho, rho_lo=np.nan, rho_hi=np.nan,
               rel_a=relA, rel_b=relB, r_corrected=rc, r_corrected_lo=np.nan, r_corrected_hi=np.nan)
    if n_boot:
        brng = child_rng(seed, 1)
        I = len(shared)
        W = bootstrap_counts(brng, I, n_boot)
        rb = corr_rows(la[None], lb[None], W)[:, 0]
        rhob = np.array([wpearson(weighted_ranks(acc_a, w), weighted_ranks(acc_b, w), w) for w in W])
        row["r_logit_lo"], row["r_logit_hi"] = percentile_interval(rb)
        row["rho_lo"], row["rho_hi"] = percentile_interval(rhob)

        def rel_boot(N, S, masks):
            k = masks[:n_splits_boot]
            n1, s1, n2, s2 = k @ N, k @ S, (1 - k) @ N, (1 - k) @ S
            l1, l2 = elogit(n1, s1), elogit(n2, s2)
            out = np.empty((n_boot, len(k)))
            for j in range(len(k)):
                okj = ((n1[j] > 0) & (n2[j] > 0)).astype(float)
                out[:, j] = corr_rows(l1[j][None], l2[j][None], W * okj)[:, 0]
            return np.nanmean(spearman_brown(out), axis=1)

        ra, rbb = rel_boot(NA, SA, mA), rel_boot(NB, SB, mB)
        with np.errstate(invalid="ignore"):
            joint = rb / np.sqrt(np.where((ra > 0) & (rbb > 0), ra * rbb, np.nan))
        row["r_corrected_lo"], row["r_corrected_hi"] = percentile_interval(joint)
    if same_participants:
        srng = child_rng(seed, 2)
        P = len(PA)
        res = np.full((2 * n_splits, 2), np.nan)
        k = 0
        for _ in range(n_splits):
            perm = srng.permutation(P)
            w1 = np.zeros(P)
            w1[perm[: P // 2]] = 1
            for wa in (w1, 1 - w1):
                wb = 1 - wa
                na, sa, nb, sb = wa @ NA, wa @ SA, wb @ NB, wb @ SB
                naa, saa, nbb, sbb = wb @ NA, wb @ SA, wa @ NB, wa @ SB
                ok = (na > 0) & (nb > 0)
                rl = pearson(elogit(na[ok], sa[ok]), elogit(nb[ok], sb[ok]))
                ha = pearson(elogit(na[ok], sa[ok]), elogit(naa[ok], saa[ok]))
                hb = pearson(elogit(nb[ok], sb[ok]), elogit(nbb[ok], sbb[ok]))
                res[k] = (rl, rl / np.sqrt(ha * hb) if (ha > 0 and hb > 0) else np.nan)
                k += 1
        for j, key in enumerate(["r_disjoint", "r_disjoint_corrected"]):
            v = res[:, j][np.isfinite(res[:, j])]
            row[key] = float(np.median(v)) if len(v) else np.nan
            row[key + "_lo"], row[key + "_hi"] = percentile_interval(v)
    return pd.DataFrame([row])
