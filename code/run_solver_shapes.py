"""Vary fold count and vocabulary shape without treating synthetic data as a benchmark."""
import argparse
import time

import numpy as np
import pandas as pd

from label_availability import exact_oracle, oracle_sandwich
from oracle_milp import solve_milp


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("out")
args = parser.parse_args()
rng = np.random.default_rng(20261108)
rows = []
for folds in [6, 30, 60, 100]:
    records = []
    for f in range(folds):
        allowed = set(rng.choice(6, size=3, replace=False))
        for k in range(7):
            test = int(rng.integers(1, 6)) if k == 6 else int(k in allowed)
            records.append({"fold": f, "class": k, "training_rows": int(k in allowed), "test_rows": test})
    counts = pd.DataFrame(records)
    row = {"folds": folds, "shape": "synthetic varied vocabulary", **oracle_sandwich(counts)}
    start = time.perf_counter()
    try:
        row.update(exact_oracle(counts, method="branch", max_choices=10000))
        row["branch_status"] = "certified"
    except ValueError as error:
        row["branch_status"] = str(error)
    row["branch_seconds"] = time.perf_counter() - start
    start = time.perf_counter()
    row.update(solve_milp(counts, time_limit=10))
    row["milp_seconds"] = time.perf_counter() - start
    if row["milp_status"] == 0 and "exact_oracle" in row:
        assert abs(row["exact_oracle"] - row["milp_feasible_score"]) < 1e-7
    rows.append(row)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(row, flush=True)
