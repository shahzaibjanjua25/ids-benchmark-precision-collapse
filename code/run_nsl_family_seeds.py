"""Fit prespecified NSL-KDD pipelines over the declared seed set."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from time import perf_counter
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import confusion_matrix
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits

SEEDS = (42, 43, 44, 45, 46)
DETERMINISTIC = {"gaussian_nb", "knn"}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("data", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
seed_dir = args.out / "by_seed"
seed_dir.mkdir(exist_ok=True)
signature = {
    f"KDD{part}+.txt": hashlib.sha256((args.data / f"KDD{part}+.txt").read_bytes()).hexdigest()
    for part in ("Train", "Test")
}
manifest = args.out / "input_sha256.json"
if manifest.exists() and json.loads(manifest.read_text()) != signature:
    raise ValueError("Input files differ from the cached NSL fits")
manifest.write_text(json.dumps(signature, indent=2) + "\n")
train, test = [pd.read_csv(args.data / f"KDD{part}+.txt", header=None) for part in ("Train", "Test")]
y = test[41].to_numpy()
seen = np.isin(y, train[41].unique())
labels = np.asarray(sorted(set(y) | set(train[41])))
models = {
    "extra_trees": lambda seed: ExtraTreesClassifier(n_estimators=200, min_samples_leaf=2, min_samples_split=5, random_state=seed, n_jobs=2),
    "decision_tree": lambda seed: DecisionTreeClassifier(min_samples_leaf=2, min_samples_split=5, random_state=seed),
    "gaussian_nb": lambda seed: GaussianNB(),
    "sgd_logistic": lambda seed: SGDClassifier(loss="log_loss", alpha=.0001, max_iter=1000, tol=.001, random_state=seed),
    "knn": lambda seed: KNeighborsClassifier(n_neighbors=5, weights="uniform", n_jobs=2),
}

def macro(cm):
    support = cm.sum(axis=1)
    denom = support + cm.sum(axis=0)
    f1 = np.divide(2 * np.diag(cm), denom, out=np.zeros(len(support)), where=denom > 0)
    return float(f1[support > 0].mean())

def union_macro(cm):
    support = cm.sum(axis=1)
    predicted = cm.sum(axis=0)
    denom = support + predicted
    f1 = np.divide(2 * np.diag(cm), denom, out=np.zeros(len(support)), where=denom > 0)
    return float(f1[denom > 0].mean())

records = []
for name, factory in models.items():
    for seed in SEEDS:
        path = seed_dir / f"{name}_{seed}.npz"
        if seed == 42 and not path.exists() and (args.out / f"{name}.npz").exists():
            shutil.copy2(args.out / f"{name}.npz", path)
            shutil.copy2(args.out / f"{name}_fit.json", seed_dir / f"{name}_{seed}_fit.json")
        if name in DETERMINISTIC and seed != 42 and not path.exists():
            shutil.copy2(seed_dir / f"{name}_42.npz", path)
            source = json.loads((seed_dir / f"{name}_42_fit.json").read_text())
            source.update(seed=seed, source_seed=42, seconds=0.0,
                          reused_deterministic_predictions=True)
            (seed_dir / f"{name}_{seed}_fit.json").write_text(json.dumps(source, indent=2) + "\n")
        if name == "knn" and seed != 42 and path.exists():
            meta_path = seed_dir / f"{name}_{seed}_fit.json"
            meta = json.loads(meta_path.read_text())
            if not meta.get("reused_deterministic_predictions", False):
                meta.update(seed=seed, source_seed=42, seconds=0.0,
                            reused_deterministic_predictions=True)
                meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        if not path.exists():
            estimator = factory(seed)
            pre = ColumnTransformer([
                ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), [1, 2, 3]),
                ("numeric", StandardScaler(), [i for i in range(41) if i not in [1, 2, 3]]),
            ])
            model = make_pipeline(pre, estimator)
            start = perf_counter()
            with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=2):
                warnings.simplefilter("always")
                model.fit(train.iloc[:, :41], train[41])
                pred = model.predict(test.iloc[:, :41])
            assert set(pred) <= set(train[41]) and not np.any(pred[~seen] == y[~seen])
            covered = confusion_matrix(y[seen], pred[seen], labels=labels)
            unavailable = confusion_matrix(y[~seen], pred[~seen], labels=labels)
            np.savez_compressed(path, labels=labels, covered=covered, unavailable=unavailable)
            (seed_dir / f"{name}_{seed}_fit.json").write_text(json.dumps({
                "seed": seed, "seconds": perf_counter() - start,
                "parameters": estimator.get_params(),
                "warnings": [str(w.message) for w in caught],
            }, indent=2) + "\n")
        saved = np.load(path, allow_pickle=False)
        covered, unavailable = saved["covered"], saved["unavailable"]
        records.append({
            "model": name, "seed": seed,
            "full_macro_f1": macro(covered + unavailable),
            "covered_macro_f1": macro(covered),
            "full_union_macro_f1": union_macro(covered + unavailable),
            "covered_union_macro_f1": union_macro(covered),
            "covered_rows": int(covered.sum()),
            "unavailable_rows": int(unavailable.sum()),
            "fit_seconds": json.loads((seed_dir / f"{name}_{seed}_fit.json").read_text())["seconds"],
        })
        pd.DataFrame(records).to_csv(args.out / "seed_metrics.csv", index=False)
        print(records[-1], flush=True)

summary = pd.DataFrame(records).groupby("model", as_index=False).agg(
    full_mean=("full_macro_f1", "mean"), full_sd=("full_macro_f1", "std"),
    full_min=("full_macro_f1", "min"), full_max=("full_macro_f1", "max"),
    covered_mean=("covered_macro_f1", "mean"), covered_sd=("covered_macro_f1", "std"),
    covered_min=("covered_macro_f1", "min"), covered_max=("covered_macro_f1", "max"),
    full_union_mean=("full_union_macro_f1", "mean"), full_union_sd=("full_union_macro_f1", "std"),
    covered_union_mean=("covered_union_macro_f1", "mean"), covered_union_sd=("covered_union_macro_f1", "std"),
    seeds=("seed", "count"),
)
summary.to_csv(args.out / "seed_summary.csv", index=False)
print(summary.to_string(index=False), flush=True)
