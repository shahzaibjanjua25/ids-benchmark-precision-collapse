"""Check frozen sampling and scores reconstructed from released confusion counts."""
from pathlib import Path
import hashlib
import itertools
import json
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[1]
p=root/'audit/crossref_20261108'
frame=pd.read_csv(p/'candidate_frame.csv').sort_values('doi').reset_index(drop=True)
sample=pd.read_csv(p/'selected_sample.csv')
choice=np.random.default_rng(20261108).choice(len(frame),size=50,replace=False)
assert sample.doi.tolist()==frame.iloc[choice].doi.tolist()
assert hashlib.sha256((p/'candidate_frame.csv').read_bytes()).hexdigest()==(p/'frame_sha256.txt').read_text().strip()
coding=pd.read_csv(p/'coding.csv')
assert coding.doi.tolist()==sample.doi.tolist() and not coding.doi.duplicated().any()
assert not coding.astype(str).eq('pending').any().any()
summary=json.loads((p/'summary.json').read_text())
assert coding.eligibility.value_counts().to_dict()==summary['eligibility']

def macro(cm):
    n=cm.sum(axis=1)
    denom=n+cm.sum(axis=0)
    f=np.divide(2*np.diag(cm),denom,out=np.zeros(len(n)),where=denom>0)
    return float(f[n>0].mean())
r=root/'results'
grid=pd.read_csv(r/'rank_audit/runs.csv')
assert len(grid)==180 and not grid.duplicated(['withheld','seed']).any()
for row in grid.itertuples():
    name=row.withheld.replace(' + ','_')+'_'+str(row.seed)+'.npz'
    data=np.load(r/'rank_audit/confusion'/name,allow_pickle=False)
    covered,unavailable=data['covered'],data['unavailable']
    assert covered.sum()+unavailable.sum()==82332
    assert np.trace(unavailable)==0
    assert abs(macro(covered+unavailable)-row.full_macro_f1)<1e-12
    assert abs(macro(covered)-row.covered_macro_f1)<1e-12
families=pd.read_csv(r/'nsl_families/models.csv')
assert len(families)==5
for row in families.itertuples():
    data=np.load(r/'nsl_families'/(row.model+'.npz'),allow_pickle=False)
    covered,unavailable=data['covered'],data['unavailable']
    assert covered.sum()==18794 and unavailable.sum()==3750 and np.trace(unavailable)==0
    assert abs(macro(covered+unavailable)-row.full_macro_f1)<1e-12
    assert abs(macro(covered)-row.covered_macro_f1)<1e-12
seeded=pd.read_csv(r/'nsl_families/seed_metrics.csv')
assert len(seeded)==25 and set(seeded.seed)=={42,43,44,45,46}
for row in seeded.itertuples():
    data=np.load(r/'nsl_families/by_seed'/f'{row.model}_{row.seed}.npz',allow_pickle=False)
    covered,unavailable=data['covered'],data['unavailable']
    assert covered.sum()==18794 and unavailable.sum()==3750 and np.trace(unavailable)==0
    assert abs(macro(covered+unavailable)-row.full_macro_f1)<1e-12
    assert abs(macro(covered)-row.covered_macro_f1)<1e-12
    union=lambda cm: float(np.divide(2*np.diag(cm),cm.sum(axis=1)+cm.sum(axis=0),out=np.zeros(len(cm)),where=(cm.sum(axis=1)+cm.sum(axis=0))>0)[(cm.sum(axis=1)+cm.sum(axis=0))>0].mean())
    assert abs(union(covered+unavailable)-row.full_union_macro_f1)<1e-12
    assert abs(union(covered)-row.covered_union_macro_f1)<1e-12
granularity=pd.read_csv(r/'nsl_kdd_official/granularity_reanalysis.csv')
assert len(granularity)==5 and set(granularity.seed)=={42,43,44,45,46}
assert set(granularity.test_rows)=={22544} and set(granularity.test_rows_with_unavailable_fine_label)=={3750}
assert np.allclose(granularity.fine_label_ceiling,21/38,rtol=0,atol=1e-12)
assert np.allclose(granularity.five_category_ceiling,1,rtol=0,atol=1e-12)
assert np.allclose(
    granularity.five_category_macro_f1,
    granularity.five_category_inferred_union_macro_f1,
    rtol=0, atol=1e-12,
)
summary=pd.read_csv(r/'nsl_kdd_official/granularity_reanalysis_summary.csv').iloc[0]
assert abs(summary.fine_label_f1_mean-granularity.fine_label_macro_f1.mean())<1e-12
assert abs(summary.five_category_f1_mean-granularity.five_category_macro_f1.mean())<1e-12
assert abs(summary.five_category_inferred_union_f1_mean-granularity.five_category_macro_f1.mean())<1e-12
assert summary.mixed_resolution_equals_five_category
family_map=pd.read_csv(r/'family_mapping.csv')
nsl_map=family_map.loc[family_map.dataset.eq('NSL')].merge(
    pd.read_csv(r/'nsl_kdd_official/label_counts.csv'),
    left_on='original', right_on='class', validate='one_to_one',
)
assert len(nsl_map)==40 and nsl_map.original.nunique()==40
unavailable_families=set(nsl_map.loc[
    nsl_map.test_rows.gt(0) & nsl_map.training_rows.eq(0), 'family'
])
assert unavailable_families=={'DoS','Probe','R2L','U2R'}
natural=pd.read_csv(r/'manuscript_tables/table_3_natural_protocols.csv')
np.testing.assert_allclose(
    natural.observed_over_oracle.to_numpy(dtype=float),
    [0.4334291976354778, 0.9045642624384151, 0.592735822748516, 0.6437780261910188],
    rtol=0, atol=1e-10,
)
target_resolution=pd.read_csv(r/'cic_lodo_target_resolution.csv').set_index('resolution')
assert set(target_resolution.index)=={'fine attack label','eight-family mapping','binary benign/attack'}
assert set(target_resolution.test_rows)=={2830743}
assert np.allclose(target_resolution.loc['fine attack label',['coverage_ceiling','macro_f1']].to_numpy(dtype=float),[1/15,0.06030428],atol=1e-8,rtol=0)
assert np.allclose(target_resolution.loc['eight-family mapping',['coverage_ceiling','macro_f1']].to_numpy(dtype=float),[0.25,0.15629612],atol=1e-8,rtol=0)
assert np.allclose(target_resolution.loc['binary benign/attack',['coverage_ceiling','macro_f1','attack_recall']].to_numpy(dtype=float),[1,0.57972301,0.14690144],atol=1e-8,rtol=0)
assert abs(target_resolution.loc['fine attack label','ceiling_attainment']-0.90456427)<1e-8
print('Frozen 50-record sample, 180 pair/seed matrices and 25 NSL pipeline/seed outputs verified')
print('NSL-KDD fine-label and five-category scores verified from the same five confusion matrices')
print('NSL-KDD mapping verifies test-only labels in all four attack families; mixed score equals five categories')
print('CICIDS2017 day-holdout fine, family and binary scores verified from the same prediction matrix')
for path in (r/'nsl_destination_audit').glob('*.npz'):
    data=np.load(path,allow_pickle=False)
    np.testing.assert_array_equal(data['original'].sum(axis=1),data['rerouted'].sum(axis=1))
    np.testing.assert_array_equal(np.diag(data['original']),np.diag(data['rerouted']))
print('NSL destination controls preserve every true-class support and true-positive count')
