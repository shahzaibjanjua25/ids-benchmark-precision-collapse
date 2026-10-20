"""Summarize paired UNSW overlap contrasts across five seeds on one fixed test set."""
from itertools import product
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
dirs = [f"unsw_overlap_seed_{seed}" for seed in range(42, 47)]
if not (args.source / dirs[0] / "metrics.csv").exists():
    dirs = ["unsw_overlap_control", "unsw_overlap_matched", *dirs[1:]]
membership = pd.read_csv(args.source / dirs[0] / "test_membership.csv")
for name in dirs[1:]:
    other = pd.read_csv(args.source / name / "test_membership.csv")
    pd.testing.assert_frame_equal(membership, other)
runs = pd.concat([pd.read_csv(args.source / name / "metrics.csv") for name in dirs])
wide = runs.pivot(index="seed", columns="condition", values="macro_f1")
assert list(wide.index) == list(range(42, 47))
assert not wide.isna().any().any()
assert len(membership) == 82332 and (runs.test_rows == len(membership)).all()
counts = runs.pivot(index="seed", columns="condition", values="train_rows")
assert counts.overlap_removed.equals(counts.class_count_matched_removal)
args.out.mkdir(parents=True, exist_ok=True)
runs.sort_values(["seed", "condition"]).to_csv(args.out / "metrics.csv", index=False)
per_class = pd.concat([pd.read_csv(args.source / name / "per_class.csv").assign(seed=pd.read_csv(args.source / name / "metrics.csv").seed.iloc[0]) for name in dirs])
per_class.to_csv(args.out / "per_class.csv", index=False)
rows = []
for arm in ("official_train", "class_count_matched_removal"):
    delta = (wide.overlap_removed - wide[arm]).to_numpy()
    n = len(delta)
    mean = delta.mean()
    sd = delta.std(ddof=1)
    margin = t.ppf(.975, n - 1) * sd / np.sqrt(n)
    signed = np.asarray(list(product([-1, 1], repeat=n))) @ delta / n
    p = np.mean(np.abs(signed) >= abs(mean) - 1e-12)
    wide["delta_vs_" + arm] = delta
    rows.append({"comparison": arm, "n_seeds": n, "mean_delta": mean, "seed_sd": sd,
                 "t_interval_low": mean - margin, "t_interval_high": mean + margin,
                 "sign_flip_p": p, "min_delta": delta.min(), "max_delta": delta.max()})
wide.to_csv(args.out / "paired_seed_scores.csv")
pd.DataFrame(rows).to_csv(args.out / "paired_seed_summary.csv", index=False)

