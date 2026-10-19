"""Demonstrate fractional label coverage on the bundled handwritten digits benchmark."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_digits
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold

from label_coverage_bound import coverage_bound

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("out", type=Path)
args = parser.parse_args()
X, y = load_digits(return_X_y=True)
splitter = StratifiedKFold(5, shuffle=True, random_state=42)
fold = np.full(len(y), -1)
pred = np.full(len(y), -1)
records = []
for i, (train, test) in enumerate(splitter.split(X, y)):
    if i < 2:
        train = train[~np.isin(y[train], [0, 1])]
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X[train], y[train])
    pred[test] = model.predict(X[test])
    fold[test] = i
    for label in range(10):
        records.append({"fold": i, "class": label, "training_rows": int((y[train] == label).sum()),
                        "test_rows": int((y[test] == label).sum())})
assert (fold >= 0).all()
counts = pd.DataFrame(records)
classes, ceiling = coverage_bound(counts)
score = f1_score(y, pred, labels=np.arange(10), average="macro")
assert score <= ceiling
args.out.mkdir(parents=True, exist_ok=False)
counts.to_csv(args.out / "fold_label_counts.csv", index=False)
classes.to_csv(args.out / "coverage_by_class.csv")
pd.DataFrame({"row": np.arange(len(y)), "test_fold": fold}).to_csv(args.out / "test_membership.csv", index=False)
pd.DataFrame(confusion_matrix(y, pred), index=range(10), columns=range(10)).to_csv(args.out / "confusion.csv")
pd.DataFrame([{"test_rows":len(y),"ceiling":ceiling,"macro_f1":score}]).to_csv(args.out / "metrics.csv", index=False)
print(ceiling, score)

