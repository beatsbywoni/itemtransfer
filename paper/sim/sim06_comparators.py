"""S6. The procedure next to the analyses a researcher would otherwise run.

(a) grouped cross-validation as in scikit-learn (leave one group out): one logistic model with a single intercept
    and the measure, fitted to the trials of the training families; held-out log loss against a baseline that
    predicts the training base rate; no recalibration of the intercept;
(b) a logistic regression per family and Cochran's Q test of slope heterogeneity (equivalent to a measure-by-family
    interaction), with model-based standard errors (items treated as fixed, as in a plain GLM) and with
    item-cluster-robust (sandwich) standard errors;
(c) a random-effects meta-analysis of the per-family slopes (DerSimonian-Laird, prediction interval with t on k - 2
    degrees of freedom), with the item-robust standard errors;
and the procedure itself (three criteria, two-way bootstrap, weak-training flag, tolerance reading 0.80 to 1.25).
"""
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

from itemtransfer._fit import fit_logit
from simcore import RESULTS, analyse, families, generate, large_sample_targets, mean_se, rate, run_study

STUDY, SEED, N_BOOT = "sim06", 2606, 500
R3 = float(np.sqrt(3))
BAND = (0.80, 1.25)


def cells():
    cont = ("uniform", -R3, R3)
    c = {
        "1_common": dict(label="1 common slope", fams=families(4)),
        "2_easier": dict(label="2 common slope, held-out intercept 2 (training 1)", fams=families(4, held=dict(intercept=2.0))),
        "2_harder": dict(label="2 common slope, held-out intercept 0 (training 1)", fams=families(4, held=dict(intercept=0.0))),
        "3_half": dict(label="3 held-out slope 0.5 x training", fams=families(4, held=dict(slope=-0.25))),
        "4_twice": dict(label="4 held-out slope 2 x training", fams=families(4, held=dict(slope=-1.0))),
        "5_two_level_step": dict(label="5 step relation, held-out family with two levels",
                                 fams=families(4, driver=cont, effect=("step", 0.0),
                                               held=dict(driver=("levels", [-1.0, 1.0], 0.1)))),
        "6_range_saturating": dict(label="6 saturating relation, held-out range 2 to 8 (training 1 to 4)",
                                   fams=families(4, driver=("uniform", 1.0, 4.0), effect=("sat", 2.0), slope=-3.67,
                                                 intercept=3.02, held=dict(driver=("uniform", 2.0, 8.0)))),
        "7_null_sd0.5": dict(label="7 measure without relation, item residual SD 0.5", fams=families(4, slope=0.0)),
        "7_null_sd1": dict(label="7 measure without relation, item residual SD 1", fams=families(4, slope=0.0, item_sd=1.0)),
    }
    for k, cid in enumerate(c):
        c[cid]["seed"] = k
    return c


def family_slope(n, s, x):
    """Slope of a logistic regression within one family with model-based and item-cluster-robust standard errors."""
    X = np.column_stack([np.ones(len(x)), x])
    fit = fit_logit(X, n, s)
    p = 1 / (1 + np.exp(-(X @ fit.coef)))
    bread = np.linalg.inv((X.T * (n * p * (1 - p))) @ X)
    r = s - n * p                                    # score residual summed over the trials of an item
    g = len(x)
    meat = (X.T * r ** 2) @ X * g / (g - 1)
    robust = bread @ meat @ bread
    return fit.coef[1], float(np.sqrt(bread[1, 1])), float(np.sqrt(robust[1, 1]))


def cochran_q(b, se):
    w = 1 / se ** 2
    mu = np.sum(w * b) / np.sum(w)
    q = float(np.sum(w * (b - mu) ** 2))
    return q, float(stats.chi2.sf(q, len(b) - 1)), w, mu


def one_rep(cell, rng):
    data = generate(cell["fams"], rng)
    row = analyse(data, ["x"], rng, n_boot=N_BOOT)[0]
    lo, hi = row["calibration_slope_lo"], row["calibration_slope_hi"]
    row["reading"] = "within" if (lo >= BAND[0] and hi <= BAND[1]) else ("outside" if (hi < BAND[0] or lo > BAND[1])
                                                                        else "undetermined")
    row["ratio_of_slopes"] = row["heldout_slope"] / row["train_slope"]
    # (a) grouped cross-validation, held-out family H, no recalibration
    cnt = {f: data.samples[f + "1"].counts() for f in data.families}
    x = {f: data.X[f][:, 0] for f in data.families}
    tr = [f for f in data.families if f != "H"]
    n_tr, s_tr = np.concatenate([cnt[f][0] for f in tr]), np.concatenate([cnt[f][1] for f in tr])
    x_tr = np.concatenate([x[f] for f in tr])
    fit = fit_logit(np.column_stack([np.ones(len(x_tr)), x_tr]), n_tr, s_tr)
    n_h, s_h = cnt["H"]
    p = np.clip(1 / (1 + np.exp(-(fit.coef[0] + fit.coef[1] * x["H"]))), 1e-12, 1 - 1e-12)
    p0 = s_tr.sum() / n_tr.sum()
    ll = -np.sum(s_h * np.log(p) + (n_h - s_h) * np.log(1 - p)) / n_h.sum()
    ll0 = -np.sum(s_h * np.log(p0) + (n_h - s_h) * np.log(1 - p0)) / n_h.sum()
    row.update(gcv_score=1 - ll / ll0, gcv_logloss=ll, gcv_logloss_baseline=ll0)
    # (b) per-family slopes and heterogeneity test; (c) random-effects meta-analysis
    est = np.array([family_slope(cnt[f][0], cnt[f][1], x[f]) for f in data.families])
    b, se_m, se_i = est[:, 0], est[:, 1], est[:, 2]
    row["q_p_model"] = cochran_q(b, se_m)[1]
    q, row["q_p_item"], w, mu_f = cochran_q(b, se_i)
    k = len(b)
    tau2 = max(0.0, (q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    ws = 1 / (se_i ** 2 + tau2)
    mu = float(np.sum(ws * b) / ws.sum())
    se_mu = float(np.sqrt(1 / ws.sum()))
    half = stats.t.ppf(0.975, k - 2) * np.sqrt(tau2 + se_mu ** 2)
    row.update(se_ratio=float(np.mean(se_i / se_m)), slope_heldout_family=b[0], slope_sd_between=float(np.std(b, ddof=1)),
               re_tau=float(np.sqrt(tau2)), re_mean=mu, re_ci_lo=mu - 1.96 * se_mu, re_ci_hi=mu + 1.96 * se_mu,
               re_pi_lo=mu - half, re_pi_hi=mu + half)
    return [row]


def summary(df, cs):
    rows = []
    for cid, cell in cs.items():
        g = df[df["cell"] == cid]
        tg = large_sample_targets(cell["fams"], seed=cell["seed"], reps=2).iloc[0]
        null = cid.startswith("7")
        s = dict(cell=cid, label=cell["label"], n_rep=len(g))
        s["target_calibration_slope"] = np.nan if null else tg["calibration_slope"]
        s["target_logloss_reduction"] = tg["logloss_reduction"]
        for st in ("ordering", "logloss_reduction", "gcv_score", "se_ratio", "re_tau", "re_mean", "slope_sd_between"):
            s[st + "_mean"], s[st + "_mcse"] = mean_se(g[st])
        s["calibration_slope_median"] = float(g["calibration_slope"].median())
        lo, hi = g["calibration_slope_lo"], g["calibration_slope_hi"]
        for name, x in (("ord_pos", g["ordering_lo"] > 0), ("cal_excl0", (lo > 0) | (hi < 0)),
                        ("cal_incl1", (lo <= 1) & (hi >= 1)), ("ll_pos", g["logloss_reduction_lo"] > 0),
                        ("ll_neg", g["logloss_reduction_hi"] < 0),
                        ("weak", (g["train_slope_lo"] <= 0) & (g["train_slope_hi"] >= 0)),
                        ("within", g["reading"] == "within"), ("outside", g["reading"] == "outside"),
                        ("undetermined", g["reading"] == "undetermined"),
                        ("gcv_positive", g["gcv_score"] > 0), ("q_reject_model", g["q_p_model"] < 0.05),
                        ("q_reject_item", g["q_p_item"] < 0.05), ("tau_zero", g["re_tau"] == 0),
                        ("re_ci_excl0", (g["re_ci_lo"] > 0) | (g["re_ci_hi"] < 0)),
                        ("re_pi_excl0", (g["re_pi_lo"] > 0) | (g["re_pi_hi"] < 0))):
            s[name], s[name + "_mcse"], _ = rate(x)
        s["re_pi_width_median"] = float((g["re_pi_hi"] - g["re_pi_lo"]).median())
        s["re_ci_width_median"] = float((g["re_ci_hi"] - g["re_ci_lo"]).median())
        s["gcv_score_q05"], s["gcv_score_q95"] = np.percentile(g["gcv_score"], [5, 95])
        # the calibration slope is the held-out family's own slope divided by the training slope
        d = (g["calibration_slope"] - g["ratio_of_slopes"]).abs()
        ok = g["converged"] & (g["train_slope"].abs() > 0.02)
        s["identity_max_abs_diff"] = float(d[ok].max())
        s["identity_correlation"] = float(np.corrcoef(g.loc[ok, "calibration_slope"], g.loc[ok, "ratio_of_slopes"])[0, 1])
        s["identity_n"] = int(ok.sum())
        rows.append(s)
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / f"{STUDY}_summary.csv", index=False)
    return out


if __name__ == "__main__":
    pilot = "--pilot" in sys.argv
    cs = cells()
    if pilot:
        STUDY += "_pilot"
    t0 = time.time()
    df = run_study(STUDY, one_rep, cs, n_rep=20 if pilot else 1000, chunk_size=20 if pilot else 100, study_seed=SEED)
    out = summary(df, cs)
    pd.set_option("display.width", 300)
    print(out[["cell", "calibration_slope_median", "cal_excl0", "ll_pos", "ll_neg", "within", "outside", "gcv_score_mean",
               "gcv_positive", "q_reject_model", "q_reject_item", "se_ratio_mean", "tau_zero", "re_pi_width_median",
               "re_pi_excl0", "identity_max_abs_diff", "identity_correlation"]].round(3).to_string())
    print(f"{time.time() - t0:.0f} s")
