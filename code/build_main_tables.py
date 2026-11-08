"""Export manuscript tables from saved counts and predictions, without refitting."""
import argparse
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from label_availability import exact_oracle

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--partial',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
r=root/'results'
out=r/'manuscript_tables'
out.mkdir(exist_ok=True)
command=[sys.executable,str(root/'code/summarize_rank_audit.py')]
if args.partial: command.append('--partial')
subprocess.run(command,check=True)
nsl=pd.read_csv(r/'rank_audit/nsl_ranks.csv')
nsl.to_csv(out/'table_1_nsl_seed_rankings.csv',index=False)
natural=[
    dict(case='NSL original forest',coverage_ceiling=21/38,oracle=21/38,observed=nsl.loc[nsl.seed.eq(42),'full_macro_f1'].item()),
    dict(case='CIC day forest',coverage_ceiling=1/15,oracle=1/15,observed=np.nan),
    dict(case='Gas forest',coverage_ceiling=np.nan,oracle=np.nan,observed=np.nan),
    dict(case='Gas logistic',coverage_ceiling=np.nan,oracle=np.nan,observed=np.nan),
]
# Read fitted values instead of trusting display precision.
cic=pd.read_csv(r/'cic_full_replication.csv')
row=cic.query("protocol == 'lodo' and arm == 'none'").iloc[0]
natural[1]['observed']=row.macro_f1
gas=pd.read_csv(r/'gas_model_comparison/models.csv')
for i,name in [(2,'forest'),(3,'logistic')]:
    natural[i]['observed']=gas.loc[gas.model.eq(name)&gas.seed.eq(42),'macro_f1'].item()
    counts=pd.read_csv(r/'gas_drift_adjacent/fold_label_counts.csv')
    oracle=exact_oracle(counts)
    natural[i]['coverage_ceiling']=oracle['coverage_ceiling']
    natural[i]['oracle']=oracle['exact_oracle']
pd.DataFrame(natural).to_csv(out/'table_3_natural_protocols.csv',index=False)
families=pd.read_csv(r/'nsl_families/models.csv')
if not args.partial: assert len(families)==5
base=nsl.loc[nsl.seed.eq(42)].assign(model='forest')
families=pd.concat([base,families],ignore_index=True)
families['full_rank']=families.full_macro_f1.rank(ascending=False)
families['covered_rank']=families.covered_macro_f1.rank(ascending=False)
routes=pd.read_csv(r/'nsl_destination_audit/scores.csv')
families=families.merge(routes[['model','routed_support_f1','routed_union_f1']],on='model',validate='one_to_one')
families.to_csv(out/'table_2_nsl_families.csv',index=False)
for name in ['table_2_natural_protocols.csv','table_3_nsl_families.csv']:
    path=out/name
    if path.exists(): path.unlink()
print('Saved main manuscript tables to',out)
