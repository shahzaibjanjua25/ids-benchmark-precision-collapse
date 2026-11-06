"""Decompose archived CICIDS2017 held-out-day predictions by label coverage."""
import argparse
from pathlib import Path

import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
args = parser.parse_args()
root = args.results
coverage = pd.read_csv(root / "cic_day_coverage.csv")
unseen = coverage.loc[coverage.training_rows_other_days.eq(0)]
assert not coverage.loc[coverage.training_rows_other_days.gt(0), "class"].isin(unseen["class"]).any()
rows = []
for path in sorted((root / "confusion").glob("cic_raw_lodo_rf_*.csv")):
    cm = pd.read_csv(path, index_col=0)
    for group, classes in [("seen", sorted(set(cm.index) - set(unseen["class"]))),
                           ("unseen", sorted(set(unseen["class"])))]:
        selected = cm.loc[classes]
        support = int(selected.to_numpy().sum())
        correct = sum(int(selected.at[label, label]) for label in classes)
        assert support > 0
        rows.append({"arm": path.stem.removeprefix("cic_raw_lodo_rf_"),
                     "coverage": group, "classes": len(classes), "test_rows": support,
                     "correct_exact_label": correct, "exact_label_accuracy": correct / support,
                     "predicted_benign": int(selected["BENIGN"].sum())})
pd.DataFrame(rows).to_csv(root / "cic_lodo_label_decomposition.csv", index=False)

