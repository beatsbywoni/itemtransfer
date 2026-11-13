"""Steps 2 to 5 of the second worked example (leave-one-family-out transfer validation, lexical decision).

Usage (from this directory, with the package installed):
    python3 run_lexical.py step2 | step3 | step3_equal | step4 | sensitivity | step5
Every stage writes tidy CSV files to results/ and a timing/count record to results/run_info_<stage>.json
(merged into results/run_info.json by finish_lexical.py). Word-level tables go to cache/ only (licences).
Pre-specification: PLAN.md.
"""
import json, os, pickle, platform, resource, sys, time
import numpy as np, pandas as pd, scipy
import itemtransfer as it
from itemtransfer._data import sample_matrices, validate_trials, prepare
from itemtransfer._fit import fit_logit, fit_logit_batch
from itemtransfer.reliability import _half_masks
from itemtransfer.transfer import _draw, _batch_sizes
import lexical_common as lc

SEED = lc.SEED
N_BOOT, BOOT_BATCH, N_SPLITS = 1000, 50, 500
R = lc.RESULTS
stage = sys.argv[1]
t0 = time.time()
info = dict(stage=stage, started=time.strftime("%Y-%m-%dT%H:%M:%S%z"), seed=SEED, python=platform.python_version(),
            numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__, itemtransfer=it.__version__,
            cpu_count=os.cpu_count(), itemtransfer_path=os.path.dirname(it.__file__))


def done():
    info["seconds"] = round(time.time() - t0, 1)
    info["max_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)
    json.dump(info, open(os.path.join(R, f"run_info_{stage}.json"), "w"), indent=1, default=str)
    print(json.dumps(info, indent=1, default=str))


def save(df, name):
    df.to_csv(os.path.join(R, name), index=False)
    print("\n==", name); print(df.round(4).to_string(), flush=True)


def boot_long(res, extra):
    frames = []
    for (f, m), b in res.bootstrap.items():
        frames.append(b.assign(family=f, model=m, resample=np.arange(len(b)), **extra))
    return pd.concat(frames, ignore_index=True)


def paired_differences(res, extra):
    """Bootstrap interval of the difference between the three-measure model and frequency alone (same resamples)."""
    rows = []
    tab = res.table.set_index(["family", "model"])
    for f in res.settings["holdout"]:
        for other in [m for m in tab.loc[f].index if m != "zipf"]:
            for st in ["logloss_reduction", "brier_reduction", "ordering"]:
                d = res.bootstrap[(f, other)][st].to_numpy() - res.bootstrap[(f, "zipf")][st].to_numpy()
                rows.append(dict(family=f, model=other, reference="zipf", statistic=st,
                                 difference=tab.at[(f, other), st] - tab.at[(f, "zipf"), st],
                                 difference_lo=np.percentile(d, 2.5), difference_hi=np.percentile(d, 97.5), **extra))
    return pd.DataFrame(rows)


trials_all, words = lc.load_megastudies()
info["n_word_trials_all"] = int(len(trials_all))
info["n_shared_words_elp_blp"] = int(len(lc.shared_words(words)))

if stage == "step2":
    # ---- exposure: how sparse is the participant x word matrix, and how many trials does a half hold?
    t = validate_trials(trials_all)
    rows = []
    for fam in lc.FAMILIES:
        parts, labels, N, S = sample_matrices(t, fam)
        per_p = (N > 0).sum(axis=1)
        per_i = N.sum(axis=0)
        masks = _half_masks(len(parts), 200, np.random.default_rng(SEED))
        mins, meds, zero = [], [], 0
        for a in range(0, 200, 20):
            nA = masks[a:a + 20] @ N
            nB = per_i[None, :] - nA
            small = np.minimum(nA, nB)
            mins.append(small.min(axis=1)); meds.append(np.median(nA, axis=1)); zero += int((small == 0).sum())
        mins, meds = np.concatenate(mins), np.concatenate(meds)
        rows.append(dict(sample=fam, n_participants=len(parts), n_words=len(labels), n_trials=int(N.sum()),
                         max_trials_per_cell=int(N.max()),
                         words_per_participant_median=float(np.median(per_p)), words_per_participant_min=int(per_p.min()),
                         words_per_participant_max=int(per_p.max()), share_of_list_per_participant=float(np.median(per_p) / len(labels)),
                         trials_per_word_median=float(np.median(per_i)), trials_per_word_min=int(per_i.min()),
                         trials_per_word_max=int(per_i.max()),
                         trials_per_word_per_half_median=float(np.median(meds)),
                         smaller_half_min_over_words_median_over_splits=float(np.median(mins)),
                         smaller_half_min_over_words_min_over_splits=int(mins.min()),
                         n_word_half_cells_without_trial_in_200_splits=zero,
                         mean_accuracy=float(S.sum() / N.sum()), share_words_at_ceiling=float((S.sum(0) == per_i).mean()),
                         share_words_above_0_95=float((S.sum(0) / per_i > 0.95).mean())))
        del N, S
    save(pd.DataFrame(rows), "step2_exposure.csv")
    rel = it.reliability(trials_all, n_splits=1000, seed=SEED)
    rel.insert(1, "word_set", "all words of the megastudy")
    tf, items = lc.build(trials_all, words)
    rel2 = it.reliability(tf, n_splits=1000, seed=SEED)
    rel2.insert(1, "word_set", "family as analysed (shared words assigned)")
    save(pd.concat([rel, rel2], ignore_index=True), "step2_reliability.csv")
    ag = it.agreement(trials_all, "ELP", "BLP", n_splits=1000, n_boot=2000, seed=SEED)
    save(ag, "step2_agreement_elp_blp.csv")
    # the same on words whose difficulty is not at ceiling in either sample (descriptive)
    info["agreement_n_shared"] = int(ag["n_shared"].iloc[0])

elif stage in ("step3", "step3_equal"):
    weights = "trials" if stage == "step3" else "equal"
    tf, items = lc.build(trials_all, words)
    del trials_all
    info["n_items_by_family"] = items.groupby("family").size().to_dict()
    info["n_trials_by_family"] = tf.groupby("sample").size().to_dict()
    info["settings"] = dict(n_boot=N_BOOT, boot_batch=BOOT_BATCH, n_splits=N_SPLITS, n_splits_boot=10, weights=weights)
    res = it.transfer(tf, items, lc.MEASURES, weights=weights, n_boot=N_BOOT, boot_batch=BOOT_BATCH,
                      n_splits=N_SPLITS, seed=SEED)
    tag = "" if weights == "trials" else "_equal_weights"
    save(res.table.assign(weights=weights), f"step3_transfer{tag}.csv")
    boot_long(res, dict(weights=weights)).to_csv(os.path.join(R, f"step3_bootstrap{tag}.csv"), index=False)
    save(paired_differences(res, dict(weights=weights)), f"step3_model_differences{tag}.csv")
    pickle.dump(res, open(os.path.join(lc.CACHE, f"transfer_{weights}.pkl"), "wb"))
    if stage == "step3":
        # ---- coefficients of the three-measure model: training folds (point) and within each family (two-way bootstrap)
        data = prepare(tf, items, lc.MEASURES)
        rows = []
        for hold in data.families:
            tr = [f for f in data.families if f != hold]
            X = np.vstack([data.X[f] for f in tr])
            ind = np.vstack([np.eye(len(tr))[[j] * data.n_items(f)] for j, f in enumerate(tr)])
            n = np.concatenate([data.samples[f].counts()[0] for f in tr])
            s = np.concatenate([data.samples[f].counts()[1] for f in tr])
            fit = fit_logit(np.hstack([ind, X]), n, s)
            for j, m in enumerate(lc.MEASURES):
                rows.append(dict(fit="training families", held_out_family=hold, family="+".join(tr), measure=m,
                                 coefficient=fit.coef[len(tr) + j], coefficient_lo=np.nan, coefficient_hi=np.nan))
        rng = np.random.default_rng([SEED, 7])
        nb = 500
        for f in data.families:
            smp = data.samples[f]
            n0, s0 = smp.counts()
            Xf = np.column_stack([np.ones(data.n_items(f)), data.X[f]])
            pt = fit_logit(Xf, n0, s0).coef
            bs = []
            for size in _batch_sizes(nb, 50):
                wp, wi = _draw(data, size, rng)
                c, _ = fit_logit_batch(Xf, wp[f] @ smp.N, wp[f] @ smp.S, wi[f], n_indicator=1)
                bs.append(c)
            bs = np.concatenate(bs)
            for j, m in enumerate(lc.MEASURES):
                rows.append(dict(fit="within family", held_out_family="", family=f, measure=m, coefficient=pt[1 + j],
                                 coefficient_lo=np.percentile(bs[:, 1 + j], 2.5), coefficient_hi=np.percentile(bs[:, 1 + j], 97.5)))
        save(pd.DataFrame(rows), "step3_three_measure_coefficients.csv")
        info["three_measure_within_family_bootstrap"] = dict(n_boot=nb, seed=[SEED, 7])

elif stage == "step4":
    tf, items = lc.build(trials_all, words)
    del trials_all
    res = pickle.load(open(os.path.join(lc.CACHE, "transfer_trials.pkl"), "rb"))
    info["settings"] = dict(max_levels=25, n_boot_common_range=400, boot_batch=BOOT_BATCH)
    diag = it.diagnose(tf, items, lc.MEASURES, result=res, max_levels=25, n_boot=400, boot_batch=BOOT_BATCH)
    for key in ["levels", "level_baseline", "within_level", "range", "weak_training", "measure_correlations", "weighting"]:
        save(diag[key], f"step4_{key}.csv")
    open(os.path.join(R, "step4_warnings.txt"), "w").write("\n".join(diag["warnings"]) + "\n")
    print("\n".join(diag["warnings"]))
    # descriptive: mean accuracy and number of words at each length, per family (aggregate, no word listed)
    data = prepare(tf, items, lc.MEASURES)
    rows = []
    for f in data.families:
        n, s = data.samples[f].counts()
        L = data.X[f][:, lc.MEASURES.index("length")]
        Z = data.X[f][:, lc.MEASURES.index("zipf")]
        O = data.X[f][:, lc.MEASURES.index("old20")]
        for v in np.unique(L):
            m = L == v
            rows.append(dict(family=f, length=int(v), n_words=int(m.sum()), accuracy_trials=float(s[m].sum() / n[m].sum()),
                             accuracy_words_mean=float((s[m] / n[m]).mean()), zipf_mean=float(Z[m].mean()),
                             old20_mean=float(O[m].mean())))
    save(pd.DataFrame(rows), "step4_accuracy_by_length.csv")

elif stage == "sensitivity":
    rows, diffs = [], []
    for assignment in ["opposite", "dropped"]:
        tf, items = lc.build(trials_all, words, assignment=assignment)
        res = it.transfer(tf, items, lc.MEASURES, n_boot=200, boot_batch=BOOT_BATCH, n_splits=N_SPLITS, seed=SEED)
        rows.append(res.table.assign(analysis=f"shared words: {assignment}", measures="zipf, length, old20"))
        info[f"n_items_{assignment}"] = items.groupby("family").size().to_dict()
        del tf
    tf, items = lc.build(trials_all, words)
    it2 = items.drop(columns=["old20"]).rename(columns={"old20_equal_lexicon": "old20"})
    res = it.transfer(tf, it2, lc.MEASURES, n_boot=200, boot_batch=BOOT_BATCH, n_splits=N_SPLITS, seed=SEED)
    rows.append(res.table.assign(analysis="old20 against a 14,089-word reference lexicon in every family",
                                 measures="zipf, length, old20 (equal lexicon size)"))
    # words unknown to wordfreq removed (zipf = 0): does the floor value drive the frequency result?
    keep = items[items["zipf"] > 0]
    res = it.transfer(tf[tf["item"].isin(set(keep["item"]))], keep, lc.MEASURES, n_boot=200, boot_batch=BOOT_BATCH,
                      n_splits=N_SPLITS, seed=SEED)
    rows.append(res.table.assign(analysis="words unknown to wordfreq removed", measures="zipf, length, old20"))
    info["n_items_known_to_wordfreq"] = keep.groupby("family").size().to_dict()
    info["settings"] = dict(n_boot=200, boot_batch=BOOT_BATCH, n_splits=N_SPLITS, weights="trials")
    save(pd.concat(rows, ignore_index=True), "sensitivity_transfer.csv")

elif stage == "step5":
    NW = 1000
    tf, items = lc.build(trials_all, words, n_words=NW)
    del trials_all
    info["sample"] = dict(n_words_per_family=NW, seed=SEED, n_trials=tf.groupby("sample").size().to_dict(),
                          rule="numpy.random.default_rng(seed).choice without replacement, families in the order "
                               "ELP, BLP, DLP, MEGALEX, words sorted by identifier, after the shared-word assignment")
    res = it.transfer(tf, items, lc.MEASURES, n_boot=N_BOOT, n_splits=N_SPLITS, seed=SEED)
    save(res.table.assign(weights="trials"), "step5_transfer_1000_words.csv")
    info["seconds_transfer_sample"] = round(time.time() - t0, 1)
    out, designs = [], []
    for label, common in [("common slope", True), ("family-specific slopes", False)]:
        design = it.design_from_data(tf, items, "zipf", common_slope=common, null_measure=True, seed=SEED)
        designs.append(dict(design=label, slope=design.slope, participant_sd=design.participant_sd, item_sd=design.item_sd,
                            **{f"slope_{f.name}": (design.slope if f.slope is None else f.slope) for f in design.families},
                            **{f"intercept_{f.name}": f.samples[0].intercept for f in design.families},
                            **{f"items_per_participant_{f.name}": f.samples[0].items_per_participant for f in design.families}))
        chk = it.check_intervals(design, n_sim=200, n_boot=200, n_jobs=2, target_scale=(8, 4), target_reps=5,
                                 prediction=True, seed=SEED)
        out.append(chk.assign(design=label))
        print(label, round(time.time() - t0, 1), flush=True)
    save(pd.DataFrame(designs), "step5_designs.csv")
    save(pd.concat(out, ignore_index=True), "step5_check_intervals.csv")
    info["settings"] = dict(n_sim=200, n_boot=200, target_scale=[8, 4], target_reps=5, prediction=True, measure="zipf")
done()
