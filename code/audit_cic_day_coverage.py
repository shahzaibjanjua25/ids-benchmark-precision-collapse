import argparse
from pathlib import Path
import pandas as pd
from clean_repo.ids_full_study import norm_label

parser = argparse.ArgumentParser()
parser.add_argument("data", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
tables = []
for path in sorted(args.data.rglob("*.csv")):
    day = path.name.split("-", 1)[0].lower()
    labels = pd.read_csv(path, encoding="latin1", usecols=lambda name: name.strip() == "Label").iloc[:, 0].map(norm_label)
    tables.append(labels.value_counts().rename_axis("class").reset_index(name="test_rows").assign(day=day))
counts = pd.concat(tables).groupby(["day", "class"], as_index=False).test_rows.sum()
counts["training_rows_other_days"] = counts.groupby("class").test_rows.transform("sum") - counts.test_rows
counts.to_csv(args.out, index=False)


