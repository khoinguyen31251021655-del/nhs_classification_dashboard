"""
Section 3.5 - Leakage-Safe Evaluation Protocol.

Builds:
  1. A Session-aware/Group-aware Train/Val/Test split (60/20/20), grouped by
     `group_key` (tag_local_id / UID) so no tag ever appears on both sides of
     a boundary -- prevents the model from "remembering" tag identity instead
     of learning clone behaviour (see docs/leakage_note.md for the concrete
     numbers that make this non-optional on this dataset).
  2. Group-aware K-fold indices *within the training split only*, for
     hyperparameter tuning (train_detectors.py's CrossValidator loop reads
     these instead of a random/StratifiedKFold).

Usage:
    python split_leakage_safe.py --features features_all.csv \
        --out splits.csv --seed 42 --n-folds 5
"""
import argparse

import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit


def make_split(df: pd.DataFrame, seed: int, test_size=0.2, val_size=0.25):
    # val_size is relative to the remaining (train+val) pool after test is cut,
    # so 0.25 of the 80% left == 20% of the whole set -> 60/20/20 overall
    gss1 = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    trainval_idx, test_idx = next(gss1.split(df, groups=df["group_key"]))

    trainval = df.iloc[trainval_idx]
    gss2 = GroupShuffleSplit(n_splits=1, test_size=val_size, random_state=seed)
    train_idx_rel, val_idx_rel = next(gss2.split(trainval, groups=trainval["group_key"]))
    train_idx = trainval.index[train_idx_rel]
    val_idx = trainval.index[val_idx_rel]

    split = pd.Series("train", index=df.index, name="split")
    split.iloc[df.index.get_indexer(val_idx)] = "val"
    split.iloc[df.index.get_indexer(test_idx)] = "test"
    return split


def assert_no_group_leakage(df: pd.DataFrame, split: pd.Series):
    merged = df.assign(split=split)
    groups_per_split = merged.groupby("group_key")["split"].nunique()
    leaking = groups_per_split[groups_per_split > 1]
    if len(leaking):
        raise AssertionError(
            f"leakage: these group_key values appear in >1 split: {list(leaking.index)}"
        )


def make_cv_folds(train_df: pd.DataFrame, n_folds: int):
    gkf = GroupKFold(n_splits=n_folds)
    fold_col = pd.Series(-1, index=train_df.index, name="cv_fold")
    for fold, (_, val_idx) in enumerate(gkf.split(train_df, groups=train_df["group_key"])):
        fold_col.iloc[val_idx] = fold
    return fold_col


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", default="splits.csv")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-folds", type=int, default=5)
    args = ap.parse_args()

    df = pd.read_csv(args.features)
    split = make_split(df, seed=args.seed)
    assert_no_group_leakage(df, split)

    out = df[["session_id", "group_key", "label"]].copy()
    out["split"] = split.values

    train_df = df[split.values == "train"]
    cv_fold = make_cv_folds(train_df, args.n_folds)
    out["cv_fold"] = -1
    out.loc[train_df.index, "cv_fold"] = cv_fold.values

    out.to_csv(args.out, index=False)

    print(out["split"].value_counts())
    print("\nlabel balance per split:")
    print(df.assign(split=split).groupby("split")["label"].mean())
    print(f"\nwrote {args.out} (no group_key crosses a split boundary -- verified)")


if __name__ == "__main__":
    main()
