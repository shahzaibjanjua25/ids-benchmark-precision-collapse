import argparse
from pathlib import Path
import pandas as pd

parser = argparse.ArgumentParser(description="Summarize withheld-label and forest-seed sensitivity.")
parser.add_argument("results", type=Path)
args = parser.parse_args()
root = args.results / "unsw_coverage_sensitivity"
runs = pd.read_csv(root / "runs.csv")
assert len(runs) == 15
assert all(seeds == set(range(42, 47)) for seeds in runs.groupby("pair").seed.apply(set))
assert (runs.test_rows == 82332).all()
assert (runs.ceiling == .8).all()
assert ((runs.covered_error_gap + runs.forced_assignment_gap - (runs.ceiling-runs.macro_f1)).abs() < 1e-12).all()
summary = runs.groupby("pair", sort=False).agg(
    withheld=("withheld", "first"), unseen=("unseen_rows", "first"), baseline=("majority_macro_f1", "first"),
    mean=("macro_f1", "mean"), sd=("macro_f1", "std"), covered=("covered_error_gap", "mean"),
    forced=("forced_assignment_gap", "mean"), errors=("covered_errors", "mean"))
supports = pd.read_csv(args.results / "unsw_official_label_counts.csv").set_index("class").test_rows
for pair, row in summary.iterrows():
    seen_support = supports.drop(row.withheld.split(" + "))
    # With all covered rows correct, assigning every unseen row to the largest
    # seen test class minimizes the macro-F1 loss among simplex vertices.
    largest = seen_support.max()
    unavoidable = row.unseen / (2 * largest + row.unseen) / len(supports)
    oracle_ceiling = .8 - unavoidable
    assert runs.loc[runs.pair.eq(pair), "repaired_macro_f1"].max() <= oracle_ceiling + 1e-12
    summary.loc[pair, "oracle_ceiling"] = oracle_ceiling
summary.to_csv(root / "summary.csv")

