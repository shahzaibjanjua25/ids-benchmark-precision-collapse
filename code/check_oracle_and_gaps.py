"""Rebuild the three-part gaps and check the exact oracle on small cases."""
import argparse
import itertools
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from exact_fold_oracle import oracle

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results",type=Path)
args = parser.parse_args()
root=args.results
summary=pd.read_csv(root/"unsw_coverage_sensitivity/summary.csv")
parts=pd.DataFrame({
    "withheld":summary.withheld, "coverage_ceiling":.8, "oracle":summary.oracle_ceiling,
    "observed":summary["mean"], "minimum_vocabulary_penalty":.8-summary.oracle_ceiling,
    "destination_loss":summary.oracle_ceiling-(summary["mean"]+summary.covered),
    "covered_row_gain":summary.covered,
})
assert np.allclose(parts.iloc[:,-3:].sum(axis=1),parts.coverage_ceiling-parts.observed,atol=1e-12,rtol=0)
parts.to_csv(root/"unsw_three_part_gap.csv",index=False)
examples={
    "partial": [([0,1,2,2],[0,1]),([0,1,1,2],[1,2])],
    "train_only": [([0,1,1],[0,2])],
    "full": [([0,1,1],[0,1])],
    "all_destinations_cost": [([0,0,1,2],[0,1])],
}
for name, folds in examples.items():
    labels=sorted(set(k for y,_ in folds for k in y))
    truth=[k for y,_ in folds for k in y]
    counts=pd.DataFrame([{"fold":i,"class":k,"training_rows":int(k in vocab),"test_rows":y.count(k)}
                         for i,(y,vocab) in enumerate(folds) for k in sorted(set(y)|set(vocab))])
    brute=max(f1_score(truth,p,labels=labels,average="macro",zero_division=0)
              for p in itertools.product(*(vocab for y,vocab in folds for _ in y)))
    result=oracle(counts)
    assert abs(brute-result["exact_oracle"])<1e-12,name
    print(name,brute)

