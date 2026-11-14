# Current evidence map

Original commit: `33f16a6cd72506f5c9fe816af36f9f6908331ad4`.
Branch: `research/publication-ready-revision` (branch name is not a readiness claim).

| Claim / artifact | Executed source and evidence |
|---|---|
| Original saved numerical evidence | `code/reproduce_release.py --mode saved`, run at original commit in a detached worktree; `original_commit_saved.log` |
| Original solvers and independent MILP | `code/reproduce_release.py --mode solvers`, original worktree; `original_commit_solvers.log` |
| Revised software and selected saved evidence | `python code/reproduce_revision.py`; machine-readable `verification_run.json` records exit codes and captured outputs |
| Rational exactness and feasible routing | `code/check_certified.py`; `results/revision_20261115/rational_validation.json`; 240 inputs, 3 conventions, 720 comparisons |
| Official-split fresh matched models | `code/run_revision_nsl.py ../work/data results/revision_20261115/nsl_matched`; 6 fits, NPZ predictions, counts and manifest |
| Overlap-controlled fresh matched models | same entry point, `--remove-feature-overlap`; `results/revision_20261115/nsl_no_feature_overlap`; 6 fits |
| Independent overlap and prediction check | `code/verify_revision_results.py --data ../work/data`; exact pandas merge, 658 removed rows; `fresh_verification.log`, `result_verification.json` |
| Exact historical replication | Three fresh RF confusion matrices equal the original seen+unseen matrices cell for cell; checked in verifier |
| Historical five-seed NSL projection | `code/audit_nsl_granularity.py`; `results/nsl_kdd_official/granularity_reanalysis*.csv` |
| CIC target-resolution results | `code/audit_cic_target_resolution.py`; `results/cic_lodo_target_resolution.csv` and class scores |
| Corrected CIC saved evidence | `code/verify_cic_corrected_friday.py`; nine historical fits, chronology, label counts, confusion and binary scores checked; raw refits not repeated |
| First published paper | `code/verify_external_artifact_audit.py`; existing ten saved matrices under audit/external; reproduced mean 0.90002 |
| Second published paper | `code/audit_ciciot2023_published.py --source-pdf ../work/sources/ciciot2023.pdf`; 128 cells checked against PDF; provenance and 2 matrices under results/revision_20261115/ciciot2023_published |
| Reference existence / metadata | `code/verify_revision_references.py`; 14/16 Crossref successes, 2 rate limits; authoritative page fallbacks in audit records |
| Source-level interpretations | `audit/revision_20261115/sources.csv`; not numerically reproduced model outputs |
| Tables and figure | `code/build_revision_paper.py` and `code/plot_revision_targets.py`; CSV provenance in paper/revision/generated/table_sources.json |
| PDF | Typst 0.15.2; `paper/revision/*.typ`; compiled PDFs and page QA record |
| Package | 0.10.0 wheel built with no build isolation; clean-target import and 5/9 API smoke passed; wheel SHA-256 recorded in manifest |
| Inventory | `code/audit_revision_inventory.py`; complete path/syntax inventory, focused semantic audit, result hashes |

`../work/data` and `../work/sources` are execution-session inputs, not delivery
prerequisites. Portable commands use `PATH_TO_NSL` and `--source-pdf PATH_TO_PDF`.
The saved audit re-scores without requiring raw data. The publisher PDF is not
redistributed in this bundle; its URL, hash and verified cells are retained.

The ordinary public data mirror was downloaded as requested. No raw data, tokens,
browser state, credentials or source-paper full text is committed. The original
datasets and published counts keep their attribution and usage conditions.

## Checks intentionally not described as completed

- Every historical raw-data refit or every script executed.
- Independent human replication or external peer review.
- Twenty complete independent published-study audits.
- Field-wide prevalence of incompatible scores, or any verified ceiling violation.
- Definitive mathematical priority for the exact vocabulary characterization.
- Native publisher-class/Word compilation and full journal submission compliance.
- GitHub authentication or a live remote push (the package supplies the final action).

Initial baseline attempts without SciPy/scikit-learn failed due to missing
dependencies. The required packages were installed in a workspace-local target;
the original-commit saved and solver suites were then rerun. All current suite
statuses must be read from their captured exit codes. Timed-out stress-case
optimizers inside otherwise successful suites remain uncertified cases.
