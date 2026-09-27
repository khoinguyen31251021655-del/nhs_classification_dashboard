"""Harmonised re-derivation of cross-reader evidence from RAW S2/S3 events.

Same pairing rule, same sign convention (tB - tA), same 1 ms resolution for
both classes, so any remaining separation cannot come from how the two
summary CSVs were produced. Adds a rate-normalised synchrony score that
removes the read-density confound.
"""
import json
import re
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.inspection import permutation_importance
import shap

import os
D = os.path.join(os.environ.get("RFID_DATA", "rfid_dataset"), "data") + "/"
W = 0.005  # 5 ms co-presence window


def load(s):
    df = pd.DataFrame([json.loads(l) for l in open(D + f"processed/rfid_dataset_{s}_all.jsonl") if l.strip()])
    df = df[df.event == "read_success"].copy()
    ts = pd.to_datetime(df.timestamp_iso, utc=True)
    df["t"] = (ts - pd.Timestamp("2025-11-01", tz="UTC")).dt.total_seconds()
    df["t"] = np.round(df["t"] * 1000) / 1000  # common 1 ms grid
    return df


plan = pd.read_csv(D + "plans/s3_plan.csv")
pair_to_tag = dict(zip(plan.pair_id, plan.tag_id))


def tag_of(sid):
    m = re.search(r"(TAG\d+)", sid)
    if m:
        return m.group(1)
    return pair_to_tag[re.search(r"_(P\d+)_", sid).group(1)]


def session_features(g):
    a = np.sort(g.loc[g.device_id == "ESP32_A", "t"].values)
    b = np.sort(g.loc[g.device_id == "ESP32_B", "t"].values)
    dur = g.t.max() - g.t.min()
    out = dict(reads_per_reader=len(g) / 2, read_rate_hz=len(g) / dur if dur > 0 else np.nan, duration_s=dur)
    if len(a) == 0 or len(b) == 0:
        return out
    i = np.clip(np.searchsorted(b, a), 1, len(b) - 1)
    nn = np.where(np.abs(b[i] - a) < np.abs(b[i - 1] - a), b[i], b[i - 1])
    d = nn - a  # signed, same convention for both classes
    pair = np.abs(d) <= W + 1e-9
    lam_b = len(b) / dur
    expected = 1 - np.exp(-2 * W * lam_b)  # chance coincidence under independent reads
    sync = pair.mean()
    out.update(
        sync_rate_5ms=sync,
        chance_rate_5ms=expected,
        excess_sync_log=np.log((sync + 1e-4) / (expected + 1e-4)),
        nn_abs_delta_median_ms=np.median(np.abs(d)) * 1000,
        negative_share_in_window=(d[pair] < 0).mean() if pair.any() else np.nan,
        zero_share_in_window=(d[pair] == 0).mean() if pair.any() else np.nan,
    )
    return out


rows = []
for s, label in [("S2", 0), ("S3", 1)]:
    df = load(s)
    for sid, g in df.groupby("session_id"):
        r = session_features(g)
        r.update(session_id=sid, scenario=s, label=label, tag=tag_of(sid))
        rows.append(r)
H = pd.DataFrame(rows)
H.to_csv("harmonised_S2_S3.csv", index=False)
lam = H.reads_per_reader / H.duration_s
H["sync_over_chance"] = H.sync_rate_5ms / H.chance_rate_5ms
H["nn_ratio_to_chance"] = H.nn_abs_delta_median_ms / (np.log(2) / (2 * lam) * 1000)
print(H.groupby("scenario")[["read_rate_hz", "sync_rate_5ms", "chance_rate_5ms", "sync_over_chance", "nn_abs_delta_median_ms", "nn_ratio_to_chance"]].median().round(3).T)

FEATS = ["negative_share_in_window", "zero_share_in_window", "reads_per_reader",
         "nn_abs_delta_median_ms", "sync_rate_5ms", "excess_sync_log", "read_rate_hz", "duration_s"]
print("groups (tags) per class:", H.groupby("label").tag.nunique().to_dict())
res = []
for c in FEATS:
    x = H[c].fillna(H[c].median())
    auc = roc_auc_score(H.label, x)
    res.append(dict(feature=c, real_S2_median=H.loc[H.label == 0, c].median(),
                    clone_S3_median=H.loc[H.label == 1, c].median(), single_AUC=max(auc, 1 - auc)))
pd.set_option("display.width", 200)
print(pd.DataFrame(res).round(4).to_string(index=False))

# tag-grouped RF on the provenance-robust subset only (drops rate/duration/resolution cues)
ROBUST = ["negative_share_in_window", "nn_abs_delta_median_ms", "excess_sync_log", "reads_per_reader"]
X, y, g = H[ROBUST].fillna(0), H.label, H.tag
rf = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
pred = cross_val_predict(rf, X, y, groups=g, cv=GroupKFold(6))
print("\nleave-tags-out RF on robust subset: acc", round((pred == y).mean(), 4))
rf.fit(X, y)
sv = shap.TreeExplainer(rf).shap_values(X)
sv = sv[:, :, 1] if sv.ndim == 3 else sv
imp = pd.DataFrame({"impurity": rf.feature_importances_, "mean_abs_shap": np.abs(sv).mean(0),
                    "direction_corr": [np.corrcoef(X[c], sv[:, i])[0, 1] if X[c].std() > 0 else np.nan
                                       for i, c in enumerate(ROBUST)]}, index=ROBUST)
print(imp.sort_values("mean_abs_shap", ascending=False).round(4).to_string())
