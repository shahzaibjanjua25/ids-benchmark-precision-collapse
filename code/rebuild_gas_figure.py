"""Rebuild the fold support chart and verify the released gas-model scores."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from exact_fold_oracle import oracle

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("results",type=Path)
parser.add_argument("out",type=Path)
args=parser.parse_args()
root=args.results/"gas_drift_adjacent"
counts=pd.read_csv(root/"fold_label_counts.csv")
summary=oracle(counts)
scores=pd.read_csv(root/"models.csv").set_index("model")
hits=pd.read_csv(root/"class_hits_by_fold.csv")
pooled=hits.groupby(["model","class"])[["hits","test_rows","predicted_rows"]].sum()
score=(2*pooled.hits/(pooled.test_rows+pooled.predicted_rows)).groupby("model").mean()
np.testing.assert_allclose(score.sort_index(),scores.macro_f1.sort_index(),rtol=0,atol=1e-12)
np.testing.assert_allclose(summary["exact_oracle"]-score.sort_index(),scores.oracle_gap.sort_index(),rtol=0,atol=1e-12)
args.out.mkdir(parents=True,exist_ok=True)
support=counts.pivot(index="fold",columns="class",values="test_rows")
available=counts.pivot(index="fold",columns="class",values="training_rows").gt(0)
fig,ax=plt.subplots(figsize=(7.4,4.3),layout="constrained")
from matplotlib.colors import ListedColormap
ax.imshow(np.where(support.eq(0),0,np.where(available,1,2)),cmap=ListedColormap(["#f2f3f4","#cce6ec","#f2a68c"]),vmin=0,vmax=2,aspect="auto")
for i,row in enumerate(support.to_numpy()):
    for j,n in enumerate(row):
        if n and not available.iloc[i, j]:
            from matplotlib.patches import Rectangle
            ax.add_patch(Rectangle((j-.5, i-.5), 1, 1, fill=False, hatch="///", edgecolor="#666666", linewidth=.3))
        ax.text(j,i,f"{n:,}" if n else "—",ha="center",va="center",fontsize=9)
ax.set_xticks(range(6),["Ethanol","Ethylene","Ammonia","Acetaldehyde","Acetone","Toluene"],rotation=22,ha="right")
ax.set_yticks(range(9),support.index)
ax.set_ylabel("Test batch (training uses the previous batch)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor="#cce6ec",label="Label available"),Patch(facecolor="#f2a68c",hatch="///",label="Label unavailable"),Patch(facecolor="#f2f3f4",label="No test rows")],loc="upper center",bbox_to_anchor=(.5,1.13),ncol=3,frameon=False)
for ext in ("pdf","png"):
    fig.savefig(args.out/f"gas_fold_coverage.{ext}",dpi=300)
print(scores.to_string())

