"""Rerun two archived UNSW random forest arms on the full official test set."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from clean_repo.ids_full_study import build, get_splits, load_unsw

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    ds = load_unsw(str(args.data))
    seed, trees = 42, 200
    train, test = get_splits(ds, "official", seed)[0]
    truth = ds.y[test]
    paired = pd.DataFrame({"combined_row": test, "truth": truth})
    archive = pd.read_csv(Path(__file__).resolve().parents[1] / "results" / "RESULTS_PARSED.csv")
    rows = []
    for arm in ("none", "balanced_subsample"):
        model = build("rf", arm, seed, trees, ds)
        model.fit(ds.X.iloc[train], ds.y[train])
        pred = model.predict(ds.X.iloc[test])
        paired[arm] = pred
        score = f1_score(truth, pred, average="macro")
        archived = archive.query("dataset == 'unsw' and variant == 'raw' and protocol == 'official' and model == 'rf' and seed == @seed and arm == @arm").iloc[0]
        rows.append({"arm": arm, "seed": seed, "trees": trees, "test_rows": len(test),
                     "accuracy": accuracy_score(truth, pred), "macro_f1": score,
                     "archived_macro_f1": archived.macro_f1, "macro_f1_delta": score - archived.macro_f1})
        print(rows[-1], flush=True)
    paired.to_csv(args.out / "paired_predictions.csv", index=False)
    pd.DataFrame(rows).to_csv(args.out / "metrics.csv", index=False)
    a = paired["none"].eq(paired.truth)
    b = paired["balanced_subsample"].eq(paired.truth)
    pd.crosstab(a, b, rownames=["unweighted_correct"], colnames=["weighted_correct"]).to_csv(args.out / "paired_correctness.csv")

if __name__ == "__main__":
    main()

