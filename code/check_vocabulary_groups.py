"""Check explicit output heads and repeated vocabulary grouping."""
import itertools
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from label_availability import count_folds, exact_oracle, coverage_ceiling, oracle_sandwich, union_ceiling

rng = np.random.default_rng(810)
for case in range(100):
    train = [[0], [1], [0]]
    vocab = [rng.choice(4, size=int(rng.integers(1, 4)), replace=False).tolist() for _ in train]
    truth = [rng.integers(0, 3, size=1).tolist() for _ in train]
    counts = count_folds(train, truth, vocab)
    y = list(itertools.chain.from_iterable(truth))
    for convention in ['support', 'union']:
        labels = np.unique(y) if convention == 'support' else None
        brute = max(f1_score(y, pred, labels=labels, average='macro', zero_division=0)
                    for pred in itertools.product(*vocab))
        for method in ['enumerate', 'branch']:
            found = exact_oracle(counts, method=method, convention=convention)['exact_oracle']
            assert abs(found - brute) < 1e-12, (case, convention, method, found, brute)
        if convention == 'union':
            assert brute <= union_ceiling(counts) + 1e-12
        else:
            sandwich = oracle_sandwich(counts)
            assert sandwich['sandwich_lower'] - 1e-12 <= brute <= sandwich['sandwich_upper'] + 1e-12
assert coverage_ceiling([[0]], [[0, 1]]) < 1
assert coverage_ceiling([[0]], [[0, 1]], [[0, 1]]) == 1
rows = []
for fold in range(300):
    vocab = [(0,), (1,), (0, 1)][fold % 3]
    for k in range(3):
        rows.append(dict(fold=fold, **{'class': k}, training_rows=int(k in vocab), test_rows=1))
result = exact_oracle(pd.DataFrame(rows), max_choices=10)
assert result['vocabulary_types'] == 3 and result['grouped_assignments'] == 2
assert result['vertex_assignments'] == 2 ** 100
print('100 explicit-head brute-force cases passed; 300 folds reduced to two assignments')
