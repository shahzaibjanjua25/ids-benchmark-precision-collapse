"""Verify the saved five-fold RT-IoT2022 vocabulary-intervention outputs."""
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, recall_score

from label_availability import certified_oracle, metric_bounds, oracle_sandwich

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/continuation_20261115/rt_iot_fold_varying_v1"
OLD = ROOT / "results/continuation_20261115/rt_iot"
SEEDS = (42, 43, 44)
BENIGN = {"Thing_Speak", "MQTT_Publish", "Wipro_bulb"}


def macro(y, pred, labels):
    return float(f1_score(y, pred, labels=labels, average="macro", zero_division=0))


def main():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    if manifest["csv_sha256"] != "956956c09c1764584fa08acd0f6876475626bcedcd6a6b1f8c492c2e9a2089ea":
        raise AssertionError("Source CSV hash changed")
    with np.load(OLD / "split.npz", allow_pickle=False) as source:
        labels = sorted(set(source["true_labels"].astype(str)))
        groups = source["feature_groups"]
    fold_ids, fold_groups = [], []
    saved_metrics = pd.read_csv(OUT / "fold_model_metrics.csv")
    group_to_fold = {}
    for fold in range(1, 6):
        with np.load(OUT / f"fold_{fold}_predictions.npz", allow_pickle=False) as z:
            ids = z["test_source_rows"]
            truth = z["truth"].astype(str)
            omitted = set(manifest["folds"][str(fold)])
            if set(truth) != set(labels):
                raise AssertionError(f"Fold {fold}: incomplete test-label inventory")
            for seed in SEEDS:
                baseline_fine = z[f"s{seed}_baseline_fine"].astype(str)
                intervention_fine = z[f"s{seed}_intervention_fine"].astype(str)
                baseline_binary = z[f"s{seed}_baseline_binary"].astype(str)
                intervention_binary = z[f"s{seed}_intervention_binary"].astype(str)
                if not set(baseline_fine).issubset(labels):
                    raise AssertionError("Baseline prediction escaped its vocabulary")
                if set(intervention_fine) & omitted:
                    raise AssertionError("Intervention predicted a withheld label")
                if not set(baseline_binary).issubset({"BENIGN", "ATTACK"}) or not set(intervention_binary).issubset({"BENIGN", "ATTACK"}):
                    raise AssertionError("Binary prediction outside binary vocabulary")
                binary_truth = np.where(np.isin(truth, list(BENIGN)), "BENIGN", "ATTACK")
                for condition, task, pred in [
                    ("baseline", "fine", baseline_fine),
                    ("intervention", "fine", intervention_fine),
                    ("baseline", "binary", baseline_binary),
                    ("intervention", "binary", intervention_binary),
                ]:
                    target = truth if task == "fine" else binary_truth
                    scored = labels if task == "fine" else ["BENIGN", "ATTACK"]
                    got = macro(target, pred, scored)
                    row = saved_metrics[(saved_metrics.fold == fold) & (saved_metrics.seed == seed) &
                                        (saved_metrics.condition == condition) &
                                        (saved_metrics.task == task)].iloc[0]
                    if abs(got - row.macro_f1) > 1e-12:
                        raise AssertionError(f"Fold metric mismatch: {fold}/{seed}/{condition}/{task}")
            fold_ids.extend(ids.tolist())
            fold_groups.extend(groups[ids].tolist())
            for group in np.unique(groups[ids]):
                if group in group_to_fold and group_to_fold[group] != fold:
                    raise AssertionError("An exact feature group appears in multiple test folds")
                group_to_fold[group] = fold
    if len(fold_ids) != 123117 or len(set(fold_ids)) != 123117:
        raise AssertionError("Five test folds do not partition all source rows exactly once")
    counts = pd.read_csv(OUT / "pooled_fold_class_counts.csv")
    pooled = certified_oracle(counts, max_assignments=1_000_000)
    pooled_bounds = metric_bounds(counts)
    sandwich = oracle_sandwich(counts)
    saved = json.loads((OUT / "oracle_certificate.json").read_text(encoding="utf-8"))
    if pooled["exact_fraction"] != saved["exact_fraction"]:
        raise AssertionError("Pooled rational certificate changed")
    if not sandwich["sandwich_lower"] <= pooled["exact_oracle"] <= sandwich["sandwich_upper"]:
        raise AssertionError("Polynomial interval does not contain the pooled exact oracle")
    fold_records = []
    for fold, data in counts.groupby("fold", sort=True):
        cert = certified_oracle(data, max_assignments=1_000_000)
        fold_records.append({"fold": int(fold) + 1,
                             "coverage_ceiling": metric_bounds(data)["coverage_ceiling"],
                             "exact_oracle": cert["exact_oracle"],
                             "exact_fraction": cert["exact_fraction"],
                             "grouped_assignments": cert["enumerated_assignments"]})
    fold_frame = pd.DataFrame(fold_records)
    fold_frame.to_csv(OUT / "fold_oracle_summary.csv", index=False)
    mean_fold = float(fold_frame.exact_oracle.mean())
    summary = {"pooled_coverage_ceiling": pooled_bounds["coverage_ceiling"],
               "pooled_exact_oracle": pooled["exact_oracle"],
               "mean_single_fold_oracle": mean_fold,
               "pooled_minus_mean_oracle": pooled["exact_oracle"] - mean_fold,
               "sandwich_lower": sandwich["sandwich_lower"],
               "sandwich_upper": sandwich["sandwich_upper"],
               "sandwich_width": sandwich["sandwich_upper"] - sandwich["sandwich_lower"],
               "pooled_grouped_assignments": pooled["enumerated_assignments"]}
    (OUT / "verified_oracle_comparison.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Five folds partition the source rows; group and prediction-vocabulary checks passed.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
