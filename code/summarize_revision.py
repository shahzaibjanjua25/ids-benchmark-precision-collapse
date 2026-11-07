"""Summarize completed grids and the repair example."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
args = parser.parse_args()
p = args.results
runs = pd.read_csv(p / "unsw_complete_pairs/runs.csv")
assert not runs.duplicated(["withheld", "seed"]).any()
pairs = runs.loc[runs.withheld.str.count(r" \+ ").eq(1)].copy()
assert len(pairs) == 180 and pairs.withheld.nunique() == 36
assert all(set(group.seed) == set(range(42, 47)) for _, group in pairs.groupby("withheld"))
summary = pairs.groupby("withheld").agg(mean=("macro_f1", "mean"), sd=("macro_f1", "std"),
                                         combined_destination_penalty=("forced_assignment_gap", "mean"))
summary.to_csv(p / "unsw_complete_pairs/pair_summary.csv")
official = runs.loc[runs.withheld.eq("NONE")].copy()
assert len(official) == 5
analysis = pairs.loc[pairs.withheld.eq("Analysis + Backdoor"), ["seed", "macro_f1"]]
paired = official[["seed", "macro_f1"]].merge(analysis, on="seed", suffixes=("_official", "_withheld"))
paired["difference_withheld_minus_official"] = paired.macro_f1_withheld - paired.macro_f1_official
paired.to_csv(p / "unsw_complete_pairs/official_paired.csv", index=False)
comparison = runs.loc[runs.oracle_routed_macro_f1.notna()].copy()
comparison["oracle_route_gain"] = comparison.oracle_routed_macro_f1 - comparison.macro_f1
comparison["confidence_route_gain"] = comparison.confidence_routed_macro_f1 - comparison.macro_f1
comparison[["withheld", "seed", "oracle_route_gain", "confidence_route_gain"]].to_csv(p / "unsw_complete_pairs/routing_checks.csv", index=False)
counts = pd.read_csv(p / "unsw_official_label_counts.csv").set_index("class")
by_size = []
for _, row in runs.loc[runs.seed.eq(42)].iterrows():
    withheld = [] if row.withheld == "NONE" else row.withheld.split(" + ")
    if withheld != sorted(counts.index.drop("Normal"))[:len(withheld)]:
        continue
    unavailable = counts.loc[withheld].test_rows.sum()
    largest = counts.drop(withheld).test_rows.max()
    oracle = row.ceiling - unavailable / (2 * largest + unavailable) / 10
    by_size.append({"withheld_count": len(withheld), "ceiling": row.ceiling,
                    "oracle": oracle, "observed_seed_42": row.macro_f1})
pd.DataFrame(by_size).sort_values("withheld_count").to_csv(p / "unsw_complete_pairs/withheld_count.csv", index=False)

cm = pd.read_csv(p / "unsw_partial_coverage/confusion.csv", index_col=0)
unseen = cm.index.isin(["Analysis", "Backdoor"])
matrix = cm.to_numpy(dtype=float)
n = matrix.sum(axis=1)
tp = np.diag(matrix)
predicted = matrix.sum(axis=0)
def macro(hits, destinations):
    return float(np.mean(2 * hits / (n + destinations)))
observed = macro(tp, predicted)
removed = macro(tp, predicted - matrix[unseen].sum(axis=0))
repaired_hits = n.copy()
repaired_hits[unseen] = 0
repaired = macro(repaired_hits, repaired_hits + matrix[unseen].sum(axis=0))
ceiling = .8
pd.DataFrame([{"observed": observed, "covered_first_destination": ceiling - repaired,
               "destination_first": removed - observed,
               "shapley_destination": ((ceiling - repaired) + (removed - observed)) / 2,
               "shapley_covered": ((repaired - observed) + (ceiling - removed)) / 2}]).to_csv(p / "repair_order_example.csv", index=False)
print("All 36 pairs x 5 seeds and official five-seed reference verified")
print(official.macro_f1.agg(["mean", "std"]).to_string())
print(paired.difference_withheld_minus_official.agg(["mean", "std"]).to_string())
