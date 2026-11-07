"""Fit a closed-set forest on the published NSL-KDD partition."""
import argparse
from pathlib import Path
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("data", type=Path)
parser.add_argument("out", type=Path)
parser.add_argument("--seeds", nargs="+", type=int, default=[42])
args = parser.parse_args()
train, test = [pd.read_csv(args.data / f"KDD{part}+.txt", header=None)
               for part in ("Train","Test")]
records = []
for seed in args.seeds:
    model = make_pipeline(
        ColumnTransformer([("category", OneHotEncoder(handle_unknown="ignore"), [1,2,3])], remainder="passthrough"),
        RandomForestClassifier(n_estimators=200, min_samples_leaf=2, min_samples_split=5, random_state=seed, n_jobs=4))
    model.fit(train.iloc[:, :41], train[41])
    pred = model.predict(test.iloc[:, :41])
    labels = sorted(set(test[41]))
    seen = test[41].isin(train[41]).to_numpy()
    correct = test[41].to_numpy() == pred
    assert not correct[~seen].any()
    all_labels = sorted(set(labels) | set(train[41]))
    args.out.mkdir(parents=True, exist_ok=True)
    for name, mask in [("seen",seen),("unseen",~seen)]:
        cm = confusion_matrix(test[41][mask], pred[mask], labels=all_labels)
        filename = f"confusion_{name}.csv" if len(args.seeds) == 1 else f"confusion_{name}_{seed}.csv"
        pd.DataFrame(cm,index=all_labels,columns=all_labels).to_csv(args.out / filename)
    result = pd.DataFrame([{"seed":seed,"trees":200,"macro_f1":f1_score(test[41],pred,labels=labels,average="macro"),
                            "seen_rows":int(seen.sum()),"seen_hits":int(correct[seen].sum()),"unseen_rows":int((~seen).sum()),
                            "unseen_hits":int(correct[~seen].sum())}])
    records.extend(result.to_dict("records"))
    pd.DataFrame(records).to_csv(args.out/"forest_metrics.csv",index=False)
    print(result.to_string(index=False))
