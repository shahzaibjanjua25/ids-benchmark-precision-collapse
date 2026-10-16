import argparse
from pathlib import Path
import pandas as pd
from clean_repo.ids_full_study import load_unsw, hashes, dedup

parser = argparse.ArgumentParser()
parser.add_argument("data")
parser.add_argument("out", type=Path)
args = parser.parse_args()
rows = []
raw = load_unsw(args.data)
for variant, ds in [("raw", raw), ("dedup", dedup(raw))]:
    feature, labeled = hashes(ds)
    train = ds.is_train
    test = ~train
    table = pd.DataFrame({
        "class": ds.y[test],
        "test_rows": 1,
        "feature_hash_seen_in_train": pd.Index(feature[train]).unique().get_indexer(feature[test]) >= 0,
        "feature_label_hash_seen_in_train": pd.Index(labeled[train]).unique().get_indexer(labeled[test]) >= 0,
    })
    grouped = table.groupby("class", as_index=False).sum()
    grouped.insert(0, "variant", variant)
    rows.append(grouped)
pd.concat(rows, ignore_index=True).to_csv(args.out, index=False)

