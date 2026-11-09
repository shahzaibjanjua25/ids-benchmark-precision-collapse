#!/usr/bin/env python3
"""Check saved scores and count matrices for the corrected CICIDS2017 run."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "cic_corrected_friday_v2"
metrics = pd.read_csv(OUT / "seed_metrics.csv")
summary = pd.read_csv(OUT / "summary.csv").set_index("model")
counts = pd.read_csv(OUT / "confusion_counts.csv")
run = json.loads((OUT / "run.json").read_text(encoding="utf-8"))

assert metrics.shape[0] == 9
assert set(metrics.model) == {"random_forest", "extra_trees", "sgd_log_loss"}
assert set(metrics.seed) == {42, 43, 44}
assert metrics.test_rows.eq(547915).all()
assert metrics.coverage_ceiling.eq(0.2).all()
assert run["train_rows"] == 1552899 and run["test_rows"] == 547915
assert run["coverage_ceiling"] == 0.2
assert run["test_positive_labels"] == ["BENIGN", "Bot", "Bot - Attempted", "DDoS", "PortScan"]
assert run["coverage_by_test_label"] == {
    "BENIGN": 1, "Bot": 0, "Bot - Attempted": 0, "DDoS": 0, "PortScan": 0
}
assert run["split"] == "chronological day holdout: Monday-Thursday train, Friday test"
assert pd.Timestamp(run["timestamp_ranges"]["Thursday"][1]) < pd.Timestamp(run["timestamp_ranges"]["Friday"][0])
assert all(len(x) == 64 for x in run["input_file_sha256"].values())

for (model, seed), group in counts.groupby(["model", "seed"]):
    assert int(group["count"].sum()) == 547915
    pivot = group.pivot(index="true_label", columns="predicted_label", values="count").fillna(0)
    scored_labels = run["test_positive_labels"]
    f1_values = []
    for label in scored_labels:
        tp = int(pivot.loc[label, label])
        support = int(pivot.loc[label].sum())
        fp = int(pivot[label].sum() - tp)
        f1_values.append(2 * tp / (2 * tp + fp + support - tp))
    row = metrics.loc[(metrics.model == model) & (metrics.seed == seed)].iloc[0]
    assert np.isclose(np.mean(f1_values), row.macro_f1)

    tn = fp = fn = tp = 0
    for true_label, predicted_label, value in group[["true_label", "predicted_label", "count"]].itertuples(index=False):
        if true_label == "BENIGN" and predicted_label == "BENIGN":
            tn += int(value)
        elif true_label == "BENIGN":
            fp += int(value)
        elif predicted_label == "BENIGN":
            fn += int(value)
        else:
            tp += int(value)
    binary_macro = 0.5 * (2 * tn / (2 * tn + fp + fn) + 2 * tp / (2 * tp + fp + fn))
    assert np.isclose(binary_macro, row.binary_macro_f1)
    assert np.isclose(tp / (tp + fn), row.attack_recall)

for model, group in metrics.groupby("model"):
    assert np.isclose(group.macro_f1.mean(), summary.loc[model, "macro_f1_mean"])
    assert np.isclose(group.binary_macro_f1.mean(), summary.loc[model, "binary_macro_f1_mean"])
    assert np.isclose(group.attack_recall.mean(), summary.loc[model, "attack_recall_mean"])

print("Corrected CICIDS2017 run: chronology, coverage, nine fits, confusion counts and binary/fine scores passed")
