"""S4. Does within-family fit rank two measures the same way as transfer?

Item difficulty in every family is driven by a latent variable t (slope -1 logit per SD, item residual SD 0.5),
so that a measure with validity .5 to .8 carries 0.5 to 0.8 logits per SD (medium to strong in the metric of S3).
Two measures A and B are noisy versions of t; the correlation of a measure with t in a family is its validity in
that family. Rankings compared:

* within-family fit: deviance explained in the training families, (i) by the training model of the procedure
  (sample intercepts, one common slope), (ii) by separate fits within each training family;
* transfer among the training families (each training family held out in turn, the held-out family not used);
* transfer to the held-out family: ordering and log-loss reduction (the outcome a user cares about).
"""
import sys
import time
from dataclasses import replace

import numpy as np
import pandas as pd

from itemtransfer._data import restrict
from simcore import RESULTS, analyse, families, generate, mean_se, rate, run_study, training_fit

STUDY, SEED = "sim04", 2604


def _cell(kind, n_fam=4, n_items=48, n_part=40, **kw):
    return dict(kind=kind, n_fam=n_fam, n_items=n_items, n_part=n_part, **kw)


def cells():
    c = {}
    # the true measure against a proxy that is valid only through its correlation with it
    for rt, rh in ((0.9, 0.9), (0.9, 0.0), (0.7, 0.0)):
        c[f"proxy_{rt:g}_{rh:g}"] = _cell("true measure vs proxy", a=(1.0, 1.0), b=(rt, rh))
    # a measure of moderate validity everywhere against one whose validity depends on the family
    for rt, rh in ((0.8, 0.8), (0.8, 0.5), (0.8, 0.3), (0.8, 0.0), (0.7, 0.5)):
        c[f"fixed_{rt:g}_{rh:g}"] = _cell("constant vs family-dependent validity", a=(0.6, 0.6), b=(rt, rh))
    # validities drawn at random for every family (Fisher z scale, SD tau)
    for ma, mb in ((0.6, 0.6), (0.65, 0.55), (0.7, 0.5)):
        for tau in (0.0, 0.15, 0.3, 0.5):
            c[f"random_{ma:g}_{mb:g}_tau{tau:g}"] = _cell("random validity", mean_a=ma, mean_b=mb, tau=tau)
    for nf in (3, 6, 10):
        c[f"random_0.65_0.55_tau0.3_f{nf}"] = _cell("random validity", n_fam=nf, mean_a=0.65, mean_b=0.55, tau=0.3)
    for tau in (0.0, 0.3):
        c[f"random_0.65_0.55_tau{tau:g}_large"] = _cell("random validity", n_items=96, n_part=80, mean_a=0.65,
                                                        mean_b=0.55, tau=tau)
    # B is the more valid measure in every family, but its unit differs between families (log-normal factor)
    for s in (0.0, 0.35, 0.7):
        c[f"scale_{s:g}"] = _cell("unstable unit", a=(0.5, 0.5), b=(0.8, 0.8), unit_sd=s)
    for k, cid in enumerate(c):
        c[cid]["seed"] = k
        c[cid]["n_rep"] = 2000
    return c


def one_rep(cell, rng):
    F = cell["n_fam"]
    if cell["kind"] == "random validity":
        va = np.tanh(np.arctanh(cell["mean_a"]) + cell["tau"] * rng.normal(size=F))
        vb = np.tanh(np.arctanh(cell["mean_b"]) + cell["tau"] * rng.normal(size=F))
    else:
        va = np.r_[cell["a"][1], np.full(F - 1, cell["a"][0])]
        vb = np.r_[cell["b"][1], np.full(F - 1, cell["b"][0])]
    fams = families(F, n_items=cell["n_items"], n_part=cell["n_part"], slope=-1.0)
    fams = [replace(f, measures={"A": ("corr", float(va[k])), "B": ("corr", float(vb[k]))}) for k, f in enumerate(fams)]
    data = generate(fams, rng)
    if cell.get("unit_sd"):
        for f in data.families:
            data.X[f][:, 1] *= float(np.exp(rng.normal(0, cell["unit_sd"])))
    row = dict(validity_a_heldout=va[0], validity_b_heldout=vb[0],
               validity2_a_train=float(np.mean(va[1:] ** 2)), validity2_b_train=float(np.mean(vb[1:] ** 2)))
    for m, r in zip("ab", analyse(data, ["A", "B"], rng, n_boot=0, n_splits=50)):
        row.update({f"ordering_{m}": r["ordering"], f"logloss_{m}": r["logloss_reduction"],
                    f"calibration_{m}": r["calibration_slope"]})
        row.update({f"{k}_{m}": v for k, v in training_fit(data, m.upper()).items()})
    # transfer among the training families only
    sub = restrict(data, {"H": np.zeros(data.n_items("H"), dtype=bool)})
    nested = [analyse(sub, ["A", "B"], rng, held=g, n_boot=0, n_splits=20) for g in sub.families]
    for j, m in enumerate("ab"):
        row[f"nested_ordering_{m}"] = float(np.mean([r[j]["ordering"] for r in nested]))
        row[f"nested_logloss_{m}"] = float(np.mean([r[j]["logloss_reduction"] for r in nested]))
    return [row]


RULES = {"fit_pooled": "dev_pooled", "fit_separate": "dev_separate", "transfer_ordering": "nested_ordering",
         "transfer_logloss": "nested_logloss"}
OUTCOMES = {"ordering": "ordering", "logloss": "logloss"}


def summary(df, cs):
    rows = []
    for cid, cell in cs.items():
        g = df[df["cell"] == cid]
        s = dict(cell=cid, **{k: (str(v) if isinstance(v, tuple) else v) for k, v in cell.items() if k != "seed"})
        s["n_rep"] = len(g)
        for m in "ab":
            for st in ("ordering", "logloss", "calibration", "dev_pooled", "dev_separate", "nested_ordering",
                       "nested_logloss"):
                s[f"{st}_{m}_mean"], s[f"{st}_{m}_mcse"] = mean_se(g[f"{st}_{m}"])
            s[f"calibration_{m}_median"] = float(g[f"calibration_{m}"].median())
        best_true = g["validity_a_heldout"].abs() >= g["validity_b_heldout"].abs()          # A truly better, held-out
        oracle_train = g["validity2_a_train"] >= g["validity2_b_train"]                    # A truly better, training
        s["true_disagreement"], s["true_disagreement_mcse"], _ = rate(best_true != oracle_train)
        for oname, ocol in OUTCOMES.items():
            a_wins_out = g[f"{ocol}_a"] > g[f"{ocol}_b"]
            s[f"a_wins_{oname}"], _, _ = rate(a_wins_out)
            for rname, rcol in RULES.items():
                a_sel = g[f"{rcol}_a"] > g[f"{rcol}_b"]
                key = f"{rname}_vs_{oname}"
                s["disagree_" + key], s["disagree_" + key + "_mcse"], _ = rate(a_sel != a_wins_out)
                sel = np.where(a_sel, g[f"{ocol}_a"], g[f"{ocol}_b"])
                other = np.where(a_sel, g[f"{ocol}_b"], g[f"{ocol}_a"])
                s["selected_" + key + "_mean"], s["selected_" + key + "_mcse"] = mean_se(sel)
                margin = 0.1 if oname == "ordering" else 0.01
                s["material_" + key], s["material_" + key + "_mcse"], _ = rate(other - sel > margin)
        for rname, rcol in RULES.items():
            a_sel = g[f"{rcol}_a"] > g[f"{rcol}_b"]
            s[f"a_selected_{rname}"], _, _ = rate(a_sel)
            s[f"wrong_truth_{rname}"], s[f"wrong_truth_{rname}_mcse"], _ = rate(a_sel != best_true)
        rows.append(s)
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / f"{STUDY}_summary.csv", index=False)
    return out


if __name__ == "__main__":
    pilot = "--pilot" in sys.argv
    cs = cells()
    if pilot:
        STUDY += "_pilot"
        for c in cs.values():
            c["n_rep"] = 40
    t0 = time.time()
    df = run_study(STUDY, one_rep, cs, n_rep=2000, chunk_size=40 if pilot else 250, study_seed=SEED)
    out = summary(df, cs)
    pd.set_option("display.width", 250)
    print(out[["cell", "a_selected_fit_pooled", "a_selected_fit_separate", "a_wins_ordering", "a_wins_logloss",
               "disagree_fit_pooled_vs_ordering", "disagree_fit_pooled_vs_logloss", "disagree_fit_separate_vs_logloss",
               "disagree_transfer_logloss_vs_logloss", "true_disagreement", "material_fit_pooled_vs_ordering",
               "logloss_a_mean", "logloss_b_mean", "selected_fit_pooled_vs_logloss_mean"]].round(3).to_string())
    print(f"{time.time() - t0:.0f} s")
