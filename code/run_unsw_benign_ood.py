#!/usr/bin/env python3
"""Evaluate a benign-only anomaly detector on the official UNSW-NB15 test set.

The detector returns only BENIGN or ATTACK. Attack subtypes are never used to
fit or calibrate the detector; they are collapsed only for evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    parser.add_argument("--trees", type=int, default=200)
    parser.add_argument("--target-fpr", type=float, default=0.01)
    args = parser.parse_args()
    if not 0 < args.target_fpr < 0.5:
        parser.error("--target-fpr must be between 0 and 0.5")
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("--out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(args.train, low_memory=False)
    test = pd.read_csv(args.test, low_memory=False)
    for frame in (train, test):
        frame.columns = [c.strip() for c in frame.columns]
        frame["attack_cat"] = frame["attack_cat"].fillna("Normal").astype(str).str.strip()
        frame.loc[frame.attack_cat.str.lower().isin(["", "nan", "normal", "benign"]), "attack_cat"] = "Normal"
    drop = [c for c in ["id", "label", "attack_cat"] if c in train.columns]
    y_train = np.where(train.attack_cat.eq("Normal"), "BENIGN", "ATTACK")
    y_test = np.where(test.attack_cat.eq("Normal"), "BENIGN", "ATTACK")
    X_train = train.drop(columns=drop).copy()
    X_test = test.drop(columns=drop).copy()
    categorical = [c for c in ["proto", "service", "state"] if c in X_train.columns]
    numeric = [c for c in X_train.columns if c not in categorical]
    for column in categorical:
        X_train[column] = X_train[column].fillna("-").astype(str).str.strip()
        X_test[column] = X_test[column].fillna("-").astype(str).str.strip()
    for column in numeric:
        X_train[column] = pd.to_numeric(X_train[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
        X_test[column] = pd.to_numeric(X_test[column], errors="coerce").replace([np.inf, -np.inf], np.nan)

    benign_ix = np.flatnonzero(y_train == "BENIGN")
    fit_ix, calibration_ix = train_test_split(benign_ix, test_size=0.2, random_state=20261109)
    preprocessing = ColumnTransformer([
        ("num", SimpleImputer(strategy="median", add_indicator=True), numeric),
        ("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]), categorical),
    ], sparse_threshold=0.3)
    X_fit = preprocessing.fit_transform(X_train.iloc[fit_ix])
    X_calibration = preprocessing.transform(X_train.iloc[calibration_ix])
    X_eval = preprocessing.transform(X_test)
    results = []
    confusion = []
    calibration_rows = []
    labels = ["BENIGN", "ATTACK"]
    for seed in args.seeds:
        detector = IsolationForest(n_estimators=args.trees, max_samples="auto",
                                   contamination="auto", n_jobs=-1, random_state=seed)
        detector.fit(X_fit)
        calibration_scores = detector.score_samples(X_calibration)
        threshold = float(np.quantile(calibration_scores, args.target_fpr, method="lower"))
        pred_calibration = np.where(calibration_scores < threshold, "ATTACK", "BENIGN")
        observed_calibration_fpr = float(np.mean(pred_calibration == "ATTACK"))
        scores = detector.score_samples(X_eval)
        prediction = np.where(scores < threshold, "ATTACK", "BENIGN")
        cm = confusion_matrix(y_test, prediction, labels=labels)
        tn, fp, fn, tp = cm.ravel()
        row = {
            "seed": seed,
            "train_benign_fit_rows": int(len(fit_ix)),
            "train_benign_calibration_rows": int(len(calibration_ix)),
            "test_rows": int(len(y_test)),
            "test_attack_rows": int(np.sum(y_test == "ATTACK")),
            "target_calibration_fpr": args.target_fpr,
            "observed_calibration_fpr": observed_calibration_fpr,
            "threshold": threshold,
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "test_fpr": float(fp / (fp + tn)),
            "attack_recall": float(tp / (tp + fn)),
            "attack_precision": float(precision_score(y_test, prediction, pos_label="ATTACK", zero_division=0)),
            "binary_macro_f1": float(f1_score(y_test, prediction, labels=labels, average="macro", zero_division=0)),
            "legal_output_ceiling": 1.0,
            "scored_outputs": "BENIGN|ATTACK",
        }
        results.append(row)
        confusion.append({"seed": seed, "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)})
        for attack, count in test.loc[test.attack_cat.ne("Normal"), "attack_cat"].value_counts().sort_index().items():
            calibration_rows.append({"seed": seed, "attack_category": attack, "test_support": int(count),
                                     "attack_detected_as_attack": int(np.sum((test.attack_cat.to_numpy() == attack) & (prediction == "ATTACK")))})
        print(f"seed={seed} macro_f1={row['binary_macro_f1']:.5f} attack_recall={row['attack_recall']:.5f} "
              f"test_fpr={row['test_fpr']:.5f}", flush=True)

    result = pd.DataFrame(results)
    result.to_csv(args.out / "seed_metrics.csv", index=False)
    pd.DataFrame(confusion).to_csv(args.out / "confusion_by_seed.csv", index=False)
    pd.DataFrame(calibration_rows).to_csv(args.out / "attack_category_detection.csv", index=False)
    summary = result[["binary_macro_f1", "attack_recall", "test_fpr", "observed_calibration_fpr"]].agg(["mean", "std"]).T
    summary.to_csv(args.out / "summary.csv", index_label="metric")
    metadata = {
        "protocol": "official UNSW-NB15 train/test partition; benign-only training; benign-only calibration holdout",
        "detector": "IsolationForest fitted only on BENIGN training rows",
        "threshold": f"lower {args.target_fpr:.3%} quantile of held-out benign training anomaly scores",
        "target": "binary BENIGN versus ATTACK; attack subtypes used only for descriptive test breakdown",
        "seeds": args.seeds,
        "trees": args.trees,
        "legal_output_vocabulary": labels,
        "legal_output_ceiling": 1.0,
        "not_a_fine_grained_attack_classifier": True,
        "files": {str(path): sha256(path) for path in [args.train, args.test]},
    }
    (args.out / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Saved benign-only OOD results under {args.out}", flush=True)


if __name__ == "__main__":
    main()
