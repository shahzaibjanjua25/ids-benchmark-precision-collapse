#!/usr/bin/env python3
"""Check the conditional ceiling calculation in the targeted source audit."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
audit = pd.read_csv(ROOT / "results" / "published_score_audit.csv")
doi = "https://doi.org/10.1038/s41598-025-34166-1"
row = audit.loc[audit.source == doi]
assert len(row) == 1
row = row.iloc[0]
assert row.status == "unresolved scoring vocabulary"
assert row.protocol.endswith("Web Attack excluded from training")
assert row.reported_metric == "macro F1"
assert abs(float(row.reported_value) - 0.9855) < 1e-12
fine_label_ceiling = 12 / 15
merged_web_ceiling = 12 / 13
binary_ceiling = 1.0
assert pd.isna(row.positive_support_ceiling)
assert abs(fine_label_ceiling - 0.8) < 1e-12
assert abs(merged_web_ceiling - 12 / 13) < 1e-12
assert float(row.reported_value) > fine_label_ceiling
assert float(row.reported_value) > merged_web_ceiling
assert float(row.reported_value) < binary_ceiling
assert "three separate Web Attack labels" in row.evidence
assert "ceiling=1" in row.evidence
assert "not coded as an incompatible score" in row.evidence
print("Published LOFO claim retained as conditional, unresolved evidence")
