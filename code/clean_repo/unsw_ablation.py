#!/usr/bin/env python3
"""
UNSW-NB15 ablation: class-weighting arms x seeds x protocol.

Arms (all fitted inside the training fold only):
  none                class_weight=None
  balanced            class_weight="balanced"            (weights from full train set)
  balanced_subsample  class_weight="balanced_subsample"  (recomputed per bootstrap sample)
  smote_none          SMOTENC oversampling + class_weight=None

Protocols:
  official    train on UNSW_NB15_training-set.csv, test on UNSW_NB15_testing-set.csv (PRIMARY)
  pooled_cv   5-fold stratified CV on pooled corpus (secondary robustness check)

Outputs (in --out):
  per_class_long.csv   one row per (arm, seed, class): support, TP, FP, FN,
                       precision/recall with 95% Wilson CIs
  aggregate.csv        accuracy, macro F1, weighted F1 per (arm, seed)
  per_class_summary.csv  per (arm, class): mean/SD across seeds, mean Wilson width

Usage:
  pip install scikit-learn imbalanced-learn pandas numpy
  python unsw_ablation.py --data-dir ./unsw --out ./out_official
  python unsw_ablation.py --data-dir ./unsw --out ./out_cv --protocol pooled_cv
  python unsw_ablation.py --data-dir ./unsw --out ./out_dedup --dedup
"""
import argparse
import os
import time

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTENC
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

CAT_COLS = ["proto", "state", "service"]
ARMS = ["none", "balanced", "balanced_subsample", "smote_none"]
Z = 1.959964


def wilson(k, n, z=Z):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def load(data_dir):
    def read(name):
        df = pd.read_csv(os.path.join(data_dir, name))
        df.columns = [c.strip() for c in df.columns]
        df["attack_cat"] = df["attack_cat"].astype(str).str.strip()
        df.loc[df["attack_cat"].str.lower().isin(["benign", "normal"]), "attack_cat"] = "Normal"
        return df

    tr = read("UNSW_NB15_training-set.csv")
    te = read("UNSW_NB15_testing-set.csv")
    return tr, te


def split_xy(df):
    y = df["attack_cat"].values
    X = df.drop(columns=[c for c in ["id", "label", "attack_cat"] if c in df.columns]).copy()
    for c in CAT_COLS:
        X[c] = X[c].fillna("-").astype(str)
    num = [c for c in X.columns if c not in CAT_COLS]
    for c in num:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X[num] = X[num].replace([np.inf, -np.inf], np.nan)
    # keep categories first for SMOTENC
    X = X[CAT_COLS + num]
    return X, y, num


def row_hash(X, y):
    return pd.util.hash_pandas_object(X.assign(_y=y), index=False).values


def build_model(arm, seed, n_est, num_cols):
    pre = ColumnTransformer(
        [
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CAT_COLS),
            ("num", SimpleImputer(strategy="median"), num_cols),
        ]
    )
    cw = {"none": None, "balanced": "balanced",
          "balanced_subsample": "balanced_subsample", "smote_none": None}[arm]
    rf = RandomForestClassifier(
        n_estimators=n_est, min_samples_split=5, min_samples_leaf=2,
        class_weight=cw, random_state=seed, n_jobs=-1,
    )
    if arm == "smote_none":
        return ImbPipeline([
            ("pre", pre),
            ("smote", SMOTENC(categorical_features=[0, 1, 2],
                              sampling_strategy="not majority", random_state=seed)),
            ("rf", rf),
        ])
    return Pipeline([("pre", pre), ("rf", rf)])


def splits(protocol, X, y, seed, X_te=None, y_te=None):
    """Yield (X_train, y_train, X_test, y_test)."""
    if protocol == "official":
        yield X, y, X_te, y_te
    else:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for tr_i, te_i in skf.split(X, y):
            yield X.iloc[tr_i], y[tr_i], X.iloc[te_i], y[te_i]


def per_class_rows(y_true, y_pred, classes, arm, seed):
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    rows = []
    for i, c in enumerate(classes):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        n, m = tp + fn, tp + fp
        p = tp / m if m else np.nan
        r = tp / n if n else np.nan
        plo, phi = wilson(tp, m)
        rlo, rhi = wilson(tp, n)
        rows.append(dict(arm=arm, seed=seed, cls=c, support=n, tp=tp, fp=fp, fn=fn,
                         precision=p, p_lo=plo, p_hi=phi,
                         recall=r, r_lo=rlo, r_hi=rhi,
                         fp_per_tp=(fp / tp) if tp else np.nan))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--protocol", choices=["official", "pooled_cv"], default="official")
    ap.add_argument("--arms", nargs="+", default=ARMS, choices=ARMS)
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    ap.add_argument("--n-estimators", type=int, default=200)
    ap.add_argument("--dedup", action="store_true",
                    help="drop exact duplicate rows (features+label); on official protocol "
                         "also drop test rows whose exact feature+label row appears in train")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tr, te = load(args.data_dir)
    X_tr, y_tr, num = split_xy(tr)
    X_te, y_te, _ = split_xy(te)

    if args.protocol == "pooled_cv":
        X = pd.concat([X_tr, X_te], ignore_index=True)
        y = np.concatenate([y_tr, y_te])
        X_te = y_te = None
    else:
        X, y = X_tr, y_tr

    if args.dedup:
        h = row_hash(X, y)
        keep = ~pd.Series(h).duplicated().values
        print(f"dedup train/pool: {len(X)} -> {keep.sum()}")
        X, y = X[keep].reset_index(drop=True), y[keep]
        if args.protocol == "official":
            h_te = row_hash(X_te, y_te)
            h_tr = set(row_hash(X, y))
            keep_te = np.array([v not in h_tr for v in h_te]) & ~pd.Series(h_te).duplicated().values
            print(f"dedup test: {len(X_te)} -> {keep_te.sum()}")
            X_te, y_te = X_te[keep_te].reset_index(drop=True), y_te[keep_te]

    all_y = y if y_te is None else np.concatenate([y, y_te])
    classes = sorted(set(all_y))
    print("classes:", classes)

    long_rows, agg_rows = [], []
    for arm in args.arms:
        for seed in args.seeds:
            t0 = time.time()
            yt, yp = [], []
            for Xa, ya, Xb, yb in splits(args.protocol, X, y, seed, X_te, y_te):
                model = build_model(arm, seed, args.n_estimators, num)
                model.fit(Xa, ya)
                yp.append(model.predict(Xb))
                yt.append(yb)
            yt, yp = np.concatenate(yt), np.concatenate(yp)
            long_rows += per_class_rows(yt, yp, classes, arm, seed)
            agg_rows.append(dict(
                arm=arm, seed=seed, n_eval=len(yt),
                accuracy=accuracy_score(yt, yp),
                macro_f1=f1_score(yt, yp, average="macro", labels=classes, zero_division=0),
                weighted_f1=f1_score(yt, yp, average="weighted", labels=classes, zero_division=0)))
            print(f"[{arm} seed={seed}] acc={agg_rows[-1]['accuracy']:.4f} "
                  f"macroF1={agg_rows[-1]['macro_f1']:.4f} ({time.time()-t0:.0f}s)", flush=True)
            # save each run as it finishes
            pd.DataFrame(long_rows).to_csv(os.path.join(args.out, "per_class_long.csv"), index=False)
            pd.DataFrame(agg_rows).to_csv(os.path.join(args.out, "aggregate.csv"), index=False)

    L = pd.DataFrame(long_rows)
    L["p_width"] = L["p_hi"] - L["p_lo"]
    L["r_width"] = L["r_hi"] - L["r_lo"]
    S = L.groupby(["arm", "cls"]).agg(
        support=("support", "first"),
        precision_mean=("precision", "mean"), precision_sd=("precision", "std"),
        recall_mean=("recall", "mean"), recall_sd=("recall", "std"),
        p_wilson_width=("p_width", "mean"), r_wilson_width=("r_width", "mean"),
        fp_per_tp_mean=("fp_per_tp", "mean"),
    ).reset_index()
    S.to_csv(os.path.join(args.out, "per_class_summary.csv"), index=False)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
