# Label Availability Audit Toolkit

Python tools for calculating label-coverage limits and attainable macro F1 under fold-specific legal output vocabularies.

## Install

```text
python -m pip install .
```

## Count-based CLI

Prepare a CSV with `fold`, `class`, `training_rows`, and `test_rows` columns. Each row represents one fold/class combination. If a legal output is permitted without training examples, add an `allowed` column containing `true` or `false` for each fold/class row.

```text
label-availability counts.csv --oracle --convention support
```

Use `--certificate` to request a rational certificate and routing witness. A search budget exception means the optimum was not certified. For fixed-inventory scoring, pass `--convention fixed --scored-labels ...` with every test-positive class included.

## Python API

```python
from label_availability import count_folds, certified_oracle

counts = count_folds([["A", "B"]], [["A", "B", "C"]])
result = certified_oracle(counts)
print(result["exact_fraction"])  # 5/9
```

The package exposes count-based bounds, exact floating-point search, and rational certification. It does not fit intrusion-detection models or make claims about deployment performance.

## Development checks

```text
python code/check_availability.py
python code/check_vocabulary_groups.py
```

The MIT license applies to the software. Dataset and third-party source terms remain with their respective owners.
