"""Recalculate RT-IoT structural limits across saved group folds.

No model is refit here: split.npz retains the complete labels and exact-feature
group IDs, while predictions are retained only for the originally evaluated
fold. The script also reports inverse-test-group-size rescoring for those saved
fold-0 predictions as a sensitivity analysis.
"""
from __future__ import annotations

import argparse
import json
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import f1_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold

from label_availability import count_folds
from label_availability.core import metric_bounds, oracle_sandwich

BENIGN = {"Thing_Speak", "MQTT_Publish", "Wipro_bulb"}
SEEDS = (42, 43, 44)


def single_omission_oracle(counts: pd.DataFrame) -> tuple[float, str] | None:
    """Return the exact support oracle for one missing label and a common head.

    With one unavailable class, all of its rows have the same destinations.
    The concave destination-loss objective has a vertex optimum, and choosing
    the available class with the largest test support minimizes the loss.
    """
    if "fold" not in counts:
        counts = counts.assign(fold=0)
    scored = counts[counts.test_rows.gt(0)]
    missing_by_fold = [set(group.loc[group.training_rows.eq(0), "class"])
                       for _, group in scored.groupby("fold", sort=False)]
    if missing_by_fold and all(not missing for missing in missing_by_fold):
        return 1.0, "1/1 (no unavailable test class)"
    common_missing = set.intersection(*missing_by_fold) if missing_by_fold else set()
    if (not missing_by_fold or len(common_missing) != 1 or
            any(missing != common_missing for missing in missing_by_fold)):
        return None
    support = scored.groupby("class", sort=False).test_rows.sum()
    withheld = next(iter(common_missing))
    n_classes = int(support.gt(0).sum())
    U = int(support[withheld])
    n = int(support.drop(index=withheld).max())
    score = Fraction(n_classes - 2, n_classes) + Fraction(2 * n, (2 * n + U) * n_classes)
    return float(score), f"{score.numerator}/{score.denominator}"


def group_weighted_prediction_checks(root: Path, groups: np.ndarray, y: np.ndarray,
                                     binary_y: np.ndarray, test_idx: np.ndarray,
                                     labels: list[str], mapping: dict[str, str]) -> pd.DataFrame:
    test_groups = groups[test_idx]
    multiplicity = pd.Series(test_groups).value_counts()
    weights = pd.Series(test_groups).map(multiplicity).rdiv(1.0).to_numpy(dtype=float)

    def single_omission_limits(truth: np.ndarray, sample_weight: np.ndarray,
                               withheld: str) -> tuple[float, float]:
        """Exact one-fold oracle when exactly one scored class is unavailable.

        All omitted-class rows share the same legal destinations. Their total
        weighted mass can be sent to one destination; concavity of destination
        loss makes a vertex optimal. The best destination has the largest
        weighted true support. This vertex assigns every row to that output,
        so the weighted oracle is row-realizable even when weights differ.
        """
        if withheld == "NONE":
            return 1.0, 1.0
        support = {label: float(sample_weight[truth == label].sum()) for label in labels}
        unavailable = support[withheld]
        covered = [value for label, value in support.items() if label != withheld]
        if unavailable <= 0 or any(value <= 0 for value in covered):
            raise ValueError("single-omission formula requires positive support for every test label")
        ceiling = (len(labels) - 1) / len(labels)
        best_destination_support = max(covered)
        oracle = (len(labels) - 2 +
                  2 * best_destination_support /
                  (2 * best_destination_support + unavailable)) / len(labels)
        return ceiling, oracle

    row_weights = np.ones(len(test_idx), dtype=float)
    row_truth = y[test_idx]
    row_limits = {w: single_omission_limits(row_truth, row_weights, w)
                  for w in ["NONE", *sorted(set(labels) - BENIGN)]}
    group_limits = {w: single_omission_limits(row_truth, weights, w)
                    for w in ["NONE", *sorted(set(labels) - BENIGN)]}
    rows = []
    for withheld in ["NONE", *sorted(set(labels) - BENIGN)]:
        for seed in SEEDS:
            path = root / f"{withheld}_{seed}.npz"
            if not path.exists():
                raise FileNotFoundError(path)
            with np.load(path, allow_pickle=False) as saved:
                fine = saved["fine_prediction"].astype(str)
                binary = saved["binary_prediction"].astype(str)
            if withheld == "NONE":
                baseline_fine, baseline_binary = fine, binary
            else:
                with np.load(root / f"NONE_{seed}.npz", allow_pickle=False) as saved:
                    baseline_fine = saved["fine_prediction"].astype(str)
                    baseline_binary = saved["binary_prediction"].astype(str)
            if len(fine) != len(test_idx) or len(binary) != len(test_idx):
                raise ValueError(f"prediction length mismatch: {path.name}")
            row = {"withheld": withheld, "seed": seed,
                   "test_rows": len(test_idx), "test_feature_groups": int(len(np.unique(test_groups))),
                   "group_weighted_test_mass": float(weights.sum()),
                   "row_weighted_coverage_ceiling": row_limits[withheld][0],
                   "row_weighted_exact_oracle": row_limits[withheld][1],
                   "group_weighted_coverage_ceiling": group_limits[withheld][0],
                   "group_weighted_exact_oracle": group_limits[withheld][1],
                   "row_weighted_fine_macro_f1": f1_score(
                       y[test_idx], fine, labels=labels, average="macro", zero_division=0),
                   "group_weighted_fine_macro_f1": f1_score(
                       y[test_idx], fine, labels=labels, average="macro", sample_weight=weights,
                       zero_division=0),
                   "row_weighted_binary_macro_f1": f1_score(
                       binary_y[test_idx], binary, labels=["BENIGN", "ATTACK"],
                       average="macro", zero_division=0),
                   "group_weighted_binary_macro_f1": f1_score(
                       binary_y[test_idx], binary, labels=["BENIGN", "ATTACK"],
                       average="macro", sample_weight=weights, zero_division=0),
                   "row_weighted_attack_recall": recall_score(
                       binary_y[test_idx], binary, pos_label="ATTACK", zero_division=0),
                   "group_weighted_attack_recall": recall_score(
                       binary_y[test_idx], binary, pos_label="ATTACK", sample_weight=weights,
                       zero_division=0)}
            if withheld != "NONE":
                mask = y[test_idx] == withheld
                row["withheld_test_rows"] = int(mask.sum())
                row["row_weighted_withheld_alarm_recall"] = float(np.mean(binary[mask] == "ATTACK"))
                row["group_weighted_withheld_alarm_recall"] = float(
                    np.average(binary[mask] == "ATTACK", weights=weights[mask]))
                row["present_in_training_baseline_fine_recall"] = recall_score(
                    y[test_idx][mask],
                    baseline_fine[mask],
                    labels=[withheld], average="macro", zero_division=0)
                row["present_in_training_baseline_alarm_recall"] = float(
                    np.mean(baseline_binary[mask] == "ATTACK"))
                row["group_weighted_present_in_training_baseline_fine_recall"] = recall_score(
                    y[test_idx][mask], baseline_fine[mask], labels=[withheld],
                    average="macro", sample_weight=weights[mask], zero_division=0)
                row["group_weighted_present_in_training_baseline_alarm_recall"] = float(
                    np.average(baseline_binary[mask] == "ATTACK", weights=weights[mask]))
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path,
                        default=Path("results/continuation_20261115/rt_iot"))
    parser.add_argument("--output", type=Path,
                        default=Path("results/continuation_20261115/rt_iot_fold_sensitivity"))
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output must be new or empty")
    args.output.mkdir(parents=True, exist_ok=True)

    with np.load(args.evidence / "split.npz", allow_pickle=False) as saved:
        groups = saved["feature_groups"]
        y = saved["true_labels"].astype(str)
        binary_y = saved["binary_labels"].astype(str)
        original_train = saved["training_source_rows"]
        original_test = saved["test_source_rows"]

    labels = sorted(np.unique(y).tolist())
    if not BENIGN.issubset(labels) or len(labels) != 12:
        raise ValueError(f"unexpected target labels: {labels}")
    mapping = {label: ("BENIGN" if label in BENIGN else "ATTACK") for label in labels}
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20261115)
                 .split(np.zeros(len(y)), y, groups))
    if not np.array_equal(folds[0][0], original_train) or not np.array_equal(folds[0][1], original_test):
        raise ValueError("saved fold 0 does not reproduce from its declared split seed")
    if any(set(groups[tr]) & set(groups[te]) for tr, te in folds):
        raise ValueError("an exact feature group crosses a train/test split")

    conditions = ["NONE", *sorted(set(labels) - BENIGN)]
    fold_rows, class_rows, pooled_rows, fold_count_rows = [], [], [], []
    started = time.perf_counter()
    for withheld in conditions:
        fold_counts = []
        for fold_id, (train_idx, test_idx) in enumerate(folds):
            train_labels = y[train_idx]
            if withheld != "NONE":
                train_labels = train_labels[train_labels != withheld]
            test_labels = y[test_idx]
            vocab = set(train_labels)
            counts = count_folds([train_labels], [test_labels])
            unavailable = int(counts.loc[counts.training_rows == 0, "test_rows"].sum())
            bounds = metric_bounds(counts)
            sandwich = oracle_sandwich(counts)
            # For a single omitted class and a common legal head, the
            # single-fold oracle has a closed form and is exact without search.
            analytic = single_omission_oracle(counts)
            exact_oracle = analytic[0] if analytic is not None else np.nan
            if analytic is not None and not np.isclose(
                    exact_oracle, sandwich["sandwich_lower"], rtol=0, atol=1e-12):
                raise AssertionError("analytic one-omission oracle disagrees with the lower sandwich bound")
            grouped_assignments = np.nan
            certified = analytic is not None
            oracle_seconds = 0.0
            q = len(vocab) if unavailable else 0
            row = {"withheld": withheld, "fold": fold_id,
                   "train_rows": int(len(train_idx)), "test_rows": int(len(test_idx)),
                   "test_groups": int(len(np.unique(groups[test_idx]))),
                   "test_classes": int(len(np.unique(test_labels))),
                   "legal_vocabulary_size": len(vocab), "q_destination_union": q,
                   "unavailable_rows": unavailable,
                   "coverage_ceiling": bounds["coverage_ceiling"],
                   "exact_oracle": exact_oracle,
                   "oracle_lower_bound": sandwich["sandwich_lower"],
                   "oracle_upper_bound": sandwich["sandwich_upper"],
                   "grouped_assignments": grouped_assignments,
                   "oracle_runtime_seconds": oracle_seconds,
                   "certified": certified,
                   "model_refit": False}
            row["certificate_note"] = (f"analytically certified: {analytic[1]}" if analytic is not None
                                        else "not enumerated; count-only sensitivity")
            fold_rows.append(row)
            fold_counts.append(counts)
            fold_count_rows.append(counts.assign(withheld=withheld, fold=fold_id))

        pooled = count_folds([y[tr][y[tr] != withheld] if withheld != "NONE" else y[tr]
                              for tr, _ in folds],
                             [y[te] for _, te in folds])
        pooled_bounds = metric_bounds(pooled)
        pooled_sandwich = oracle_sandwich(pooled)
        pooled_analytic = single_omission_oracle(pooled)
        pooled_exact = pooled_analytic[0] if pooled_analytic is not None else np.nan
        if pooled_analytic is not None and not (
                pooled_sandwich["sandwich_lower"] - 1e-12 <= pooled_exact <=
                pooled_sandwich["sandwich_upper"] + 1e-12):
            raise AssertionError("analytic pooled oracle falls outside its sandwich bounds")
        pooled_grouped = np.nan
        pooled_certified = pooled_analytic is not None
        pooled_seconds = 0.0
        pooled_rows.append({"withheld": withheld,
                            "mean_fold_coverage_ceiling": float(np.mean([x["coverage_ceiling"] for x in fold_rows if x["withheld"] == withheld])),
                            "mean_fold_exact_oracle": float(np.mean([x["exact_oracle"] for x in fold_rows if x["withheld"] == withheld])),
                            "pooled_coverage_ceiling": pooled_bounds["coverage_ceiling"],
                            "pooled_exact_oracle": pooled_exact,
                            "pooled_oracle_lower_bound": pooled_sandwich["sandwich_lower"],
                            "pooled_oracle_upper_bound": pooled_sandwich["sandwich_upper"],
                            "pooled_grouped_assignments": pooled_grouped,
                            "pooled_certified": pooled_certified,
                            "pooled_oracle_runtime_seconds": pooled_seconds,
                            "fold_averaged_score_convention": "unweighted mean of fold-level macro scores",
                            "pooled_score_convention": "pool confusion counts, then score"})

    pd.DataFrame(fold_rows).to_csv(args.output / "fold_bounds.csv", index=False)
    pd.DataFrame(class_rows, columns=["withheld", "fold", "class", "test_rows",
                                     "covered_rows", "oracle_false_positives"]).to_csv(
                                         args.output / "fold_class_support.csv", index=False)
    pd.concat(fold_count_rows, ignore_index=True).to_csv(args.output / "fold_counts.csv", index=False)
    pd.DataFrame(pooled_rows).to_csv(args.output / "pooled_vs_fold_average.csv", index=False)
    group_weighted_prediction_checks(args.evidence, groups, y, binary_y,
                                     original_test, labels, mapping).to_csv(
                                         args.output / "fold0_group_weighted_scores.csv", index=False)
    report = {"source_evidence": str(args.evidence / "split.npz"),
              "python_version": __import__("sys").version.split()[0],
              "numpy_version": np.__version__, "pandas_version": pd.__version__,
              "scikit_learn_version": sklearn.__version__,
              "split_seed": 20261115,
              "source_rows": int(len(y)), "unique_feature_groups": int(len(np.unique(groups))),
              "folds": len(folds), "withholding_conditions": len(conditions),
        "structural_fold_cases": len(fold_rows),
              "analytically_certified_single_omission_fold_oracles": int(
                  sum(bool(row["certified"]) for row in fold_rows)),
              "group_weighted_model_refits": 0,
              "saved_fold0_prediction_rescores": len(conditions) * len(SEEDS),
              "group_weight_definition": "each test feature group has total sample weight one",
              "total_structural_oracle_runtime_seconds": time.perf_counter() - started,
              "warning": "Five-fold bounds use saved labels/groups only; model predictions exist only for fold 0. No five-fold refit or independent cohort is claimed."}
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
