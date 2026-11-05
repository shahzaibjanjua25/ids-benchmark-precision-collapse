"""Check fine-grained label coverage on the published NSL-KDD split."""
import argparse
import hashlib
from pathlib import Path
import pandas as pd
from label_coverage_bound import coverage_bound

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("data", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
counts = []
checksums = []
for name, column, expected in [("KDDTrain+.txt","training_rows",125973),("KDDTest+.txt","test_rows",22544)]:
    path = args.data / name
    table = pd.read_csv(path, header=None)
    if table.shape != (expected, 43):
        raise ValueError(f"Unexpected shape for {name}: {table.shape}")
    counts.append(table[41].value_counts().rename(column))
    checksums.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {name}")
labels = pd.concat(counts, axis=1).fillna(0).astype(int).rename_axis("class")
rows, ceiling = coverage_bound(labels.reset_index())
args.out.mkdir(parents=True, exist_ok=True)
labels.to_csv(args.out / "label_counts.csv")
rows.to_csv(args.out / "coverage.csv")
(args.out / "sha256.txt").write_text("\n".join(checksums)+"\n",encoding="ascii")
print(f"covered classes={rows.coverage.gt(0).sum()}/{len(rows)}; unseen rows={int((rows.test_rows-rows.covered_rows).sum())}; ceiling={ceiling:.8f}")

