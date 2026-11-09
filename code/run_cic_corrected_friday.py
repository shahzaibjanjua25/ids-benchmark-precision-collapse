#!/usr/bin/env python3
"""Run seeded Friday holdout models on the corrected DistriNet CICIDS2017 files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import confusion_matrix, f1_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DAY_FILES = {
    "Monday": "Monday-WorkingHours.csv",
    "Tuesday": "Tuesday-WorkingHours.csv",
    "Wednesday": "Wednesday-WorkingHours.csv",
    "Thursday": "Thursday-WorkingHours.csv",
    "Friday": "Friday-WorkingHours.csv",
}
DROP_COLUMNS = {"Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Timestamp", "Label"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_day(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    frame.columns = [str(c).strip() for c in frame.columns]
    frame["Label"] = frame["Label"].fillna("UNKNOWN").astype(str).str.strip()
    if "Timestamp" not in frame:
        raise ValueError(f"No Timestamp field in {path}")
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    if frame["Timestamp"].isna().any():
        raise ValueError(f"Invalid timestamps in {path}")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path, help="Directory with the five corrected per-day CSV files")
    parser.add_argument("out", type=Path)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--per-class-cap", type=int, default=10000,
                        help="Maximum rows per training label and seed; use 0 for all rows")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)

    missing = [name for name in DAY_FILES.values() if not (args.data_dir / name).is_file()]
    if missing:
        parser.error(f"Missing corrected per-day files: {missing}")

    train_parts = []
    timestamp_ranges = {}
    day_counts = {}
    for day in ("Monday", "Tuesday", "Wednesday", "Thursday"):
        frame = load_day(args.data_dir / DAY_FILES[day])
        timestamp_ranges[day] = [frame.Timestamp.min().isoformat(), frame.Timestamp.max().isoformat()]
        day_counts[day] = frame.Label.value_counts().sort_index().to_dict()
        train_parts.append(frame)
        print(f"loaded {day}: {len(frame):,} rows", flush=True)
    train = pd.concat(train_parts, ignore_index=True)
    test = load_day(args.data_dir / DAY_FILES["Friday"])
    timestamp_ranges["Friday"] = [test.Timestamp.min().isoformat(), test.Timestamp.max().isoformat()]
    day_counts["Friday"] = test.Label.value_counts().sort_index().to_dict()
    if max(pd.Timestamp(x[1]) for d, x in timestamp_ranges.items() if d != "Friday") >= pd.Timestamp(timestamp_ranges["Friday"][0]):
        raise ValueError("The training days are not strictly earlier than Friday")

    feature_columns = [c for c in train.columns if c not in DROP_COLUMNS]
    test = test.reindex(columns=train.columns)
    categorical = [c for c in feature_columns if train[c].dtype == "object"]
    numeric = [c for c in feature_columns if c not in categorical]
    for frame in (train, test):
        for column in categorical:
            frame[column] = frame[column].fillna("UNKNOWN").astype(str).str.strip()
        for column in numeric:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
    train_labels = train.Label.to_numpy()
    test_labels = test.Label.to_numpy()
    test_inventory = sorted(pd.unique(test_labels))
    training_vocabulary = set(pd.unique(train_labels))
    coverage = {label: int(label in training_vocabulary) for label in test_inventory}
    ceiling = float(np.mean([2 * rho / (1 + rho) for rho in coverage.values()]))

    models = {
        "random_forest": lambda seed: RandomForestClassifier(
            n_estimators=100, max_depth=20, min_samples_leaf=2, n_jobs=-1, random_state=seed
        ),
        "extra_trees": lambda seed: ExtraTreesClassifier(
            n_estimators=100, max_depth=20, min_samples_leaf=2, n_jobs=-1, random_state=seed
        ),
        "sgd_log_loss": lambda seed: SGDClassifier(
            loss="log_loss", max_iter=30, tol=1e-3, early_stopping=True,
            n_jobs=-1, random_state=seed, class_weight="balanced"
        ),
    }
    runs = []
    per_class = []
    confusion_rows = []
    y_test_macro = test_labels
    for seed in args.seeds:
        if args.per_class_cap > 0:
            sampled = pd.concat(
                [group.sample(n=min(len(group), args.per_class_cap), random_state=seed)
                 for _, group in train.groupby("Label", sort=True)],
                ignore_index=True,
            )
        else:
            sampled = train
        X_fit = sampled[feature_columns]
        y_fit = sampled.Label.to_numpy()
        for model_name, factory in models.items():
            numeric_steps = [("impute", SimpleImputer(strategy="median", add_indicator=True))]
            if model_name == "sgd_log_loss":
                numeric_steps.append(("scale", StandardScaler()))
            transformers = [("num", Pipeline(numeric_steps), numeric)]
            if categorical:
                transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), categorical))
            prep = ColumnTransformer(transformers, remainder="drop")
            pipeline = Pipeline([("prep", prep), ("model", factory(seed))])
            pipeline.fit(X_fit, y_fit)
            prediction = pipeline.predict(test[feature_columns])
            prediction_inventory = sorted(training_vocabulary | set(test_inventory))
            cm = confusion_matrix(y_test_macro, prediction, labels=prediction_inventory)
            f1 = f1_score(y_test_macro, prediction, labels=test_inventory,
                          average="macro", zero_division=0)
            true_binary = np.where(y_test_macro == "BENIGN", "BENIGN", "ATTACK")
            pred_binary = np.where(prediction == "BENIGN", "BENIGN", "ATTACK")
            attack_recall = float(recall_score(true_binary, pred_binary, labels=["BENIGN", "ATTACK"],
                                               pos_label="ATTACK", average="binary", zero_division=0))
            binary_macro_f1 = float(f1_score(true_binary, pred_binary, labels=["BENIGN", "ATTACK"],
                                             average="macro", zero_division=0))
            runs.append({"model": model_name, "seed": seed, "train_rows": len(sampled),
                         "test_rows": len(test), "positive_support_labels": len(test_inventory),
                         "train_vocabulary_size": len(training_vocabulary),
                         "coverage_ceiling": ceiling, "macro_f1": float(f1),
                         "binary_macro_f1": binary_macro_f1, "attack_recall": attack_recall,
                         "scoring": "pooled macro F1 over test-positive labels; unseen train labels cannot be predicted"})
            for i, true_label in enumerate(test_inventory):
                class_index = prediction_inventory.index(true_label)
                support = int(np.sum(y_test_macro == true_label))
                tp = int(cm[class_index, class_index])
                fp = int(cm[:, class_index].sum() - tp)
                fn = support - tp
                class_f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
                per_class.append({"model": model_name, "seed": seed, "label": true_label,
                                  "test_support": support, "train_label_available": coverage[true_label],
                                  "f1": class_f1, "recall": tp / support if support else 0.0})
                for j, predicted_label in enumerate(prediction_inventory):
                    confusion_rows.append({"model": model_name, "seed": seed,
                                           "true_label": true_label, "predicted_label": predicted_label,
                                           "count": int(cm[class_index, j])})
            print(f"{model_name} seed={seed} macro_f1={f1:.5f} ceiling={ceiling:.5f} "
                  f"attack_recall={attack_recall:.5f}", flush=True)

    run_frame = pd.DataFrame(runs)
    run_frame.to_csv(args.out / "seed_metrics.csv", index=False)
    pd.DataFrame(per_class).to_csv(args.out / "per_class.csv", index=False)
    pd.DataFrame(confusion_rows).to_csv(args.out / "confusion_counts.csv", index=False)
    summary = run_frame.groupby("model").agg(
        seeds=("seed", "count"), macro_f1_mean=("macro_f1", "mean"),
        macro_f1_sd=("macro_f1", "std"), attack_recall_mean=("attack_recall", "mean"),
        attack_recall_sd=("attack_recall", "std"),
        binary_macro_f1_mean=("binary_macro_f1", "mean"),
        binary_macro_f1_sd=("binary_macro_f1", "std"), ceiling=("coverage_ceiling", "first")
    ).reset_index()
    summary.to_csv(args.out / "summary.csv", index=False)
    metadata = {
        "source": "DistriNet corrected CICIDS2017 release (official archive)",
        "source_url": "https://intrusion-detection.distrinet-research.be/WTMC2021/Dataset/dataset.zip",
        "source_archive_sha256": "4d535da19795d85376ae1397d161329e3b06fc47d9a5a68cd9be2cd7ecee0f2a",
        "split": "chronological day holdout: Monday-Thursday train, Friday test",
        "timestamp_ranges": timestamp_ranges,
        "day_label_counts": day_counts,
        "train_rows": int(len(train)), "test_rows": int(len(test)),
        "train_vocabulary": sorted(training_vocabulary), "test_positive_labels": test_inventory,
        "coverage_by_test_label": coverage, "coverage_ceiling": ceiling,
        "seeds": args.seeds, "per_class_train_cap": args.per_class_cap,
        "feature_columns": feature_columns,
        "excluded_columns": sorted(DROP_COLUMNS),
        "input_file_sha256": {name: sha256(args.data_dir / name) for name in DAY_FILES.values()},
        "interpretation": "Corrected-label, day-held-out closed-set audit. The per-class cap changes fitting data but retains each observed training label; reported ceiling uses the full Monday-Thursday training vocabulary.",
    }
    (args.out / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"saved corrected CICIDS2017 results to {args.out}", flush=True)


if __name__ == "__main__":
    main()
