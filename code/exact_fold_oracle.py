"""Exact pooled macro-F1 oracle for small fold-vocabulary products."""
import argparse
import itertools
import math
import time
import tracemalloc
from pathlib import Path
import numpy as np
import pandas as pd

def oracle(counts, max_choices=1_000_000, method='enumerate'):
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
    scored = n > 0
    def score(fp):
        return float(np.mean(2 * m[scored] / (n[scored] + m[scored] + fp[scored])))

    fp = np.zeros(len(labels), dtype=int)
    bound = score(fp)
    best = 0.0
    visited = pruned = 0
    if method == "enumerate":
        if choices > max_choices:
            raise ValueError(f"Oracle would require {choices} assignments")
        for route in itertools.product(*(allowed for _, allowed in active)):
            fp.fill(0)
            for (unseen, _), dest in zip(active, route):
                fp[dest] += unseen
            best = max(best, score(fp))
            visited += 1
    elif method == "branch":
        active.sort(key=lambda item: (-item[0], len(item[1])))
        for unseen, allowed in active:
            def loss(dest):
                if m[dest] == 0:
                    return 0.0
                denominator = int(n[dest]) + int(m[dest]) + int(fp[dest])
                return 2 * int(m[dest]) * unseen / (denominator * (denominator + unseen))
            fp[min(allowed, key=loss)] += unseen
        best = score(fp)
        fp.fill(0)
        memo = set()
        def visit(depth):
            nonlocal best, visited, pruned
            visited += 1
            if visited > max_choices:
                raise ValueError(f"Branch-and-bound exceeded {max_choices} visited nodes")
            # Further assignments only add false positives.
            upper = score(fp)
            if upper <= best:
                pruned += 1
                return
            if depth == len(active):
                best = upper
                return
            key = (depth, tuple(fp[m > 0]))
            if key in memo:
                pruned += 1
                return
            memo.add(key)
            unseen, allowed = active[depth]
            for dest in allowed:
                fp[dest] += unseen
                visit(depth + 1)
                fp[dest] -= unseen
        visit(0)
    else:
        raise ValueError(f"Unknown solver: {method}")
    return {"coverage_ceiling":bound,"exact_oracle":best,"vertex_assignments":choices,
            "visited":visited,"pruned":pruned}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--method", choices=["enumerate","branch"], default="enumerate")
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
    rows = []
    for name, counts in cases.items():
        tracemalloc.start()
        start = time.perf_counter()
        result = oracle(counts, method=args.method)
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        uncovered = counts.loc[counts.training_rows.eq(0) & counts.test_rows.gt(0), "fold"].nunique()
        rows.append({"case":name, **result, "uncovered_folds":uncovered,
                     "runtime_seconds":elapsed, "traced_peak_bytes":peak})
    results = pd.DataFrame(rows)
    filename = "exact_fold_oracles_branch.csv" if args.method == "branch" else "exact_fold_oracles.csv"
    results.to_csv(p / filename, index=False)
    print(results.to_string(index=False))

if __name__ == "__main__":
    main()
