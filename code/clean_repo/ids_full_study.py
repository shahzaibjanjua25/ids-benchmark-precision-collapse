#!/usr/bin/env python3
"""
Run the archived CIC and UNSW pipelines; see --help for settings.

CIC 'time' is a within-day/class ordered-row split. The local MachineLearningCVE
files have no verified timestamps. LODO holds out a capture day and may remove
fine-grained labels from the training vocabulary; it is not an open-set detector.
Finished settings are skipped when resuming an output directory.
"""
import argparse
import glob
import os
import re
import shutil
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_curve
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

warnings.filterwarnings("ignore")
Z = 1.959964
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
UNSW_CAT = ["proto", "state", "service"]
CIC_DROP = {"flow id", "source ip", "src ip", "destination ip", "dst ip", "source port",
            "src port", "timestamp", "flow_id"}


def log(*a):
    print(*a, flush=True)


# statistics
def wilson(k, n, z=Z):
    if n <= 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def rows_from_cm(cm, classes, meta, prevs):
    n_eval = int(cm.sum())
    rows = []
    for i, c in enumerate(classes):
        tp = int(cm[i, i])
        n = int(cm[i].sum())
        m = int(cm[:, i].sum())
        fp, fn = m - tp, n - tp
        p = tp / m if m else np.nan
        r = tp / n if n else np.nan
        plo, phi = wilson(tp, m)
        rlo, rhi = wilson(tp, n)
        fpr = fp / (n_eval - n) if (n_eval - n) > 0 else np.nan
        row = dict(meta, cls=c, support=n, pred_count=m, tp=tp, fp=fp, fn=fn, n_eval=n_eval,
                   precision=p, p_lo=plo, p_hi=phi, recall=r, r_lo=rlo, r_hi=rhi,
                   fpr=fpr, fp_per_tp=(fp / tp) if tp else np.nan)
        for pi in prevs:
            den = (r * pi + fpr * (1 - pi)) if (n and not np.isnan(fpr)) else np.nan
            row[f"op_prec_{pi}"] = (r * pi / den) if (den and den > 0) else np.nan
        rows.append(row)
    return rows


def agg_from_cm(cm, classes, meta):
    N = cm.sum()
    f1s, sup = [], []
    for i in range(len(classes)):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i].sum() - tp
        den = 2 * tp + fp + fn
        f1s.append(2 * tp / den if den else 0.0)
        sup.append(cm[i].sum())
    f1s, sup = np.array(f1s), np.array(sup)
    present = sup > 0
    return dict(meta, n_eval=int(N), accuracy=float(np.trace(cm) / N) if N else np.nan,
                macro_f1=float(f1s[present].mean()) if present.any() else np.nan,
                weighted_f1=float((f1s * sup).sum() / N) if N else np.nan)


def cluster_bootstrap(y_true, y_pred, clusters, classes, B, seed):
    """Resample clusters (not flows); return percentile 95% intervals per class."""
    C = len(classes)
    idx = pd.Index(classes)
    yt = idx.get_indexer(y_true)
    yp = idx.get_indexer(y_pred)
    _, cl = np.unique(clusters, return_inverse=True)
    K = cl.max() + 1
    ok = yt == yp
    tp = np.bincount(cl[ok] * C + yt[ok], minlength=K * C).reshape(K, C).astype(float)
    sup = np.bincount(cl * C + yt, minlength=K * C).reshape(K, C).astype(float)
    prd = np.bincount(cl * C + yp, minlength=K * C).reshape(K, C).astype(float)
    rng = np.random.default_rng(seed)
    P, R = np.empty((B, C)), np.empty((B, C))
    with np.errstate(divide="ignore", invalid="ignore"):
        for b in range(B):
            w = np.bincount(rng.integers(0, K, K), minlength=K).astype(float)
            t, s, d = w @ tp, w @ sup, w @ prd
            P[b] = t / d
            R[b] = t / s
    out = pd.DataFrame({"cls": classes,
                        "boot_p_lo": np.nanpercentile(P, 2.5, axis=0), "boot_p_hi": np.nanpercentile(P, 97.5, axis=0),
                        "boot_r_lo": np.nanpercentile(R, 2.5, axis=0), "boot_r_hi": np.nanpercentile(R, 97.5, axis=0),
                        "n_clusters": K})
    return out


# data
class DS:
    def __init__(self, name, X, y, cat_cols, num_cols, meta, is_train=None):
        self.name, self.X, self.y = name, X, np.asarray(y)
        self.cat_cols, self.num_cols, self.meta, self.is_train = cat_cols, num_cols, meta, is_train

    def subset(self, idx):
        idx = np.asarray(idx)
        return DS(self.name, self.X.iloc[idx].reset_index(drop=True), self.y[idx], self.cat_cols,
                  self.num_cols, self.meta.iloc[idx].reset_index(drop=True),
                  None if self.is_train is None else self.is_train[idx])

    @property
    def has_clusters(self):
        return (self.meta["cluster"].values >= 0).any()


def find_file(d, pattern, what):
    hits = sorted(glob.glob(os.path.join(d, "**", pattern), recursive=True))
    if not hits:
        listing = ", ".join(sorted(os.listdir(d))[:30]) if os.path.isdir(d) else "(folder does not exist)"
        raise FileNotFoundError(f"Could not find {what} ({pattern}) under '{os.path.abspath(d)}'. Contents: {listing}")
    return hits[0]


def load_unsw(d):
    def read(path):
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        df["attack_cat"] = df["attack_cat"].astype(str).str.strip()
        df.loc[df["attack_cat"].str.lower().isin(["benign", "normal", "nan"]), "attack_cat"] = "Normal"
        return df

    tr = read(find_file(d, "*training-set*.csv", "UNSW training CSV"))
    te = read(find_file(d, "*testing-set*.csv", "UNSW testing CSV"))
    df = pd.concat([tr, te], ignore_index=True)
    is_train = np.r_[np.ones(len(tr), bool), np.zeros(len(te), bool)]
    y = df["attack_cat"].values
    X = df.drop(columns=[c for c in ["id", "label", "attack_cat"] if c in df.columns]).copy()
    for c in UNSW_CAT:
        X[c] = X[c].fillna("-").astype(str)
    num = [c for c in X.columns if c not in UNSW_CAT]
    for c in num:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X[num] = X[num].replace([np.inf, -np.inf], np.nan)
    X = X[UNSW_CAT + num]
    meta = pd.DataFrame({"day": "all", "order": np.arange(len(X), dtype=float), "cluster": -1})
    return DS("unsw", X, y, UNSW_CAT, num, meta, is_train)


def norm_label(s):
    s = str(s).strip()
    low = s.lower()
    if low == "benign":
        return "BENIGN"
    if low.startswith("web attack"):
        if "brute" in low:
            return "Web Attack-Brute Force"
        if "xss" in low:
            return "Web Attack-XSS"
        if "sql" in low:
            return "Web Attack-SQL Injection"
    return s


def load_cic(d):
    files = sorted(glob.glob(os.path.join(d, "**", "*.csv"), recursive=True))
    if not files:
        raise FileNotFoundError(f"No CSV files under '{os.path.abspath(d)}'")
    has_ip = {}
    for f in files:
        cols = [c.strip().lower() for c in pd.read_csv(f, nrows=0, encoding="latin-1").columns]
        has_ip[f] = "source ip" in cols
    if any(has_ip.values()):
        keep = [f for f in files if has_ip[f]]
        if len(keep) < len(files):
            log(f"[cic] using {len(keep)} TrafficLabelling files (with Source IP); ignoring {len(files) - len(keep)} others")
        files = keep
    frames, feat_cols = [], None
    for f in files:
        df = pd.read_csv(f, encoding="latin-1", low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        base = os.path.basename(f).lower()
        day = next((x for x in DAYS if base.startswith(x)), os.path.splitext(base)[0])
        lab_col = next(c for c in df.columns if c.lower() == "label")
        lab_map = {v: norm_label(v) for v in df[lab_col].unique()}
        y = df[lab_col].map(lab_map).values
        low = {c.lower(): c for c in df.columns}
        feats = [c for c in df.columns if c.lower() not in CIC_DROP and c != lab_col]
        for c in feats:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        Xf = df[feats].replace([np.inf, -np.inf], np.nan).astype("float32")
        n = len(df)
        order = np.arange(n, dtype=float)
        if "timestamp" in low:
            ts = pd.to_datetime(df[low["timestamp"]], errors="coerce")
            if ts.notna().mean() > 0.9:
                order = ts.ffill().bfill().values.astype("datetime64[ns]").astype("int64").astype(float)
        if "source ip" in low:
            key = day + "|" + df[low["source ip"]].astype(str) + "|" + pd.Series(y).astype(str)
            cluster = key.values
        else:
            cluster = np.full(n, None, dtype=object)
        frames.append((Xf, y, pd.DataFrame({"day": day, "order": order, "cluster": cluster})))
        log(f"[cic] {os.path.basename(f)}: {n} rows, day={day}")
    X = pd.concat([f[0] for f in frames], ignore_index=True)
    y = np.concatenate([f[1] for f in frames])
    meta = pd.concat([f[2] for f in frames], ignore_index=True)
    if meta["cluster"].notna().any():
        meta["cluster"] = pd.factorize(meta["cluster"])[0]
    else:
        meta["cluster"] = -1
    return DS("cic", X, y, [], list(X.columns), meta)


def cap_classes(ds, cap, seed=0):
    if not cap:
        return ds
    rng = np.random.default_rng(seed)
    keep = []
    for c in np.unique(ds.y):
        ix = np.where(ds.y == c)[0]
        if len(ix) > cap:
            ix = rng.choice(ix, cap, replace=False)
        keep.append(ix)
    return ds.subset(np.sort(np.concatenate(keep)))


def hashes(ds):
    hf = pd.util.hash_pandas_object(ds.X, index=False).values
    hl = pd.util.hash_pandas_object(ds.X.assign(_y=ds.y), index=False).values
    return hf, hl


def audit(ds):
    hf, hl = hashes(ds)
    s = pd.DataFrame({"hf": hf, "hl": hl, "y": ds.y})
    s["dup_exact"] = s["hl"].duplicated(keep="first")
    nun = s.groupby("hf")["y"].transform("nunique")
    s["conflict"] = nun > 1
    out = s.groupby("y").agg(n=("y", "size"), exact_duplicate_rows=("dup_exact", "sum"),
                             rows_with_conflicting_label=("conflict", "sum")).reset_index().rename(columns={"y": "cls"})
    out.insert(0, "dataset", ds.name)
    out["dup_fraction"] = out["exact_duplicate_rows"] / out["n"]
    return out


def dedup(ds):
    _, hl = hashes(ds)
    keep = ~pd.Series(hl).duplicated(keep="first").values
    log(f"[{ds.name}] dedup: {len(keep)} -> {int(keep.sum())} rows")
    return ds.subset(np.where(keep)[0])


# models
def build(model, arm, seed, n_est, ds, quick=False):
    num_steps = [("imp", SimpleImputer(strategy="median"))]
    if model == "lr":
        num_steps.append(("sc", StandardScaler()))
    tfs = [("num", Pipeline(num_steps), ds.num_cols)]
    if ds.cat_cols:
        tfs.insert(0, ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), ds.cat_cols))
    pre = ColumnTransformer(tfs)
    cw = {"none": None, "balanced": "balanced", "balanced_subsample": "balanced_subsample",
          "smote_none": None}[arm]
    if model == "rf":
        est = RandomForestClassifier(n_estimators=n_est, min_samples_split=5, min_samples_leaf=2,
                                     class_weight=cw, random_state=seed, n_jobs=-1)
    elif model == "hgb":
        est = HistGradientBoostingClassifier(max_iter=30 if quick else 100, class_weight=cw, random_state=seed)
    elif model == "lr":
        est = LogisticRegression(max_iter=300, class_weight=cw)
    else:
        raise ValueError(model)
    if arm == "smote_none":
        from imblearn.over_sampling import SMOTENC
        from imblearn.pipeline import Pipeline as ImbPipeline
        return ImbPipeline([("pre", pre),
                            ("smote", SMOTENC(categorical_features=list(range(len(ds.cat_cols))),
                                              sampling_strategy="not majority", random_state=seed)),
                            ("est", est)])
    return Pipeline([("pre", pre), ("est", est)])


def full_proba(m, X, classes):
    p = m.predict_proba(X)
    out = np.zeros((p.shape[0], len(classes)))
    out[:, pd.Index(classes).get_indexer(m.classes_)] = p
    return out


def get_splits(ds, protocol, seed):
    n = len(ds.y)
    if protocol == "official":
        return [(np.where(ds.is_train)[0], np.where(~ds.is_train)[0])]
    if protocol == "cv":
        return list(StratifiedKFold(5, shuffle=True, random_state=seed).split(np.zeros(n), ds.y))
    if protocol == "time":
        tr = np.zeros(n, bool)
        g = pd.DataFrame({"day": ds.meta["day"].values, "y": ds.y, "o": ds.meta["order"].values, "i": np.arange(n)})
        for _, sub in g.groupby(["day", "y"], sort=False):
            sub = sub.sort_values("o", kind="stable")
            k = max(1, int(np.ceil(0.7 * len(sub))))
            tr[sub["i"].values[:k]] = True
        return [(np.where(tr)[0], np.where(~tr)[0])]
    if protocol == "lodo":
        days = ds.meta["day"].values
        return [(np.where(days != d)[0], np.where(days == d)[0]) for d in sorted(set(days))]
    raise ValueError(protocol)


def threshold_eval(model, arm, seed, args, ds, tr, te, classes, meta, prevs):
    ytr = ds.y[tr]
    try:
        fit_i, val_i = train_test_split(np.arange(len(tr)), test_size=0.2, stratify=ytr, random_state=seed)
    except ValueError:
        fit_i, val_i = train_test_split(np.arange(len(tr)), test_size=0.2, random_state=seed)
    n_est = args.cic_n_estimators if ds.name == "cic" else args.n_estimators
    m = build(model, arm, seed, n_est, ds, args.quick)
    m.fit(ds.X.iloc[tr[fit_i]], ds.y[tr[fit_i]])
    pv = full_proba(m, ds.X.iloc[tr[val_i]], classes)
    pt = full_proba(m, ds.X.iloc[te], classes)
    yv = ds.y[tr[val_i]]
    thr = np.full(len(classes), 0.5)
    for j, c in enumerate(classes):
        pos = yv == c
        if pos.sum() == 0 or pos.all():
            continue
        pr, rc, th = precision_recall_curve(pos, pv[:, j])
        if len(th) == 0:
            continue
        f = 2 * pr[:-1] * rc[:-1] / np.maximum(pr[:-1] + rc[:-1], 1e-12)
        thr[j] = max(th[int(np.argmax(f))], 1e-3)
    cl = np.array(classes)
    rows = []
    for mode, pred in (("default_argmax", cl[np.argmax(pt, axis=1)]), ("tuned", cl[np.argmax(pt / thr, axis=1)])):
        cm = confusion_matrix(ds.y[te], pred, labels=classes)
        for r in rows_from_cm(cm, classes, dict(meta, mode=mode), prevs):
            r["threshold"] = thr[classes.index(r["cls"])] if mode == "tuned" else 0.5
            rows.append(r)
    return rows


# runner
def append_csv(df, path):
    df.to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def arms_for(dsname, protocol, model, args):
    if model != "rf":
        return ["none", "balanced"]
    if args.rf_arms:
        return [a for a in args.rf_arms if not (a == "smote_none" and dsname == "cic")]
    if dsname == "unsw":
        return ["none", "balanced", "balanced_subsample", "smote_none"] if protocol == "official" \
            else ["none", "balanced_subsample"]
    return ["none", "balanced_subsample"]


def seeds_for(dsname, protocol, model, args):
    if model != "rf":
        return [args.seeds[0]]
    if protocol == "cv":
        return args.cv_seeds
    if dsname == "cic":
        return args.cic_seeds
    return args.seeds


def run_dataset(ds_raw, args, out, prevs, done):
    name = ds_raw.name
    protocols = args.unsw_protocols if name == "unsw" else args.cic_protocols
    models = args.unsw_models if name == "unsw" else args.cic_models
    variants = args.unsw_variants if name == "unsw" else args.cic_variants
    primary = "official" if name == "unsw" else "time"
    for variant in variants:
        ds = dedup(ds_raw) if variant == "dedup" else ds_raw
        classes = sorted(set(ds.y))
        log(f"[{name}/{variant}] rows={len(ds.y)} classes={classes}")
        for protocol in protocols:
            for model in models:
                for arm in arms_for(name, protocol, model, args):
                    key = f"{name}|{variant}|{protocol}|{model}|{arm}"
                    if key in done:
                        log(f"skip (done): {key}")
                        continue
                    t0 = time.time()
                    seeds = seeds_for(name, protocol, model, args)
                    cm_sum = np.zeros((len(classes), len(classes)), dtype=np.int64)
                    long_rows, agg_rows, thr_rows, boot_rows = [], [], [], []
                    for seed in seeds:
                        meta = dict(dataset=name, variant=variant, protocol=protocol, model=model, arm=arm, seed=seed)
                        n_est = args.cic_n_estimators if name == "cic" else args.n_estimators
                        yt_all, yp_all, ix_all = [], [], []
                        splits = get_splits(ds, protocol, seed)
                        for tr, te in splits:
                            m = build(model, arm, seed, n_est, ds, args.quick)
                            m.fit(ds.X.iloc[tr], ds.y[tr])
                            yp_all.append(m.predict(ds.X.iloc[te]))
                            yt_all.append(ds.y[te])
                            ix_all.append(te)
                        yt, yp, ix = np.concatenate(yt_all), np.concatenate(yp_all), np.concatenate(ix_all)
                        cm = confusion_matrix(yt, yp, labels=classes)
                        cm_sum += cm
                        rows = rows_from_cm(cm, classes, meta, prevs)
                        long_rows += rows
                        agg_rows.append(agg_from_cm(cm, classes, meta))
                        log(f"  [{key} seed={seed}] acc={agg_rows[-1]['accuracy']:.4f} "
                            f"macroF1={agg_rows[-1]['macro_f1']:.4f} ({time.time() - t0:.0f}s)")
                        first = seed == seeds[0]
                        if (first and model == "rf" and protocol in ("cv", "time") and ds.has_clusters):
                            bt = cluster_bootstrap(yt, yp, ds.meta["cluster"].values[ix], classes, args.n_boot, seed)
                            wil = pd.DataFrame(rows)[["cls", "support", "precision", "p_lo", "p_hi", "recall", "r_lo", "r_hi"]]
                            bt = wil.merge(bt, on="cls")
                            for k, v in meta.items():
                                bt[k] = v
                            bt["r_width_wilson"] = bt["r_hi"] - bt["r_lo"]
                            bt["r_width_boot"] = bt["boot_r_hi"] - bt["boot_r_lo"]
                            bt["r_width_ratio"] = bt["r_width_boot"] / bt["r_width_wilson"]
                            bt["p_width_wilson"] = bt["p_hi"] - bt["p_lo"]
                            bt["p_width_boot"] = bt["boot_p_hi"] - bt["boot_p_lo"]
                            bt["p_width_ratio"] = bt["p_width_boot"] / bt["p_width_wilson"]
                            boot_rows.append(bt)
                        if (first and not args.no_threshold and protocol == primary and len(splits) == 1
                                and (model == "rf" or args.threshold_all_models)):
                            tr, te = splits[0]
                            thr_rows += threshold_eval(model, arm, seed, args, ds, tr, te, classes, meta, prevs)
                    append_csv(pd.DataFrame(long_rows), os.path.join(out, "per_class_long.csv"))
                    append_csv(pd.DataFrame(agg_rows), os.path.join(out, "aggregate.csv"))
                    if thr_rows:
                        append_csv(pd.DataFrame(thr_rows), os.path.join(out, "threshold.csv"))
                    if boot_rows:
                        append_csv(pd.concat(boot_rows), os.path.join(out, "cluster_bootstrap.csv"))
                    os.makedirs(os.path.join(out, "confusion"), exist_ok=True)
                    pd.DataFrame(cm_sum, index=classes, columns=classes).to_csv(
                        os.path.join(out, "confusion", key.replace("|", "_") + ".csv"))
                    fps = []
                    for j, c in enumerate(classes):
                        col = cm_sum[:, j].copy()
                        fp_tot = int(col.sum() - col[j])
                        col[j] = 0
                        for i in np.argsort(-col)[:5]:
                            if col[i] > 0:
                                fps.append(dict(dataset=name, variant=variant, protocol=protocol, model=model,
                                                arm=arm, predicted_cls=c, true_cls=classes[i], count=int(col[i]),
                                                share_of_fp=col[i] / fp_tot if fp_tot else np.nan, fp_total=fp_tot))
                    if fps:
                        append_csv(pd.DataFrame(fps), os.path.join(out, "fp_sources.csv"))
                    with open(os.path.join(out, "done.txt"), "a") as fh:
                        fh.write(key + "\n")
                    done.add(key)
                    log(f"done {key} in {time.time() - t0:.0f}s")


# summary / report
def make_summary(out, prevs, thr):
    p = os.path.join(out, "per_class_long.csv")
    if not os.path.exists(p):
        return
    L = pd.read_csv(p)
    L["p_width"], L["r_width"] = L["p_hi"] - L["p_lo"], L["r_hi"] - L["r_lo"]
    agg = dict(support=("support", "first"), n_seeds=("seed", "nunique"),
               precision_mean=("precision", "mean"), precision_sd=("precision", "std"),
               recall_mean=("recall", "mean"), recall_sd=("recall", "std"),
               p_wilson_width=("p_width", "mean"), r_wilson_width=("r_width", "mean"),
               fp_per_tp=("fp_per_tp", "mean"))
    for pi in prevs:
        agg[f"op_prec_{pi}"] = (f"op_prec_{pi}", "mean")
    S = L.groupby(["dataset", "variant", "protocol", "model", "arm", "cls"], sort=False).agg(**agg).reset_index()
    S.to_csv(os.path.join(out, "per_class_summary.csv"), index=False)

    lines = ["REPORT (auto-generated; numbers come straight from the CSVs)", "=" * 70, ""]
    lines.append(f"1. Precision by arm for RF. '*' marks precision < {thr} (pre-registered collapse threshold).")
    rf = S[S.model == "rf"]
    for (d, v, pr), g in rf.groupby(["dataset", "variant", "protocol"], sort=False):
        piv = g.pivot(index="cls", columns="arm", values="precision_mean")
        txt = piv.round(3).astype(str)
        txt = txt.where(~(piv < thr), txt + "*")
        sup = g.drop_duplicates("cls").set_index("cls")["support"]
        txt.insert(0, "support", sup.reindex(txt.index).astype(int))
        lines += [f"\n[{d} / {v} / {pr}]", txt.to_string()]
        lines.append("  Arms with collapse: " + ", ".join(
            f"{c}: {[a for a in piv.columns if piv.loc[c, a] < thr]}" for c in piv.index
            if any(piv.loc[c] < thr)) if (piv < thr).any().any() else "  No class below threshold.")
    lines += ["", "2. Seed SD vs Wilson half-width (RF, classes with ratio > 1 mean Wilson understates seed noise).", ""]
    g = rf[rf.n_seeds > 1].copy()
    if len(g):
        g["sd_over_halfwidth_precision"] = g["precision_sd"] / (g["p_wilson_width"] / 2)
        g["sd_over_halfwidth_recall"] = g["recall_sd"] / (g["r_wilson_width"] / 2)
        lines.append(g[["dataset", "variant", "protocol", "arm", "cls", "precision_sd", "p_wilson_width",
                        "sd_over_halfwidth_precision", "recall_sd", "r_wilson_width",
                        "sd_over_halfwidth_recall"]].round(3).to_string(index=False))
    else:
        lines.append("(no multi-seed settings found)")
    bp = os.path.join(out, "cluster_bootstrap.csv")
    lines += ["", "3. Cluster bootstrap vs Wilson (recall CI width ratio; >1 means Wilson too narrow).", ""]
    if os.path.exists(bp):
        B = pd.read_csv(bp)
        lines.append(B[["dataset", "protocol", "arm", "cls", "support", "n_clusters", "r_width_wilson",
                        "r_width_boot", "r_width_ratio", "p_width_ratio"]].round(3).to_string(index=False))
    else:
        lines.append("(skipped: needs CIC TrafficLabelling CSVs with 'Source IP')")
    tp_ = os.path.join(out, "threshold.csv")
    lines += ["", "4. Threshold tuning (thresholds chosen on a validation split of TRAIN only).", ""]
    if os.path.exists(tp_):
        T = pd.read_csv(tp_)
        w = T.pivot_table(index=["dataset", "variant", "arm", "cls"], columns="mode", values=["precision", "recall"])
        lines.append(w.round(3).to_string())
    else:
        lines.append("(not run)")
    lines += ["", "5. Base-rate projection: operational precision at prevalence of each class (RF, primary protocol).", ""]
    cols = ["dataset", "variant", "protocol", "arm", "cls", "precision_mean"] + [f"op_prec_{pi}" for pi in prevs]
    prim = rf[((rf.dataset == "unsw") & (rf.protocol == "official")) | ((rf.dataset == "cic") & (rf.protocol == "time"))]
    lines.append(prim[cols].round(4).to_string(index=False) if len(prim) else "(none)")
    lines += ["", "Files: per_class_long.csv, per_class_summary.csv, aggregate.csv, confusion/, fp_sources.csv,",
              "       threshold.csv, cluster_bootstrap.csv, data_audit.csv"]
    with open(os.path.join(out, "report.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    log("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--unsw-dir", default=".")
    ap.add_argument("--cic-dir", default="CICIDS2017")
    ap.add_argument("--out", default="study_out")
    ap.add_argument("--datasets", nargs="+", default=["unsw", "cic"], choices=["unsw", "cic"])
    ap.add_argument("--quick", action="store_true", help="tiny smoke test (class-capped, few trees, 1 seed)")
    ap.add_argument("--fresh", action="store_true", help="delete --out first")
    ap.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    ap.add_argument("--cv-seeds", nargs="+", type=int, default=[42])
    ap.add_argument("--cic-seeds", nargs="+", type=int, default=[42])
    ap.add_argument("--n-estimators", type=int, default=200)
    ap.add_argument("--cic-n-estimators", type=int, default=100)
    ap.add_argument("--cap-per-class", type=int, default=0, help="cap rows per class (0 = off)")
    ap.add_argument("--unsw-models", nargs="+", default=["rf", "hgb", "lr"], choices=["rf", "hgb", "lr"])
    ap.add_argument("--cic-models", nargs="+", default=["rf"], choices=["rf", "hgb", "lr"])
    ap.add_argument("--unsw-protocols", nargs="+", default=["official", "cv"], choices=["official", "cv"])
    ap.add_argument("--cic-protocols", nargs="+", default=["cv", "time", "lodo"], choices=["cv", "time", "lodo"])
    ap.add_argument("--unsw-variants", nargs="+", default=["raw", "dedup"], choices=["raw", "dedup"])
    ap.add_argument("--cic-variants", nargs="+", default=["raw"], choices=["raw", "dedup"])
    ap.add_argument("--rf-arms", nargs="+", default=None,
                    choices=["none", "balanced", "balanced_subsample", "smote_none"])
    ap.add_argument("--no-threshold", action="store_true")
    ap.add_argument("--threshold-all-models", action="store_true")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--prevalences", nargs="+", type=float, default=[0.001, 0.01])
    ap.add_argument("--collapse-thr", type=float, default=0.5)
    args = ap.parse_args()

    if args.quick:
        args.seeds = args.cv_seeds = args.cic_seeds = [42, 43]
        args.n_estimators, args.cic_n_estimators = 30, 20
        args.cap_per_class = args.cap_per_class or 3000
        args.n_boot = 200
    if args.fresh and os.path.isdir(args.out):
        shutil.rmtree(args.out)
    os.makedirs(args.out, exist_ok=True)
    dpath = os.path.join(args.out, "done.txt")
    done = set(open(dpath).read().split()) if os.path.exists(dpath) else set()

    aud = []
    for name in args.datasets:
        t0 = time.time()
        ds = load_unsw(args.unsw_dir) if name == "unsw" else load_cic(args.cic_dir)
        log(f"[{name}] loaded {len(ds.y)} rows, {ds.X.shape[1]} features in {time.time() - t0:.0f}s")
        ds = cap_classes(ds, args.cap_per_class)
        if args.cap_per_class:
            log(f"[{name}] capped to {len(ds.y)} rows ({args.cap_per_class}/class)")
        if os.path.exists(os.path.join(args.out, "data_audit.csv")) is False or name not in done:
            aud.append(audit(ds))
            append_csv(aud[-1], os.path.join(args.out, "data_audit.csv"))
        run_dataset(ds, args, args.out, args.prevalences, done)
        del ds
    make_summary(args.out, args.prevalences, args.collapse_thr)


if __name__ == "__main__":
    main()
