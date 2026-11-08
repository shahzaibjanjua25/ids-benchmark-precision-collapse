#!/usr/bin/env python3
"""Fit an attack/benign forest on the CICIDS2017 capture-day folds."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE / "clean_repo"))
from ids_full_study import build, get_splits, load_cic  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cic-dir", type=Path, required=True,
                        help="Directory containing the CICIDS2017 MachineLearningCVE CSV files")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("--out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)

    ds = load_cic(str(args.cic_dir))
    original_y = ds.y.copy()
    ds.y = np.where(original_y == "BENIGN", "BENIGN", "ATTACK")
    classes = ["BENIGN", "ATTACK"]
    days = sorted(ds.meta["day"].unique())
    splits = get_splits(ds, "lodo", args.seeds[0])
    fold_rows, label_rows, confusion_rows = [], [], []

    for seed in args.seeds:
        all_truth, all_prediction, all_original = [], [], []
        for day, (train_idx, test_idx) in zip(days, splits):
            model = build("rf", "none", seed, args.n_estimators, ds)
            model.fit(ds.X.iloc[train_idx], ds.y[train_idx])
            prediction = model.predict(ds.X.iloc[test_idx])
            truth = ds.y[test_idx]
            cm = confusion_matrix(truth, prediction, labels=classes)
            attack_index = classes.index("ATTACK")
            attack_support = int(cm[attack_index, :].sum())
            attack_tp = int(cm[attack_index, attack_index])
            fold_rows.append({
                "seed": seed,
                "held_out_day": day,
                "test_rows": int(len(test_idx)),
                "attack_support": attack_support,
                "attack_recall": attack_tp / attack_support if attack_support else np.nan,
                "attack_precision": precision_score(truth, prediction, pos_label="ATTACK", zero_division=0),
                "binary_macro_f1": f1_score(truth, prediction, labels=sorted(set(truth)),
                                             average="macro", zero_division=0),
                "accuracy": accuracy_score(truth, prediction),
            })
            label_counts = pd.DataFrame({"fine_label": original_y[test_idx],
                                         "truth": truth, "prediction": prediction})
            for label, rows in label_counts.groupby("fine_label", sort=True):
                support = int(len(rows))
                detected = int((rows["prediction"] == "ATTACK").sum())
                label_rows.append({
                    "seed": seed,
                    "held_out_day": day,
                    "fine_label": label,
                    "test_support": support,
                    "attack_detection_recall": detected / support if label != "BENIGN" else np.nan,
                    "benign_false_positive_rate": (detected / support) if label == "BENIGN" else np.nan,
                })
            all_truth.append(truth)
            all_prediction.append(prediction)
            all_original.append(original_y[test_idx])
            print(f"seed={seed} day={day} rows={len(test_idx)} attack_recall="
                  f"{fold_rows[-1]['attack_recall']:.5f} macro_f1={fold_rows[-1]['binary_macro_f1']:.5f}",
                  flush=True)

        truth = np.concatenate(all_truth)
        prediction = np.concatenate(all_prediction)
        cm = confusion_matrix(truth, prediction, labels=classes)
        tn, fp, fn, tp = cm.ravel()
        confusion_rows.append({"seed": seed, "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)})
        fold_rows.append({
            "seed": seed,
            "held_out_day": "POOLED",
            "test_rows": int(len(truth)),
            "attack_support": int(tp + fn),
            "attack_recall": tp / (tp + fn) if tp + fn else np.nan,
            "attack_precision": tp / (tp + fp) if tp + fp else np.nan,
            "binary_macro_f1": f1_score(truth, prediction, labels=classes,
                                         average="macro", zero_division=0),
            "accuracy": accuracy_score(truth, prediction),
        })

    pd.DataFrame(fold_rows).to_csv(args.out / "cic_binary_lodo_scores.csv", index=False)
    pd.DataFrame(label_rows).to_csv(args.out / "cic_binary_lodo_fine_label_recall.csv", index=False)
    pd.DataFrame(confusion_rows).to_csv(args.out / "cic_binary_lodo_confusion.csv", index=False)
    dataset_files = []
    for path in sorted(args.cic_dir.rglob("*.csv")):
        dataset_files.append({
            "name": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    (args.out / "cic_binary_lodo_run.json").write_text(json.dumps({
        "target_mapping": "BENIGN remains BENIGN; every other original label maps to ATTACK",
        "protocol": "one capture day held out; all other days train; pooled out-of-fold score also saved",
        "seeds": args.seeds,
        "n_estimators": args.n_estimators,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "class_weight": None,
        "data_files": dataset_files,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Saved binary CICIDS2017 LODO results under {args.out}", flush=True)


if __name__ == "__main__":
    main()
