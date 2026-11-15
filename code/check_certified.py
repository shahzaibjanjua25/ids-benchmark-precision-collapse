"""Independent integer row enumeration, fixed inventories and certificate checks."""
import itertools
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

from label_availability import certified_oracle, count_folds, exact_oracle, metric_bounds


def direct_score(truth, pred, inventory):
    terms = []
    for k in inventory:
        tp = sum(a == k and b == k for a, b in zip(truth, pred))
        total = sum(a == k for a in truth) + sum(b == k for b in pred)
        terms.append(Fraction(2 * tp, total) if total else Fraction())
    return sum(terms, Fraction()) / len(terms)


def main():
    rng = np.random.default_rng(20261115)
    checks = 0
    for case in range(240):
        heads = [rng.choice(4, size=int(rng.integers(1, 4)), replace=False).tolist() for _ in range(2)]
        tests = [rng.integers(0, 3, size=int(rng.integers(1, 3))).tolist() for _ in heads]
        counts = count_folds([[0], [1]], tests, heads)
        truth = sum(tests, [])
        support = sorted(set(truth))
        for convention in ["support", "union", "fixed"]:
            fixed = list(range(5)) if convention == "fixed" else None
            oracle = certified_oracle(counts, convention, fixed)
            brute = Fraction(-1)
            for pred in itertools.product(*(head for head, test in zip(heads, tests) for _ in test)):
                inventory = fixed if fixed is not None else (support if convention == "support" else sorted(set(truth) | set(pred)))
                brute = max(brute, direct_score(truth, pred, inventory))
            assert Fraction(oracle["exact_fraction"]) == brute, (case, convention)
            routes = {row["fold"]: row["destination"] for row in oracle["routing"]}
            witness = [y if y in head else routes[f]
                       for f, (head, test) in enumerate(zip(heads, tests)) for y in test]
            offset = 0
            for head, test in zip(heads, tests):
                assert all(p in head for p in witness[offset:offset + len(test)])
                offset += len(test)
            inventory = fixed if fixed is not None else (support if convention == "support" else sorted(set(truth) | set(witness)))
            assert direct_score(truth, witness, inventory) == brute
            assert (brute == Fraction(oracle["ceiling_fraction"])) == oracle["ceiling_attainable"]
            if convention != "fixed":
                for method in ["enumerate", "branch"]:
                    assert abs(exact_oracle(counts, convention=convention, method=method)["exact_oracle"] - float(brute)) < 1e-12
            checks += 1
    # Minimal all-cost example: two available labels and one unavailable label.
    minimal = count_folds([[0, 1]], [[0, 1, 2]])
    assert certified_oracle(minimal)["exact_fraction"] == "5/9"
    assert certified_oracle(minimal)["ceiling_fraction"] == "2/3"
    # Output-only routing can attain C under support but not under inferred union.
    output_only = count_folds([[0]], [[0, 1]], [[0, 2]])
    assert certified_oracle(output_only)["exact_fraction"] == "1/2"
    assert certified_oracle(output_only, "union")["exact_fraction"] == "1/3"
    # Every true label unavailable; C=O=0 even if only outside outputs are legal.
    assert certified_oracle(count_folds([[3]], [[0]]), "union")["ceiling_attainable"]
    for invalid in [minimal.assign(test_rows=-1), minimal.assign(test_rows=0.5),
                    minimal.assign(test_rows="1"),
                    minimal.assign(test_rows=2 ** 62), minimal.assign(test_rows=float(2 ** 54)),
                    pd.concat([minimal, minimal]), minimal.assign(allowed=False)]:
        try:
            certified_oracle(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid counts accepted")
    large = minimal.copy()
    large["test_rows"] = [2 ** 53 + 1, 1, 1]
    assert metric_bounds(large)["micro_f1_ceiling"] <= 1
    large_float = pd.DataFrame({'fold':[0,1,1], 'class':['A','A','B'],
        'training_rows':[1.,1.,0.], 'test_rows':[float(2**52), float(2**52+1), 1.]})
    certificate = certified_oracle(large_float)
    total = 2**53+1
    assert certificate['class_totals'][0]['test_rows'] == total
    assert Fraction(certificate['exact_fraction']) == Fraction(total, 2*total+1)
    nonintegral = minimal.copy()
    nonintegral['test_rows'] = pd.Series([Fraction(2**53+1,2),1,1],dtype=object)
    try:
        certified_oracle(nonintegral)
    except ValueError:
        pass
    else:
        raise AssertionError('Nonintegral rational count accepted')
    try:
        certified_oracle(minimal, max_assignments=1)
    except ValueError:
        pass
    else:
        raise AssertionError("Budget not enforced")
    for kwargs in [{"convention": "fixed"}, {"convention": "fixed", "scored_labels": [0, 1]},
                   {"convention": "fixed", "scored_labels": [0, 1, 2, 2]},
                   {"convention": "bad"}, {"max_assignments": 0}]:
        try:
            certified_oracle(minimal, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Invalid scoring configuration accepted: {kwargs}")
    root = Path(__file__).resolve().parents[1]
    out = root / "results/revision_20261115"
    out.mkdir(exist_ok=True)
    (out / "rational_validation.json").write_text(json.dumps({
        "seed": 20261115, "random_inputs": 240, "row_enumeration_comparisons": checks,
        "conventions": ["support", "union", "fixed"], "passed": True,
        "minimal_all_cost": certified_oracle(minimal)}, indent=2), encoding="utf8")
    print(f"{checks} exact rational row-enumeration comparisons passed; witnesses and edge cases passed")


if __name__ == "__main__":
    main()
