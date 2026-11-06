"""Exact pooled macro-F1 oracle for small fold-vocabulary products."""
import argparse
import itertools
import math
from pathlib import Path
import numpy as np
import pandas as pd

def oracle(counts, max_choices=1_000_000):
    # Include train-only labels in the vocabulary.
    labels = sorted(counts["class"].unique())
    label_index = {label: i for i, label in enumerate(labels)}
    n = counts.groupby("class").test_rows.sum().reindex(labels).to_numpy()
    m = counts.test_rows.where(counts.training_rows.gt(0), 0).groupby(counts["class"]).sum().reindex(labels).to_numpy()
    active = []
    for _, fold in counts.groupby("fold"):
        unseen = int(fold.loc[fold.training_rows.eq(0), "test_rows"].sum())
        if not unseen:
            continue
        allowed = [label_index[label] for label in fold.loc[fold.training_rows.gt(0), "class"]]
        if not allowed:
            raise ValueError("Fold has unseen rows but no allowed predictions")
        free = [i for i in allowed if m[i] == 0]
        active.append((unseen, free[:1] or allowed))
    choices = math.prod(len(allowed) for _, allowed in active)
    if choices > max_choices:
        raise ValueError(f"Oracle would require {choices} assignments")
    scored = n > 0
    best = 0.0
    for route in itertools.product(*(allowed for _, allowed in active)):
        fp = np.zeros(len(labels), dtype=int)
        for (unseen, _), dest in zip(active, route):
            fp[dest] += unseen
        score = np.mean(2 * m[scored] / (n[scored] + m[scored] + fp[scored]))
        best = max(best, float(score))
    bound = float(np.mean(2*m[scored]/(n[scored]+m[scored])))
    return {"coverage_ceiling":bound,"exact_oracle":best,"vertex_assignments":choices}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    p = args.results
    day = pd.read_csv(p/"cic_day_coverage.csv").pivot(index="day",columns="class",values="test_rows").fillna(0).astype(int)
    cic = day.stack().rename("test_rows").reset_index().rename(columns={"day":"fold"})
    totals = day.sum()
    cic["training_rows"] = cic["class"].map(totals)-cic.test_rows
    cases = {
        "CICIDS2017 LODO":cic,
        "NSL-KDD official":pd.read_csv(p/"nsl_kdd_official/label_counts.csv").assign(fold=0),
        "UNSW-NB15 mixed":pd.read_csv(p/"unsw_partial_coverage/fold_label_counts.csv").assign(fold=0),
        "Digits partial":pd.read_csv(p/"digits_fractional_coverage/fold_label_counts.csv"),
    }
    results = pd.DataFrame([{"case":name,**oracle(counts)} for name,counts in cases.items()])
    results.to_csv(p/"exact_fold_oracles.csv",index=False)
    print(results.to_string(index=False))

if __name__ == "__main__":
    main()

