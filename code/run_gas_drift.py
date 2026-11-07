"""Audit and fit the published adjacent-batch gas drift protocol."""
import argparse
import hashlib
from pathlib import Path
import time
import tracemalloc
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.datasets import load_svmlight_file
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from exact_fold_oracle import oracle

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("archive", type=Path)
parser.add_argument("out", type=Path)
parser.add_argument("--fit", action="store_true")
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
with ZipFile(args.archive) as archive:
    names = {Path(name).name: name for name in archive.namelist()}
    batches = []
    for i in range(1, 11):
        with archive.open(names[f"batch{i}.dat"]) as stream:
            X, y = load_svmlight_file(stream, n_features=128)
            batches.append((X.toarray(), y.astype(int)))
assert sum(len(y) for _, y in batches) == 13910
labels = np.arange(1, 7)
counts = pd.DataFrame([dict(fold=i+1, **{"class":int(k)}, training_rows=int((batches[i-1][1]==k).sum()),
                            test_rows=int((batches[i][1]==k).sum()))
                       for i in range(1,10) for k in labels])
counts.to_csv(args.out/"fold_label_counts.csv",index=False)
(args.out/"input_sha256.txt").write_text(hashlib.sha256(args.archive.read_bytes()).hexdigest()+"\n",encoding="ascii")
tracemalloc.start()
start = time.perf_counter()
bounds = oracle(counts)
elapsed = time.perf_counter()-start
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
covered = counts.test_rows.where(counts.training_rows.gt(0), 0)
audit = {**bounds, "test_rows":int(counts.test_rows.sum()),"covered_rows":int(covered.sum()),
         "uncovered_folds":int(counts.loc[(counts.training_rows==0)&(counts.test_rows>0),"fold"].nunique()),
         "global_label_fraction":float(counts.groupby("class").training_rows.sum().gt(0).mean()),
         "runtime_seconds":elapsed,"traced_peak_bytes":peak}
pd.DataFrame([audit]).to_csv(args.out/"audit.csv",index=False)
print(audit, flush=True)
if args.fit:
    rows, classes = [], []
    for name in ("forest","logistic"):
        predictions, truth = [], []
        for i in range(1,10):
            X_train,y_train = batches[i-1]
            X_test,y_test = batches[i]
            model = (RandomForestClassifier(n_estimators=200,min_samples_leaf=2,random_state=42,n_jobs=-1)
                     if name=="forest" else make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000,random_state=42)))
            model.fit(X_train,y_train)
            pred=model.predict(X_test)
            predictions.extend(pred)
            truth.extend(y_test)
            cm=confusion_matrix(y_test,pred,labels=labels)
            for j,k in enumerate(labels):
                classes.append(dict(model=name,fold=i+1,**{"class":int(k)}, hits=int(cm[j,j]), test_rows=int(cm[j].sum()), predicted_rows=int(cm[:,j].sum())))
        score=f1_score(truth,predictions,labels=labels,average="macro")
        assert score <= bounds["exact_oracle"]+1e-12
        rows.append(dict(model=name,macro_f1=score,oracle_gap=bounds["exact_oracle"]-score))
    pd.DataFrame(rows).to_csv(args.out/"models.csv",index=False)
    pd.DataFrame(classes).to_csv(args.out/"class_hits_by_fold.csv",index=False)
    print(rows,flush=True)

