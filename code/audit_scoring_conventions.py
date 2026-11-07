"""Regenerate metric, threshold, and label-granularity audits."""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from label_availability import exact_oracle, metric_bounds, oracle_sandwich, union_ceiling


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
args = parser.parse_args()
p = args.results
cic = pd.read_csv(p / "cic_lodo_label_counts.csv").rename(columns={"day": "fold"})
day_counts = cic.pivot(index="fold", columns="class", values="test_rows").fillna(0).astype(int)
cic = day_counts.stack().rename("test_rows").reset_index()
cic["training_rows"] = cic["class"].map(day_counts.sum()) - cic.test_rows
nsl = pd.read_csv(p / "nsl_kdd_official/label_counts.csv").assign(fold=0)
cases = {"CICIDS2017 day holdout": cic, "NSL-KDD official": nsl,
         "UNSW mixed": pd.read_csv(p / "unsw_partial_coverage/fold_label_counts.csv").assign(fold=0),
         "Gas adjacent batch": pd.read_csv(p / "gas_drift_adjacent/fold_label_counts.csv"),
         "Digits partial": pd.read_csv(p / "digits_fractional_coverage/fold_label_counts.csv")}
cases["UNSW official"] = pd.read_csv(p / "unsw_official_label_counts.csv").assign(fold=0)
rows, fold_rows, thresholds = [], [], []
(p / "availability_counts").mkdir(exist_ok=True)
for name, counts in cases.items():
    filename = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") + ".csv"
    counts.to_csv(p / "availability_counts" / filename, index=False)
    bounds = metric_bounds(counts)
    rows.append({"case": name, **bounds, **oracle_sandwich(counts),
                 "union_ceiling": union_ceiling(counts),
                 "support_oracle": exact_oracle(counts, method="branch")["exact_oracle"],
                 "union_oracle": exact_oracle(counts, method="branch", convention="union")["exact_oracle"]})
    for fold, group in counts.groupby("fold"):
        fold_rows.append({"case": name, "fold": fold, **metric_bounds(group),
                          "support_oracle": exact_oracle(group, method="branch")["exact_oracle"]})
    for threshold in [1, 2, 5, 10, 20, 50, 100, 500, 1000]:
        restricted = counts.assign(allowed=counts.training_rows.ge(threshold))
        try:
            score = metric_bounds(restricted)["coverage_ceiling"]
        except ValueError:
            score = np.nan
        thresholds.append({"case": name, "minimum_training_count": threshold,
                           "restricted_vocabulary_ceiling": score})
pd.DataFrame(rows).to_csv(p / "metric_conventions.csv", index=False)
pd.DataFrame(fold_rows).to_csv(p / "fold_metric_conventions.csv", index=False)
pd.DataFrame(thresholds).to_csv(p / "threshold_sensitivity.csv", index=False)

def aggregate(counts, mapping):
    data = counts.copy()
    data["class"] = data["class"].map(mapping)
    assert data["class"].notna().all()
    return data.groupby(["fold", "class"], as_index=False)[["training_rows", "test_rows"]].sum()

labels = cic["class"].unique()
web = {label: "Web attack" if label.startswith("Web Attack") else label for label in labels}
binary = {label: "BENIGN" if label == "BENIGN" else "ATTACK" for label in labels}
family = {}
for label in labels:
    if label.startswith("DoS") or label == "DDoS":
        family[label] = "DoS"
    elif label.endswith("Patator"):
        family[label] = "Credential brute force"
    elif label.startswith("Web Attack"):
        family[label] = "Web attack"
    else:
        family[label] = label
nsl_mapping = {"normal": "Normal"}
groups = {
    "DoS": "neptune smurf back teardrop pod land apache2 processtable mailbomb udpstorm",
    "Probe": "satan ipsweep portsweep nmap mscan saint",
    "R2L": "warezclient guess_passwd warezmaster imap ftp_write multihop phf spy snmpguess snmpgetattack httptunnel named sendmail xlock xsnoop worm",
    "U2R": "buffer_overflow rootkit loadmodule perl ps xterm sqlattack"}
for group, names in groups.items():
    nsl_mapping.update(dict.fromkeys(names.split(), group))
granularity = []
for name, counts in [("CIC original", cic), ("CIC web merged", aggregate(cic, web)),
                     ("CIC family (declared mapping)", aggregate(cic, family)),
                     ("CIC binary", aggregate(cic, binary)), ("NSL original", nsl),
                     ("NSL five category", aggregate(nsl, nsl_mapping))]:
    granularity.append({"case": name, "test_labels": counts.loc[counts.test_rows.gt(0), "class"].nunique(),
                        **metric_bounds(counts)})
pd.DataFrame(granularity).to_csv(p / "granularity_sensitivity.csv", index=False)
pd.DataFrame([{"dataset": "CIC", "original": k, "family": v} for k, v in family.items()] +
             [{"dataset": "NSL", "original": k, "family": v} for k, v in nsl_mapping.items()]).to_csv(p / "family_mapping.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))
print(pd.DataFrame(granularity).to_string(index=False))
