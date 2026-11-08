# Manuscript-to-evidence map, release 0.8.0

Run from the repository root with the pinned Python environment. The single
saved-evidence command is `python code/reproduce_release.py --mode saved`.

| Item | Regeneration/check | Released evidence |
| --- | --- | --- |
| Table 1: NSL forest seed variation on a fixed cohort | code/summarize_rank_audit.py | results/nsl_model_comparison/confusion_seen_*.csv and confusion_unseen_*.csv; results/manuscript_tables/table_1_nsl_seed_scores.csv |
| Table 2: NSL pipeline scores over five declared seeds and both scoring conventions | code/run_nsl_family_seeds.py DATA OUT; code/build_main_tables.py | audit/nsl_family_plan.md; results/nsl_families/by_seed/*.npz, seed_metrics.csv and seed_summary.csv; results/manuscript_tables/table_2_nsl_families.csv |
| NSL train-only routing score-convention control | code/audit_nsl_destinations.py | results/nsl_destination_audit/*.npz and scores.csv; supplementary discussion only |
| Table 3: natural protocol scores and ceilings | code/build_main_tables.py | results/manuscript_tables/table_3_natural_protocols.csv; original count files and fresh CIC/NSL/gas metrics |
| NSL label-resolution analysis: same five forest matrices, fine labels and five categories | code/audit_nsl_granularity.py | results/nsl_kdd_official/granularity_reanalysis.csv and granularity_reanalysis_summary.csv; code/verify_release_evidence.py |
| CICIDS2017 day-holdout target-resolution analysis: the same prediction matrix at 15 labels, eight families and binary detection | code/audit_cic_target_resolution.py | results/cic_lodo_target_resolution.csv and cic_lodo_target_class_scores.csv; code/verify_release_evidence.py |
| Figure 1: CIC observed/ceiling contrast | code/plot_cic_hero.py OUT | results/cic_full_replication.csv; figures/cic_hero.pdf in paper package |
| 180-fit UNSW full/covered score grid | code/run_rank_audit.py DATA OUT; code/summarize_rank_audit.py | results/rank_audit/confusion/*.npz, runs.csv, rank_summary.csv; matches results/unsw_complete_pairs/runs.csv |
| Gas null ranking result across 19 fits | code/run_gas_models.py ZIP OUT; code/summarize_rank_audit.py | results/gas_model_comparison, results/gas_coral, results/rank_audit/gas_ranks.csv |
| Natural NSL 21/38 and union oracle | code/audit_scoring_conventions.py results; code/exact_fold_oracle.py results | results/nsl_kdd_official/label_counts.csv; results/metric_conventions.csv |
| All six CIC archive/fresh matches | code/verify_cic_archive.py results | results/cic_full_replication.csv; results/RESULTS_PARSED.csv; results/confusion |
| Legal heads and vocabulary-group reduction | code/check_vocabulary_groups.py | 100 seeded explicit-head row-level checks; 300-fold/two-assignment check |
| Both score conventions and bounds | code/check_availability.py | 80 seeded exhaustive row-level cases |
| Grouped exact search/MILP | code/run_solver_shapes.py OUT.csv; code/oracle_milp.py | results/solver_shapes_grouped.csv; exact or bounds with explicit status |
| Literature sample and coding totals | code/build_literature_frame.py OUT; code/verify_release_evidence.py | audit/protocol.md; audit/crossref_20261108/raw, candidate_frame.csv, selected_sample.csv, coding.csv, summary.json |
| Additional source compatibility checks, including the Ayantayo et al. NSL-KDD label-resolution case | manual primary-source reading | EXTERNAL-AUDIT.md; results/published_score_audit.csv; audit/reference_verification.csv; supplement |

The sampling builder reuses cached responses and preserves an existing coding
sheet. Publisher abstracts/reference lists are redacted from public snapshots;
the selection uses titles and DOIs only. The source screen is a single-reviewer,
AI-assisted pilot, not an independently adjudicated systematic review.

Raw-data fitting for current main-paper comparisons is bundled by
`python code/reproduce_release.py --mode refit --out NEW --data UNSW --cic CIC --nsl NSL --gas ZIP`.
Outputs are separate and do not overwrite frozen manuscript results. For the
supplementary/historical controls, individual commands are:

    python code/run_unsw_coverage_sensitivity.py UNSW results_new
    python code/run_unsw_partial_coverage.py --help
    python code/run_digits_fractional_coverage.py digits_new
    python code/check_oracle_and_gaps.py results
    python code/audit_scoring_conventions.py results

Consult `--help` for paths and supported flags. Rejection scoring and
repair-order summaries remain historical controls. NSL covered-row scores use a
different target inventory from full scores; their differences are not treated
as evidence that either ranking is wrong. Conditional bootstrap intervals in the
supplement condition on fixed predictions and assume exchangeable rows.

The Dockerfile is an environment recipe, not a verified image. No Zenodo DOI,
external anonymous mirror, PyPI publication, external adoption or independent
clean-room reproduction is claimed.
