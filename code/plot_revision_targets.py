"""Plot paired target-resolution evidence directly from saved result tables."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main():
    nsl = pd.read_csv(ROOT / "results/nsl_kdd_official/granularity_reanalysis_summary.csv").iloc[0]
    cic = pd.read_csv(ROOT / "results/cic_lodo_target_resolution.csv")
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.65), sharey=True)
    values = [
        (["Fine subtype", "Five categories"], [nsl.fine_label_f1_mean, nsl.five_category_f1_mean],
         [nsl.fine_label_ceiling, nsl.five_category_ceiling], "NSL-KDD: five saved forest fits"),
        (["Fine subtype", "Eight families", "Binary alarm"], cic.macro_f1.tolist(),
         cic.coverage_ceiling.tolist(), "CICIDS2017: saved day holdout")]
    for ax, (names, scores, ceilings, title) in zip(axes, values):
        x = np.arange(len(names))
        ax.bar(x, scores, width=.48, color="#5d6c7b", label="Observed macro F1")
        ax.scatter(x, ceilings, marker="_", s=650, linewidths=2, color="black", label="Coverage bound", zorder=3)
        for i, (score, bound) in enumerate(zip(scores, ceilings)):
            ax.text(i, score + .025, f"{score:.3f}", ha="center", fontsize=8)
        ax.set_xticks(x, names, rotation=0, fontsize=8)
        ax.set_title(title, fontsize=9, loc="left", pad=10)
        ax.set_ylim(0, 1.12)
        ax.set_yticks([0, .25, .5, .75, 1])
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#dddddd", linewidth=.5)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Pooled macro F1")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncols=2, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, .12, 1, 1))
    out = ROOT / "paper/revision/generated"
    out.mkdir(exist_ok=True)
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(out / f"target_resolution.{ext}", dpi=600, bbox_inches="tight")
    svg = out / "target_resolution.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf8").splitlines()) + "\n", encoding="utf8")
    plt.close(fig)
    print("Generated target-resolution figure from verified NSL and CIC tables")


if __name__ == "__main__":
    main()
