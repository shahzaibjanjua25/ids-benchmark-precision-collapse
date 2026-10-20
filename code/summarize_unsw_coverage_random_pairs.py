"""Summarize a fixed-seed sample of withheld pairs without extrapolation."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
args = parser.parse_args()
root = args.results / "unsw_coverage_random_pairs"
runs = pd.read_csv(root / "runs.csv")
assert len(runs) == runs.withheld.nunique() == 20
assert (runs.seed == 42).all() and (runs.test_rows == 82332).all()
assert (runs.ceiling == .8).all()
runs["total_gap"] = runs.ceiling - runs.macro_f1
np.testing.assert_allclose(runs.total_gap, runs.covered_error_gap + runs.forced_assignment_gap, rtol=0, atol=1e-12)
columns = ["unseen_rows", "macro_f1", "total_gap", "covered_error_gap", "forced_assignment_gap"]
runs[columns].agg(["min", "median", "max"]).to_csv(root / "summary.csv")

