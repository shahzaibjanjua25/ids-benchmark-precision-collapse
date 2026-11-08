"""Compare fine-label and five-category scores from the same saved NSL predictions."""
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FINE_TO_CATEGORY = {"normal": "Normal"}
CATEGORY_MEMBERS = {
    "DoS": "neptune smurf back teardrop pod land apache2 processtable mailbomb udpstorm",
    "Probe": "satan ipsweep portsweep nmap mscan saint",
    "R2L": "warezclient guess_passwd warezmaster imap ftp_write multihop phf spy snmpguess snmpgetattack httptunnel named sendmail xlock xsnoop worm",
    "U2R": "buffer_overflow rootkit loadmodule perl ps xterm sqlattack",
}
for category, members in CATEGORY_MEMBERS.items():
    FINE_TO_CATEGORY.update(dict.fromkeys(members.split(), category))
CATEGORIES = ["Normal", "DoS", "Probe", "R2L", "U2R"]


def macro_f1(confusion: np.ndarray) -> float:
    support = confusion.sum(axis=1)
    denominator = support + confusion.sum(axis=0)
    class_f1 = np.divide(
        2 * np.diag(confusion), denominator,
        out=np.zeros(len(support), dtype=float), where=denominator > 0,
    )
    return float(class_f1[support > 0].mean())


def main() -> None:
    rows = []
    fine_counts = pd.read_csv(RESULTS / "nsl_kdd_official/label_counts.csv")
    fine_supported = fine_counts.test_rows.gt(0)
    fine_available = fine_counts.training_rows.gt(0)
    fine_rho = fine_counts.loc[fine_supported, "training_rows"].gt(0).astype(float)
    fine_ceiling = float((2 * fine_rho / (1 + fine_rho)).mean())

    coarse_counts = fine_counts.assign(category=fine_counts["class"].map(FINE_TO_CATEGORY))
    if coarse_counts.category.isna().any():
        missing = coarse_counts.loc[coarse_counts.category.isna(), "class"].tolist()
        raise ValueError(f"Unmapped NSL-KDD labels: {missing}")
    coarse_counts = coarse_counts.groupby("category")[["training_rows", "test_rows"]].sum()
    coarse_supported = coarse_counts.test_rows.gt(0)
    coarse_rho = coarse_counts.loc[coarse_supported, "training_rows"].gt(0).astype(float)
    coarse_ceiling = float((2 * coarse_rho / (1 + coarse_rho)).mean())
    if list(coarse_counts.index.sort_values()) != sorted(CATEGORIES):
        raise ValueError("The five-category mapping did not produce all expected labels")

    for seed in range(42, 47):
        fine = pd.read_csv(
            RESULTS / f"nsl_model_comparison/confusion_seen_{seed}.csv", index_col=0
        ) + pd.read_csv(
            RESULTS / f"nsl_model_comparison/confusion_unseen_{seed}.csv", index_col=0
        )
        if set(fine.index) != set(FINE_TO_CATEGORY) or set(fine.columns) != set(FINE_TO_CATEGORY):
            raise ValueError(f"Seed {seed}: confusion matrix does not match the mapping")

        category_index = {label: i for i, label in enumerate(CATEGORIES)}
        aggregation = np.zeros((len(fine.index), len(CATEGORIES)), dtype=np.int64)
        for i, label in enumerate(fine.index):
            aggregation[i, category_index[FINE_TO_CATEGORY[label]]] = 1
        category_confusion = aggregation.T @ fine.to_numpy(dtype=np.int64) @ aggregation
        rows.append({
            "seed": seed,
            "fine_label_macro_f1": macro_f1(fine.to_numpy(dtype=np.int64)),
            "five_category_macro_f1": macro_f1(category_confusion),
            "fine_label_ceiling": fine_ceiling,
            "five_category_ceiling": coarse_ceiling,
            "test_rows": int(fine.to_numpy().sum()),
            "test_rows_with_unavailable_fine_label": int(
                fine_counts.loc[fine_supported & ~fine_available, "test_rows"].sum()
            ),
        })

    frame = pd.DataFrame(rows)
    nsl_seed = pd.read_csv(RESULTS / "rank_audit/nsl_ranks.csv")
    np.testing.assert_allclose(
        frame.fine_label_macro_f1, nsl_seed.full_macro_f1, rtol=0, atol=1e-12
    )
    frame.to_csv(RESULTS / "nsl_kdd_official/granularity_reanalysis.csv", index=False)
    summary = pd.DataFrame([{
        "seeds": len(frame),
        "test_rows": int(frame.test_rows.iloc[0]),
        "test_rows_with_unavailable_fine_label": int(
            frame.test_rows_with_unavailable_fine_label.iloc[0]
        ),
        "fine_label_ceiling": fine_ceiling,
        "fine_label_f1_mean": frame.fine_label_macro_f1.mean(),
        "fine_label_f1_sd": frame.fine_label_macro_f1.std(ddof=1),
        "five_category_ceiling": coarse_ceiling,
        "five_category_f1_mean": frame.five_category_macro_f1.mean(),
        "five_category_f1_sd": frame.five_category_macro_f1.std(ddof=1),
        "prediction_reaggregation_only": True,
    }])
    summary.to_csv(RESULTS / "nsl_kdd_official/granularity_reanalysis_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
