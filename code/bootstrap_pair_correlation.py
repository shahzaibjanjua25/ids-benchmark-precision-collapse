"""Resample the observed seed-42 pairs for the support/penalty correlation."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
args = parser.parse_args()
root = args.results / "unsw_coverage_random_pairs"
runs = pd.read_csv(root / "runs.csv")
x = runs.unseen_rows.to_numpy()
y = runs.forced_assignment_gap.to_numpy()
draw = np.random.default_rng(2026).integers(len(x), size=(10000, len(x)))
a, b = (rankdata(values[draw], axis=1) for values in (x,y))
a -= a.mean(axis=1, keepdims=True)
b -= b.mean(axis=1, keepdims=True)
den = np.linalg.norm(a, axis=1)*np.linalg.norm(b, axis=1)
sample = (a[den>0]*b[den>0]).sum(axis=1)/den[den>0]
low, high = np.quantile(sample, [.025,.975])
pd.DataFrame([{"pairs":len(x),"rho":spearmanr(x,y).statistic,"low":low,"high":high}]).to_csv(root / "spearman_bootstrap.csv",index=False)
print(low,high)

