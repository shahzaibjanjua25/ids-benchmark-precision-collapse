#!/usr/bin/env python3
"""Check the published LOFO target interpretation and ceiling."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
audit = pd.read_csv(ROOT / "results" / "published_score_audit.csv")
doi = "https://doi.org/10.1038/s41598-025-34166-1"
row = audit.loc[audit.source == doi]
assert len(row) == 1
row = row.iloc[0]
assert row.status == "compatible; binary target specified in Methods"
assert "Web Attack excluded from training" in row.protocol
assert row.reported_metric == "macro F1"
assert abs(float(row.reported_value) - 0.9855) < 1e-12
fine_label_ceiling = 12 / 15
merged_web_ceiling = 12 / 13
binary_ceiling = 1.0
assert abs(float(row.positive_support_ceiling) - 1.0) < 1e-12
assert abs(fine_label_ceiling - 0.8) < 1e-12
assert abs(merged_web_ceiling - 12 / 13) < 1e-12
assert float(row.reported_value) <= binary_ceiling
assert "binary Normal/Attack" in row.evidence
assert "no alternative multiclass vocabulary" in row.evidence
assert "predictions are not released" in row.evidence
print("Published LOFO score is compatible with the stated binary task")
