"""Compare full and covered-row rankings without independent-sample claims."""
from itertools import combinations
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--partial', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
out = root / 'results/rank_audit'
out.mkdir(exist_ok=True)
def macro(cm):
    n = cm.sum(axis=1)
    d = n + cm.sum(axis=0)
    f = np.divide(2*np.diag(cm), d, out=np.zeros(len(n)), where=d>0)
    return float(f[n>0].mean())
def stats(df, name):
    x, y = df.full_macro_f1.to_numpy(), df.covered_macro_f1.to_numpy()
    discordant = concordant = tied = 0
    for i, j in combinations(range(len(x)), 2):
        sign = np.sign(x[i]-x[j])*np.sign(y[i]-y[j])
        discordant += int(sign < 0)
        concordant += int(sign > 0)
        tied += int(sign == 0)
    return dict(comparison=name, n=len(df), spearman=float(spearmanr(x,y).statistic),
                kendall=float(kendalltau(x,y).statistic), discordant=discordant,
                concordant=concordant, tied=tied)
summaries = []
nsl = []
for seed in range(42,47):
    folder = root/'results/nsl_model_comparison'
    seen = pd.read_csv(folder/f'confusion_seen_{seed}.csv', index_col=0).to_numpy()
    unseen = pd.read_csv(folder/f'confusion_unseen_{seed}.csv', index_col=0).to_numpy()
    nsl.append(dict(seed=seed, full_macro_f1=macro(seen+unseen), covered_macro_f1=macro(seen)))
nsl = pd.DataFrame(nsl)
expected = pd.read_csv(root/'results/nsl_model_comparison/forest_metrics.csv')
np.testing.assert_allclose(nsl.full_macro_f1,expected.macro_f1,rtol=0,atol=1e-12)
nsl.to_csv(out/'nsl_ranks.csv', index=False)
legacy = out/'nsl_family_ranks.csv'
if legacy.exists(): legacy.unlink()
gas = pd.concat([pd.read_csv(root/'results/gas_model_comparison/models.csv'),
                 pd.read_csv(root/'results/gas_coral/models.csv')], ignore_index=True)
gas = gas.rename(columns={'macro_f1':'full_macro_f1','covered_only_macro_f1':'covered_macro_f1'})
gas.to_csv(out/'gas_ranks.csv',index=False)
summaries.append(stats(gas, 'gas all fitted models'))
if (out/'runs.csv').exists():
    grid = pd.read_csv(out/'runs.csv')
    if not args.partial:
        assert len(grid) == 180 and not grid.duplicated(['withheld','seed']).any()
    reference = pd.read_csv(root/'results/unsw_complete_pairs/runs.csv')
    joined = grid.merge(reference,on=['withheld','seed'],validate='one_to_one')
    assert len(joined) == len(grid)
    np.testing.assert_allclose(joined.full_macro_f1,joined.macro_f1,rtol=0,atol=1e-12)
    summaries.append(stats(grid, 'UNSW pair-seed conditions'))
    means = grid.groupby('withheld')[['full_macro_f1','covered_macro_f1']].mean().reset_index()
    summaries.append(stats(means, 'UNSW pair means'))
    for pair, df in grid.groupby('withheld'):
        summaries.append(stats(df, 'UNSW within '+pair))
pd.DataFrame(summaries).to_csv(out/'rank_summary.csv',index=False)
print(pd.DataFrame(summaries).to_string(index=False))
print(nsl.to_string(index=False))
