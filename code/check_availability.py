"""Cross-check the bounds against row-level search."""
import itertools

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from label_availability import count_folds, coverage_ceiling, exact_oracle, oracle_sandwich, union_ceiling


def main():
    rng = np.random.default_rng(20261108)
    for case in range(80):
        train, test = [], []
        for fold in range(2):
            train.append(rng.choice(4, size=2, replace=False).tolist())
            test.append(rng.integers(0, 3, size=2).tolist())
        counts = count_folds(train, test)
        truth = list(itertools.chain.from_iterable(test))
        support = np.unique(truth)
        for convention in ["support", "union"]:
            labels = support if convention == "support" else None
            brute = max(f1_score(truth, pred, labels=labels, average="macro", zero_division=0)
                        for pred in itertools.product(*(vocab for vocab, y in zip(train, test) for _ in y)))
            for method in ["enumerate", "branch"]:
                result = exact_oracle(counts, method=method, convention=convention)
                assert abs(result["exact_oracle"] - brute) < 1e-12, (case, convention, method)
            if convention == "support":
                bounds = oracle_sandwich(counts)
                assert bounds["sandwich_lower"] - 1e-12 <= brute <= bounds["sandwich_upper"] + 1e-12
            else:
                assert brute <= union_ceiling(counts) + 1e-12
        assert abs(coverage_ceiling(train, test) - exact_oracle(counts)["coverage_ceiling"]) < 1e-12
    empty = count_folds([[0]], [[]])
    try:
        exact_oracle(empty)
    except ValueError:
        pass
    else:
        raise AssertionError("Empty cohort accepted")
    missing = count_folds([[0]], [[0, np.nan]])
    try:
        exact_oracle(missing)
    except ValueError:
        pass
    else:
        raise AssertionError("Missing label accepted")
    print("80 row-level cases: both conventions, both solvers, sandwich and array API passed")


if __name__ == "__main__":
    main()
