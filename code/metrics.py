#!/usr/bin/env python3
"""
Instance complexity measures for 0-1 knapsack instances (project 3, step 3-A3).

Every function takes integer item weights w, item values v, a capacity c and, for the decision variant, a target
profit p. Running this file performs self-checks on small hand-made instances (`python3 code/metrics.py`).

Measures
  enumerate_instance   exact optimum p*, the least weight of an optimal subset, the number of optimal subsets, and for a
                       target p the satisfiability and the number of witnesses (subsets with weight <= c and value >= p),
                       by enumerating all 2^n subsets (fine for n <= 20)
  ic                   instance complexity |p - p*| / sum(v); signed version (p - p*) / sum(v). Decision variant only.
                       This is the "IC ex post" of Franco et al. (2021) and the IC of Doroc et al. (2025) and
                       Lu et al. (2025).
  alpha_c, alpha_p     normalised capacity c / sum(w) and normalised profit p / sum(v), the two parameters of the
                       typical-case complexity (TCC) phase diagram. For an optimisation instance the profit
                       coordinate is p* / sum(v): the optimisation problem is as hard as the decision problem at p*.
  sahni_k_opt          smallest k such that, for some set S of k items, putting S in the knapsack and then adding the
                       remaining items greedily (highest value/weight first, skipping items that do not fit, ties by
                       item order) reaches the optimum p* (Sahni 1975; Murawski & Bossaerts 2016)
  sahni_k_dec          decision analogue (defined here): smallest k such that some k items plus the same greedy
                       completion reach value >= p within the capacity; None for an unsatisfiable instance, where no
                       subset reaches p
  value_weight_corr    Pearson correlation of the item values and weights
  input_size           n log2(c), the "input size" of Murawski & Bossaerts (2016, Table S2)
  p_sat_reference      probability that a random instance with the same number of items, item weights and values
                       drawn independently from Uniform(0, 1), and the same (alpha_c, alpha_p) is satisfiable, by Monte
                       Carlo with a fixed seed; tcc = 1 - |2 p_sat - 1| is 1 on the phase transition and 0 far from it
  gecode_stats         Gecode 6 search statistics through MiniZinc for the two models below. With MiniZinc 2.9.3 and
                       Gecode 6.3.0 they reproduce the statistics in the K2 authors' instance files exactly: all
                       statistics of the 18 optimisation instances, and nodes, failures and peak depth of the 72
                       decision instances (propagation counts of the decision model differ, because the authors' older
                       MiniZinc flattened the model into more variables and propagators).
"""
from __future__ import annotations

import hashlib
import itertools
import math
import os
import re
import shutil
import subprocess
import tempfile
from fractions import Fraction

import numpy as np

MZN_OPT = """int: n; array[1..n] of int: w; array[1..n] of int: v; int: c;
array[1..n] of var 0..1: x;
constraint sum(i in 1..n)(w[i]*x[i]) <= c;
solve :: int_search(x, input_order, indomain_max) maximize sum(i in 1..n)(v[i]*x[i]);
"""
MZN_DEC = """include "knapsack.mzn";
int: n; array[1..n] of int: w; array[1..n] of int: v; int: c; int: p;
array[1..n] of var 0..1: x; var 0..c: W; var p..sum(v): P;
constraint knapsack(w, v, x, W, P);
solve :: int_search(x, input_order, indomain_max) satisfy;
"""
GECODE_FIELDS = ("solutions", "variables", "propagators", "propagations", "nodes", "failures", "peakDepth")


def parse_items(s) -> list[int]:
    """'3,5,8' or '[3, 5, 8]' -> [3, 5, 8]"""
    if isinstance(s, (list, tuple, np.ndarray)):
        return [int(x) for x in s]
    return [int(x) for x in re.findall(r"-?\d+", str(s))]


def _subset_sums(w, v):
    n = len(w)
    masks = np.arange(1 << n, dtype=np.int64)
    bits = ((masks[:, None] >> np.arange(n)) & 1).astype(np.int64)
    return masks, bits, bits @ np.asarray(w, dtype=np.int64), bits @ np.asarray(v, dtype=np.int64)


def enumerate_instance(w, v, c, p=None) -> dict:
    """Exact optimum and, for a target p, satisfiability and witnesses, by enumeration of all subsets."""
    w, v = parse_items(w), parse_items(v)
    if len(w) != len(v) or len(w) > 20:
        raise ValueError("weights and values must have the same length (at most 20 items)")
    masks, bits, sw, sv = _subset_sums(w, v)
    feas = sw <= c
    p_star = int(sv[feas].max())
    opt = feas & (sv == p_star)
    out = {"p_star": p_star, "c_star": int(sw[opt].min()), "n_optimal_sets": int(opt.sum()),
           "optimal_sets": [[i for i in range(len(w)) if m >> i & 1] for m in masks[opt]]}
    if p is not None:
        out["sat"] = int(p_star >= p)
        out["n_witness"] = int((feas & (sv >= p)).sum())
    return out


def ic(p, p_star, sum_v, signed=False) -> float:
    d = (p - p_star) / sum_v
    return d if signed else abs(d)


def alpha_c(c, w) -> float:
    return c / sum(parse_items(w))


def alpha_p(p, v) -> float:
    return p / sum(parse_items(v))


def value_weight_corr(w, v) -> float:
    w, v = np.asarray(parse_items(w), float), np.asarray(parse_items(v), float)
    if w.std() == 0 or v.std() == 0:
        return float("nan")
    return float(np.corrcoef(v, w)[0, 1])


def input_size(n, c) -> float:
    return n * math.log2(c)


def density_order(w, v) -> list[int]:
    """Items by value/weight, highest first; ties by item order (exact rational comparison)."""
    return sorted(range(len(w)), key=lambda i: (-Fraction(v[i], w[i]), i))


def greedy_completion(w, v, c, fixed=()):
    """Put the items in `fixed` in the knapsack, then add the others by density, skipping those that do not fit.
    Returns (value, weight, items) or None if the fixed items alone exceed the capacity."""
    fixed = list(fixed)
    cw = sum(w[i] for i in fixed)
    if cw > c:
        return None
    cv = sum(v[i] for i in fixed)
    chosen = set(fixed)
    for i in density_order(w, v):
        if i not in chosen and cw + w[i] <= c:
            chosen.add(i)
            cw += w[i]
            cv += v[i]
    return cv, cw, sorted(chosen)


def sahni_k_opt(w, v, c, p_star=None):
    """Smallest k such that fixing some k items and completing greedily reaches the optimum."""
    w, v = parse_items(w), parse_items(v)
    if p_star is None:
        p_star = enumerate_instance(w, v, c)["p_star"]
    for k in range(len(w) + 1):
        for S in itertools.combinations(range(len(w)), k):
            r = greedy_completion(w, v, c, S)
            if r is not None and r[0] == p_star:
                return k
    return None


def sahni_k_dec(w, v, c, p):
    """Smallest k such that fixing some k items and completing greedily reaches value >= p; None if unsatisfiable."""
    w, v = parse_items(w), parse_items(v)
    if enumerate_instance(w, v, c, p)["sat"] == 0:
        return None
    for k in range(len(w) + 1):
        for S in itertools.combinations(range(len(w)), k):
            r = greedy_completion(w, v, c, S)
            if r is not None and r[0] >= p:
                return k
    return None


def _seed(*parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "little")


def p_sat_reference(n, a_c, a_p, samples=4000, seed_key="") -> float:
    """P(satisfiable) for random instances with n items, weights and values i.i.d. Uniform(0, 1), capacity
    a_c * sum(w) and target a_p * sum(v). Monte Carlo; the seed is derived from (n, a_c, a_p, seed_key), so the
    same instance always gets the same estimate."""
    rng = np.random.default_rng(_seed("p_sat_reference", n, repr(float(a_c)), repr(float(a_p)), seed_key))
    W = rng.random((samples, n))
    V = rng.random((samples, n))
    sat = 0
    for lo in range(0, samples, 2000):          # chunks keep memory small for 12-item instances
        w, v = W[lo:lo + 2000], V[lo:lo + 2000]
        sw, sv = _float_subset_sums(w), _float_subset_sums(v)
        cap = a_c * w.sum(1, keepdims=True)
        tgt = a_p * v.sum(1, keepdims=True)
        sat += int(((sw <= cap) & (sv >= tgt)).any(1).sum())
    return sat / samples


def _float_subset_sums(X):
    """All subset sums of each row of X, built by adding the items one at a time in item order (no matrix product,
    so the floating-point result does not depend on the linear-algebra library)."""
    out = np.zeros((X.shape[0], 1))
    for i in range(X.shape[1]):
        out = np.concatenate([out, out + X[:, i:i + 1]], axis=1)
    return out


def tcc_from_psat(p_sat) -> float:
    return 1.0 - abs(2.0 * p_sat - 1.0)


def find_minizinc():
    """Path to the minizinc executable: $MINIZINC, then PATH. Returns None if not found."""
    cand = os.environ.get("MINIZINC") or shutil.which("minizinc")
    return cand if cand and os.path.exists(cand) else None


def minizinc_version(minizinc) -> dict:
    out = subprocess.run([minizinc, "--version"], capture_output=True, text=True).stdout
    sol = subprocess.run([minizinc, "--solvers"], capture_output=True, text=True).stdout
    g = re.search(r"Gecode ([\d.]+) \(org\.gecode\.gecode", sol)
    m = re.search(r"version ([\d.]+)", out)
    return {"minizinc": m.group(1) if m else out.strip(), "gecode": g.group(1) if g else ""}


def gecode_stats(w, v, c, p=None, minizinc=None, timeout=60) -> dict:
    """Gecode statistics for the optimisation model (p is None) or the decision model (target p)."""
    minizinc = minizinc or find_minizinc()
    if not minizinc:
        raise RuntimeError("minizinc not found (set MINIZINC or add it to PATH)")
    w, v = parse_items(w), parse_items(v)
    with tempfile.TemporaryDirectory() as tmp:
        model = os.path.join(tmp, "m.mzn")
        data = os.path.join(tmp, "d.dzn")
        with open(model, "w") as f:
            f.write(MZN_OPT if p is None else MZN_DEC)
        with open(data, "w") as f:
            f.write(f"n = {len(w)}; w = {w}; v = {v}; c = {int(c)};" + ("" if p is None else f" p = {int(p)};"))
        r = subprocess.run([minizinc, "--solver", "gecode", "-s", model, data], capture_output=True, text=True,
                           timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"minizinc failed: {r.stderr.strip()[:300]}")
    stats = {}
    for k, val in re.findall(r"%%%mzn-stat: (\w+)=([-\d.]+)\n", r.stdout):
        if k in GECODE_FIELDS:
            stats[k] = int(float(val))
    stats["unsat"] = int("=====UNSATISFIABLE=====" in r.stdout)
    # The MiniZinc compiler can prove unsatisfiability before Gecode runs (for example when the target exceeds the
    # sum of all values, so the domain of P is empty). Then there is no search: the counts are set to 0.
    stats["decided_before_search"] = int(stats["unsat"] == 1 and "nodes" not in stats)
    if stats["decided_before_search"]:
        stats.update({k: 0 for k in GECODE_FIELDS})
    return stats


def _selftest() -> None:
    # 4 items; optimum 9 by items {0, 3} or {1, 2} (weight 7 each)
    w, v, c = [2, 3, 4, 5], [3, 4, 5, 6], 7
    e = enumerate_instance(w, v, c, p=9)
    assert e["p_star"] == 9 and e["c_star"] == 7 and e["n_optimal_sets"] == 2 and e["sat"] == 1, e
    assert enumerate_instance(w, v, c, p=10)["sat"] == 0
    assert abs(ic(10, 9, sum(v)) - 1 / 18) < 1e-12 and ic(10, 9, 18, signed=True) > 0
    # greedy by density: 1.5, 1.33, 1.25, 1.2 -> items 0 and 1 (value 7, weight 5), nothing else fits
    assert greedy_completion(w, v, c) == (7, 5, [0, 1])
    assert sahni_k_opt(w, v, c) == 1                       # fix item 3, greedy adds item 0 -> 9
    assert sahni_k_dec(w, v, c, 7) == 0 and sahni_k_dec(w, v, c, 9) == 1 and sahni_k_dec(w, v, c, 10) is None
    assert abs(value_weight_corr(w, v) - 1.0) < 1e-12
    # the phase transition: far below (a_p small) almost surely satisfiable, far above almost surely not
    assert p_sat_reference(6, 0.42, 0.20, samples=2000) > 0.95 and p_sat_reference(6, 0.42, 0.95, samples=2000) < 0.05
    assert p_sat_reference(6, 0.42, 0.62, samples=500, seed_key="x") == p_sat_reference(6, 0.42, 0.62, samples=500,
                                                                                        seed_key="x")
    print("metrics.py self-test passed")


if __name__ == "__main__":
    _selftest()
