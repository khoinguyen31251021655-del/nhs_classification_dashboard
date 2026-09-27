"""Section 4.6 (RQ3): detection effectiveness vs computational overhead.

Rows follow the table requested for 4.6:
  MB/MCM  -> the notebook's E1 protocol detector (univariate threshold on protocol evidence)
  RF, SVM -> E2 behavioral-only detectors
  Hybrid  -> E3 protocol + behavioral (RF and SVM)

Processing time  = building one session's feature vector from its event records,
                   using the notebook's own feature code (single-session call).
Inference time   = one decision for one feature vector (single-sample call).
Both are medians over repeated calls; batch-amortised figures are printed too.
"""
import os
import pickle
import platform
import re
import time
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import recall_score, confusion_matrix
from replicate_team import (evidence_data, E1, E2, E3, group_split, make_rf, make_svm,
                            protocol_features_from_collision_events, s2_coll, s3)
from harmonize import load, session_features as raw_pairing_features

SEEDS = [42, 7, 123, 2024, 99]
REPS = 200

plan = pd.read_csv(os.path.join(os.environ.get("RFID_DATA", "rfid_dataset"), "data", "plans", "s3_plan.csv"))
p2t = dict(zip(plan.pair_id, plan.tag_id))
ed = evidence_data.copy()
ed["tag_true"] = [re.search(r"(TAG\d+)", s).group(1) if "TAG" in s
                  else p2t[re.search(r"_(P\d+)_", s).group(1)] for s in ed.session_id]


def fit_protocol_detector(X, y):  # notebook cell 16, unchanged logic
    scores = {}
    for c in X.columns:
        a, b = X.loc[y == 0, c].dropna(), X.loc[y == 1, c].dropna()
        pooled = np.sqrt((a.var() + b.var()) / 2)
        scores[c] = 0.0 if (pooled == 0 or np.isnan(pooled)) else abs((a.mean() - b.mean()) / pooled)
    f = max(scores, key=scores.get)
    a, b = X.loc[y == 0, f].median(), X.loc[y == 1, f].median()
    return {"feature": f, "threshold": (a + b) / 2, "real_is_low": a < b}


def predict_protocol(X, d):
    x = X[d["feature"]].fillna(d["threshold"])
    return ((x > d["threshold"]) if d["real_is_low"] else (x < d["threshold"])).astype(int).to_numpy()


def median_ms(fn, reps=REPS):
    fn()
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter(); fn(); ts.append(time.perf_counter() - t0)
    return float(np.median(ts) * 1000)


def rates(y, p):
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    return tp / (tp + fn), fp / (fp + tn)


def run(group_col):
    rows = []
    for s in SEEDS:
        sp1 = group_split(ed, E1, seed=s, group_col=group_col)
        det = fit_protocol_detector(sp1["X_train"], sp1["y_train"])
        p = predict_protocol(sp1["X_test"], det)
        r, f = rates(sp1["y_test"], p)
        one = sp1["X_test"].iloc[[0]]
        rows.append(dict(method="MB/MCM (E1 protocol detector)", seed=s, recall=r, fpr=f,
                         infer_ms=median_ms(lambda: predict_protocol(one, det)), fit_s=np.nan,
                         size_kb=len(pickle.dumps(det)) / 1024, feature=det["feature"]))
        for name, cols in [("E2", E2), ("E3", E3)]:
            sp = group_split(ed, cols, seed=s, group_col=group_col)
            for mname, mk in [("RF", lambda: make_rf(seed=s)), ("SVM", make_svm)]:
                m = mk()
                t0 = time.perf_counter(); m.fit(sp["X_train"], sp["y_train"]); fit_s = time.perf_counter() - t0
                r, f = rates(sp["y_test"], m.predict(sp["X_test"]))
                one = sp["X_test"].iloc[[0]]
                n = len(sp["X_test"])
                batch = median_ms(lambda: m.predict(sp["X_test"]), reps=50) / n
                label = (mname if name == "E2" else f"Hybrid ({mname})")
                extra = {}
                if mname == "RF":
                    extra["nodes"] = sum(t.tree_.node_count for t in m.named_steps["rf"].estimators_)
                else:
                    extra["n_sv"] = int(m.named_steps["svm"].n_support_.sum())
                rows.append(dict(method=label, seed=s, recall=r, fpr=f, infer_ms=median_ms(lambda: m.predict(one)),
                                 batch_ms_per_sample=batch, fit_s=fit_s,
                                 size_kb=len(pickle.dumps(m)) / 1024, **extra))
    return pd.DataFrame(rows)


def processing_times():
    s3w = s3.copy(); s3w["dt_sec"] = s3w["delta_ms"] / 1000.0
    s2_ids = s2_coll.session_id.unique()[:40]
    s3_ids = s3w.session_id.unique()[:40]
    prot = [median_ms(lambda g=s2_coll[s2_coll.session_id == i]: protocol_features_from_collision_events(g, "session_id", "dt"), 30) for i in s2_ids]
    prot += [median_ms(lambda g=s3w[s3w.session_id == i]: protocol_features_from_collision_events(g, "session_id", "dt_sec"), 30) for i in s3_ids]
    beh = [median_ms(lambda g=s3[s3.session_id == i]: len(g), 200) for i in s3_ids]
    t0 = time.perf_counter(); protocol_features_from_collision_events(s2_coll, "session_id", "dt")
    batch_prot = (time.perf_counter() - t0) * 1000 / s2_coll.session_id.nunique()
    raw = pd.concat([load("S2"), load("S3")])
    ids = raw.session_id.unique()[::6]
    pair = [median_ms(lambda g=raw[raw.session_id == i]: raw_pairing_features(g), 30) for i in ids]
    return dict(protocol_ms=np.median(prot), behavior_ms=np.median(beh),
                protocol_batch_ms_per_session=batch_prot, raw_pairing_ms=np.median(pair))


if __name__ == "__main__":
    print(f"env: {platform.processor() or platform.machine()} | {os.cpu_count()} vCPU | Python {platform.python_version()} | sklearn {sklearn.__version__}")
    pt = processing_times()
    print("processing (ms/session):", {k: round(v, 4) for k, v in pt.items()})
    for gc in ["tag_true", "tag_group"]:
        df = run(gc)
        agg = df.groupby("method", sort=False).agg(
            recall=("recall", "mean"), fpr=("fpr", "mean"),
            infer_ms=("infer_ms", "median"), batch_ms=("batch_ms_per_sample", "median"),
            fit_s=("fit_s", "median"), size_kb=("size_kb", "median"),
            nodes=("nodes", "median") if "nodes" in df else ("seed", "size"),
            n_sv=("n_sv", "median") if "n_sv" in df else ("seed", "size"))
        print(f"\n=== grouping: {gc} ===")
        print(agg.round(4).to_string())
        if gc == "tag_true":
            print("E1 selected feature per seed:", df[df.method.str.startswith("MB")].feature.tolist())
