"""Post-hoc routing check on fixed predictions, with no extra true positives."""
from pathlib import Path
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[1]
r=root/'results'
out=r/'nsl_destination_audit'
out.mkdir(exist_ok=True)
def scores(cm):
    n=cm.sum(axis=1)
    pred=cm.sum(axis=0)
    f=np.divide(2*np.diag(cm),n+pred,out=np.zeros(len(n)),where=n+pred>0)
    return float(f[n>0].mean()),float(f.sum()/np.count_nonzero((n+pred)>0))
records=[]
for name in ['forest','extra_trees','decision_tree','gaussian_nb','sgd_logistic','knn']:
    if name=='forest':
        folder=r/'nsl_model_comparison'
        covered=pd.read_csv(folder/'confusion_seen_42.csv',index_col=0)
        unavailable=pd.read_csv(folder/'confusion_unseen_42.csv',index_col=0).to_numpy()
        labels=covered.index.to_numpy(dtype=str)
        covered=covered.to_numpy()
    else:
        saved=np.load(r/'nsl_families'/(name+'.npz'),allow_pickle=False)
        covered,unavailable,labels=saved['covered'],saved['unavailable'],saved['labels']
    full=covered+unavailable
    outside=np.flatnonzero(full.sum(axis=1)==0)
    # Pick the first legal train-only label in sorted order, not the best score.
    dest=int(outside[0])
    routed=covered.copy()
    routed[:,dest]+=unavailable.sum(axis=1)
    np.testing.assert_array_equal(full.sum(axis=1),routed.sum(axis=1))
    np.testing.assert_array_equal(np.diag(full),np.diag(routed))
    assert np.trace(unavailable)==0
    a,b=scores(full)
    c,d=scores(routed)
    np.savez_compressed(out/(name+'.npz'),labels=labels,original=full,rerouted=routed)
    records.append(dict(model=name,destination=labels[dest],original_support_f1=a,
                        routed_support_f1=c,original_union_f1=b,routed_union_f1=d,
                        true_positives_before=int(np.trace(full)),true_positives_after=int(np.trace(routed))))
pd.DataFrame(records).to_csv(out/'scores.csv',index=False)
print(pd.DataFrame(records).to_string(index=False))
