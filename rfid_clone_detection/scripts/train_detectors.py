"""
Section 3.4 - Detection Configurations (PySpark).

Ablation by security evidence, exactly as specified:
    E1 - Protocol Only        -> threshold rule read off MB/MCM signals
                                  (no RF/SVM: this is the protocol baseline
                                  itself, tuned on val, scored on test)
    E2 - Behavioral Only      -> Random Forest + SVM (LinearSVC)
    E3 - Protocol + Behavioral -> Random Forest + SVM (LinearSVC)

Group-aware hyperparameter tuning uses Spark's CrossValidator(foldCol=...)
fed with the group-aware folds produced by split_leakage_safe.py, so no
random/StratifiedKFold ever mixes a tag's rows across folds (see 3.5).

Repeats every RF/SVM run over several seeds (paper asks for >=3, ideally 5)
and reports mean +/- SD, ready to paste into the 4.2/4.3 result tables.

Usage:
    python train_detectors.py --features features_all.csv --splits splits.csv \
        --out results_3_4.csv --seeds 42,7,123,2024,99 --n-folds 5
"""
import argparse
import time

import numpy as np
import pandas as pd
from pyspark.ml import Pipeline
from pyspark.ml.classification import LinearSVC, RandomForestClassifier
from pyspark.ml.feature import StandardScaler, VectorAssembler
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.mllib.evaluation import MulticlassMetrics
from pyspark.sql import SparkSession

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
    "E1_protocol_only": PROTOCOL_COLS,
    "E2_behavioral_only": BEHAVIORAL_COLS,
    "E3_combined": BEHAVIORAL_COLS + PROTOCOL_COLS,
}


def metrics_from_predictions(pred_df):
    pl = pred_df.select("prediction", "label").rdd.map(lambda r: (float(r[0]), float(r[1])))
    m = MulticlassMetrics(pl)
    return {
        "accuracy": m.accuracy,
        "f1_cloned": m.fMeasure(1.0),
        "recall_cloned": m.recall(1.0),        # sensitivity to clones = what matters most
        "precision_cloned": m.precision(1.0),
        "fpr": m.falsePositiveRate(0.0),        # genuine wrongly flagged
        "fnr": 1.0 - m.recall(1.0),             # clone missed
    }


def eval_protocol_only_rule(pdf: pd.DataFrame, val_mask, test_mask):
    """E1: no ML - pick the mcm_suspicion_score threshold that maximises F1
    on the validation split (the val split is exactly there so this tuning
    step doesn't touch test), flag mb_duplicate_flag==1 as an immediate hit."""
    val = pdf[val_mask]
    best_t, best_f1 = None, -1
    for t in np.quantile(val["mcm_suspicion_score"], np.linspace(0.05, 0.95, 19)):
        pred = ((val["mb_duplicate_flag"] == 1) | (val["mcm_suspicion_score"] > t)).astype(int)
        tp = ((pred == 1) & (val["label"] == 1)).sum()
        fp = ((pred == 1) & (val["label"] == 0)).sum()
        fn = ((pred == 0) & (val["label"] == 1)).sum()
        f1 = tp / (tp + 0.5 * (fp + fn) + 1e-9)
        if f1 > best_f1:
            best_f1, best_t = f1, t

    test = pdf[test_mask]
    t0 = time.perf_counter()
    pred = ((test["mb_duplicate_flag"] == 1) | (test["mcm_suspicion_score"] > best_t)).astype(int)
    infer_ms_per_sample = (time.perf_counter() - t0) * 1000.0 / max(len(test), 1)

    y = test["label"].values
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    recall = tp / (tp + fn + 1e-9)
    precision = tp / (tp + fp + 1e-9)
    return {
        "config": "E1_protocol_only", "model": "rule(MB/MCM)", "seed": 0,
        "accuracy": (tp + tn) / len(test),
        "f1_cloned": 2 * precision * recall / (precision + recall + 1e-9),
        "recall_cloned": recall,
        "precision_cloned": precision,
        "fpr": fp / (fp + tn + 1e-9),
        "fnr": 1 - recall,
        "inference_ms_per_sample": infer_ms_per_sample,
        "threshold": best_t,
    }


def build_pipeline(feature_cols, model_name, seed):
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw", handleInvalid="skip")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True, withStd=True)
    if model_name == "RandomForest":
        clf = RandomForestClassifier(featuresCol="features", labelCol="label", seed=seed)
        grid = (ParamGridBuilder()
                .addGrid(clf.numTrees, [100, 300])
                .addGrid(clf.maxDepth, [5, 10])
                .build())
    else:  # SVM
        clf = LinearSVC(featuresCol="features", labelCol="label", maxIter=100)
        grid = (ParamGridBuilder()
                .addGrid(clf.regParam, [0.01, 0.1, 1.0])
                .build())
    pipeline = Pipeline(stages=[assembler, scaler, clf])
    return pipeline, grid


def run_ml_config(spark, train_sdf, test_sdf, feature_cols, config_name, model_name, seed, n_folds):
    from pyspark.ml.evaluation import BinaryClassificationEvaluator

    pipeline, grid = build_pipeline(feature_cols, model_name, seed)
    evaluator = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
    cv = CrossValidator(
        estimator=pipeline, estimatorParamMaps=grid, evaluator=evaluator,
        numFolds=n_folds, foldCol="cv_fold", parallelism=2, seed=seed,
    )
    cv_model = cv.fit(train_sdf)  # group-aware CV via precomputed cv_fold column

    t0 = time.perf_counter()
    pred = cv_model.bestModel.transform(test_sdf)
    n_test = pred.count()  # forces the lazy transform so timing is meaningful
    infer_ms_per_sample = (time.perf_counter() - t0) * 1000.0 / max(n_test, 1)

    row = metrics_from_predictions(pred)
    row.update({
        "config": config_name, "model": model_name, "seed": seed,
        "inference_ms_per_sample": infer_ms_per_sample,
    })
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--splits", required=True)
    ap.add_argument("--out", default="results_3_4.csv")
    ap.add_argument("--seeds", default="42,7,123,2024,99")
    ap.add_argument("--n-folds", type=int, default=5)
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    pdf = pd.read_csv(args.features).merge(
        pd.read_csv(args.splits)[["session_id", "split", "cv_fold"]], on="session_id"
    )
    val_mask, test_mask = pdf["split"] == "val", pdf["split"] == "test"
    train_mask = pdf["split"] == "train"

    results = [eval_protocol_only_rule(pdf, val_mask.values, test_mask.values)]

    spark = SparkSession.builder.appName("rfid-clone-detection-3.4").getOrCreate()
    train_sdf_full = spark.createDataFrame(pdf[train_mask])
    test_sdf_full = spark.createDataFrame(pdf[test_mask])

    for config_name, feature_cols in CONFIGS.items():
        if config_name == "E1_protocol_only":
            continue  # handled by the rule above, per the proposal's design
        for model_name in ["RandomForest", "SVM"]:
            for seed in seeds:
                row = run_ml_config(
                    spark, train_sdf_full, test_sdf_full, feature_cols,
                    config_name, model_name, seed, args.n_folds,
                )
                results.append(row)
                print(row)

    spark.stop()

    df = pd.DataFrame(results)
    df.to_csv(args.out, index=False)

    metric_cols = ["accuracy", "f1_cloned", "recall_cloned", "precision_cloned",
                    "fpr", "fnr", "inference_ms_per_sample"]
    summary = (df.groupby(["config", "model"])[metric_cols]
                 .agg(["mean", "std"]))
    summary.to_csv(args.out.replace(".csv", "_summary.csv"))
    print("\n=== mean +/- SD across seeds (paste into 4.2/4.3 tables) ===")
    print(summary)


if __name__ == "__main__":
    main()
