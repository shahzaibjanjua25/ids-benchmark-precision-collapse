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
conditional_ceiling = 14 / 15
assert abs(float(row.positive_support_ceiling) - conditional_ceiling) < 1e-12
assert float(row.reported_value) > conditional_ceiling
assert "not coded as a confirmed incompatible score" in row.evidence
print("Published LOFO claim retained as conditional, unresolved evidence")
