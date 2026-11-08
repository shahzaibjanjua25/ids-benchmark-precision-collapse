#!/usr/bin/env python3
"""Check the saved CICIDS2017 binary day-holdout outputs."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "cic_binary_lodo_seed42"

scores = pd.read_csv(OUT / "cic_binary_lodo_scores.csv")
confusion = pd.read_csv(OUT / "cic_binary_lodo_confusion.csv")
metadata = json.loads((OUT / "cic_binary_lodo_run.json").read_text(encoding="utf-8"))
target = pd.read_csv(ROOT / "results" / "cic_lodo_target_resolution.csv")

assert metadata["seeds"] == [42]
assert metadata["target_mapping"] == "BENIGN remains BENIGN; every other original label maps to ATTACK"
assert metadata["n_estimators"] == 100
assert len(metadata["data_files"]) == 8
assert len(set(item["sha256"] for item in metadata["data_files"])) == 8
assert set(scores["held_out_day"]) == {"friday", "monday", "thursday", "tuesday", "wednesday", "POOLED"}
assert len(scores) == 6 and confusion["seed"].tolist() == [42]

pooled = scores.loc[scores.held_out_day == "POOLED"].iloc[0]
friday = scores.loc[scores.held_out_day == "friday"].iloc[0]
monday = scores.loc[scores.held_out_day == "monday"].iloc[0]
assert int(pooled.test_rows) == 2_830_743
assert int(pooled.attack_support) == 557_646
assert abs(pooled.binary_macro_f1 - 0.5806327743703612) < 1e-12
assert abs(pooled.attack_recall - 0.14782317097226555) < 1e-12
assert abs(friday.binary_macro_f1 - 0.6175363773535545) < 1e-12
assert abs(friday.attack_recall - 0.278942832519391) < 1e-12
assert int(monday.attack_support) == 0 and pd.isna(monday.attack_recall)

binary_projection = target.loc[target.resolution == "binary benign/attack"].iloc[0]
assert abs(pooled.binary_macro_f1 - binary_projection.macro_f1) < 0.001
assert abs(pooled.attack_recall - binary_projection.attack_recall) < 0.001
cm = confusion.loc[0]
assert int(cm[["tn", "fp", "fn", "tp"]].sum()) == 2_830_743
assert int(cm.fn + cm.tp) == 557_646
print("CICIDS2017 binary LODO outputs, row counts, target mapping and score checks passed")
