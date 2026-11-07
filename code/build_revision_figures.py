"""Figures from the released aggregates."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
parser.add_argument("out", type=Path)
args = parser.parse_args()
args.out.mkdir(exist_ok=True, parents=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
def save(fig, name):
    for extension in ["pdf", "png"]:
        fig.savefig(args.out / f"{name}.{extension}", dpi=220, bbox_inches="tight")
    plt.close(fig)

metrics = pd.read_csv(args.results / "metric_conventions.csv")
scores = [0.060298442346659, 0.254558997633246, 0.47067224193788937,
          float(pd.read_csv(args.results / "gas_drift_adjacent/models.csv").query("model == 'forest'").macro_f1.iloc[0]),
          float(pd.read_csv(args.results / "digits_fractional_coverage/metrics.csv").macro_f1.iloc[0])]
# Read the two remaining values directly rather than trust a rounded transcription.
cic = pd.read_csv(args.results / "cic_full_replication.csv")
scores[0] = float(cic.query("protocol == 'lodo' and arm == 'none'").macro_f1.iloc[0])
scores[1] = float(pd.read_csv(args.results / "nsl_kdd_official/forest_metrics.csv").macro_f1.iloc[0])
scores[2] = float(pd.read_csv(args.results / "unsw_partial_coverage/metrics.csv").macro_f1.iloc[0])
official = pd.read_csv(args.results / "RESULTS_PARSED.csv")
scores.append(float(official.query("dataset == 'unsw' and variant == 'raw' and protocol == 'official' and model == 'rf' and arm == 'none' and seed == 42").macro_f1.iloc[0]))
metrics["observed_seed_42"] = scores
assert (metrics.observed_seed_42 <= metrics.support_oracle + 1e-12).all()
metrics["oracle_attainment"] = metrics.observed_seed_42 / metrics.support_oracle.replace(0, np.nan)
metrics.to_csv(args.results / "figure_score_summary.csv", index=False)
fig, ax = plt.subplots(figsize=(7.8, 3.8), layout="constrained")
x = np.arange(len(metrics))
for offset, column, title, color, hatch in [(-.25, "coverage_ceiling", "Coverage ceiling", "#0072B2", ""),
                                           (0, "support_oracle", "Vocabulary oracle", "#E69F00", "//"),
                                           (.25, "observed_seed_42", "Observed", "#009E73", "..")]:
    ax.bar(x + offset, metrics[column], width=.24, label=title, color=color, hatch=hatch, edgecolor="black", linewidth=.3)
ax.set_xticks(x, ["CIC day", "NSL official", "UNSW mixed", "Gas adjacent", "Digits control", "UNSW official"], rotation=12, ha="right")
ax.set_ylabel("Pooled macro F1")
ax.set_ylim(0, 1.13)
ax.legend(ncol=3, fontsize=8, loc="upper center")
save(fig, "score_summary")

parts = pd.read_csv(args.results / "unsw_three_part_gap.csv")
fig, ax = plt.subplots(figsize=(7.4, 3.2), layout="constrained")
left = np.zeros(len(parts))
for column, name, color, hatch in [("minimum_vocabulary_penalty", "C - O", "#0072B2", ""),
                                   ("destination_loss", "O - R", "#E69F00", "//"),
                                   ("covered_row_gain", "R - F", "#009E73", "..")]:
    ax.barh(parts.withheld, parts[column], left=left, color=color, hatch=hatch, label=name, edgecolor="black", linewidth=.3)
    left += parts[column]
ax.set_xlabel("Macro-F1 shortfall under covered-row-first repair")
ax.legend(ncol=3)
save(fig, "unsw_gap_components")

sizes_path = args.results / "unsw_complete_pairs/withheld_count.csv"
if sizes_path.exists():
    sizes = pd.read_csv(sizes_path)
    fig, ax = plt.subplots(figsize=(7.2, 3.3), layout="constrained")
    for column, name, color, marker in [("ceiling", "Coverage ceiling", "#0072B2", "o"),
                                        ("oracle", "Vocabulary oracle", "#E69F00", "s"),
                                        ("observed_seed_42", "Observed", "#009E73", "^")]:
        ax.plot(sizes.withheld_count, sizes[column], marker=marker, label=name, color=color)
    ax.set_xlabel("Alphabetically first attack labels withheld")
    ax.set_ylabel("Pooled macro F1")
    ax.set_xticks(range(6))
    ax.legend(ncol=3, fontsize=8)
    save(fig, "withheld_count")

fig, ax = plt.subplots(figsize=(3.8, 3.4), layout="constrained")
ax.axis("off")
boxes = [(0.5, .9, "Fix evaluation question and permitted outputs"),
         (.5, .65, "State labels, pooling and zero-division rule"),
         (.5, .4, "Compute ceiling, oracle or certified interval"),
         (.5, .15, "Report absolute score and availability strata")]
for x, y, text in boxes:
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5, bbox=dict(boxstyle="round,pad=.6", facecolor="#E8F1F8", edgecolor="#0072B2"))
for (_, top, _), (_, bottom, _) in zip(boxes, boxes[1:]):
    ax.annotate("", xy=(.5, bottom + .07), xytext=(.5, top - .07), arrowprops=dict(arrowstyle="->"))
save(fig, "reporting_flowchart")
