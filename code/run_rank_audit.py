"""Save covered/unavailable confusion counts for the complete withholding grid."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

from clean_repo.ids_full_study import build, get_splits, load_unsw, find_file


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("data", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
matrices = args.out / "confusion"
matrices.mkdir(exist_ok=True)
inputs=[Path(find_file(str(args.data),pattern,'UNSW input'))
        for pattern in ['*training-set*.csv','*testing-set*.csv']]
signature={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
manifest=args.out/'input_sha256.json'
if manifest.exists() and json.loads(manifest.read_text())!=signature:
    raise ValueError('Input files differ from the cached rank audit')
manifest.write_text(json.dumps(signature,indent=2)+'\n')
ds = load_unsw(str(args.data))
train, test = get_splits(ds, "official", 42)[0]
truth = ds.y[test]
labels = np.unique(truth)
attacks = sorted(set(labels) - {"Normal"})
rows = []
for pair in combinations(attacks, 2):
    keep = train[~np.isin(ds.y[train], pair)]
    seen = ~np.isin(truth, pair)
    for seed in range(42, 47):
        filename = matrices / f"{pair[0]}_{pair[1]}_{seed}.npz"
        if filename.exists():
            saved = np.load(filename, allow_pickle=False)
            covered, unavailable = saved["covered"], saved["unavailable"]
        else:
            model = build("rf", "none", seed, 200, ds)
            model.fit(ds.X.iloc[keep], ds.y[keep])
            pred = model.predict(ds.X.iloc[test])
            covered = confusion_matrix(truth[seen], pred[seen], labels=labels)
            unavailable = confusion_matrix(truth[~seen], pred[~seen], labels=labels)
            np.savez_compressed(filename, labels=labels.astype(str), covered=covered, unavailable=unavailable)
        full = covered + unavailable
        def macro(matrix, scored):
            denominator = matrix.sum(axis=0) + matrix.sum(axis=1)
            terms = np.divide(2 * np.diag(matrix), denominator, out=np.zeros(len(labels)), where=denominator > 0)
            return float(terms[scored].mean())
        row = {"withheld": " + ".join(pair), "seed": seed,
               "full_macro_f1": macro(full, np.ones(len(labels), dtype=bool)),
               "covered_macro_f1": macro(covered, covered.sum(axis=1) > 0),
               "covered_rows": int(covered.sum()), "unavailable_rows": int(unavailable.sum())}
        rows.append(row)
        pd.DataFrame(rows).to_csv(args.out / "runs.csv", index=False)
        print(row["withheld"], seed, row["full_macro_f1"], row["covered_macro_f1"], flush=True)
