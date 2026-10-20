"""Summarize pair variation, finite-population median intervals, and seed variation."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, spearmanr

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
args = parser.parse_args()
root = args.results / "unsw_coverage_random_pairs"
original = pd.read_csv(root / "runs.csv")
runs = original.assign(total_gap=original.ceiling-original.macro_f1)
names = ["total_gap", "forced_assignment_gap"]
for lower in range(10, 0, -1):
    upper = 21-lower
    coverage = 1-hypergeom.cdf(lower-1, 33, 17, 20)-hypergeom.sf(upper-1, 33, 16, 20)
    if coverage >= .95:
        break
ordered = np.sort(runs[names].to_numpy(), axis=0)
pd.DataFrame({"component":names, "lower_rank":lower, "upper_rank":upper,
              "coverage_at_least":coverage, "low":ordered[lower-1], "high":ordered[upper-1]}).to_csv(root / "finite_population_intervals.csv", index=False)

counts = pd.read_csv(args.results / "unsw_official_label_counts.csv").set_index("class").test_rows
supports = runs.withheld.str.split(" + ", regex=False)
for i in (0, 1):
    runs[f"withheld_support_{i+1}"] = supports.str[i].map(counts)
assert (runs.withheld_support_1 + runs.withheld_support_2 == runs.unseen_rows).all()
runs[["withheld", "withheld_support_1", "withheld_support_2", "unseen_rows", "forced_assignment_gap"]].to_csv(root / "support_mechanism.csv", index=False)
print("Spearman rho:", spearmanr(runs.unseen_rows, runs.forced_assignment_gap).statistic)
det = pd.read_csv(args.results / "unsw_coverage_sensitivity/runs.csv")
rng = np.random.default_rng(2026)
rows = []
for pair, group in det.groupby("withheld"):
    vals = group[["covered_error_gap", "forced_assignment_gap"]].to_numpy()
    draws = vals[rng.integers(0, len(vals), (10000, len(vals)))].mean(axis=1)
    for i, component in enumerate(["covered_error_gap", "forced_assignment_gap"]):
        low, high = np.quantile(draws[:, i], [.025, .975])
        rows.append(dict(withheld=pair, component=component, mean=vals[:, i].mean(), low=low, high=high))
pd.DataFrame(rows).to_csv(root / "deterministic_seed_bootstrap.csv", index=False)

extra = args.results / "unsw_random_pairs_extra_seeds"
if (extra / "runs.csv").exists():
    additions = pd.read_csv(extra / "runs.csv")
    combined = pd.concat([original, additions], ignore_index=True)
    if len(combined) == 100:
        assert set(combined.withheld) == set(original.withheld)
        assert all(seeds == set(range(42,47)) for seeds in combined.groupby("withheld").seed.apply(set))
        combined["total_gap"] = combined.ceiling - combined.macro_f1
        combined[["withheld","seed",*names]].to_csv(extra / "combined_100_runs.csv", index=False)
        medians = combined.groupby("seed")[names].median()
        medians.to_csv(extra / "seed_medians.csv")
        medians.agg(["mean","std"]).to_csv(extra / "median_seed_summary.csv")
        grid = combined.pivot(index="withheld", columns="seed", values=names)
        rows = []
        for name in names:
            scores = grid[name]
            rows.append({"component": name, "sd_of_pair_means":scores.mean(axis=1).std(),
                         "pooled_within_pair_sd":np.sqrt(scores.var(axis=1).mean())})
        pd.DataFrame(rows).to_csv(extra / "variation.csv", index=False)

