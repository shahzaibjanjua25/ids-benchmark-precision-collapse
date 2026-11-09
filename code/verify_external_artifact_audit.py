#!/usr/bin/env python3
"""Re-score the released per-seed confusion matrices for one published IDS study."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "audit" / "external" / "franco_valiente_2026"
LABELS = ["Normal", "DoS", "Probe", "R2L", "U2R"]
rows = []
for seed in range(42, 52):
    path = ARTIFACTS / f"confusion-cic-ids2017-none-conn5tuple-s{seed}-n1.csv"
    frame = pd.read_csv(path, index_col=0)
    assert frame.index.tolist() == LABELS
    assert frame.columns.tolist() == [f"pred_{label}" for label in LABELS]
    cm = frame.to_numpy(dtype=np.int64)
    support = cm.sum(axis=1)
    predicted = cm.sum(axis=0)
    assert (support > 0).all()
    f1 = []
    for i in range(len(LABELS)):
        tp = int(cm[i, i])
        fp = int(predicted[i] - tp)
        fn = int(support[i] - tp)
        f1.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    rows.append({"seed": seed, "test_rows": int(cm.sum()), "macro_f1": float(np.mean(f1)),
                 "train_u2r_support_reported": 65, "coverage_ceiling": 1.0})

result = pd.DataFrame(rows)
result.to_csv(ARTIFACTS / "recomputed_seed_scores.csv", index=False)
mean = float(result.macro_f1.mean())
sd = float(result.macro_f1.std(ddof=1))
ci_half = float(2.2621571627409915 * sd / np.sqrt(len(result)))
assert np.isclose(mean, 0.9000197011478338)
assert np.isclose(sd, 0.05142685314589269)
assert abs(mean - 0.900) < 0.001
assert abs(ci_half - 0.037) < 0.001
assert result.coverage_ceiling.eq(1.0).all()
published = pd.read_csv(ROOT / "results" / "published_score_audit.csv")
record = published.loc[published.source.eq("https://doi.org/10.3390/electronics15184074")]
assert len(record) == 1
record = record.iloc[0]
assert record.status == "compatible; independently re-scored from published artifact"
assert float(record.reported_value) == 0.9 and float(record.positive_support_ceiling) == 1.0
print(f"Re-scored one published IDS study over 10 seeds: macro F1={mean:.5f}, "
      f"sample SD={sd:.5f}, 95% CI half-width={ci_half:.5f}; ceiling=1.00000")
