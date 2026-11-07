"""Compare model families on the same adjacent-batch cohorts."""
import argparse
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.datasets import load_svmlight_file
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("archive", type=Path)
parser.add_argument("out", type=Path)
parser.add_argument("--models", nargs="+", default=["forest", "logistic", "svm", "knn", "mlp", "hist_gradient_boosting", "coral_logistic"],
                    choices=["forest", "logistic", "svm", "knn", "mlp", "hist_gradient_boosting", "coral_logistic"])
args = parser.parse_args()
args.out.mkdir(exist_ok=True)
with ZipFile(args.archive) as archive:
    names = {Path(name).name: name for name in archive.namelist()}
    batches = []
    for i in range(1, 11):
        with archive.open(names[f"batch{i}.dat"]) as stream:
            X, y = load_svmlight_file(stream, n_features=128)
            batches.append((X.toarray(), y.astype(int)))
rows, fold_rows = [], []
labels = np.arange(1, 7)
for name in args.models:
    seeds = range(42, 47) if name in {"forest", "mlp", "hist_gradient_boosting"} else [42]
    for seed in seeds:
        matrices, covered_matrices = [], []
        for fold in range(1, 10):
            X, y = batches[fold - 1]
            Xt, yt = batches[fold]
            if name == "coral_logistic":
                scaler = StandardScaler().fit(X)
                X = scaler.transform(X)
                Xt = scaler.transform(Xt)
                Xt = Xt - Xt.mean(axis=0)
                def covariance_power(data, exponent):
                    covariance = np.cov(data, rowvar=False) + np.eye(data.shape[1])
                    values, vectors = np.linalg.eigh(covariance)
                    return (vectors * values ** exponent) @ vectors.T
                X = X @ covariance_power(X, -.5) @ covariance_power(Xt, .5)
            factories = {
                "forest": lambda: RandomForestClassifier(n_estimators=200, min_samples_leaf=2, random_state=seed, n_jobs=4),
                "logistic": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, random_state=seed)),
                "svm": lambda: make_pipeline(StandardScaler(), SVC(C=1, gamma="scale")),
                "knn": lambda: make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
                "mlp": lambda: make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(64,), max_iter=500, random_state=seed)),
                "hist_gradient_boosting": lambda: HistGradientBoostingClassifier(max_iter=100, random_state=seed),
                "coral_logistic": lambda: LogisticRegression(max_iter=3000, random_state=seed)}
            model = factories[name]()
            with threadpool_limits(limits=4):
                model.fit(X, y)
                pred = model.predict(Xt)
            seen = np.isin(yt, np.unique(y))
            cm = confusion_matrix(yt, pred, labels=labels)
            matrices.append(cm)
            covered_matrices.append(confusion_matrix(yt[seen], pred[seen], labels=labels))
            fold_rows.append({"model": name, "seed": seed, "test_batch": fold + 1,
                              "test_rows": len(yt), "accuracy": float((pred == yt).mean()),
                              "macro_f1": f1_score(yt, pred, labels=np.unique(yt), average="macro", zero_division=0)})
        def macro(matrix):
            denominator = matrix.sum(axis=0) + matrix.sum(axis=1)
            return float(np.divide(2 * np.diag(matrix), denominator, out=np.zeros(6), where=denominator > 0).mean())
        pooled = sum(matrices)
        # Fixed-cohort row bootstrap is conditional on these batches and predictions.
        rng = np.random.default_rng(20261108)
        draws = rng.multinomial(int(pooled.sum()), pooled.ravel() / pooled.sum(), size=500)
        scores = [macro(draw.reshape(6, 6)) for draw in draws]
        rows.append({"model": name, "seed": seed, "macro_f1": macro(pooled),
                     "covered_only_macro_f1": macro(sum(covered_matrices)),
                     "row_bootstrap_low": float(np.quantile(scores, .025)),
                     "row_bootstrap_high": float(np.quantile(scores, .975))})
        pd.DataFrame(rows).to_csv(args.out / "models.csv", index=False)
        pd.DataFrame(fold_rows).to_csv(args.out / "fold_scores.csv", index=False)
        print(rows[-1], flush=True)
