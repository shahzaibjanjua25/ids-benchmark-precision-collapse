"""Check the headline tables and regenerate both figures from released aggregates."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pandas as pd

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("out",type=Path)
args=parser.parse_args()
start=time.perf_counter()
repo=Path(__file__).resolve().parents[1]
r=repo/"results"
args.out.mkdir(parents=True,exist_ok=True)
def run(name,*args):
    subprocess.run([sys.executable,"-B",str(repo/"code"/name),*map(str,args)],check=True)

run("exact_fold_oracle.py",r)
run("check_oracle_and_gaps.py",r)
run("verify_cic_archive.py",r)
run("decompose_cic_lodo.py",r)
run("rebuild_gas_figure.py",r,args.out)
run("plot_unsw_pair_distribution.py",r,args.out)
cic=pd.read_csv(r/"cic_full_replication.csv")
old=pd.read_csv(r/"RESULTS_PARSED.csv").query("dataset == 'cic'")
keys=["dataset","variant","protocol","model","arm","seed"]
metrics=["n_eval","accuracy","macro_f1","weighted_f1"]
assert len(cic)==len(old)==6
np.testing.assert_allclose(cic.set_index(keys)[metrics].sort_index(),old.set_index(keys)[metrics].sort_index(),rtol=0,atol=1e-12)
p=r/"nsl_kdd_official"
seen,unseen=(pd.read_csv(p/f"confusion_{kind}.csv",index_col=0) for kind in ("seen","unseen"))
cm=(seen+unseen).to_numpy()
true=cm.sum(axis=1)
pred=cm.sum(axis=0)
macro=(2*cm.diagonal()[true>0]/(true+pred)[true>0]).mean()
expected=pd.read_csv(p/"forest_metrics.csv").iloc[0]
assert abs(macro-expected.macro_f1)<1e-12
assert (np.trace(seen)==expected.seen_hits and np.trace(unseen)==expected.unseen_hits)
assert len(pd.read_csv(r/"unsw_random_pairs_extra_seeds/combined_100_runs.csv"))==100
print(f"Headline checks passed in {time.perf_counter()-start:.2f}s.")

