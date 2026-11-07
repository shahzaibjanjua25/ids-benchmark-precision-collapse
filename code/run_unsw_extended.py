"""Complete the attack-pair grid and retain an official five-seed reference."""
import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from clean_repo.ids_full_study import build, get_splits, load_unsw


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("data", type=Path)
parser.add_argument("results", type=Path)
parser.add_argument("--fresh", action="store_true", help="Refit every condition without archived fits")
parser.add_argument("--outdir", type=Path)
args = parser.parse_args()
if args.fresh and args.outdir is None:
    parser.error("--fresh requires --outdir pointing to a new folder")
out = args.outdir or args.results / "unsw_complete_pairs"
out.mkdir(parents=True, exist_ok=not args.fresh)
inputs = [args.results / "unsw_coverage_sensitivity/runs.csv",
          args.results / "unsw_coverage_random_pairs/runs.csv",
          args.results / "unsw_random_pairs_extra_seeds/runs.csv"]
records = []
if not args.fresh:
    runs = pd.concat([pd.read_csv(p) for p in inputs], ignore_index=True)
    records = runs.to_dict("records")
if (out / "runs.csv").exists():
    records = pd.read_csv(out / "runs.csv").to_dict("records")
done = {(row["withheld"], int(row["seed"])) for row in records}
ds = load_unsw(str(args.data))
train, test = get_splits(ds, "official", 42)[0]
truth = ds.y[test]
labels = np.unique(truth)
attacks = sorted(set(labels) - {"Normal"})
conditions = [(tuple(pair), seed) for pair in combinations(attacks, 2) for seed in range(42, 47)]
conditions += [((), seed) for seed in range(42, 47)]
conditions += [(tuple(attacks[:size]), 42) for size in [1, 3, 4, 5]]
for withheld, seed in conditions:
    name = " + ".join(withheld) or "NONE"
    if (name, seed) in done:
        continue
    keep = train[~np.isin(ds.y[train], withheld)]
    seen = ~np.isin(truth, withheld)
    model = build("rf", "none", seed, 200, ds)
    model.fit(ds.X.iloc[keep], ds.y[keep])
    probabilities = model.predict_proba(ds.X.iloc[test])
    pred = model.classes_[probabilities.argmax(axis=1)]
    def macro(prediction):
        return f1_score(truth, prediction, labels=labels, average="macro", zero_division=0)
    repaired = pred.copy()
    repaired[seen] = truth[seen]
    observed, repair = macro(pred), macro(repaired)
    ceiling = 1 - len(withheld) / len(labels)
    row = dict(pair="complete", withheld=name, seed=seed, train_rows=len(keep),
               test_rows=len(test), unseen_rows=int((~seen).sum()),
               ceiling=ceiling, macro_f1=observed, repaired_macro_f1=repair,
               covered_error_gap=repair-observed, forced_assignment_gap=ceiling-repair)
    # Oracle-assisted routing changes only the unavailable rows.
    majority = pd.Series(ds.y[keep]).value_counts().idxmax()
    routed = pred.copy()
    routed[~seen] = majority
    row["oracle_routed_macro_f1"] = macro(routed)
    confidence_routed = pred.copy()
    confidence_routed[probabilities.max(axis=1) < .5] = majority
    row["confidence_routed_macro_f1"] = macro(confidence_routed)
    records.append(row)
    pd.DataFrame(records).to_csv(out / "runs.csv", index=False)
    done.add((name, seed))
    print(name, seed, observed, flush=True)
