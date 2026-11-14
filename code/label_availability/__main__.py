import argparse
import json

import pandas as pd

from .core import exact_oracle, metric_bounds, oracle_sandwich, union_ceiling
from .certified import certified_oracle


def main():
    parser = argparse.ArgumentParser(description="Audit a fold/class count CSV")
    parser.add_argument("counts")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--convention", choices=["support", "union", "fixed"], default="support")
    parser.add_argument("--certificate", action="store_true", help="Enumerate with rational arithmetic and return a routing witness")
    parser.add_argument("--scored-labels", nargs="+", help="Fixed scored inventory (CSV string labels), including all true labels")
    parser.add_argument("--max-nodes", type=int, default=1_000_000)
    args = parser.parse_args()
    counts = pd.read_csv(args.counts)
    if args.convention == "fixed":
        if not args.scored_labels:
            parser.error("--convention fixed requires --scored-labels")
        counts["class"] = counts["class"].astype(str)
        result = certified_oracle(counts, convention="fixed", scored_labels=args.scored_labels,
                                  max_assignments=args.max_nodes)
        print(json.dumps(result, indent=2))
        return
    result = {**metric_bounds(counts), **oracle_sandwich(counts)}
    result["scoring_convention"] = args.convention
    result["union_ceiling"] = union_ceiling(counts)
    if result['coverage_ceiling'] < 1:
        result['warning'] = 'Some true labels are unavailable under the declared legal outputs; interpret the score with its ceiling.'
    if args.certificate:
        result.update(certified_oracle(counts, convention=args.convention, max_assignments=args.max_nodes))
    elif args.oracle:
        result.update(exact_oracle(counts, method="branch", convention=args.convention,
                                   max_choices=args.max_nodes))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
