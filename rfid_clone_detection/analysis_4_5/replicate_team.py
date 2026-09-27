"""Faithful replication of RFID_Evidence_Ablation_Colab_1.ipynb cells 7-26 (no Colab I/O)."""
import re
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

import os
D = os.path.join(os.environ.get("RFID_DATA", "rfid_dataset"), "data", "processed") + "/"
s1 = pd.read_csv(D + "meta_sessions_S1.csv")
s2_coll = pd.read_csv(D + "s2_collisions_summary.csv")
s3 = pd.read_csv(D + "s3_clone_collisions_summary.csv")

real_behavior = s1.copy()
real_behavior["read_count"] = real_behavior["total_reads"]
real_behavior["label"] = 0


def protocol_features_from_collision_events(df, session_col, dt_col):
    g = df.groupby(session_col)[dt_col]
    out = g.agg(collision_count="count", dt_mean="mean", dt_std="std", dt_median="median",
                dt_min="min", dt_max="max",
                dt_abs_mean=lambda x: np.abs(x).mean(),
                dt_abs_median=lambda x: np.abs(x).median()).reset_index()
    by = df[[session_col, dt_col]].groupby(session_col)[dt_col]
    extra = pd.DataFrame({
        session_col: by.apply(lambda x: 0).index,
        "small_dt_10ms_ratio": by.apply(lambda x: (np.abs(x) <= 0.010).mean()).values,
        "small_dt_50ms_ratio": by.apply(lambda x: (np.abs(x) <= 0.050).mean()).values,
        "positive_dt_ratio": by.apply(lambda x: (x > 0).mean()).values,
        "negative_dt_ratio": by.apply(lambda x: (x < 0).mean()).values,
        "zero_dt_ratio": by.apply(lambda x: (x == 0).mean()).values,
    })
    return out.merge(extra, on=session_col, how="left")


s2_protocol = protocol_features_from_collision_events(s2_coll, "session_id", "dt")
s2_protocol["label"] = 0

s3_work = s3.copy()
s3_work["dt_sec"] = s3_work["delta_ms"] / 1000.0
s3_protocol = protocol_features_from_collision_events(s3_work, "session_id", "dt_sec")
s3_protocol["label"] = 1
s3_behavior = s3.groupby("session_id").agg(read_count=("uid_hash", "count")).reset_index()
s3_behavior["label"] = 1

PROTOCOL_FEATURES = ["collision_count", "dt_mean", "dt_std", "dt_median", "dt_min", "dt_max",
                     "dt_abs_mean", "dt_abs_median", "small_dt_10ms_ratio", "small_dt_50ms_ratio",
                     "positive_dt_ratio", "negative_dt_ratio", "zero_dt_ratio"]

protocol_data = pd.concat([s2_protocol[["session_id"] + PROTOCOL_FEATURES + ["label"]],
                           s3_protocol[["session_id"] + PROTOCOL_FEATURES + ["label"]]], ignore_index=True)
behavior_data = pd.concat([real_behavior[["session_id", "read_count", "label"]],
                           s3_behavior[["session_id", "read_count", "label"]]], ignore_index=True)


def extract_tag(x):
    m = re.search(r"(TAG\d+)", str(x))
    return m.group(1) if m else str(x)


def make_sample_index(df):
    out = df.copy()
    out["tag_group"] = out["session_id"].map(extract_tag)
    out["within_tag_order"] = out.groupby("tag_group").cumcount()
    out["sample_key"] = out["tag_group"].astype(str) + "__" + out["within_tag_order"].astype(str)
    return out


protocol_data = make_sample_index(protocol_data)
behavior_data = make_sample_index(behavior_data)
common = sorted(set(protocol_data["sample_key"]) & set(behavior_data["sample_key"]))
p = protocol_data[protocol_data["sample_key"].isin(common)].copy()
b = behavior_data[behavior_data["sample_key"].isin(common)].copy()
evidence_data = p[["sample_key", "tag_group", "label", "session_id"] + PROTOCOL_FEATURES].merge(
    b[["sample_key", "read_count", "session_id"]].rename(columns={"session_id": "behavior_session_id"}),
    on="sample_key", how="inner")

E1 = PROTOCOL_FEATURES
E2 = ["read_count"]
E3 = PROTOCOL_FEATURES + ["read_count"]


def group_split(df, cols, test_size=0.2, val_size=0.2, seed=42, group_col="tag_group"):
    X, y, g = df[cols].copy(), df["label"].copy(), df[group_col].copy()
    tv, te = next(GroupShuffleSplit(1, test_size=test_size, random_state=seed).split(X, y, g))
    Xtv, ytv, gtv = X.iloc[tv].reset_index(drop=True), y.iloc[tv].reset_index(drop=True), g.iloc[tv].reset_index(drop=True)
    tr, va = next(GroupShuffleSplit(1, test_size=val_size / (1 - test_size), random_state=seed + 1).split(Xtv, ytv, gtv))
    return dict(X_train=Xtv.iloc[tr].reset_index(drop=True), y_train=ytv.iloc[tr].reset_index(drop=True),
                g_train=gtv.iloc[tr].reset_index(drop=True),
                X_val=Xtv.iloc[va].reset_index(drop=True), y_val=ytv.iloc[va].reset_index(drop=True),
                X_test=X.iloc[te].reset_index(drop=True), y_test=y.iloc[te].reset_index(drop=True),
                g_test=g.iloc[te].reset_index(drop=True))


def make_rf(seed=42):
    return Pipeline([("imputer", SimpleImputer(strategy="median")),
                     ("rf", RandomForestClassifier(n_estimators=300, random_state=seed, class_weight="balanced"))])


def make_svm():
    return Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()),
                     ("svm", SVC(kernel="rbf", class_weight="balanced", random_state=42))])


if __name__ == "__main__":
    print("unified:", evidence_data.shape, "groups:", evidence_data["tag_group"].nunique())
    print(evidence_data["label"].value_counts().to_dict())
    for name, cols in [("E2", E2), ("E3", E3)]:
        sp = group_split(evidence_data, cols)
        for mname, m in [("RF", make_rf()), ("SVM", make_svm())]:
            m.fit(sp["X_train"], sp["y_train"])
            pr = m.predict(sp["X_test"])
            print(name, mname, "test acc", accuracy_score(sp["y_test"], pr), "n_test", len(pr),
                  "real/clone", (sp["y_test"] == 0).sum(), (sp["y_test"] == 1).sum())
