"""Independently reconstruct RT-IoT scores and validate saved memberships."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def macro(truth, prediction, labels):
    terms = []
    for label in labels:
        tp = int(np.sum((truth == label) & (prediction == label)))
        denom = int(np.sum(truth == label) + np.sum(prediction == label))
        terms.append(2 * tp / denom if denom else 0.)
    return sum(terms) / len(terms)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path)
    args = parser.parse_args()
    out = ROOT / 'results/continuation_20261115/rt_iot'
    split = np.load(out / 'split.npz')
    runs = pd.read_csv(out / 'runs.csv')
    assert len(runs) == 30 and not runs.duplicated(['withheld', 'seed']).any()
    mapping = pd.read_csv(out / 'label_mapping.csv').set_index('class').binary.to_dict()
    groups, y = split['feature_groups'], split['true_labels']
    tr, te = split['training_source_rows'], split['test_source_rows']
    assert len(tr) == 92056 and len(te) == 31061
    assert set(tr).isdisjoint(te) and len(set(tr) | set(te)) == len(y) == 123117
    assert set(groups[tr]).isdisjoint(groups[te])
    if args.data:
        import hashlib
        manifest = json.loads((out / 'manifest.json').read_text())
        assert hashlib.sha256(args.data.read_bytes()).hexdigest() == manifest['csv_sha256']
        raw = pd.read_csv(args.data)
        features = raw.drop(columns=manifest['dropped_columns'])
        assert np.array_equal(pd.util.hash_pandas_object(features, index=False), groups)
        assert len(features.drop_duplicates()) == len(np.unique(groups)) == 18272
        assert np.array_equal(raw.Attack_type.astype(str), y)
        from sklearn.model_selection import StratifiedGroupKFold
        expected_tr, expected_te = next(StratifiedGroupKFold(n_splits=5, shuffle=True,
            random_state=20261115).split(features, y, groups))
        assert np.array_equal(tr, expected_tr) and np.array_equal(te, expected_te)
    base = {}
    for row in runs.itertuples():
        saved = np.load(out / f'{row.withheld}_{row.seed}.npz')
        ids = saved['fit_source_rows']
        assert np.array_equal(saved['test_source_rows'], te)
        assert np.array_equal(saved['truth'], y[te])
        assert set(ids).issubset(tr) and len(set(ids)) == len(ids)
        if row.withheld == 'NONE':
            base[row.seed] = ids
            rng = np.random.default_rng(row.seed)
            expected_cap = np.concatenate([rng.choice(tr[y[tr] == k],
                size=min(1000, sum(y[tr] == k)), replace=False) for k in sorted(set(y))])
            assert np.array_equal(ids, expected_cap)
        expected = base[row.seed] if row.withheld == 'NONE' else base[row.seed][y[base[row.seed]] != row.withheld]
        assert np.array_equal(ids, expected)
        assert max(np.unique(y[ids], return_counts=True)[1]) <= 1000
        assert set(saved['fine_prediction']).issubset(set(y[ids]))
        expected_binary = np.array([mapping[k] for k in y[te]])
        assert np.array_equal(saved['binary_truth'], expected_binary)
        assert set(saved['binary_prediction']).issubset({mapping[k] for k in y[ids]})
        for target, labels in [('fine', saved['labels']), ('binary', ['BENIGN', 'ATTACK'])]:
            truth = saved['truth'] if target == 'fine' else saved['binary_truth']
            pred = saved[target + '_prediction']
            score = macro(truth, pred, labels)
            assert abs(score - getattr(row, target + '_macro_f1')) < 1e-12
            matrix = np.array([[np.sum((truth == a) & (pred == b)) for b in labels] for a in labels])
            assert np.array_equal(matrix, saved[target + '_confusion'])
        projected = np.array([mapping[k] for k in saved['fine_prediction']])
        assert abs(macro(saved['binary_truth'], projected, ['BENIGN', 'ATTACK']) - row.projected_binary_macro_f1) < 1e-12
        for name, predictions in [('projected', projected), ('binary', saved['binary_prediction'])]:
            recall = np.mean(predictions[expected_binary == 'ATTACK'] == 'ATTACK')
            assert abs(recall - getattr(row, name + '_attack_recall')) < 1e-12
            if row.withheld != 'NONE':
                withheld_recall = np.mean(predictions[y[te] == row.withheld] == 'ATTACK')
                assert abs(withheld_recall - getattr(row, name + '_withheld_alarm_recall')) < 1e-12
        # One-fold exact oracle: repair all legal rows, then enumerate every legal destination.
        labels = saved['labels']
        n = np.array([sum(y[te] == k) for k in labels], dtype=float)
        m = n * np.array([k in set(y[ids]) for k in labels])
        u = sum(n - m)
        scores = []
        for dest in np.where(m > 0)[0]:
            fp = np.zeros(len(n)); fp[dest] = u
            scores.append(float(np.mean(2*m/(n+m+fp))))
        oracle = max(scores)
        assert abs(oracle - row.exact_oracle) < 1e-12
        assert abs(float(np.mean(2*m/(n+m))) - row.coverage_ceiling) < 1e-12
        assert row.fine_macro_f1 <= oracle + 1e-12
    report = {'prediction_vectors_verified': 60, 'confusion_matrices_verified': 60,
              'matched_conditions_verified': 30, 'independent_oracle_checks': 30,
              'raw_feature_groups_verified': bool(args.data), 'status': 'passed'}
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
