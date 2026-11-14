"""Matched-preprocessing fresh NSL refits; no test-driven model selection."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from label_availability import count_folds, certified_oracle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--remove-feature-overlap", action="store_true")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("out must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)
    paths = [args.data / f"KDD{part}+.txt" for part in ["Train", "Test"]]
    train, test = [pd.read_csv(p, header=None) for p in paths]
    source_training_ids = np.arange(len(train))
    assert train.shape == (125973, 43) and test.shape == (22544, 43)
    assert not train.isna().any().any() and not test.isna().any().any()
    train_hash = pd.util.hash_pandas_object(train.iloc[:, :41], index=False)
    test_hash = pd.util.hash_pandas_object(test.iloc[:, :41], index=False)
    # Confirm possible hash collisions by actual feature tuples before counting.
    shared = set(train_hash) & set(test_hash)
    tr = set(map(tuple, train.loc[train_hash.isin(shared), :40].to_numpy()))
    te = set(map(tuple, test.loc[test_hash.isin(shared), :40].to_numpy()))
    feature_overlap = len(tr & te)
    overlap_before = feature_overlap
    original_training_rows = len(train)
    if args.remove_feature_overlap:
        overlap_keys = tr & te
        keep = [tuple(row) not in overlap_keys for row in train.iloc[:, :41].to_numpy()]
        train = train.loc[keep].reset_index(drop=True)
        source_training_ids = source_training_ids[keep]
        train_hash = pd.util.hash_pandas_object(train.iloc[:, :41], index=False)
        assert not (set(train_hash) & set(test_hash))
        feature_overlap = 0
    mapping = pd.read_csv(Path(__file__).resolve().parents[1] / "results/family_mapping.csv")
    mapping = dict(mapping.loc[mapping.dataset.eq("NSL"), ["original", "family"]].itertuples(index=False, name=None))
    labels = sorted(set(train[41]) | set(test[41]))
    support = sorted(set(test[41]))
    counts = count_folds([train[41]], [test[41]])
    counts.to_csv(args.out / "label_counts.csv", index=False)
    np.savez_compressed(args.out / "split_membership.npz", training_source_rows=source_training_ids,
                        test_source_rows=np.arange(len(test)))
    records = []
    for name, cls in [("random_forest", RandomForestClassifier), ("extra_trees", ExtraTreesClassifier)]:
        for seed in [42, 43, 44]:
            model = make_pipeline(
                ColumnTransformer([("category", OneHotEncoder(handle_unknown="ignore"), [1, 2, 3])], remainder="passthrough"),
                cls(n_estimators=200, min_samples_leaf=2, min_samples_split=5, random_state=seed, n_jobs=4))
            model.fit(train.iloc[:, :41], train[41])
            pred = model.predict(test.iloc[:, :41])
            assert set(pred).issubset(set(train[41]))
            y = test[41].to_numpy(dtype=str)
            unavailable = ~test[41].isin(train[41]).to_numpy()
            assert not (pred[unavailable] == y[unavailable]).any()
            coarse_y = [mapping[x] for x in y]
            coarse_p = [mapping[x] for x in pred]
            cm = confusion_matrix(y, pred, labels=labels)
            np.savez_compressed(args.out / f"{name}_{seed}.npz", truth=y,
                                prediction=np.asarray(pred, dtype=str), labels=np.array(labels), confusion=cm)
            records.append({"model": name, "seed": seed,
                            "fine_macro_f1": f1_score(y, pred, labels=support, average="macro", zero_division=0),
                            "union_macro_f1": f1_score(y, pred, average="macro", zero_division=0),
                            "category_macro_f1": f1_score(coarse_y, coarse_p, average="macro", zero_division=0),
                            "unavailable_hits": 0})
            pd.DataFrame(records).to_csv(args.out / "runs.csv", index=False)
            print(records[-1], flush=True)
    pd.DataFrame(records).groupby("model").agg({x: ["mean", "std"] for x in ["fine_macro_f1", "union_macro_f1", "category_macro_f1"]}).to_csv(args.out / "summary.csv")
    (args.out / "manifest.json").write_text(json.dumps({
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "download_mirror": "https://github.com/jmnwong/NSL-KDD-Dataset",
        "training_rows": len(train), "test_rows": len(test), "feature_count": 41,
        "excluded_columns": ["class (41)", "difficulty (42)"],
        "exact_feature_overlap_between_partitions": feature_overlap,
        "original_feature_overlap": overlap_before, "original_training_rows": original_training_rows,
        "removed_training_rows": original_training_rows-len(train),
        "feature_overlap_control": args.remove_feature_overlap,
        "training_duplicate_feature_rows": int(train_hash.duplicated().sum()),
        "test_duplicate_feature_rows": int(test_hash.duplicated().sum()),
        "python": platform.python_version(), "sklearn": sklearn.__version__,
        "seeds": [42, 43, 44], "preprocessing": "train-fitted one-hot nominal; numeric passthrough; same pipeline for both estimators",
        "model_settings": {"trees": 200, "min_samples_leaf": 2, "min_samples_split": 5},
        "oracle_support": certified_oracle(counts), "oracle_union": certified_oracle(counts, "union"),
        "protocol": "official split; no test tuning; fixed models and seeds recorded before execution",
        "uncertainty": "Fit variation on one cohort; no population inference"}, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
