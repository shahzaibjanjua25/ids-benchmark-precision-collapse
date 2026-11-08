import argparse
import json

import pandas as pd

from .core import exact_oracle, metric_bounds, oracle_sandwich, union_ceiling


def main():
    parser = argparse.ArgumentParser(description="Audit a fold/class count CSV")
    parser.add_argument("counts")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--convention", choices=["support", "union"], default="support")
    parser.add_argument("--max-nodes", type=int, default=1_000_000)
    args = parser.parse_args()
    counts = pd.read_csv(args.counts)
    result = {**metric_bounds(counts), **oracle_sandwich(counts)}
    result["scoring_convention"] = args.convention
    result["union_ceiling"] = union_ceiling(counts)
    if result['coverage_ceiling'] < 1:
        result['warning'] = 'Some true labels are unavailable under the declared legal outputs; interpret the score with its ceiling.'
    if args.oracle:
        result.update(exact_oracle(counts, method="branch", convention=args.convention,
                                   max_choices=args.max_nodes))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
