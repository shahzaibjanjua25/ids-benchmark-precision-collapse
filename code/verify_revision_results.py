"""Independent checks of fresh saved predictions, overlap arm and old matrices."""
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from label_availability import certified_oracle

ROOT = Path(__file__).resolve().parents[1]


def macro(truth, pred, inventory):
    result = []
    for label in inventory:
        t, p = truth == label, pred == label
        denominator = int(t.sum()) + int(p.sum())
        result.append(2 * int((t & p).sum()) / denominator if denominator else 0.0)
    return sum(result) / len(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, help="Recheck overlap through an independent exact pandas merge")
    args = parser.parse_args()
    if args.data:
        training, testing = [pd.read_csv(args.data / f"KDD{part}+.txt", header=None) for part in ["Train", "Test"]]
        matching = training.iloc[:, :41].reset_index(names="source_row").merge(
            testing.iloc[:, :41].drop_duplicates(), on=list(range(41)), how="left", indicator=True)
        excluded = matching.loc[matching._merge.eq("both"), "source_row"].to_numpy()
        assert len(excluded) == 658
        for arm in ["nsl_matched", "nsl_no_feature_overlap"]:
            ids = np.arange(len(training))
            if arm == "nsl_no_feature_overlap":
                ids = np.setdiff1d(ids, excluded)
            saved = np.load(ROOT / "results/revision_20261115" / arm / "split_membership.npz")
            assert np.array_equal(saved['training_source_rows'], ids)
            assert np.array_equal(saved['test_source_rows'], np.arange(len(testing)))
    verified = []
    mapping_frame = pd.read_csv(ROOT / "results/family_mapping.csv")
    mapping = dict(mapping_frame.loc[mapping_frame.dataset.eq("NSL"), ["original", "family"]].itertuples(index=False, name=None))
    for arm in ["nsl_matched", "nsl_no_feature_overlap"]:
        out = ROOT / "results/revision_20261115" / arm
        runs = pd.read_csv(out / "runs.csv")
        assert len(runs) == 6 and not runs.duplicated(["model", "seed"]).any()
        counts = pd.read_csv(out / "label_counts.csv")
        cert = certified_oracle(counts)
        assert cert["exact_fraction"] == "21/38"
        train_labels = set(counts.loc[counts.training_rows.gt(0), "class"])
        for row in runs.itertuples():
            data = np.load(out / f"{row.model}_{row.seed}.npz", allow_pickle=False)
            truth, pred, labels, cm = [data[k] for k in ["truth", "prediction", "labels", "confusion"]]
            assert len(truth) == len(pred) == 22544
            assert set(pred).issubset(train_labels)
            rebuilt = np.array([[sum((truth == a) & (pred == b)) for b in labels] for a in labels])
            np.testing.assert_array_equal(cm, rebuilt)
            assert abs(macro(truth, pred, set(truth)) - row.fine_macro_f1) < 1e-12
            assert abs(macro(truth, pred, set(truth) | set(pred)) - row.union_macro_f1) < 1e-12
            cy, cp = np.array([mapping[k] for k in truth]), np.array([mapping[k] for k in pred])
            assert abs(macro(cy, cp, set(cy)) - row.category_macro_f1) < 1e-12
            if arm == "nsl_matched" and row.model == "random_forest":
                folder = ROOT / "results/nsl_model_comparison"
                historical = sum(pd.read_csv(folder / f"confusion_{kind}_{row.seed}.csv", index_col=0)
                                 for kind in ["seen", "unseen"])
                historical = historical.reindex(index=labels, columns=labels)
                np.testing.assert_array_equal(cm, historical.to_numpy())
            verified.append(f"{arm}/{row.model}/{row.seed}")
        manifest = json.loads((out / "manifest.json").read_text())
        assert manifest["training_rows"] == (125973 if arm == "nsl_matched" else 125315)
        assert manifest["exact_feature_overlap_between_partitions"] == (654 if arm == "nsl_matched" else 0)
    external = pd.read_csv(ROOT / "results/revision_20261115/ciciot2023_published/summary.csv")
    assert len(external) == 2 and set(external.test_rows) == {10340161}
    assert external.absolute_difference.gt(1e-7).all()
    out = ROOT / "review/revision_20261115/result_verification.json"
    out.write_text(json.dumps({"fresh_predictions_recomputed": verified,
                               "historical_forest_matrix_matches": 3,
                               "feature_overlap_control": "zero exact feature overlap after removing 658 training rows",
                               "external_reconciliation": "Two mismatches retained as unresolved, not ceiling violations",
                               "passed": True}, indent=2), encoding="utf8")
    print("12 fresh prediction sets verified; 3 old forest matrices reproduced exactly")


if __name__ == "__main__":
    main()
