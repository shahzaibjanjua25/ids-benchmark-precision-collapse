"""Write the archived day-holdout counts with seen/unseen labels."""
import argparse
from pathlib import Path

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("results", type=Path)
args = parser.parse_args()
coverage = pd.read_csv(args.results / "cic_day_coverage.csv")
groups = coverage.assign(unseen=coverage.training_rows_other_days.eq(0)).groupby("class").unseen
assert groups.nunique().eq(1).all()  # pooled rows have one coverage status per label here
unseen = groups.first()
tables = []
for path in sorted((args.results / "confusion").glob("cic_raw_lodo_rf_*.csv")):
    cm = pd.read_csv(path, index_col=0)
    counts = cm.rename_axis("truth").reset_index().melt("truth", var_name="prediction", value_name="rows")
    counts["coverage"] = counts.truth.map(unseen).map({True:"unseen", False:"seen"})
    counts["arm"] = path.stem.removeprefix("cic_raw_lodo_rf_")
    assert counts.coverage.notna().all()
    tables.append(counts)
result = pd.concat(tables, ignore_index=True)
assert result.groupby(["arm", "coverage"]).rows.sum().unstack().eq({"seen":2273097,"unseen":557646}).all().all()
result.to_csv(args.results / "cic_lodo_confusion_by_coverage.csv", index=False)

