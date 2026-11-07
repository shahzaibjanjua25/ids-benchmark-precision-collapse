"""Seed summaries and a fixed-prediction row bootstrap."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("out", type=Path)
args = parser.parse_args()
metrics = pd.read_csv(args.out / "forest_metrics.csv")
assert set(metrics.seed) == set(range(42, 47)) and len(metrics) == 5
rows = []
for seed in metrics.seed:
    cm = sum(pd.read_csv(args.out / f"confusion_{kind}_{seed}.csv", index_col=0).to_numpy()
             for kind in ["seen", "unseen"])
    scored = cm.sum(axis=1) > 0
    rng = np.random.default_rng(20261108)
    draws = rng.multinomial(int(cm.sum()), cm.ravel() / cm.sum(), size=500)
    scores = []
    for draw in draws:
        matrix = draw.reshape(cm.shape)
        denominator = (matrix.sum(axis=0) + matrix.sum(axis=1))[scored]
        scores.append(np.divide(2 * np.diag(matrix)[scored], denominator,
                                out=np.zeros(scored.sum()), where=denominator > 0).mean())
    rows.append({"seed": seed, "row_bootstrap_low": np.quantile(scores, .025),
                 "row_bootstrap_high": np.quantile(scores, .975)})
metrics.merge(pd.DataFrame(rows), on="seed").to_csv(args.out / "seed_intervals.csv", index=False)
print(metrics.macro_f1.agg(["mean", "std"]).to_string())
