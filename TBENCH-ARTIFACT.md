# Current revision entry points

The current claim map is CLAIMS.md. Run the following from the repository root.

    python code/check_availability.py
    python code/audit_scoring_conventions.py results
    python code/summarize_revision.py results
    python code/summarize_nsl_seeds.py results/nsl_model_comparison
    python code/build_revision_figures.py results regenerated_figures

The complete grid has 36 withheld attack pairs and five forest seeds. Historical
pair subsets remain for provenance. The exact oracle handles positive-support
and inferred-union scoring. Current count audits include fold averages, weighted,
micro and balanced-accuracy ceilings, and restricted-vocabulary thresholds.
Primary normalized input files are under results/availability_counts.

The additional model-family results are results/gas_model_comparison,
results/gas_coral and results/nsl_model_comparison. EXTERNAL-AUDIT.md records
the illustrative source screen. The MIT license covers research code, while
the separately supplied TBench class retains its own submission-only terms.
# TBench artifact

## Historical aggregate verification

Extract the code archive into a clean directory. Use Python 3.13 with the packages pinned in code/requirements.txt. From the repository root run:

    python -B code/reproduce_tbench.py regenerated_figures

This recomputes the gas-model macro F1 from per-fold confusion marginals, the NSL-KDD score from both coverage strata, the exact oracles, the UNSW three-part gaps, and the archived CIC confusion-matrix metrics. It checks all six fresh CIC score records against the archive. It also regenerates two historical figures. Run in a disposable checkout because the checks regenerate some result CSVs in place, including machine-specific timings.

| Manuscript item | Command in fast path or source | Main output or input |
|---|---|---|
| Related work and notation | Editorial tables in manuscript source | main.tex |
| Gas adjacent-batch scores | code/rebuild_gas_figure.py results regenerated_figures | results/gas_drift_adjacent/models.csv and class_hits_by_fold.csv |
| CIC protocol scores | code/verify_cic_archive.py results | results/cic_archive_verification.csv and cic_full_replication.csv |
| Oracle comparison | code/exact_fold_oracle.py results | results/exact_fold_oracles.csv, gas_drift_adjacent/audit.csv and nsl_kdd_official/forest_metrics.csv |
| Coverage regimes | same commands as oracle comparison | results/unsw_partial_coverage/metrics.csv and results/rerun_unsw_official/metrics.csv |
| UNSW five-seed scores | source aggregation in code/summarize_unsw_coverage_sensitivity.py | results/unsw_coverage_sensitivity/summary.csv |
| Three-part gaps | code/check_oracle_and_gaps.py results | results/unsw_three_part_gap.csv |
| CIC seen and unseen counts | code/decompose_cic_lodo.py results | results/cic_lodo_label_decomposition.csv |
| Gas fold chart | code/rebuild_gas_figure.py results regenerated_figures | regenerated_figures/gas_fold_coverage.pdf and results/gas_drift_adjacent/fold_label_counts.csv |
| UNSW pair chart | code/plot_unsw_pair_distribution.py results regenerated_figures | regenerated_figures/unsw_pair_distribution.pdf and results/unsw_coverage_random_pairs/distribution_figure_data.csv |

## Full path

- Download the [UCI gas drift archive](https://archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip). Compare its SHA-256 with results/gas_drift_adjacent/input_sha256.txt. Run code/run_gas_drift.py ARCHIVE results/gas_drift_adjacent --fit. It uses batches 1 through 9 as training batches for their immediate successors, all 128 released features, original labels 1 through 6, and seed 42. Scaling is fit on the previous batch for logistic regression only.
- Download the two published NSL-KDD partition files from the mirror named in README.md and check results/nsl_kdd_official/sha256.txt. Run code/audit_nsl_kdd_coverage.py and code/run_nsl_kdd_forest.py as shown in README.md. The fitted model excludes the label and difficulty fields, uses training-only one-hot encoding and seed 42, and scores the original attack labels.
- Obtain CICIDS2017 and UNSW-NB15 through the owner links in README.md. Check results/dataset_sha256.txt. The README lists the split, verification, and refit entry points. For a complete CIC run, execute code/clean_repo/ids_full_study.py --datasets cic --cic-dir PATH_TO_CICIDS2017 --out PATH_TO_NEW_OUTPUT --no-threshold. The archive includes separately labeled original and fresh aggregate records. For UNSW, use the documented official forest and withholding scripts, including the extra-seeds invocation for the sampled pairs.
- Run code/run_digits_fractional_coverage.py results/digits_fractional_coverage on a fresh output path for the controlled digits demonstration. The scikit-learn version is pinned in code/requirements.txt.

No external clean-room replication is claimed. Only the documented fixed-cohort comparisons are inferred from these results.

## External audit and exact search

The external audit records source links, evaluated tasks, scores, and comparison status in results/published_score_audit.csv. The Friday technical report uses a different scoring denominator or leaves it unspecified, so 0.25 is a conservative upper bound and the artifact does not claim an exact normalized comparison.

Run python code/check_branch_oracle.py results to compare branch-and-bound against enumeration on fixed-seed count cases and the archived gas and digits counts, and regenerate results/oracle_solver_checks.csv. Times are machine-dependent. The repeated-vocabulary case now uses the closed form and supplies no evidence about difficult search. Varied-vocabulary checks and MILP status are in results/solver_shapes.csv. Use python code/exact_fold_oracle.py results --method branch to exercise the standard cases. A node-budget error means the run did not certify an optimum.
