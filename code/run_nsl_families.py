"""Fit the prespecified natural-split pipeline comparison."""
import argparse
import hashlib
import json
from pathlib import Path
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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('data',type=Path)
parser.add_argument('out',type=Path)
args = parser.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
signature={f'KDD{part}+.txt':hashlib.sha256((args.data/f'KDD{part}+.txt').read_bytes()).hexdigest()
           for part in ['Train','Test']}
manifest=args.out/'input_sha256.json'
if manifest.exists() and json.loads(manifest.read_text())!=signature:
    raise ValueError('Input files differ from the cached NSL fits')
manifest.write_text(json.dumps(signature,indent=2)+'\n')
train,test = [pd.read_csv(args.data/f'KDD{part}+.txt',header=None) for part in ['Train','Test']]
y = test[41].to_numpy()
seen = np.isin(y,train[41].unique())
labels = sorted(set(y)|set(train[41]))
models = {
    'extra_trees':ExtraTreesClassifier(n_estimators=200,min_samples_leaf=2,min_samples_split=5,random_state=42,n_jobs=2),
    'decision_tree':DecisionTreeClassifier(min_samples_leaf=2,min_samples_split=5,random_state=42),
    'gaussian_nb':GaussianNB(),
    'sgd_logistic':SGDClassifier(loss='log_loss',alpha=.0001,max_iter=1000,tol=.001,random_state=42),
    'knn':KNeighborsClassifier(n_neighbors=5,weights='uniform',n_jobs=2),
}
records=[]
for name,estimator in models.items():
    path=args.out/f'{name}.npz'
    if path.exists():
        saved=np.load(path,allow_pickle=False)
        covered,unavailable=saved['covered'],saved['unavailable']
        timing=json.loads((args.out/f'{name}_fit.json').read_text())
    else:
        pre=ColumnTransformer([
            ('category',OneHotEncoder(handle_unknown='ignore',sparse_output=False),[1,2,3]),
            ('numeric',StandardScaler(),[i for i in range(41) if i not in [1,2,3]])])
        model=make_pipeline(pre,estimator)
        start=perf_counter()
        with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=2):
            warnings.simplefilter('always')
            model.fit(train.iloc[:,:41],train[41])
            pred=model.predict(test.iloc[:,:41])
        assert set(pred)<=set(train[41]) and not np.any(pred[~seen]==y[~seen])
        covered=confusion_matrix(y[seen],pred[seen],labels=labels)
        unavailable=confusion_matrix(y[~seen],pred[~seen],labels=labels)
        timing=dict(seconds=perf_counter()-start,parameters=estimator.get_params(),
                    warnings=[str(w.message) for w in caught])
        (args.out/f'{name}_fit.json').write_text(json.dumps(timing,indent=2))
        np.savez_compressed(path,labels=np.asarray(labels),covered=covered,unavailable=unavailable)
    def macro(cm):
        n=cm.sum(axis=1)
        d=n+cm.sum(axis=0)
        f=np.divide(2*np.diag(cm),d,out=np.zeros(len(n)),where=d>0)
        return float(f[n>0].mean())
    record=dict(model=name,seed=42,full_macro_f1=macro(covered+unavailable),
                covered_macro_f1=macro(covered),covered_rows=int(covered.sum()),
                unavailable_rows=int(unavailable.sum()),fit_seconds=timing['seconds'])
    records.append(record)
    pd.DataFrame(records).to_csv(args.out/'models.csv',index=False)
    print(record,flush=True)
