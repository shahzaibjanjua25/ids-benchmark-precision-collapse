# Manuscript claims and regeneration

Commands run from the repository root with Python 3.13 and code/requirements.txt.
Fold-count files for an oracle must include every permitted training label, even
when its test count is zero. Absence of a row means absence of that vocabulary entry.

| Claim | Script | Recorded evidence |
| --- | --- | --- |
| CICIDS2017 six fitted configurations and 0.85347 vs 0.06030 | Fitting: code/clean_repo/ids_full_study.py; aggregate checks: code/reproduce_tbench.py and code/verify_cic_archive.py | results/cic_full_replication.csv and results/confusion |
| Pooled, weighted, micro, balanced-accuracy, union and fold ceilings | code/audit_scoring_conventions.py | results/metric_conventions.csv and results/fold_metric_conventions.csv |
| CIC and NSL label-granularity sensitivity | code/audit_scoring_conventions.py | results/granularity_sensitivity.csv and results/family_mapping.csv |
| Minimum-support sensitivity under a restricted vocabulary | code/audit_scoring_conventions.py | results/threshold_sensitivity.csv |
| Oracle and sandwich, both score conventions | code/check_availability.py and code/label_availability/core.py | deterministic row-level checks and results/metric_conventions.csv |
| Solver shape comparison | code/run_solver_shapes.py and code/oracle_milp.py | results/solver_shapes.csv |
| Original 15 deterministic pair fits | code/run_unsw_coverage_sensitivity.py | results/unsw_coverage_sensitivity/runs.csv |
| Complete pair grid and official five-seed reference | code/run_unsw_extended.py | results/unsw_complete_pairs/runs.csv |
| Five-seed gap decomposition | code/check_oracle_and_gaps.py | results/unsw_three_part_gap.csv |
| Natural gas availability and original baselines | code/run_gas_drift.py | results/gas_drift_adjacent |
| Gas model families and conditional row intervals | code/run_gas_models.py | results/gas_model_comparison |
| Digits availability and fitted score | code/run_digits_fractional_coverage.py | results/digits_fractional_coverage |
| External scoring comparisons | Manual source coding, no fitted values inferred | results/published_score_audit.csv and EXTERNAL-AUDIT.md |

`make verify` runs count/score correctness checks and checks archived CIC scores.
`make reproduce DATA=/path/to/official/UNSW` also regenerates count audits,
solver-shape checks and missing UNSW grid fits. It resumes completed conditions.
Raw datasets must be obtained separately and retain their original licenses.

The Dockerfile is a build recipe. A published image, permanent DOI, and external
anonymous mirror require their respective service accounts. Reproduction by a
second investigator remains pending.
