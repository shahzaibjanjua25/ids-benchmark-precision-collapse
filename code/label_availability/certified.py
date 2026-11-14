"""Independent rational oracle with feasible routing witnesses.

This deliberately simple implementation enumerates grouped vertices without the
floating-point solver's pruning or free-destination reductions. It is intended
for verification and modest vocabulary products, not large unrestricted inputs.
"""
from fractions import Fraction
from itertools import product
from math import prod

from .core import _prepare


def _scalar(value):
    return value.item() if hasattr(value, "item") else value


def certified_oracle(counts, convention="support", scored_labels=None,
                     max_assignments=1_000_000):
    """Return an exact rational optimum and one legal allocation attaining it.

    ``fixed`` uses a supplied, nonempty inventory containing every true label;
    absent scored labels contribute zero (zero_division=0). ``union`` activates
    only actually predicted outside labels. The witness repairs covered rows
    and routes each fold's unavailable rows to its recorded destination.
    A budget error returns no claim of optimality.
    """
    if convention not in {"support", "union", "fixed"}:
        raise ValueError("convention must be support, union or fixed")
    if not isinstance(max_assignments, int) or isinstance(max_assignments, bool) or max_assignments < 1:
        raise ValueError("max_assignments must be a positive integer")
    prepared, labels, n_array, m_array, _ = _prepare(counts)
    n, m = list(map(int, n_array)), list(map(int, m_array))
    support = {labels[i] for i, total in enumerate(n) if total}
    if convention == "fixed":
        if scored_labels is None:
            raise ValueError("fixed scoring requires scored_labels")
        inventory = list(scored_labels)
        if len(set(inventory)) != len(inventory) or not support.issubset(inventory):
            raise ValueError("fixed inventory must be unique and include every true label")
        denominator = len(inventory)
    else:
        if scored_labels is not None:
            raise ValueError("scored_labels is only valid for fixed scoring")
        denominator = len(support)
    index = {label: i for i, label in enumerate(labels)}
    groups = {}
    for fold_id, fold in prepared.groupby("fold", sort=False):
        amount = sum(int(x) for x in fold.test_rows - fold.covered_rows)
        if not amount:
            continue
        allowed = fold.allowed.astype(bool) if "allowed" in fold else fold.training_rows.gt(0)
        vocabulary = tuple(sorted(index[x] for x in fold.loc[allowed, "class"]))
        groups.setdefault(vocabulary, []).append((fold_id, amount))
    assignments = prod(map(len, groups))
    if assignments > max_assignments:
        raise ValueError(f"Rational oracle requires {assignments} grouped assignments")
    def score(fp):
        divisor = denominator
        if convention == "union":
            divisor += sum(total == 0 and pred > 0 for total, pred in zip(n, fp))
        return sum((Fraction(2 * hits, total + hits + pred)
                    for total, hits, pred in zip(n, m, fp) if total), Fraction()) / divisor
    best, best_route, best_fp = Fraction(-1), None, None
    visited = 0
    for route in product(*groups):
        fp = [0] * len(labels)
        for records, dest in zip(groups.values(), route):
            fp[dest] += sum(amount for _, amount in records)
        value = score(fp)
        visited += 1
        if value > best:
            best, best_route, best_fp = value, route, fp
    witness = []
    for records, dest in zip(groups.values(), best_route):
        for fold_id, amount in records:
            witness.append({"fold": _scalar(fold_id), "unavailable_rows": amount, "destination": _scalar(labels[dest])})
    ceiling = sum((Fraction(2 * b, a + b) for a, b in zip(n, m) if a), Fraction()) / denominator
    # Equality to C is structural for support/fixed; union needs no outside activation.
    tight = ceiling == 0 or all(any(m[k] == 0 and (convention != "union" or n[k] > 0)
                    for k in vocab) for vocab in groups)
    assert (best == ceiling) == tight
    return {"convention": convention, "exact_oracle": float(best),
            "exact_fraction": str(best), "coverage_ceiling": float(ceiling),
            "ceiling_fraction": str(ceiling), "ceiling_attainable": tight,
            "grouped_assignments": assignments, "enumerated_assignments": visited,
            "routing": witness,
            "class_totals": [{"class": _scalar(label), "test_rows": a, "covered_rows": b,
                              "oracle_false_positives": c}
                             for label, a, b, c in zip(labels, n, m, best_fp)]}
