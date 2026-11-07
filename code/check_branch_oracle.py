"""Compare the two oracle solvers and record a repeated-vocabulary stress case."""
import argparse
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from exact_fold_oracle import oracle

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("results",type=Path)
args=parser.parse_args()
p=args.results
rng=np.random.default_rng(42)
for _ in range(100):
    rows=[]
    for fold in range(4):
        train=rng.integers(0,2,4)
        train[0]=1
        for k in range(4):
            rows.append(dict(fold=fold,**{"class":k},training_rows=train[k],test_rows=int(rng.integers(1,5))))
    counts=pd.DataFrame(rows)
    exact=oracle(counts)
    branch=oracle(counts,method="branch")
    np.testing.assert_allclose(branch["exact_oracle"],exact["exact_oracle"],rtol=0,atol=1e-12)
gas=pd.read_csv(p/"gas_drift_adjacent/fold_label_counts.csv")
digits=pd.read_csv(p/"digits_fractional_coverage/fold_label_counts.csv")
stress=pd.DataFrame([dict(fold=0,**{"class":k},training_rows=1,test_rows=20) for k in range(3)]+[
    dict(fold=f,**{"class":k},training_rows=int(k<3),test_rows=10 if k==3 else 0)
    for f in range(1,21) for k in range(4)])
rows=[]
for name, counts in [("gas",gas),("digits",digits),("repeated_vocabulary_synthetic",stress)]:
    for method in (["enumerate","branch"] if name!="repeated_vocabulary_synthetic" else ["branch"]):
        start=perf_counter()
        result=oracle(counts,method=method)
        rows.append(dict(case=name,method=method,**result,runtime_seconds=perf_counter()-start))
pd.DataFrame(rows).to_csv(p/"oracle_solver_checks.csv",index=False)
print(pd.DataFrame(rows).to_string(index=False))

