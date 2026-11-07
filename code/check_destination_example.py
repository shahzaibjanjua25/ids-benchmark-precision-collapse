"""A constructed ranking inversion, with the cohort and output vocabulary fixed."""
import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from label_availability import count_folds, exact_oracle


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("out")
args = parser.parse_args()
truth = np.array(["A"] * 100 + ["B"] + ["C"] * 100)
first = np.array(["A"] * 100 + ["B"] + ["B"] * 100)
second = np.array(["B"] + ["A"] * 99 + ["B"] + ["A"] * 100)
seen = truth != "C"
counts = count_folds([["A", "B"]], [truth])
oracle = exact_oracle(counts)["exact_oracle"]
rows = []
for name, pred in [("perfect covered; unavailable to B", first),
                   ("one covered error; unavailable to A", second)]:
    rows.append({"case": "constructed", "policy": name,
                 "covered_macro_f1": f1_score(truth[seen], pred[seen], labels=["A", "B"], average="macro"),
                 "full_macro_f1": f1_score(truth, pred, labels=["A", "B", "C"], average="macro"),
                 "oracle": oracle})
assert rows[0]["covered_macro_f1"] > rows[1]["covered_macro_f1"]
assert rows[0]["full_macro_f1"] < rows[1]["full_macro_f1"]
pd.DataFrame(rows).to_csv(args.out, index=False)
print(pd.DataFrame(rows).to_string(index=False))
