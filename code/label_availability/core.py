"""Count-based bounds, including sklearn's inferred-label convention."""
import itertools
import math

import numpy as np
import pandas as pd


def count_folds(train_labels_per_fold, test_labels_per_fold):
    train = list(train_labels_per_fold)
    test = list(test_labels_per_fold)
    if len(train) != len(test):
        raise ValueError("Training and test fold lists must have equal length")
    rows = []
    for fold, (training, testing) in enumerate(zip(train, test)):
        tr = pd.Series(list(training), dtype=object).value_counts(dropna=False)
        te = pd.Series(list(testing), dtype=object).value_counts(dropna=False)
        for label in tr.index.union(te.index):
            rows.append({"fold": fold, "class": label,
                         "training_rows": int(tr.get(label, 0)),
                         "test_rows": int(te.get(label, 0))})
    return pd.DataFrame(rows, columns=["fold", "class", "training_rows", "test_rows"])


def _prepare(counts):
    counts = counts.copy().reset_index(drop=True)
    if "fold" not in counts:
        counts["fold"] = 0
    required = ["fold", "class", "training_rows", "test_rows"]
    if any(column not in counts for column in required):
        raise ValueError("Counts require fold, class, training_rows and test_rows")
    if counts[required].isna().any().any() or counts.duplicated(["fold", "class"]).any():
        raise ValueError("Missing values and repeated fold/class records are unsupported")
    for column in ["training_rows", "test_rows"]:
        values = counts[column].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 0).any() or (values != np.floor(values)).any():
            raise ValueError("Counts must be finite nonnegative integers")
    permitted = counts.training_rows.gt(0)
    if "allowed" in counts:
        if not counts.allowed.isin([0, 1, False, True]).all():
            raise ValueError("allowed must contain boolean values")
        permitted &= counts.allowed.astype(bool)
    counts["covered_rows"] = counts.test_rows.where(permitted, 0)
    labels = list(pd.unique(counts["class"]))
    index = {label: i for i, label in enumerate(labels)}
    totals = counts.groupby("class", sort=False)[["test_rows", "covered_rows"]].sum().reindex(labels)
    n = totals.test_rows.to_numpy(dtype=np.int64)
    m = totals.covered_rows.to_numpy(dtype=np.int64)
    if n.sum() == 0:
        raise ValueError("At least one test row is required")
    active = []
    for _, fold in counts.groupby("fold", sort=False):
        indices = fold.index
        allowed = [index[label] for label in fold.loc[permitted.loc[indices], "class"]]
        unseen = int((fold.test_rows - fold.covered_rows).sum())
        if fold.test_rows.sum() and not allowed:
            raise ValueError("A nonempty test fold must permit at least one label")
        if unseen:
            active.append((unseen, allowed))
    return counts, labels, n, m, active


def metric_bounds(counts):
    _, _, n, m, _ = _prepare(counts)
    support = n > 0
    rho = m[support] / n[support]
    terms = 2 * rho / (1 + rho)
    return {"coverage_ceiling": float(terms.mean()),
            "weighted_f1_ceiling": float(np.dot(n[support], terms) / n.sum()),
            "micro_f1_ceiling": float(m.sum() / n.sum()),
            "balanced_accuracy_ceiling": float(rho.mean()),
            "harmonic_macro_pr_ceiling": float(2 * rho.mean() / (1 + rho.mean()))}


def coverage_ceiling(train_labels_per_fold, test_labels_per_fold):
    return metric_bounds(count_folds(train_labels_per_fold, test_labels_per_fold))["coverage_ceiling"]


def oracle_sandwich(counts):
    _, _, n, m, active = _prepare(counts)
    support = n > 0
    terms = 2 * m[support] / (n[support] + m[support])
    ceiling = float(terms.mean())
    def cost(unseen, dest):
        if m[dest] == 0:
            return 0.0
        base = int(n[dest]) + int(m[dest])
        return 2 * int(m[dest]) * unseen / (base * (base + unseen)) / support.sum()
    costs = [min(cost(unseen, dest) for dest in allowed) for unseen, allowed in active]
    return {"sandwich_lower": max(0.0, ceiling - sum(costs)),
            "sandwich_upper": ceiling - max(costs, default=0.0)}


def union_ceiling(counts):
    prepared, labels, n, _, _ = _prepare(counts)
    support = {label for label, amount in zip(labels, n) if amount > 0}
    allowed = prepared.training_rows.gt(0)
    if "allowed" in prepared:
        allowed &= prepared.allowed.astype(bool)
    outside = allowed & ~prepared["class"].isin(support)
    restricted = prepared.assign(allowed=allowed & prepared["class"].isin(support))
    try:
        within_upper = oracle_sandwich(restricted)["sandwich_upper"]
    except ValueError:
        within_upper = 0.0
    if not outside.any():
        return within_upper
    classes = len(support)
    ceiling = metric_bounds(counts)["coverage_ceiling"]
    return max(within_upper, ceiling * classes / (classes + 1))


def exact_oracle(counts, max_choices=1_000_000, method="enumerate", convention="support"):
    if convention not in {"support", "union"}:
        raise ValueError("convention must be support or union")
    _, _, n, m, active = _prepare(counts)
    scored = n > 0
    classes = int(scored.sum())
    routes = []
    for unseen, allowed in active:
        free = [dest for dest in allowed if m[dest] == 0 and (convention == "support" or scored[dest])]
        routes.append((unseen, free[:1] or allowed))
    active = routes
    choices = math.prod(len(allowed) for _, allowed in active)
    fp = np.zeros(len(n), dtype=np.int64)
    def score():
        denominator = classes
        if convention == "union":
            denominator += int(((n == 0) & (fp > 0)).sum())
        return float((2 * m[scored] / (n[scored] + m[scored] + fp[scored])).sum() / denominator)
    ceiling = score()
    visited = pruned = 0
    # One common vocabulary reduces to a single simplex.
    if active and all(set(vocab) == set(active[0][1]) for _, vocab in active):
        unseen = sum(amount for amount, _ in active)
        active = [(unseen, active[0][1])]
    best = 0.0
    if method == "enumerate":
        search_choices = math.prod(len(allowed) for _, allowed in active)
        if search_choices > max_choices:
            raise ValueError(f"Oracle would require {search_choices} assignments")
        for route in itertools.product(*(allowed for _, allowed in active)):
            fp.fill(0)
            for (unseen, _), dest in zip(active, route):
                fp[dest] += unseen
            best = max(best, score())
            visited += 1
    elif method == "branch":
        active.sort(key=lambda item: (-item[0], len(item[1])))
        for unseen, allowed in active:
            candidates = []
            for dest in allowed:
                fp[dest] += unseen
                candidates.append((score(), dest))
                fp[dest] -= unseen
            fp[max(candidates)[1]] += unseen
        best = score()
        fp.fill(0)
        memo = set()
        def visit(depth):
            nonlocal best, visited, pruned
            visited += 1
            if visited > max_choices:
                raise ValueError(f"Branch-and-bound exceeded {max_choices} visited nodes")
            upper = score()
            if upper <= best:
                pruned += 1
                return
            if depth == len(active):
                best = upper
                return
            union_used = tuple(np.flatnonzero((n == 0) & (fp > 0))) if convention == "union" else ()
            key = (depth, tuple(fp[m > 0]), union_used)
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
        raise ValueError("method must be enumerate or branch")
    return {"coverage_ceiling": ceiling, "exact_oracle": best,
            "vertex_assignments": choices, "visited": visited, "pruned": pruned}
