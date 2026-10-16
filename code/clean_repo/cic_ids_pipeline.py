# cic_ids_pipeline.py
"""
CIC-IDS2017 end-to-end detection-evaluation pipeline.
Usage:
    python cic_ids_pipeline.py --data-dir ./CICIDS2017/MachineLearningCSV --out outputs
Outputs:
    - Preprocessed feature matrix and encoded labels
    - Random Forest baseline (5-fold stratified CV)
    - Classification report, confusion matrix, ROC AUC
    - Feature-importance plot
    - metrics.json (ready for the paper's results table)
"""

from __future__ import annotations
import argparse, json, warnings
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, accuracy_score, f1_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# 1. Load and concatenate
# ---------------------------------------------------------------------------

def load_cicids(data_dir: Path) -> pd.DataFrame:
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSV files found in {data_dir}.\n"
            "Download MachineLearningCSV.zip from "
            "https://www.unb.ca/cic/datasets/ids-2017.html and extract there."
        )
    dfs = []
    for f in files:
        df = pd.read_csv(f, low_memory=False)
        dfs.append(df)
        print(f"  loaded {f.name}: {len(df):,} rows")
    full = pd.concat(dfs, ignore_index=True)
    print(f"concatenated: {len(full):,} rows, {len(full.columns)} columns")
    return full

# ---------------------------------------------------------------------------
# 2. Clean and split features / labels
# ---------------------------------------------------------------------------

def clean_and_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    df.columns = [c.strip() for c in df.columns]

    label_col = next((c for c in df.columns if c.lower() == "label"), None)
    if label_col is None:
        raise ValueError("No 'Label' column found. Check the CSV format.")

    y_raw = df[label_col].astype(str).str.strip()
    y_raw = y_raw.replace({"BENIGN": "BENIGN", "Benign": "BENIGN"})

    drop_cols = [label_col]
    for c in ["Flow ID", "Source IP", "Destination IP",
              "Timestamp", "Src IP", "Dst IP"]:
        if c in df.columns:
            drop_cols.append(c)

    X = df.drop(columns=drop_cols, errors="ignore").copy()
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    X = X[numeric_cols]
    X = X.replace([np.inf, -np.inf], np.nan)
    return X, y_raw, pd.Series(y_raw)

# ---------------------------------------------------------------------------
# 3. Encode labels
# ---------------------------------------------------------------------------

def encode_labels(y: pd.Series) -> Tuple[np.ndarray, LabelEncoder]:
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"label classes ({len(le.classes_)}): {list(le.classes_)}")
    return y_enc, le

# ---------------------------------------------------------------------------
# 4. Build model and cross-validate
# ---------------------------------------------------------------------------

def build_model(n_estimators: int = 200, random_state: int = 42) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("rf", RandomForestClassifier(
            n_estimators=n_estimators,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=random_state,
        )),
    ])

def evaluate_cv(model, X: pd.DataFrame, y: np.ndarray, n_splits: int = 5):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    print(f"running {n_splits}-fold stratified CV...")
    y_pred = cross_val_predict(model, X, y, cv=skf, n_jobs=-1, method="predict")
    y_prob = cross_val_predict(model, X, y, cv=skf, n_jobs=-1, method="predict_proba")
    return y_pred, y_prob

# ---------------------------------------------------------------------------
# 5. Metrics and figures
# ---------------------------------------------------------------------------

def save_metrics(y_true, y_pred, y_prob, le, out: Path):
    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro")
    f1_weighted = f1_score(y_true, y_pred, average="weighted")

    print(f"\naccuracy:    {acc:.4f}")
    print(f"macro F1:    {f1_macro:.4f}")
    print(f"weighted F1: {f1_weighted:.4f}")
    print("\nclassification report:")
    print(classification_report(y_true, y_pred, target_names=le.classes_))

    auc = None
    try:
        if y_prob.shape[1] == len(le.classes_):
            auc = roc_auc_score(y_true, y_prob, multi_class="ovr", average="weighted")
            print(f"weighted AUC (OVR): {auc:.4f}")
    except Exception as e:
        print(f"AUC skipped: {e}")

    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=le.classes_, yticklabels=le.classes_, ax=ax)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("CIC-IDS2017 confusion matrix (Random Forest, 5-fold CV)")
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=160)
    plt.close(fig)

    metrics = dict(
        accuracy=float(acc),
        f1_macro=float(f1_macro),
        f1_weighted=float(f1_weighted),
        auc_weighted_ovr=float(auc) if auc is not None else None,
        classes=list(le.classes_),
        confusion_matrix=cm.tolist(),
    )
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    print(f"metrics saved to {out / 'metrics.json'}")

# ---------------------------------------------------------------------------
# 6. Feature importance
# ---------------------------------------------------------------------------

def plot_feature_importance(model: Pipeline, feature_names: list, out: Path, top_n: int = 20):
    rf = model.named_steps["rf"]
    imp = rf.feature_importances_
    idx = np.argsort(imp)[::-1][:top_n]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(idx)), imp[idx][::-1], align="center")
    ax.set_yticks(range(len(idx)))
    ax.set_yticklabels([feature_names[i] for i in idx][::-1])
    ax.set_xlabel("importance")
    ax.set_title(f"Top {top_n} features (Random Forest)")
    fig.tight_layout()
    fig.savefig(out / "feature_importance.png", dpi=160)
    plt.close(fig)
    print("feature-importance plot saved")

# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("outputs"))
    ap.add_argument("--n-estimators", type=int, default=200)
    ap.add_argument("--sample-frac", type=float, default=None,
                    help="optional random subsample fraction (e.g. 0.3) to reduce runtime")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    print("[1/5] loading data...")
    df = load_cicids(args.data_dir)

    if args.sample_frac and args.sample_frac < 1.0:
        df = df.sample(frac=args.sample_frac, random_state=42).reset_index(drop=True)
        print(f"after subsample: {len(df):,} rows")

    print("\n[2/5] cleaning and splitting...")
    X, y_str, _ = clean_and_split(df)
    print(f"feature matrix: {X.shape[0]:,} rows x {X.shape[1]} columns")

    print("\n[3/5] encoding labels...")
    y_enc, le = encode_labels(y_str)

    print("\n[4/5] building and cross-validating model...")
    model = build_model(n_estimators=args.n_estimators)
    y_pred, y_prob = evaluate_cv(model, X, y_enc, n_splits=5)

    print("\n[5/5] saving results...")
    save_metrics(y_enc, y_pred, y_prob, le, args.out)

    print("fitting full model for feature importance...")
    model.fit(X, y_enc)
    plot_feature_importance(model, X.columns.tolist(), args.out)

    print(f"\ndone. results in {args.out.resolve()}")

if __name__ == "__main__":
    main()