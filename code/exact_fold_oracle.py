"""Exact pooled macro-F1 oracle for small fold-vocabulary products."""
import argparse
import time
import tracemalloc
from pathlib import Path
import pandas as pd

from label_availability import exact_oracle as oracle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--method", choices=["enumerate","branch"], default="enumerate")
    args = parser.parse_args()
    p = args.results
    day = pd.read_csv(p/"cic_day_coverage.csv").pivot(index="day",columns="class",values="test_rows").fillna(0).astype(int)
    cic = day.stack().rename("test_rows").reset_index().rename(columns={"day":"fold"})
    totals = day.sum()
    cic["training_rows"] = cic["class"].map(totals)-cic.test_rows
    cases = {
        "CICIDS2017 LODO":cic,
        "NSL-KDD official":pd.read_csv(p/"nsl_kdd_official/label_counts.csv").assign(fold=0),
        "UNSW-NB15 mixed":pd.read_csv(p/"unsw_partial_coverage/fold_label_counts.csv").assign(fold=0),
        "Digits partial":pd.read_csv(p/"digits_fractional_coverage/fold_label_counts.csv"),
    }
    rows = []
    for name, counts in cases.items():
        tracemalloc.start()
        start = time.perf_counter()
        result = oracle(counts, method=args.method)
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        uncovered = counts.loc[counts.training_rows.eq(0) & counts.test_rows.gt(0), "fold"].nunique()
        rows.append({"case":name, **result, "uncovered_folds":uncovered,
                     "runtime_seconds":elapsed, "traced_peak_bytes":peak})
    results = pd.DataFrame(rows)
    filename = "exact_fold_oracles_branch.csv" if args.method == "branch" else "exact_fold_oracles.csv"
    results.to_csv(p / filename, index=False)
    print(results.to_string(index=False))

if __name__ == "__main__":
    main()
