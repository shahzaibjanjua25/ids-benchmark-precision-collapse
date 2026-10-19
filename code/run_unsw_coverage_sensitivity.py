"""Measure seed and withheld-pair sensitivity on the fixed official UNSW test set."""
import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from clean_repo.ids_full_study import build, get_splits, load_unsw
from label_coverage_bound import coverage_bound

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument('--random-pairs', action='store_true')
    parser.add_argument('--forest-seeds', nargs='+', type=int)
    args = parser.parse_args()
    ds = load_unsw(str(args.data))
    train, test = get_splits(ds, "official", 42)[0]
    truth = ds.y[test]
    labels = np.unique(truth)
    attack_counts = pd.Series(ds.y[train]).value_counts().drop("Normal")
    ranked = sorted(attack_counts.index, key=lambda label: (attack_counts[label], label))
    pairs = {"alphabetical": sorted(attack_counts.index)[:2],
             "largest": ranked[-2:], "smallest": ranked[:2]}
    seeds = range(42, 47)
    if args.random_pairs:
        excluded = {tuple(sorted(pair)) for pair in pairs.values()}
        candidates = [pair for pair in combinations(sorted(attack_counts.index), 2) if pair not in excluded]
        sampled = np.random.default_rng(2026).choice(len(candidates), size=20, replace=False)
        pairs = {f"draw_{i:02d}": candidates[j] for i, j in enumerate(sampled, 1)}
        seeds = (42,)
    if args.forest_seeds is not None:
        seeds = args.forest_seeds
    args.out.mkdir(parents=True, exist_ok=False)
    rows = []
    destinations = []
    for group, withheld in pairs.items():
        assert set(withheld).issubset(labels)
        keep = train[~np.isin(ds.y[train], withheld)]
        seen = ~np.isin(truth, withheld)
        train_counts = pd.Series(ds.y[keep]).value_counts()
        counts = pd.DataFrame({"class": labels,
                               "training_rows": train_counts.reindex(labels, fill_value=0).values,
                               "test_rows": pd.Series(truth).value_counts().reindex(labels).values})
        _, ceiling = coverage_bound(counts)
        majority = sorted(train_counts.index, key=lambda label: (-train_counts[label], label))[0]
        def macro(pred):
            return f1_score(truth, pred, labels=labels, average="macro")
        majority_f1 = macro(np.repeat(majority, len(test)))
        for seed in seeds:
            model = build("rf", "none", seed, 200, ds)
            model.fit(ds.X.iloc[keep], ds.y[keep])
            probabilities = model.predict_proba(ds.X.iloc[test])
            pred = model.classes_[probabilities.argmax(axis=1)]
            abstain = probabilities.max(axis=1) < .5
            rejected = pred.astype(object)
            rejected[abstain] = "UNKNOWN"
            coarse_truth = truth.copy().astype(object)
            coarse_truth[~seen] = "UNKNOWN"
            abstain_f1 = macro(rejected)
            unknown_f1 = f1_score(coarse_truth, rejected, labels=np.unique(coarse_truth.astype(str)), average="macro", zero_division=0)
            for label in labels:
                if label not in withheld:
                    support = int((truth == label).sum())
                    false_positive = int((pred[~seen] == label).sum())
                    destinations.append(dict(pair=group, seed=seed, destination=label,
                                             test_support=support, unseen_false_positives=false_positive,
                                             loss=false_positive / (2 * support + false_positive) / len(labels)))
            repaired = pred.copy()
            repaired[seen] = truth[seen]
            observed, repaired_score = macro(pred), macro(repaired)
            assert observed <= repaired_score + 1e-12 <= ceiling + 2e-12
            rows.append(dict(pair=group, withheld=" + ".join(sorted(withheld)), seed=seed,
                             train_rows=len(keep), test_rows=len(test), unseen_rows=int((~seen).sum()),
                             covered_errors=int((truth[seen] != pred[seen]).sum()),
                             majority_label=majority, majority_macro_f1=majority_f1, ceiling=ceiling,
                             macro_f1=observed, repaired_macro_f1=repaired_score,
                             abstention_f1=abstain_f1, explicit_unknown_f1=unknown_f1, abstained_rows=int(abstain.sum()),
                             covered_error_gap=repaired_score-observed,
                             forced_assignment_gap=ceiling-repaired_score))
            pd.DataFrame(rows).to_csv(args.out / "runs.csv", index=False)
            pd.DataFrame(destinations).to_csv(args.out / "destinations.csv", index=False)
            print(group, seed, observed, flush=True)

if __name__ == "__main__":
    main()

