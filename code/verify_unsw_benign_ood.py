#!/usr/bin/env python3
"""Verify the saved benign-only open-set baseline and audit fields."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "unsw_benign_ood"
metrics = pd.read_csv(OUT / "seed_metrics.csv")
confusion = pd.read_csv(OUT / "confusion_by_seed.csv")
summary = pd.read_csv(OUT / "summary.csv").set_index("metric")
run = json.loads((OUT / "run.json").read_text(encoding="utf-8"))

assert metrics.seed.tolist() == [42, 43, 44, 45, 46]
assert metrics.train_benign_fit_rows.eq(44800).all()
assert metrics.train_benign_calibration_rows.eq(11200).all()
assert metrics.test_rows.eq(82332).all()
assert metrics.test_attack_rows.eq(45332).all()
assert metrics.scored_outputs.eq("BENIGN|ATTACK").all()
assert metrics.legal_output_ceiling.eq(1.0).all()
assert np.allclose(metrics.observed_calibration_fpr, 0.009910714285714285)
assert np.allclose(metrics.binary_macro_f1, confusion.apply(
    lambda r: 0.5 * (
        2 * r.tp / (2 * r.tp + r.fp + r.fn)
        + 2 * r.tn / (2 * r.tn + r.fp + r.fn)
    ), axis=1))
assert np.isclose(metrics.binary_macro_f1.mean(), summary.loc["binary_macro_f1", "mean"])
assert np.isclose(metrics.attack_recall.mean(), summary.loc["attack_recall", "mean"])
assert run["not_a_fine_grained_attack_classifier"] is True
assert run["legal_output_ceiling"] == 1.0
assert len(run["files"]) == 2
print("UNSW benign-only OOD results, binary ceiling and saved confusion counts passed")
