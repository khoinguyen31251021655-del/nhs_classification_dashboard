"""
Section 4.5 - Feature Importance and Security Interpretation.

Trains a Random Forest on E2 (behavioral only) and E3 (combined) using the
SAME leakage-safe train/test split as 3.4/3.5, then reports three
complementary importance measures (impurity-based alone is known to be
biased under correlated features, which this dataset has plenty of):

  1. Native RF impurity importance (mean decrease in Gini)
  2. Permutation importance on the held-out test split (drop in F1)
  3. SHAP (mean |SHAP value| + direction of effect via corr(feature, shap))

Answers the question 4.5 actually asks -- not "what does the chart look
like" but "which security evidence is the detector relying on, and does
raising that evidence raise or lower predicted clone risk" -- by printing
a directional table (Feature UP -> Clone Risk UP/DOWN) alongside the
ranking, and saves one bar chart (SHAP-based, E3) for the writeup.

Usage:
    python feature_importance.py --features features_all.csv --splits splits.csv \
        --out-dir results_4_5/
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

BEHAVIORAL_COLS = [
    "n_reads", "success_rate", "duration_s",
    "mean_inter_read_ms", "std_inter_read_ms", "max_inter_read_ms",
    "n_distinct_readers", "reader_transition_count", "reader_transition_rate",
    "n_distinct_distance", "distance_std",
    "n_distinct_orientation", "orientation_std",
    "impossible_movement_count", "impossible_movement_rate",
]
PROTOCOL_COLS = [
    "mb_duplicate_flag", "mb_concurrent_reader_max",
    "mb_min_cross_reader_delta_ms",
    "mcm_read_count_window", "mcm_suspicion_score",
]
CONFIGS = {
    "E2_behavioral_only": BEHAVIORAL_COLS,
    "E3_combined": BEHAVIORAL_COLS + PROTOCOL_COLS,
}


def analyse(train, test, cols, seed=42):
    Xtr, ytr = train[cols], train["label"]
    Xte, yte = test[cols], test["label"]

    rf = RandomForestClassifier(n_estimators=300, max_depth=10, random_state=seed,
                                 class_weight="balanced")
    rf.fit(Xtr, ytr)

    impurity = pd.Series(rf.feature_importances_, index=cols, name="impurity_importance")

    perm = permutation_importance(rf, Xte, yte, n_repeats=30, random_state=seed, scoring="f1")
    perm_imp = pd.Series(perm.importances_mean, index=cols, name="permutation_importance_f1")

    explainer = shap.TreeExplainer(rf)
    sv = explainer.shap_values(Xte)
    sv_pos = sv[:, :, 1] if getattr(sv, "ndim", 2) == 3 else (sv[1] if isinstance(sv, list) else sv)
    mean_abs_shap = pd.Series(np.abs(sv_pos).mean(axis=0), index=cols, name="mean_abs_shap")

    direction = {}
    for i, c in enumerate(cols):
        if Xte[c].std() == 0:
            direction[c] = np.nan  # constant feature in this split -> no direction to report
        else:
            direction[c] = np.corrcoef(Xte[c].values, sv_pos[:, i])[0, 1]
    direction = pd.Series(direction, name="direction_corr")

    table = pd.concat([impurity, perm_imp, mean_abs_shap, direction], axis=1)
    table = table.sort_values("mean_abs_shap", ascending=False)
    return table, rf, sv_pos, Xte


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--splits", required=True)
    ap.add_argument("--out-dir", default="results_4_5")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.features).merge(
        pd.read_csv(args.splits)[["session_id", "split"]], on="session_id"
    )
    train, test = df[df.split == "train"], df[df.split == "test"]

    for config_name, cols in CONFIGS.items():
        table, rf, sv_pos, Xte = analyse(train, test, cols)
        table.to_csv(out_dir / f"feature_importance_{config_name}.csv")
        print(f"\n=== {config_name} ===")
        print(table.round(4).to_string())

        if config_name == "E3_combined":
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt

                ranked = table.sort_values("mean_abs_shap")
                colors = ["#c0392b" if d > 0 else "#2980b9" for d in ranked["direction_corr"].fillna(0)]
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.barh(ranked.index, ranked["mean_abs_shap"], color=colors)
                ax.set_xlabel("mean |SHAP value| (impact on predicted clone risk)")
                ax.set_title("E3 Combined -- feature importance (red = raises clone risk, blue = lowers it)")
                fig.tight_layout()
                fig.savefig(out_dir / "shap_importance_E3.png", dpi=150)
                print(f"\nsaved chart -> {out_dir / 'shap_importance_E3.png'}")
            except ImportError:
                print("matplotlib not installed, skipped chart")


if __name__ == "__main__":
    main()
