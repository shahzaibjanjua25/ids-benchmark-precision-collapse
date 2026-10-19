"""Visualize fixed-seed pair sensitivity and bootstrap the sampled medians."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
parser.add_argument("figures", type=Path)
args = parser.parse_args()
root = args.results / "unsw_coverage_random_pairs"
runs = pd.read_csv(root / "runs.csv")
runs["total_gap"] = runs.ceiling - runs.macro_f1
reference = pd.read_csv(args.results / "unsw_coverage_sensitivity/runs.csv").query("seed == 42").copy()
reference["total_gap"] = reference.ceiling - reference.macro_f1
assert len(runs) == runs.withheld.nunique() == 20 and len(reference) == 3
assert (runs.seed == 42).all() and (reference.seed == 42).all()
rng = np.random.default_rng(2026)
indices = rng.integers(0, len(runs), (10000, len(runs)))
columns = ["total_gap", "forced_assignment_gap"]
vals = runs[columns].to_numpy()
bounds = np.quantile(np.median(vals[indices], axis=1), [.025, .975], axis=0)
pd.DataFrame({"component": columns, "median": np.median(vals, axis=0),
              "bootstrap_low": bounds[0], "bootstrap_high": bounds[1]}).to_csv(root / "bootstrap_medians.csv", index=False)
pd.concat([runs.assign(group="sampled"), reference.assign(group="deterministic")])[["withheld", "seed", "group", *columns]].to_csv(root / "distribution_figure_data.csv", index=False)
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4), sharex=True, sharey=True, layout="constrained")
for ax, col, title in zip(axes, columns, ["Total macro-F1 shortfall", "Forced-assignment component"]):
    ax.boxplot(runs[col], positions=[0], widths=.42, orientation="horizontal", showfliers=False)
    ax.scatter(runs[col], np.linspace(-.13, .13, len(runs)), s=13, alpha=.60, color="#24678a")
    for j, row in enumerate(reference.itertuples(index=False), 1):
        ax.scatter(getattr(row, col), j, marker="D", s=26, color="#9b4628")
    ax.set_title(title)
    ax.set_xlim(-.012, .53)
    ax.grid(axis="x", alpha=.25)
    ax.set_axisbelow(True)
axes[0].set_yticks(range(4), ["20 sampled pairs", *reference.withheld.tolist()])
args.figures.mkdir(parents=True, exist_ok=True)
fig.savefig(args.figures / "unsw_pair_distribution.pdf")
fig.savefig(args.figures / "unsw_pair_distribution.png", dpi=300)

cm = pd.read_csv(args.results / "unsw_partial_coverage/confusion.csv", index_col=0)
covered = ~cm.index.isin(["Analysis", "Backdoor"])
matrix = cm.to_numpy()
support = matrix.sum(axis=1)
def macro(scored):
    return np.mean(2 * scored.diagonal() / (support + scored.sum(axis=0)))
fixed = np.diag(np.where(covered, support, 0))
covered_first = fixed.copy()
covered_first[~covered] = matrix[~covered]
unseen_first = matrix.copy()
unseen_first[~covered] = 0
observed = macro(matrix)
ceiling = macro(fixed)
rows = [
    {"order":"covered_first", "observed":observed, "intermediate":macro(covered_first),
     "covered_component":macro(covered_first)-observed, "forced_component":ceiling-macro(covered_first)},
    {"order":"unseen_first", "observed":observed, "intermediate":macro(unseen_first),
     "covered_component":ceiling-macro(unseen_first), "forced_component":macro(unseen_first)-observed},
]
pd.DataFrame(rows).to_csv(root / "repair_order_sensitivity.csv", index=False)

