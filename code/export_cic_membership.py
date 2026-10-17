"""Export row-level test membership for the current CICIDS2017 ML CSV cohort."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from clean_repo.ids_full_study import DAYS, DS, get_splits, norm_label

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    labels, days, order, files = [], [], [], []
    for path in sorted(args.data.rglob("*.csv")):
        columns = pd.read_csv(path, encoding="latin-1", nrows=0).columns
        names = {column.strip().lower(): column for column in columns}
        if "source ip" in names or "timestamp" in names:
            raise ValueError("Expected the MachineLearningCSV files without Source IP or Timestamp")
        day = next(day for day in DAYS if path.name.lower().startswith(day))
        y = pd.read_csv(path, encoding="latin-1", usecols=[names["label"]]).iloc[:, 0].map(norm_label)
        labels.append(y.to_numpy())
        days.append(np.repeat(day, len(y)))
        order.append(np.arange(len(y), dtype=float))
        files.append({"file": path.relative_to(args.data).as_posix(), "rows": len(y)})
    y = np.concatenate(labels)
    meta = pd.DataFrame({"day": np.concatenate(days), "order": np.concatenate(order)})
    ds = DS("cic", pd.DataFrame(index=range(len(y))), y, [], [], meta)
    values = {}
    for protocol in ("cv", "time", "lodo"):
        folds = np.full(len(y), -1, dtype=np.int8)
        for fold, (_, test) in enumerate(get_splits(ds, protocol, 42)):
            folds[test] = fold
        values[protocol] = folds
    args.out.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(args.out / "cic_test_folds_seed42.npz", **values)
    pd.DataFrame(files).to_csv(args.out / "cic_row_order.csv", index=False)

if __name__ == "__main__":
    main()

