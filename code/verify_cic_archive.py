from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from clean_repo.ids_full_study import agg_from_cm

def main():
    parser = argparse.ArgumentParser(description="Recompute archived CIC metrics from saved confusion matrices.")
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    base = args.results
    runs = pd.read_csv(base / "RESULTS_PARSED.csv").query("dataset == 'cic'")
    rows = []
    for run in runs.itertuples(index=False):
        stem = "_".join([run.dataset, run.variant, run.protocol, run.model, run.arm])
        table = pd.read_csv(base / "confusion" / (stem + ".csv"), index_col=0)
        if list(table.index) != list(table.columns):
            raise ValueError(f"Confusion matrix class order differs: {stem}")
        metrics = agg_from_cm(table.to_numpy(), list(table.index), {"protocol": run.protocol, "arm": run.arm, "seed": run.seed})
        for metric in ("n_eval", "accuracy", "macro_f1", "weighted_f1"):
            recorded = getattr(run, metric)
            if not np.isclose(metrics[metric], recorded, atol=1e-12, rtol=0):
                raise ValueError(f"{stem}: {metric} differs from archived aggregate")
        rows.append(metrics)
    pd.DataFrame(rows).to_csv(base / "cic_archive_verification.csv", index=False)

if __name__ == "__main__":
    main()

