"""Fit a five-fold RT-IoT2022 vocabulary-intervention sensitivity experiment.

This is a controlled, non-temporal group-CV experiment. Each fold has a
fixed set of withheld fine labels; the fine model is fit only on the
remaining labels. A paired binary model uses the same retained examples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from label_availability import count_folds, certified_oracle, metric_bounds, oracle_sandwich

BENIGN = {"Thing_Speak", "MQTT_Publish", "Wipro_bulb"}
DROP = ["Unnamed: 0", "Attack_type", "id.orig_p", "id.resp_p"]
SEEDS = (42, 43, 44)
# Fold indices here are zero-based. This fixed scenario is a targeted
# post hoc sensitivity design, not a prospective or temporal protocol.
# Retained records do not establish when it was selected relative to earlier fits.
WITHHELD = {
    0: ("DOS_SYN_Hping",),
    1: ("ARP_poisioning",),
    2: ("DOS_SYN_Hping", "NMAP_UDP_SCAN"),
    3: (),
    4: ("ARP_poisioning", "DDOS_Slowloris"),
}


def build_model(seed: int, numeric: list[str], categorical: list[str]):
    prep = ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), numeric),
        ("categorical", make_pipeline(
            SimpleImputer(strategy="most_frequent"),
            OneHotEncoder(handle_unknown="ignore")), categorical),
    ])
    return make_pipeline(prep, ExtraTreesClassifier(
        n_estimators=100, min_samples_leaf=2, random_state=seed, n_jobs=4))


def macro(y, pred, labels):
    return float(f1_score(y, pred, labels=labels, average="macro", zero_division=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="official RT_IOT2022 CSV")
    parser.add_argument("out", type=Path, help="new output directory")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)
    data_bytes = args.data.read_bytes()
    data_hash = hashlib.sha256(data_bytes).hexdigest()
    expected_hash = "956956c09c1764584fa08acd0f6876475626bcedcd6a6b1f8c492c2e9a2089ea"
    if data_hash != expected_hash:
        raise ValueError(f"Unexpected RT-IoT2022 CSV hash: {data_hash}")

    d = pd.read_csv(args.data)
    if d.shape != (123117, 85):
        raise ValueError(f"Unexpected source shape: {d.shape}")
    X = d.drop(columns=DROP).copy()
    y = d.Attack_type.astype(str).to_numpy(dtype=str)
    if len(set(y)) != 12 or not BENIGN.issubset(set(y)):
        raise ValueError("Unexpected label set")
    groups = pd.util.hash_pandas_object(X, index=False).to_numpy()
    if len(np.unique(groups)) != len(X.drop_duplicates()):
        raise ValueError("Feature-group hashes do not match exact unique rows")
    labels = sorted(set(y))
    attacks = sorted(set(y) - BENIGN)
    binary = np.where(np.isin(y, list(BENIGN)), "BENIGN", "ATTACK")
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20261115)
    splits = list(splitter.split(X, y, groups))
    if len(splits) != 5:
        raise ValueError("Expected five group folds")
    for train, test in splits:
        if set(groups[train]) & set(groups[test]):
            raise ValueError("Exact feature groups cross a train/test split")
        if set(y[test]) != set(labels):
            raise ValueError("Every test fold must contain all twelve labels")

    X = X.replace([np.inf, -np.inf], np.nan)
    categorical = X.select_dtypes(include=["object", "str"]).columns.tolist()
    numeric = [c for c in X if c not in categorical]
    fold_train, fold_test = [], []
    vocabularies = []
    fold_records = []
    pooled_records = []
    per_seed = {seed: {"truth": [], "baseline_fine": [], "intervention_fine": [],
                       "baseline_binary": [], "intervention_binary": []} for seed in SEEDS}

    for fold, (train_ids, test_ids) in enumerate(splits):
        omitted = tuple(WITHHELD[fold])
        fold_test.append(y[test_ids])
        fold_fit_labels = []
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            capped = np.concatenate([
                rng.choice(train_ids[y[train_ids] == label],
                           size=min(1000, int(np.sum(y[train_ids] == label))),
                           replace=False)
                for label in labels
            ])
            intervention_ids = capped[~np.isin(y[capped], omitted)]
            if not set(y[intervention_ids]) == set(labels) - set(omitted):
                raise ValueError(f"Training vocabulary mismatch in fold {fold + 1}")
            fold_fit_labels.append(y[intervention_ids])
            fit_sets = [("baseline", capped), ("intervention", intervention_ids)]
            outputs = {}
            for condition, fit_ids in fit_sets:
                for task, train_targets in (("fine", y), ("binary", binary)):
                    model = build_model(seed, numeric, categorical)
                    start = time.perf_counter()
                    model.fit(X.iloc[fit_ids], train_targets[fit_ids])
                    pred = model.predict(X.iloc[test_ids]).astype(str)
                    elapsed = time.perf_counter() - start
                    expected_vocab = set(train_targets[fit_ids])
                    if not set(pred).issubset(expected_vocab):
                        raise AssertionError("Prediction escaped its fitted output vocabulary")
                    outputs[(condition, task)] = pred
                    fold_records.append({
                        "fold": fold + 1, "seed": seed, "condition": condition,
                        "task": task, "withheld": ";".join(omitted) or "NONE",
                        "fit_rows": len(fit_ids), "test_rows": len(test_ids),
                        "fit_seconds": elapsed,
                        "macro_f1": macro(train_targets[test_ids], pred,
                                           labels if task == "fine" else ["BENIGN", "ATTACK"]),
                        "attack_recall": (float(recall_score(binary[test_ids], pred,
                                                              pos_label="ATTACK"))
                                          if task == "binary" else np.nan),
                    })
            per_seed[seed]["truth"].append(y[test_ids])
            per_seed[seed]["baseline_fine"].append(outputs[("baseline", "fine")])
            per_seed[seed]["intervention_fine"].append(outputs[("intervention", "fine")])
            per_seed[seed]["baseline_binary"].append(outputs[("baseline", "binary")])
            per_seed[seed]["intervention_binary"].append(outputs[("intervention", "binary")])
            # Store one shared truth and the paired seed-specific predictions.
            if seed == SEEDS[0]:
                fold_npz = {"truth": y[test_ids], "binary_truth": binary[test_ids],
                            "test_source_rows": test_ids, "omitted": np.asarray(omitted)}
            fold_npz[f"s{seed}_baseline_fine"] = outputs[("baseline", "fine")]
            fold_npz[f"s{seed}_intervention_fine"] = outputs[("intervention", "fine")]
            fold_npz[f"s{seed}_baseline_binary"] = outputs[("baseline", "binary")]
            fold_npz[f"s{seed}_intervention_binary"] = outputs[("intervention", "binary")]
        np.savez_compressed(args.out / f"fold_{fold + 1}_predictions.npz", **fold_npz)
        vocabularies.append(sorted(set(fold_fit_labels[0])))
        # Check that the capped training procedure induces the same declared
        # vocabulary across seeds; this makes fold-level coverage seed-invariant.
        if any(set(v) != set(vocabularies[-1]) for v in fold_fit_labels[1:]):
            raise AssertionError("Seed-specific fitted vocabularies differ")

    train_labels = [y[tr][~np.isin(y[tr], WITHHELD[fold])] for fold, (tr, _) in enumerate(splits)]
    counts = count_folds(train_labels, fold_test, vocabularies=vocabularies)
    counts.to_csv(args.out / "pooled_fold_class_counts.csv", index=False)
    bounds = metric_bounds(counts)
    sandwich = oracle_sandwich(counts)
    oracle = certified_oracle(counts, max_assignments=1_000_000)
    pd.DataFrame([{**bounds, **sandwich, **oracle}]).drop(columns=["class_totals", "routing"], errors="ignore").to_csv(
        args.out / "pooled_oracle_summary.csv", index=False)
    (args.out / "oracle_certificate.json").write_text(json.dumps(oracle, indent=2), encoding="utf-8")

    pd.DataFrame(fold_records).to_csv(args.out / "fold_model_metrics.csv", index=False)
    for seed, outputs in per_seed.items():
        y_true = np.concatenate(outputs["truth"])
        for condition in ("baseline", "intervention"):
            fine_pred = np.concatenate(outputs[f"{condition}_fine"])
            binary_pred = np.concatenate(outputs[f"{condition}_binary"])
            pooled_records.append({
                "seed": seed, "condition": condition,
                "pooled_fine_macro_f1": macro(y_true, fine_pred, labels),
                "mean_fold_fine_macro_f1": float(np.mean([
                    macro(outputs["truth"][i], outputs[f"{condition}_fine"][i], labels)
                    for i in range(5)])),
                "pooled_binary_macro_f1": macro(np.where(np.isin(y_true, list(BENIGN)), "BENIGN", "ATTACK"),
                                                 binary_pred, ["BENIGN", "ATTACK"]),
                "mean_fold_binary_macro_f1": float(np.mean([
                    macro(np.where(np.isin(outputs["truth"][i], list(BENIGN)), "BENIGN", "ATTACK"),
                          outputs[f"{condition}_binary"][i], ["BENIGN", "ATTACK"])
                    for i in range(5)])),
                "pooled_attack_recall": float(recall_score(
                    np.where(np.isin(y_true, list(BENIGN)), "BENIGN", "ATTACK"), binary_pred,
                    pos_label="ATTACK")),
            })
    pooled = pd.DataFrame(pooled_records)
    pooled.to_csv(args.out / "pooled_model_metrics_by_seed.csv", index=False)
    pooled.groupby("condition").agg({c: ["mean", "std"] for c in pooled.columns
                                      if c not in {"condition", "seed"}}).to_csv(
                                          args.out / "pooled_model_metrics_summary.csv")

    sizes = pd.DataFrame([{"fold": i + 1, "train_rows": len(tr), "test_rows": len(te),
                           "test_groups": int(pd.Series(groups[te]).nunique()),
                           "omitted": ";".join(WITHHELD[i]) or "NONE"}
                          for i, (tr, te) in enumerate(splits)])
    sizes.to_csv(args.out / "fold_manifest.csv", index=False)
    (args.out / "manifest.json").write_text(json.dumps({
        "source_url": "https://archive.ics.uci.edu/static/public/942/rt-iot2022.zip",
        "source_doi": "10.24432/C5P338", "csv_sha256": data_hash,
        "rows": len(y), "features": len(X.columns), "exact_feature_groups": len(np.unique(groups)),
        "fold_splitter": "StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20261115)",
        "folds": {str(i + 1): list(WITHHELD[i]) for i in range(5)},
        "seeds": list(SEEDS), "model": "ExtraTreesClassifier(n_estimators=100,min_samples_leaf=2)",
        "per_class_cap": 1000, "fits": len(fold_records),
        "interpretation": "Exploratory controlled fold-dependent vocabulary intervention; not temporal validation or independent data replication.",
        "pooled_aggregation": "pool fold predictions before macro F1",
        "mean_fold_sensitivity": "unweighted mean of fixed-inventory fold macro F1",
    }, indent=2), encoding="utf-8")
    print("Completed", len(fold_records), "fits across five exact-feature-group folds")
    print("Coverage", bounds["coverage_ceiling"], "oracle", oracle["exact_oracle"],
          "interval", sandwich["sandwich_lower"], sandwich["sandwich_upper"],
          "assignments", oracle["enumerated_assignments"])
    print(pooled.groupby("condition").mean(numeric_only=True).to_string())


if __name__ == "__main__":
    main()
