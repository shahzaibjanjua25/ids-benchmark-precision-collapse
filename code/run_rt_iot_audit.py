"""Execute the prespecified grouped RT-IoT2022 vocabulary/target experiment."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, f1_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from label_availability import count_folds, certified_oracle

BENIGN = {'Thing_Speak', 'MQTT_Publish', 'Wipro_bulb'}
DROP = ['Unnamed: 0', 'Attack_type', 'id.orig_p', 'id.resp_p']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error('out must be new or empty')
    args.out.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(args.data)
    assert d.shape == (123117, 85)
    X, y = d.drop(columns=DROP), d.Attack_type.astype(str).to_numpy(dtype=str)
    assert BENIGN.issubset(set(y)) and len(set(y)) == 12 and len(X.columns) == 81
    groups = pd.util.hash_pandas_object(X, index=False).to_numpy()
    assert len(np.unique(groups)) == len(X.drop_duplicates())
    tr, te = next(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20261115).split(X, y, groups))
    assert len(te) == 31061 and len(tr) == 92056
    assert not set(groups[tr]) & set(groups[te])
    assert set(y[te]) == set(y[tr]) == set(y)
    labels = sorted(set(y))
    mapping = {label: 'BENIGN' if label in BENIGN else 'ATTACK' for label in labels}
    binary_y = np.array([mapping[label] for label in y])
    cat = X.select_dtypes(include=['object', 'str']).columns.tolist()
    num = [c for c in X if c not in cat]
    X[num] = X[num].replace([np.inf, -np.inf], np.nan)
    def model(seed):
        prep = ColumnTransformer([
            ('numeric', SimpleImputer(strategy='median'), num),
            ('categorical', make_pipeline(SimpleImputer(strategy='most_frequent'),
                                          OneHotEncoder(handle_unknown='ignore')), cat)])
        return make_pipeline(prep, ExtraTreesClassifier(n_estimators=100, min_samples_leaf=2,
                                                        random_state=seed, n_jobs=4))
    np.savez_compressed(args.out / 'split.npz', training_source_rows=tr, test_source_rows=te,
                        feature_groups=groups, true_labels=y, binary_labels=binary_y)
    pd.DataFrame({'class': labels, 'binary': [mapping[k] for k in labels]}).to_csv(args.out / 'label_mapping.csv', index=False)
    cases = ['NONE'] + sorted(set(y) - BENIGN)
    runs, certificates, counts_parts = [], {}, []
    for seed in [42, 43, 44]:
        rng = np.random.default_rng(seed)
        capped = np.concatenate([rng.choice(tr[y[tr] == k], size=min(1000, sum(y[tr] == k)), replace=False)
                                 for k in labels])
        for withheld in cases:
            fit_ids = capped if withheld == 'NONE' else capped[y[capped] != withheld]
            assert not set(groups[fit_ids]) & set(groups[te])
            vocab = set(y[fit_ids])
            key = f'{withheld}_{seed}'
            counts = count_folds([y[fit_ids]], [y[te]])
            if seed == 42:
                counts_parts.append(counts.assign(condition=withheld))
                certificates[withheld] = certified_oracle(counts)
            result = {'withheld': withheld, 'seed': seed, 'fit_rows': len(fit_ids),
                      'test_rows': len(te), 'coverage_ceiling': certificates[withheld]['coverage_ceiling'],
                      'exact_oracle': certificates[withheld]['exact_oracle']}
            outputs = {}
            for target, training_labels in [('fine', y), ('binary', binary_y)]:
                estimator = model(seed)
                start = time.perf_counter()
                estimator.fit(X.iloc[fit_ids], training_labels[fit_ids])
                pred = estimator.predict(X.iloc[te]).astype(str)
                result[target + '_fit_predict_seconds'] = time.perf_counter() - start
                outputs[target] = pred
                scored = labels if target == 'fine' else ['BENIGN', 'ATTACK']
                assert set(pred).issubset(set(training_labels[fit_ids]))
                if target == 'fine' and withheld != 'NONE':
                    assert not (pred[y[te] == withheld] == withheld).any()
                result[target + '_macro_f1'] = f1_score(training_labels[te], pred, labels=scored,
                                                        average='macro', zero_division=0)
            projected = np.array([mapping[k] for k in outputs['fine']])
            result['projected_binary_macro_f1'] = f1_score(binary_y[te], projected, average='macro', zero_division=0)
            for name, predictions in [('projected', projected), ('binary', outputs['binary'])]:
                result[name + '_attack_recall'] = recall_score(binary_y[te], predictions, pos_label='ATTACK')
                if withheld != 'NONE':
                    result[name + '_withheld_alarm_recall'] = float(np.mean(predictions[y[te] == withheld] == 'ATTACK'))
            assert result['fine_macro_f1'] <= result['exact_oracle'] + 1e-12
            np.savez_compressed(args.out / (key + '.npz'), truth=y[te], fine_prediction=outputs['fine'],
                                binary_truth=binary_y[te], binary_prediction=outputs['binary'],
                                fine_confusion=confusion_matrix(y[te], outputs['fine'], labels=labels),
                                binary_confusion=confusion_matrix(binary_y[te], outputs['binary'], labels=['BENIGN','ATTACK']),
                                labels=np.array(labels), fit_source_rows=fit_ids, test_source_rows=te)
            runs.append(result)
            pd.DataFrame(runs).to_csv(args.out / 'runs.csv', index=False)
            print({k: result[k] for k in ['withheld','seed','fine_macro_f1','binary_macro_f1','exact_oracle']}, flush=True)
    pd.concat(counts_parts, ignore_index=True).to_csv(args.out / 'count_audit.csv', index=False)
    (args.out / 'oracle_certificates.json').write_text(json.dumps(certificates, indent=2), encoding='utf8')
    pd.DataFrame(runs).groupby('withheld', sort=False).agg({k:['mean','std'] for k in
        ['fine_macro_f1','binary_macro_f1','projected_binary_macro_f1','projected_attack_recall','binary_attack_recall']}).to_csv(args.out / 'summary.csv')
    (args.out / 'manifest.json').write_text(json.dumps({
        'source_url': 'https://archive.ics.uci.edu/static/public/942/rt-iot2022.zip',
        'source_doi': '10.24432/C5P338', 'license': 'CC BY 4.0',
        'csv_sha256': hashlib.sha256(args.data.read_bytes()).hexdigest(), 'rows': len(y),
        'unique_feature_groups': len(np.unique(groups)), 'input_features': X.columns.tolist(),
        'dropped_columns': DROP, 'categorical_features': cat,
        'group_seed': 20261115, 'group_folds': 5, 'evaluated_fold': 0,
        'training_pool_rows':len(tr), 'test_rows':len(te), 'seed_values':[42,43,44],
        'condition_count':len(cases), 'actual_fits':len(runs)*2,
        'training_cap_per_fine_class':1000, 'no_exact_feature_overlap':True,
        'protocol': 'one exact-feature-group holdout, exhaustive single-attack-label withholding; no chronology claim',
        'uncertainty': 'seed SD includes capped training sampling and fitting on one fixed dependent test cohort'
    }, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
