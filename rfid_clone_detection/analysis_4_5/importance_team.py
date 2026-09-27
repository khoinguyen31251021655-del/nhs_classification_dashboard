import os
import re
import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score
from replicate_team import evidence_data, E3, group_split, make_rf, make_svm

AUDIT = {  # provenance category of each team feature (from diagnose_team.py / harmonize.py)
    "negative_dt_ratio": "sign convention", "positive_dt_ratio": "sign convention", "dt_min": "sign convention",
    "dt_mean": "sign convention", "dt_median": "sign convention",
    "dt_std": "pairing window", "dt_max": "pairing window", "dt_abs_mean": "pairing window",
    "dt_abs_median": "pairing window", "small_dt_10ms_ratio": "pairing window",
    "small_dt_50ms_ratio": "pairing window", "collision_count": "pairing window",
    "zero_dt_ratio": "timestamp resolution", "read_count": "definition mismatch",
}

seeds = [42, 7, 123, 2024, 99]
imp_rows, shap_rows, perm_rows = [], [], []
for s in seeds:
    sp = group_split(evidence_data, E3, seed=s)
    m = make_rf(seed=s).fit(sp["X_train"], sp["y_train"])
    rf = m.named_steps["rf"]
    Xte = pd.DataFrame(m.named_steps["imputer"].transform(sp["X_test"]), columns=E3)
    imp_rows.append(rf.feature_importances_)
    sv = shap.TreeExplainer(rf).shap_values(Xte)
    sv = sv[:, :, 1] if sv.ndim == 3 else sv
    shap_rows.append(np.abs(sv).mean(0))
    perm_rows.append(permutation_importance(m, sp["X_test"], sp["y_test"], n_repeats=20,
                                            random_state=s, scoring="f1").importances_mean)

imp, sh, pm = (np.array(r) for r in (imp_rows, shap_rows, perm_rows))
ranks = np.array([(-r).argsort().argsort() + 1 for r in sh])
T = pd.DataFrame({
    "impurity_mean": imp.mean(0), "impurity_sd": imp.std(0),
    "shap_mean": sh.mean(0), "shap_sd": sh.std(0),
    "shap_rank_best": ranks.min(0), "shap_rank_worst": ranks.max(0),
    "permutation_F1_drop": pm.mean(0),
    "provenance": [AUDIT[c] for c in E3],
}, index=E3).sort_values("shap_mean", ascending=False)
pd.set_option("display.width", 220)
print(T.round(4).to_string())
print("\nshare of total SHAP mass by provenance category:")
print((T.groupby("provenance").shap_mean.sum() / T.shap_mean.sum()).round(3).to_string())

# grouping fix: map S3 pair -> physical tag via plan, rerun team's split/models
plan = pd.read_csv(os.path.join(os.environ.get("RFID_DATA", "rfid_dataset"), "data", "plans", "s3_plan.csv"))
p2t = dict(zip(plan.pair_id, plan.tag_id))
ed = evidence_data.copy()
ed["tag_true"] = [re.search(r"(TAG\d+)", s).group(1) if "TAG" in s
                  else p2t[re.search(r"_(P\d+)_", s).group(1)] for s in ed.session_id]
print("\ncorrected groups:", ed.tag_true.nunique(), "| tags containing both classes:",
      (ed.groupby("tag_true").label.nunique() == 2).sum())
for s in seeds:
    sp = group_split(ed, E3, seed=s, group_col="tag_true")
    accs = []
    for mk in (make_rf, make_svm):
        mdl = mk(seed=s) if mk is make_rf else mk()
        mdl.fit(sp["X_train"], sp["y_train"])
        accs.append(accuracy_score(sp["y_test"], mdl.predict(sp["X_test"])))
    print(f"seed {s}: test n={len(sp['y_test'])}  RF acc={accs[0]:.3f}  SVM acc={accs[1]:.3f}")
