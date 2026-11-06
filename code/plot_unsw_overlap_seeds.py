"""Plot the paired macro-F1 changes across UNSW-NB15 seeds."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("scores", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
data = pd.read_csv(args.scores)
fig, ax = plt.subplots(figsize=(6.6, 3.3), layout="constrained")
ax.axhline(0, color="#6d7882", linewidth=1)
for column, label, style in [
    ("delta_vs_official_train", "vs. full training", "o-"),
    ("delta_vs_class_count_matched_removal", "vs. matched random removal", "s--"),
]:
    ax.plot(data.seed, data[column], style, label=label)
ax.set(xlabel="Seed", ylabel="Macro F1 change after targeted removal", xticks=data.seed)
ax.grid(axis="y", alpha=.25)
ax.legend(frameon=False)
args.out.mkdir(parents=True, exist_ok=True)
fig.savefig(args.out / "unsw_overlap_seeds.pdf")
fig.savefig(args.out / "unsw_overlap_seeds.png", dpi=300)

