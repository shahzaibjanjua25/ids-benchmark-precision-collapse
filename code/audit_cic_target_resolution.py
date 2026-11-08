"""Re-score one saved CICIDS2017 day-holdout matrix at coarser targets."""
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def score(matrix: np.ndarray) -> tuple[float, float, np.ndarray]:
    support = matrix.sum(axis=1)
    denom = support + matrix.sum(axis=0)
    class_f1 = np.divide(
        2 * np.diag(matrix), denom,
        out=np.zeros(len(support), dtype=float), where=denom > 0,
    )
    return float(class_f1[support > 0].mean()), float(np.trace(matrix) / matrix.sum()), class_f1


def main() -> None:
    labels = pd.read_csv(RESULTS / "cic_lodo_label_counts.csv")
    matrix_path = RESULTS / "confusion/cic_raw_lodo_rf_none.csv"
    fine = pd.read_csv(matrix_path, index_col=0)
    names = list(fine.index)
    if list(fine.columns) != names:
        raise ValueError("Confusion matrix row and column labels differ")
    if set(names) != set(labels["class"]):
        raise ValueError("Confusion matrix labels do not match the LODO count file")

    family_map = {}
    for label in names:
        if label == "BENIGN":
            family_map[label] = "BENIGN"
        elif label.startswith("DoS") or label == "DDoS":
            family_map[label] = "DoS"
        elif label.endswith("Patator"):
            family_map[label] = "Credential brute force"
        elif label.startswith("Web Attack"):
            family_map[label] = "Web attack"
        else:
            family_map[label] = label
    binary_map = {label: "BENIGN" if label == "BENIGN" else "ATTACK" for label in names}
    target_maps = {
        "fine attack label": {label: label for label in names},
        "eight-family mapping": family_map,
        "binary benign/attack": binary_map,
    }

    days = sorted(labels.day.unique())
    by_fold = labels.pivot(index="day", columns="class", values="test_rows").reindex(
        index=days, columns=names, fill_value=0
    ).fillna(0).astype(int)
    fine_test = by_fold.sum(axis=0)
    rows = []
    class_rows = []

    for resolution, mapping in target_maps.items():
        targets = list(dict.fromkeys(mapping[label] for label in names))
        aggregated_counts = {}
        for day in days:
            for target in targets:
                member_labels = [label for label in names if mapping[label] == target]
                test_support = int(by_fold.loc[day, member_labels].sum())
                train_support = int((fine_test[member_labels] - by_fold.loc[day, member_labels]).sum())
                aggregated_counts[(day, target)] = (test_support, train_support)

        rho = {}
        for target in targets:
            supports = [aggregated_counts[(day, target)] for day in days]
            n = sum(test for test, _ in supports)
            m = sum(test for test, train in supports if train > 0)
            if n:
                rho[target] = m / n
        ceiling = float(np.mean([2 * value / (1 + value) for value in rho.values()]))

        ids = {target: i for i, target in enumerate(targets)}
        aggregation = np.zeros((len(names), len(targets)), dtype=np.int64)
        for i, label in enumerate(names):
            aggregation[i, ids[mapping[label]]] = 1
        mapped = aggregation.T @ fine.to_numpy(dtype=np.int64) @ aggregation
        macro_f1, accuracy, class_f1 = score(mapped)
        supports = mapped.sum(axis=1)
        for i, target in enumerate(targets):
            class_rows.append({
                "resolution": resolution,
                "class": target,
                "test_support": int(supports[i]),
                "coverage_fraction": rho.get(target, np.nan),
                "f1": float(class_f1[i]),
            })
        rows.append({
            "resolution": resolution,
            "target_classes": len(rho),
            "coverage_ceiling": ceiling,
            "macro_f1": macro_f1,
            "ceiling_attainment": macro_f1 / ceiling if ceiling > 0 else np.nan,
            "accuracy": accuracy,
            "test_rows": int(mapped.sum()),
            "attack_recall": float(mapped[1, 1] / mapped[1].sum()) if resolution == "binary benign/attack" else np.nan,
            "prediction_reaggregation_only": True,
        })

    result = pd.DataFrame(rows)
    expected = {
        "fine attack label": (1 / 15, 0.06030428),
        "eight-family mapping": (0.25, 0.15629612),
        "binary benign/attack": (1.0, 0.57972301),
    }
    for row in result.itertuples():
        ceiling, observed = expected[row.resolution]
        np.testing.assert_allclose(row.coverage_ceiling, ceiling, atol=1e-8, rtol=0)
        np.testing.assert_allclose(row.macro_f1, observed, atol=1e-8, rtol=0)
        if row.test_rows != int(fine.to_numpy().sum()):
            raise ValueError("Mapped confusion matrix changed the test cohort size")

    result.to_csv(RESULTS / "cic_lodo_target_resolution.csv", index=False)
    pd.DataFrame(class_rows).to_csv(RESULTS / "cic_lodo_target_class_scores.csv", index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
