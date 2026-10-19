"""Compute pooled closed-set macro-F1 ceiling from per-fold label counts."""
import argparse
from pathlib import Path

import pandas as pd

def coverage_bound(counts):
    scored = counts.loc[counts.test_rows.gt(0)].copy()
    scored["covered_rows"] = scored.test_rows.where(scored.training_rows.gt(0), 0)
    by_label = scored.groupby("class")[["test_rows", "covered_rows"]].sum()
    if by_label.empty:
        raise ValueError("At least one test row is required")
    by_label["coverage"] = by_label.covered_rows / by_label.test_rows
    by_label["f1_ceiling"] = 2 * by_label.coverage / (1 + by_label.coverage)
    return by_label, by_label.f1_ceiling.mean()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("counts", type=Path, help="CSV with class, training_rows, and test_rows for each fold")
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    classes, bound = coverage_bound(pd.read_csv(args.counts))
    classes.to_csv(args.out)
    print(f"Pooled macro-F1 ceiling: {bound:.12f}")

if __name__ == "__main__":
    main()

