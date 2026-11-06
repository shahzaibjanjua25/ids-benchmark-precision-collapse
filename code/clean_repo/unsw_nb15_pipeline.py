
from __future__ import annotations
import argparse, json, math, warnings
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, accuracy_score, f1_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore", category=FutureWarning)

NOMINAL_COLS = ["proto", "state", "service"]
DROP_COLS = ["id", "attack_cat", "label"]


def load_unsw(data_dir):
    frames = []
    entries = [
        ("UNSW_NB15_training-set.csv", "training"),
        ("UNSW_NB15_testing-set.csv", "testing"),
    ]
    for name, label in entries:
        p = data_dir / name
        if p.exists():
            df = pd.read_csv(p)
            print(f"  {label} set: {len(df):,} rows")
            frames.append(df)
        else:
            print(f"  {label} set missing: {name}")
    if not frames:
        raise FileNotFoundError("No UNSW-NB15 CSV found in " + str(data_dir))
    df = pd.concat(frames, ignore_index=True)
    print(f"  combined:     {len(df):,} rows, {len(df.columns)} columns")
    return df


def prepare(df):
    df.columns = [c.strip() for c in df.columns]
    lower_map = {c.lower(): c for c in df.columns}
    if "attack_cat" not in lower_map:
        raise ValueError("attack_cat column not found")
    attack_col = lower_map["attack_cat"]
    y_raw = df[attack_col].astype(str).str.strip()
    y_raw = y_raw.replace({"Normal": "Normal",
                           "normal": "Normal",
                           "Benign": "Normal",
                           "benign": "Normal"})
    binary_col = lower_map.get("label")
    y_binary = df[binary_col].astype(int) if binary_col else None
    drop = [lower_map[c] for c in DROP_COLS if c in lower_map]
    X = df.drop(columns=drop, errors="ignore").copy()
    nominal_present = [c for c in NOMINAL_COLS if c in X.columns]
    numeric_present = [c for c in X.columns if c not in nominal_present]
    for c in numeric_present:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X[numeric_present] = X[numeric_present].replace([np.inf, -np.inf], np.nan)
    return X, y_raw, (pd.Series(y_binary) if y_binary is not None else None), nominal_present, numeric_present


def build_preprocessor(nominal_cols, numeric_cols):
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    nominal_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value",
                                   unknown_value=-1)),
    ])
    return ColumnTransformer(
        [("num", numeric_pipe, numeric_cols),
         ("nom", nominal_pipe, nominal_cols)],
        remainder="drop",
    )


def wilson_ci(k, n, alpha=0.05):
    if n == 0:
        return (float("nan"), float("nan"))
    z = stats.norm.ppf(1.0 - alpha / 2.0)
    p = k / n
    z_sq = z * z
    denom = 1.0 + z_sq / n
    centre = (p + z_sq / (2.0 * n)) / denom
    inner = (p * (1.0 - p)) / n + z_sq / (4.0 * n * n)
    half = (z * math.sqrt(inner)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def per_class_table(y_true, y_pred, le):
    cm = confusion_matrix(y_true, y_pred, labels=np.arange(len(le.classes_)))
    rows = []
    for i, cls in enumerate(le.classes_):
        tp = int(cm[i, i])
        fn = int(cm[i, :].sum() - tp)
        fp = int(cm[:, i].sum() - tp)
        support = tp + fn
        pred_pos = tp + fp
        recall = tp / support if support else float("nan")
        precision = tp / pred_pos if pred_pos else float("nan")
        if precision and recall and (precision + recall) > 0:
            f1 = (2 * precision * recall) / (precision + recall)
        else:
            f1 = 0.0
        r_lo, r_hi = wilson_ci(tp, support)
        p_lo, p_hi = wilson_ci(tp, pred_pos)
        rows.append({
            "class_name": cls,
            "support": support,
            "precision": precision,
            "precision_lo": p_lo,
            "precision_hi": p_hi,
            "recall": recall,
            "recall_lo": r_lo,
            "recall_hi": r_hi,
            "f1": f1,
        })
    return pd.DataFrame(rows).sort_values("support", ascending=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("outputs_unsw"))
    ap.add_argument("--n-estimators", type=int, default=200)
    ap.add_argument("--sample-frac", type=float, default=None)
    ap.add_argument("--n-splits", type=int, default=5)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    print("[1/5] loading UNSW-NB15...")
    df = load_unsw(args.data_dir)
    if args.sample_frac and args.sample_frac < 1.0:
        df = df.sample(frac=args.sample_frac, random_state=42).reset_index(drop=True)
        print(f"  after subsample: {len(df):,} rows")

    print("\n[2/5] preparing features and labels...")
    X, y_str, y_bin, nominal_cols, numeric_cols = prepare(df)
    print(f"  nominal columns: {nominal_cols}")
    print(f"  numeric columns: {len(numeric_cols)}")

    le = LabelEncoder()
    y = le.fit_transform(y_str)
    print(f"  classes ({len(le.classes_)}): {list(le.classes_)}")

    print("\n[3/5] building pipeline...")
    pre = build_preprocessor(nominal_cols, numeric_cols)
    clf = RandomForestClassifier(
        n_estimators=args.n_estimators,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=42,
    )
    pipe = Pipeline([("pre", pre), ("rf", clf)])

    print(f"\n[4/5] running {args.n_splits}-fold stratified CV on {len(X):,} rows...")
    skf = StratifiedKFold(n_splits=args.n_splits, shuffle=True, random_state=42)
    y_pred = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1, method="predict")
    y_prob = cross_val_predict(pipe, X, y, cv=skf, n_jobs=-1, method="predict_proba")

    print("\n[5/5] computing metrics and intervals...")
    acc = accuracy_score(y, y_pred)
    f1m = f1_score(y, y_pred, average="macro")
    f1w = f1_score(y, y_pred, average="weighted")
    auc = None
    if y_prob.shape[1] == len(le.classes_):
        auc = roc_auc_score(y, y_prob, multi_class="ovr", average="weighted")

    print(f"\naccuracy:    {acc:.4f}")
    print(f"macro F1:    {f1m:.4f}")
    print(f"weighted F1: {f1w:.4f}")
    if auc is not None:
        print(f"weighted AUC: {auc:.4f}")

    print("\nclassification report (point estimates):")
    print(classification_report(y, y_pred, target_names=le.classes_, digits=3))

    table = per_class_table(y, y_pred, le)
    table.to_csv(args.out / "unsw_per_class_wilson.csv", index=False)
    table.to_latex(args.out / "unsw_per_class_wilson.tex", index=False, float_format="%.3f")
    print(f"per-class Wilson table saved")

    cm = confusion_matrix(y, y_pred, labels=np.arange(len(le.classes_)))
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=le.classes_, yticklabels=le.classes_, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("UNSW-NB15 confusion matrix")
    fig.tight_layout()
    fig.savefig(args.out / "unsw_confusion_matrix.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    t = table.sort_values("support")
    y_pos = np.arange(len(t))
    x = t["support"].to_numpy()
    med = t["recall"].to_numpy()
    lo = med - t["recall_lo"].to_numpy()
    hi = t["recall_hi"].to_numpy() - med
    ax.errorbar(x, y_pos, yerr=np.vstack([lo, hi]), fmt="o", capsize=4)
    ax.set_xscale("log")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(t["class_name"])
    ax.set_xlabel("Support (log scale)")
    ax.set_ylabel("Recall (95% Wilson CI)")
    ax.set_title("UNSW-NB15: recall interval width vs. class support")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(args.out / "unsw_support_uncertainty.png", dpi=160)
    plt.close(fig)

    out = {
        "dataset": "UNSW-NB15",
        "n_rows": int(len(X)),
        "n_features": int(X.shape[1]),
        "n_classes": len(le.classes_),
        "accuracy": float(acc),
        "macro_f1": float(f1m),
        "weighted_f1": float(f1w),
        "weighted_auc": float(auc) if auc is not None else None,
        "per_class": table.to_dict(orient="records"),
    }
    (args.out / "unsw_metrics.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"metrics saved")


if __name__ == "__main__":
    main()
