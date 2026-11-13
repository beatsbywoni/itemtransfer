"""Regression test against the published knapsack analysis.

The package is run on the knapsack data with the family, sample and trial
definitions of the published analysis and compared with its saved result
files. Statistics that do not depend on a bootstrap are required to agree
closely ("exact" rows); bootstrap intervals come from different random
number streams and are compared loosely ("interval" rows). The comparison
table is written to ``paper/package_regression.csv``.

The test is skipped when the data or result files are absent. Their
location can be set with the environment variable
``ITEMTRANSFER_KNAPSACK_ROOT`` (a directory with ``data_proc/`` and
``results/``).
"""
import importlib.util
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import itemtransfer as it

PKG = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("ITEMTRANSFER_KNAPSACK_ROOT", PKG))
DATA, RESULTS = ROOT / "data_proc", ROOT / "results"
NEEDED = [DATA / "trials_harmonized.csv"] + [RESULTS / f for f in (
    "q1_transfer.csv", "q2_within.csv", "q2_between.csv", "expl_prediction.csv", "expl_prediction_balanced_slopes.csv",
    "expl_two_level.csv", "expl_range_check.csv", "expl_q2_revised_intervals.csv")]
pytestmark = pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="knapsack data or result files absent")

N_BOOT = int(os.environ.get("ITEMTRANSFER_REGRESSION_BOOT", 2000))
EXACT_TOL = 5e-7      # absolute, or relative to the published value when that is larger than 1
SEED_BOOT, SEED_SPLIT = 20261016, 20261017
MEASURES = ["ic", "tcc", "sahni_k_opt", "solver"]
EVALUATE = {"F1": "K2_dec", "F2": "K5_dec", "F3": "K7_dec_main"}


def _example_module():
    spec = importlib.util.spec_from_file_location("knapsack_example", PKG / "examples" / "knapsack.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The example script uses plain names; the stored reference results use the codes of the original analysis.
FAMILY_CODE = {"Franco": "F1", "Doroc": "F2", "Lu": "F3"}


def _codes(ex):
    sample = {v: k for k, v in ex.SAMPLE_NAME.items()}
    measure = {v: k for k, v in ex.SOURCE_MEASURES.items()}
    return sample, measure


class Table:
    def __init__(self):
        self.rows = []

    def add(self, source, key, statistic, published, package, kind="exact", note=""):
        published, package = float(published), float(package)
        diff = abs(published - package)
        if kind == "exact":
            tol = EXACT_TOL * max(1.0, abs(published))
            ok = diff <= tol
        else:
            tol, ok = np.nan, True
        self.rows.append(dict(source=source, key=key, statistic=statistic, kind=kind, published=published,
                              package=package, abs_diff=diff, tolerance=tol, passed=bool(ok), note=note))


@pytest.fixture(scope="module")
def comparison():
    t0 = time.time()
    ex = _example_module()
    tab = Table()
    trials, items = ex.load_knapsack(DATA, pilot=False)
    sample_code, measure_code = _codes(ex)
    trials = trials.assign(sample=trials["sample"].map(sample_code), family=trials["family"].map(FAMILY_CODE))
    items = items.assign(family=items["family"].map(FAMILY_CODE)).rename(columns=measure_code)

    # ---------------------------------------------------------------- transfer: ordering, scale, training slope
    q1 = pd.read_csv(RESULTS / "q1_transfer.csv").set_index(["fold", "model", "stat"])
    res = it.transfer(trials, items, MEASURES, evaluate=EVALUATE, n_boot=N_BOOT, seed=SEED_BOOT)
    tb = res.table.set_index(["family", "model"])
    names = {"rho": "ordering", "slope": "calibration_slope", "train_slope": "train_slope"}
    for f in ["F1", "F2", "F3"]:
        for m in MEASURES + ["combined"]:
            for st, col in names.items():
                if (f, m, st) not in q1.index:
                    continue
                pub = q1.loc[(f, m, st)]
                tab.add("q1_transfer.csv", f"{f}.{m}", st, pub["est"], tb.at[(f, m), col])
                tab.add("q1_transfer.csv", f"{f}.{m}", st + " interval low", pub["lo2"], tb.at[(f, m), col + "_lo"], "interval")
                tab.add("q1_transfer.csv", f"{f}.{m}", st + " interval high", pub["hi2"], tb.at[(f, m), col + "_hi"], "interval")
    for m in MEASURES + ["combined"]:
        for st, col in [("rho", "ordering"), ("slope", "calibration_slope")]:
            tab.add("q1_transfer.csv", f"mean.{m}", st, q1.loc[("mean", m, st), "est"],
                    np.mean([tb.at[(f, m), col] for f in ["F1", "F2", "F3"]]))

    # ---------------------------------------------------------------- prediction (same random number stream)
    pred = pd.read_csv(RESULTS / "expl_prediction.csv").set_index(["weighting", "fold", "model"])
    bal = pd.read_csv(RESULTS / "expl_prediction_balanced_slopes.csv").set_index(["weighting", "fold", "model"])
    rng = np.random.default_rng(SEED_BOOT + 15)
    by_weight = {"trials": it.transfer(trials, items, MEASURES, evaluate=EVALUATE, weights="trials", n_boot=0, seed=rng),
                 "balanced": it.transfer(trials, items, MEASURES, evaluate=EVALUATE, weights="equal", n_boot=0, seed=rng)}
    # diagnose() draws its item splits from the generator it is given: a fresh one reproduces the splits of the
    # first pass (weights by trials); one advanced by a first pass reproduces those of the second pass
    rng_t = np.random.default_rng(SEED_BOOT + 15)
    rng_b = np.random.default_rng(SEED_BOOT + 15)
    it.transfer(trials, items, MEASURES, evaluate=EVALUATE, n_boot=0, seed=rng_b)
    diag = {"trials": it.diagnose(trials, items, MEASURES, result=by_weight["trials"], seed=rng_t,
                                  range_limits={"ic": (None, 0.17)}, n_boot=N_BOOT),
            "balanced": it.diagnose(trials, items, MEASURES, result=by_weight["balanced"], seed=rng_b, n_boot=0)}
    for wname, r in by_weight.items():
        t = r.table.set_index(["family", "model"])
        base = diag[wname]["level_baseline"].set_index(["family", "measure"])
        for f in ["F1", "F2", "F3"]:
            src = "expl_prediction.csv"
            tab.add(src, f"{wname}.{f}.constant", "logloss", pred.at[(wname, f, "constant"), "logloss"], t.at[(f, "ic"), "logloss_constant"])
            tab.add(src, f"{wname}.{f}.constant", "brier", pred.at[(wname, f, "constant"), "brier"], t.at[(f, "ic"), "brier_constant"])
            for m in MEASURES + ["combined"]:
                p = pred.loc[(wname, f, m)]
                key = f"{wname}.{f}.{m}"
                tab.add(src, key, "logloss", p["logloss"], t.at[(f, m), "logloss"])
                tab.add(src, key, "brier", p["brier"], t.at[(f, m), "brier"])
                tab.add(src, key, "logloss_skill", p["logloss_skill"], t.at[(f, m), "logloss_reduction"])
                tab.add(src, key, "logloss_skill_lo (over splits)", p["logloss_skill_lo"], t.at[(f, m), "logloss_split_lo"])
                tab.add(src, key, "logloss_skill_hi (over splits)", p["logloss_skill_hi"], t.at[(f, m), "logloss_split_hi"])
                tab.add(src, key, "brier_skill", p["brier_skill"], t.at[(f, m), "brier_reduction"])
                tab.add("expl_prediction_balanced_slopes.csv", key, "calibration_slope",
                        bal.at[(wname, f, m), "calibration_slope"], t.at[(f, m), "calibration_slope"])
            if (f, "ic") in base.index:
                lv = pred.loc[(wname, f, "level indicator (2 parameters)")]
                dv = pred.loc[(wname, f, "ic minus level indicator (log-loss skill)")]
                key = f"{wname}.{f}.level indicator"
                tab.add(src, key, "logloss_skill", lv["logloss_skill"], base.at[(f, "ic"), "logloss_reduction_levels"])
                tab.add(src, key, "ic minus level indicator", dv["logloss_skill"], base.at[(f, "ic"), "logloss_difference"])
                tab.add(src, key, "ic minus level indicator, lo (over splits)", dv["logloss_skill_lo"],
                        base.at[(f, "ic"), "logloss_difference_split_lo"])
                tab.add(src, key, "ic minus level indicator, hi (over splits)", dv["logloss_skill_hi"],
                        base.at[(f, "ic"), "logloss_difference_split_hi"])
    # the weighting table of diagnose() gives the same slopes
    wt = diag["trials"]["weighting"].set_index(["family", "model"])
    for f in ["F1", "F2", "F3"]:
        for m in MEASURES + ["combined"]:
            tab.add("expl_prediction_balanced_slopes.csv", f"balanced.{f}.{m}", "calibration_slope (diagnose weighting table)",
                    bal.at[("balanced", f, m), "calibration_slope"], wt.at[(f, m), "calibration_slope_equal"])

    # ---------------------------------------------------------------- two-level decomposition
    two = pd.read_csv(RESULTS / "expl_two_level.csv").set_index(["part", "stat"])["value"]
    d = diag["trials"]
    base = d["level_baseline"].set_index(["family", "measure"])
    within = d["within_level"].set_index(["family", "measure", "level"])
    for f, part in [("F2", "K5_dec"), ("F3", "K7_dec_main")]:
        src = "expl_two_level.csv"
        tab.add(src, part, "rho_ic_all", two[(part, "rho_ic_all")], base.at[(f, "ic"), "ordering_measure"])
        tab.add(src, part, "point_biserial_level_accuracy", two[(part, "point_biserial_level_accuracy")],
                base.at[(f, "ic"), "level_accuracy_r"])
        for lev, name in [(0, "low"), (1, "high")]:
            w = within.loc[(f, "ic", lev)]
            tab.add(src, part, f"accuracy_{name}_level_mean", two[(part, f"accuracy_{name}_level_mean")], w["accuracy_mean"])
            tab.add(src, part, f"rho_ic_within_{name}", two[(part, f"rho_ic_within_{name}")], w["ordering_within"])
            tab.add(src, part, f"ic_sd_within_{name}", two[(part, f"ic_sd_within_{name}")], w["measure_sd"])
            tab.add(src, part, f"ic_range_within_{name}", two[(part, f"ic_range_within_{name}")], w["measure_max"] - w["measure_min"])
            tab.add(src, part, f"accuracy_sd_within_{name}", two[(part, f"accuracy_sd_within_{name}")], w["accuracy_sd"])

    # ---------------------------------------------------------------- range check
    rc = pd.read_csv(RESULTS / "expl_range_check.csv").set_index(["variant", "fold", "model", "stat"])
    rg = d["range"].set_index(["family", "measure"])
    src = "expl_range_check.csv"
    for f in ["F1", "F2", "F3"]:
        v = "training IC <= 0.17"
        tab.add(src, f"{v}.{f}", "rho", rc.at[(v, f, "ic", "rho"), "est"], rg.at[(f, "ic"), "ordering_common"])
        tab.add(src, f"{v}.{f}", "slope", rc.at[(v, f, "ic", "slope"), "est"], rg.at[(f, "ic"), "calibration_slope_common"])
        tab.add(src, f"{v}.{f}", "train_slope", rc.at[(v, f, "ic", "train_slope"), "est"], rg.at[(f, "ic"), "train_slope_common"])
        tab.add(src, f"{v}.{f}", "slope interval low", rc.at[(v, f, "ic", "slope"), "lo2"], rg.at[(f, "ic"), "calibration_slope_common_lo"], "interval")
        tab.add(src, f"{v}.{f}", "slope interval high", rc.at[(v, f, "ic", "slope"), "hi2"], rg.at[(f, "ic"), "calibration_slope_common_hi"], "interval")
    log_items = items.assign(log_ic=np.log(items["ic"].clip(lower=0.005)))
    lg = it.transfer(trials, log_items, ["log_ic"], evaluate=EVALUATE, n_boot=N_BOOT, seed=SEED_BOOT).table.set_index("family")
    for f in ["F1", "F2", "F3"]:
        v = "log IC"
        for st, col in names.items():
            pub = rc.loc[(v, f, "ic", st)]
            tab.add(src, f"{v}.{f}", st, pub["est"], lg.at[f, col])
            if st != "rho":
                tab.add(src, f"{v}.{f}", st + " interval low", pub["lo2"], lg.at[f, col + "_lo"], "interval")
                tab.add(src, f"{v}.{f}", st + " interval high", pub["hi2"], lg.at[f, col + "_hi"], "interval")

    # ---------------------------------------------------------------- reliability within samples
    allt = ex.load_all_trials(DATA)
    allt["part"] = allt["part"].map(sample_code).fillna(allt["part"])
    frames = [pd.DataFrame({"participant": allt["participant"], "item": allt["hash_full"], "sample": allt["part"],
                            "correct": allt["correct"]})]
    for part, prefix in [("K5_dec", "K5 "), ("K8_opt", "K8 ")]:
        sub = allt[allt["part"].eq(part)]
        frames.append(pd.DataFrame({"participant": sub["participant"], "item": sub["hash_full"],
                                    "sample": prefix + sub["condition"].astype(str), "correct": sub["correct"]}))
    long = pd.concat(frames, ignore_index=True)
    rel = it.reliability(long, seed=SEED_SPLIT).set_index("sample")
    qw = pd.read_csv(RESULTS / "q2_within.csv").set_index(["label", "scale"])
    label = {"K2 decision": "K2_dec", "K4 decision": "K4_dec", "K5 control session": "K5 control",
             "K5 stress session": "K5 stress", "K5 both sessions": "K5_dec", "K7 main": "K7_dec_main",
             "K7 pilot": "K7_dec_pilot", "K2 optimisation": "K2_opt", "K4 optimisation": "K4_opt",
             "K8 placebo session": "K8 PLC", "K8 all sessions": "K8_opt"}
    for lab, smp in label.items():
        for scale, col in [("logit_pearson_sb", "logit_sb"), ("spearman_sb", "spearman_sb")]:
            pub = qw.loc[(lab, scale)]
            tab.add("q2_within.csv", lab, f"{scale} median", pub["median"], rel.at[smp, col])
            tab.add("q2_within.csv", lab, f"{scale} 2.5th percentile", pub["lo"], rel.at[smp, col + "_lo"])
            tab.add("q2_within.csv", lab, f"{scale} 97.5th percentile", pub["hi"], rel.at[smp, col + "_hi"])
        pub = qw.loc[(lab, "logit_pearson_sb")]
        for a, b in [("n_participants", "n_participants"), ("n_instances", "n_items"), ("n_trials", "n_trials")]:
            tab.add("q2_within.csv", lab, a, pub[a], rel.at[smp, b])

    # ---------------------------------------------------------------- agreement between samples
    qb = pd.read_csv(RESULTS / "q2_between.csv")
    qb = qb[qb["outcome"].eq("accuracy")].set_index(["label", "stat"])
    rev = pd.read_csv(RESULTS / "expl_q2_revised_intervals.csv").set_index(["label", "stat"])
    pairs = {"K2 vs K4, decision": ("K2_dec", "K4_dec"), "K2 vs K4, optimisation": ("K2_opt", "K4_opt"),
             "K5 control vs stress": ("K5 control", "K5 stress"), "K7 main vs pilot": ("K7_dec_main", "K7_dec_pilot"),
             "K8 placebo vs MPH": ("K8 PLC", "K8 MPH"), "K8 placebo vs MOD": ("K8 PLC", "K8 MOD"),
             "K8 placebo vs DEX": ("K8 PLC", "K8 DEX")}
    for lab, (a, b) in pairs.items():
        ag = it.agreement(long, a, b, n_boot=N_BOOT, seed=SEED_SPLIT).iloc[0]
        for st, col in [("r_logit", "r_logit"), ("rho", "rho"), ("r_corrected", "r_corrected"), ("rel_a", "rel_a"),
                        ("rel_b", "rel_b")]:
            tab.add("q2_between.csv", lab, st, qb.at[(lab, st), "est"], ag[col])
        tab.add("q2_between.csv", lab, "n_shared", qb.at[(lab, "r_logit"), "n_shared"], ag["n_shared"])
        tab.add("q2_between.csv", lab, "same_participants", float(qb.at[(lab, "r_logit"), "same_participants"]),
                float(ag["same_participants"]))
        src = "expl_q2_revised_intervals.csv"
        note = "item bootstrap, participants fixed"
        tab.add(src, lab, "r_logit interval low", rev.at[(lab, "r_logit"), "inst_lo"], ag["r_logit_lo"], "interval", note)
        tab.add(src, lab, "r_logit interval high", rev.at[(lab, "r_logit"), "inst_hi"], ag["r_logit_hi"], "interval", note)
        tab.add(src, lab, "rho interval low", rev.at[(lab, "rho"), "inst_lo"], ag["rho_lo"], "interval", note)
        tab.add(src, lab, "rho interval high", rev.at[(lab, "rho"), "inst_hi"], ag["rho_hi"], "interval", note)
        note = "item bootstrap, reliabilities recomputed in each resample"
        tab.add(src, lab, "r_corrected interval low", rev.at[(lab, "r_corrected_fixedrel"), "joint_lo"],
                ag["r_corrected_lo"], "interval", note)
        tab.add(src, lab, "r_corrected interval high", rev.at[(lab, "r_corrected_fixedrel"), "joint_hi"],
                ag["r_corrected_hi"], "interval", note)

    out = pd.DataFrame(tab.rows)
    out.attrs["seconds"] = time.time() - t0
    target = ROOT / "paper"
    if target.is_dir():
        out.to_csv(target / "package_regression.csv", index=False)
        summ = (out.groupby(["source", "kind"]).agg(n=("abs_diff", "size"), max_abs_diff=("abs_diff", "max"),
                                                    median_abs_diff=("abs_diff", "median"), failed=("passed", lambda x: int((~x).sum())))
                .reset_index())
        summ["n_boot"] = N_BOOT
        summ["seconds_total"] = round(out.attrs["seconds"], 1)
        summ.to_csv(target / "package_regression_summary.csv", index=False)
    return out


def test_point_estimates_reproduce_the_published_values(comparison):
    exact = comparison[comparison["kind"] == "exact"]
    bad = exact[~exact["passed"]]
    assert len(exact) > 300
    assert bad.empty, "\n" + bad.to_string()


def test_three_decimals(comparison):
    exact = comparison[comparison["kind"] == "exact"]
    assert (exact["abs_diff"] < 5e-4 * np.maximum(1.0, exact["published"].abs())).all()


def test_bootstrap_intervals_agree_approximately(comparison):
    iv = comparison[comparison["kind"] == "interval"].copy()
    # interval bounds of well-determined statistics: within 0.15 (absolute) of the published bound
    stable = iv[iv["key"].str.contains(r"\.(?:ic|tcc|combined)$") | iv["source"].str.contains("range_check|q2_revised")]
    stable = stable[~stable["statistic"].str.startswith("train_slope")]
    assert len(stable) > 80
    assert (stable["abs_diff"] < 0.15).mean() > 0.9, stable.sort_values("abs_diff").tail(15).to_string()
