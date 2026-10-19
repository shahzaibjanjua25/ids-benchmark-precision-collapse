"""Evaluate the pre-fit ceiling on a fixed test set with two withheld training labels."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score
from clean_repo.ids_full_study import load_unsw, get_splits, build
from label_coverage_bound import coverage_bound

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    ds = load_unsw(str(args.data))
    train, test = get_splits(ds, "official", 42)[0]
    withheld = ("Analysis", "Backdoor")
    assert set(withheld).issubset(ds.y[train]) and set(withheld).issubset(ds.y[test])
    keep = train[~np.isin(ds.y[train], withheld)]
    truth = ds.y[test]
    counts = pd.concat([pd.Series(ds.y[ix]).value_counts().rename(name)
                        for ix, name in [(keep, "training_rows"), (test, "test_rows")]], axis=1).fillna(0).astype(int)
    counts.index.name = "class"
    classes, ceiling = coverage_bound(counts.reset_index())
    model = build("rf", "none", 42, 200, ds)
    model.fit(ds.X.iloc[keep], ds.y[keep])
    pred = model.predict(ds.X.iloc[test])
    labels = classes.index.tolist()
    score = f1_score(truth, pred, labels=labels, average="macro")
    assert score <= ceiling + 1e-12
    groups = np.isin(truth, withheld)
    args.out.mkdir(parents=True, exist_ok=False)
    counts.to_csv(args.out / "fold_label_counts.csv")
    classes.to_csv(args.out / "coverage_by_class.csv")
    pd.DataFrame(confusion_matrix(truth, pred, labels=labels), index=labels, columns=labels).to_csv(args.out / "confusion.csv")
    pd.DataFrame({"combined_row": train, "included": ~np.isin(ds.y[train], withheld)}).to_csv(args.out / "training_membership.csv", index=False)
    pd.DataFrame([{"stratum": name, "test_rows": int(mask.sum()), "exact_hits": int((truth[mask] == pred[mask]).sum())}
                  for name, mask in [("seen", ~groups), ("unseen", groups)]]).to_csv(args.out / "strata.csv", index=False)
    pd.DataFrame([{"seed": 42, "trees": 200, "train_rows": len(keep), "test_rows": len(test), "macro_f1": score, "ceiling": ceiling}]).to_csv(args.out / "metrics.csv", index=False)
    print(score, ceiling)

if __name__ == "__main__":
    main()

