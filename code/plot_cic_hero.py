"""Show observed scores against their protocol ceilings."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('out',type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
df=pd.read_csv(root/'results/cic_full_replication.csv').query("arm == 'none'").set_index('protocol')
values=[df.loc[p,'macro_f1'] for p in ['cv','lodo']]
fig,ax=plt.subplots(figsize=(5.4,3.2),layout='constrained')
x=np.arange(2)
ax.bar(x,values,width=.48,color=['#276B86','#B86936'])
for i,(value,ceiling) in enumerate(zip(values,[1,1/15])):
    ax.hlines(ceiling,i-.34,i+.34,color='#202B36',linewidth=2,linestyle='--')
    ax.text(i,value+.025,f'{value:.5f}',ha='center',fontsize=10)
    ax.text(i+.36,ceiling,f'C = {ceiling:.5f}',ha='left',va='center',fontsize=9)
ax.set_xticks(x,['Shuffled CV','Day holdout'])
ax.set_ylabel('Pooled macro F1')
ax.set_ylim(0,1.09)
ax.set_xlim(-.55,1.95)
ax.spines[['top','right']].set_visible(False)
args.out.mkdir(parents=True,exist_ok=True)
for suffix in ['pdf','png']:
    fig.savefig(args.out/f'cic_hero.{suffix}',dpi=220)
