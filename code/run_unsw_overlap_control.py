"""Compare official UNSW-NB15 test predictions with and without training overlap."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

from clean_repo.ids_full_study import build, get_splits, hashes, load_unsw

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument('--matched-only', action='store_true')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    ds = load_unsw(str(args.data))
    train, test = get_splits(ds, "official", args.seed)[0]
    feature, _ = hashes(ds)
    overlap = np.isin(feature[train], feature[test])
    args.out.mkdir(parents=True, exist_ok=False)

    pd.DataFrame({"combined_row": test}).to_csv(args.out / "test_membership.csv", index=False)
    rows, reports = [], []
    predictions = pd.DataFrame({"combined_row": test, "truth": ds.y[test]})
    rng = np.random.default_rng(args.seed)
    matched_keep = np.ones(len(train), dtype=bool)
    for label in np.unique(ds.y[train]):
        positions = np.flatnonzero(ds.y[train] == label)
        remove = int(overlap[positions].sum())
        matched_keep[rng.choice(positions, size=remove, replace=False)] = False
    pd.DataFrame({"combined_row": train, "removed_for_overlap": overlap,
                  "removed_for_matched_control": ~matched_keep}).to_csv(args.out / "training_membership.csv", index=False)
    matched = ("class_count_matched_removal", train[matched_keep])
    arms = [matched] if args.matched_only else [("official_train", train), ("overlap_removed", train[~overlap]), matched]
    for name, keep in arms:
        model = build("rf", "none", args.seed, 200, ds)
        model.fit(ds.X.iloc[keep], ds.y[keep])
        pred = model.predict(ds.X.iloc[test])
        predictions[name] = pred
        truth = ds.y[test]
        rows.append({"condition": name, "seed": args.seed, "trees": 200, "train_rows": len(keep), "test_rows": len(test),
                     "accuracy": accuracy_score(truth, pred), "macro_f1": f1_score(truth, pred, average="macro")})
        report = classification_report(truth, pred, labels=np.unique(truth), output_dict=True, zero_division=0)
        reports.extend({"condition": name, "class": label, **report[label]} for label in np.unique(truth))
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(args.out / "metrics.csv", index=False)
    pd.DataFrame(reports).to_csv(args.out / "per_class.csv", index=False)
    predictions.to_csv(args.out / "predictions.csv", index=False)
    paths = sorted(args.data.glob("UNSW_NB15_*ing-set.csv"))
    with (args.out / "dataset_sha256.txt").open("w", encoding="utf-8") as out:
        for path in paths:
            with path.open("rb") as stream:
                out.write(f"{hashlib.file_digest(stream, 'sha256').hexdigest()}  {path.name}\n")

if __name__ == "__main__":
    main()

