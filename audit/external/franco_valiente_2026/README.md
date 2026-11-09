# External prediction-matrix audit

This folder contains the ten per-seed confusion matrices used for one external
published-score check:

- Franco-Valiente et al. (2026), *Scaling and Validating a Distributed Training
  and Retraining Pipeline for Network Intrusion Detection*, Electronics 15(18),
  4074. [Article](https://doi.org/10.3390/electronics15184074)
- [Public source artifact](https://github.com/josemifv/distributed-nids-mlops),
  `results/cic_split_modes/confusion/`, the unweighted connection-grouped
  CICIDS2017 runs for seeds 42--51.

`verify_external_artifact_audit.py` computes positive-support macro F1 from each
5 by 5 confusion matrix. The recomputed ten-seed mean is 0.90002 (sample SD
0.05143; 95% t-interval half-width 0.03679), matching the article's 0.900 ±
0.037. Its five-class taxonomy has training support for all five classes,
including U2R (65 rows), so the legal-output ceiling is 1. This is compatible
with the ceiling. The matrices were re-scored, not used to retrain the authors'
model. The audit is one paper and one protocol; it is not a 10--20-paper survey.

`recomputed_seed_scores.csv` preserves the calculated run-level values. The
source repository, article and their licenses remain authoritative for the
upstream materials.
