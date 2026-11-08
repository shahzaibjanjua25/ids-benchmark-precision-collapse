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
nsl[['seed','full_macro_f1','covered_macro_f1']].to_csv(out/'table_1_nsl_seed_scores.csv',index=False)
old_seed_table=out/'table_1_nsl_seed_rankings.csv'
if old_seed_table.exists(): old_seed_table.unlink()
natural=[
    dict(case='NSL original forest',coverage_ceiling=21/38,oracle=21/38,
         observed_mean=nsl.full_macro_f1.mean(),observed_sd=nsl.full_macro_f1.std(ddof=1)),
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
for row in natural:
    if 'observed_mean' not in row:
        row['observed_mean']=row.pop('observed')
        row['observed_sd']=np.nan
pd.DataFrame(natural).to_csv(out/'table_3_natural_protocols.csv',index=False)
seeded=pd.read_csv(r/'nsl_families/seed_metrics.csv')
if not args.partial: assert len(seeded)==25
def union_f1(cm):
    support=cm.sum(axis=1); predicted=cm.sum(axis=0)
    den=support+predicted
    f=np.divide(2*np.diag(cm),den,out=np.zeros(len(support)),where=den>0)
    return float(f[den>0].mean())
families=[]
for model,group in seeded.groupby('model'):
    full_union=[]; covered_union=[]
    for seed in [42,43,44,45,46]:
        saved=np.load(r/'nsl_families/by_seed'/f'{model}_{seed}.npz',allow_pickle=False)
        full_union.append(union_f1(saved['covered']+saved['unavailable']))
        covered_union.append(union_f1(saved['covered']))
    row=dict(model=model,seeds=len(group),
             full_mean=group.full_macro_f1.mean(),full_sd=group.full_macro_f1.std(ddof=1),
             full_min=group.full_macro_f1.min(),full_max=group.full_macro_f1.max(),
             covered_mean=group.covered_macro_f1.mean(),covered_sd=group.covered_macro_f1.std(ddof=1),
             covered_min=group.covered_macro_f1.min(),covered_max=group.covered_macro_f1.max(),
             full_union_mean=np.mean(full_union),full_union_sd=np.std(full_union,ddof=1),
             covered_union_mean=np.mean(covered_union),covered_union_sd=np.std(covered_union,ddof=1))
    families.append(row)
forest_full=[]; forest_covered=[]; forest_union=[]; forest_covered_union=[]
for seed in [42,43,44,45,46]:
    seen=pd.read_csv(r/f'nsl_model_comparison/confusion_seen_{seed}.csv',index_col=0).to_numpy()
    unseen=pd.read_csv(r/f'nsl_model_comparison/confusion_unseen_{seed}.csv',index_col=0).to_numpy()
    forest_full.append(float(nsl.loc[nsl.seed.eq(seed),'full_macro_f1'].item()))
    forest_covered.append(float(nsl.loc[nsl.seed.eq(seed),'covered_macro_f1'].item()))
    forest_union.append(union_f1(seen+unseen)); forest_covered_union.append(union_f1(seen))
families.append(dict(model='forest',seeds=5,full_mean=np.mean(forest_full),full_sd=np.std(forest_full,ddof=1),
                     full_min=np.min(forest_full),full_max=np.max(forest_full),
                     covered_mean=np.mean(forest_covered),covered_sd=np.std(forest_covered,ddof=1),
                     covered_min=np.min(forest_covered),covered_max=np.max(forest_covered),
                     full_union_mean=np.mean(forest_union),full_union_sd=np.std(forest_union,ddof=1),
                     covered_union_mean=np.mean(forest_covered_union),covered_union_sd=np.std(forest_covered_union,ddof=1)))
families=pd.DataFrame(families)
families['full_rank']=families.full_mean.rank(ascending=False)
families['covered_rank']=families.covered_mean.rank(ascending=False)
families['full_union_rank']=families.full_union_mean.rank(ascending=False,na_option='bottom')
families['covered_union_rank']=families.covered_union_mean.rank(ascending=False,na_option='bottom')
families.to_csv(out/'table_2_nsl_families.csv',index=False)
for name in ['table_2_natural_protocols.csv','table_3_nsl_families.csv']:
    path=out/name
    if path.exists(): path.unlink()
print('Saved main manuscript tables to',out)
