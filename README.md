# Label coverage bounds for pooled macro F1

Code and aggregate evidence for auditing fold-dependent prediction vocabularies.
The manuscript and bibliography are in the accompanying submission package.
Code is MIT-licensed. Dataset owners retain their original data terms.

## Install

Use Python 3.13. Fit replication uses the pinned experimental environment.

    python -m pip install -r code/requirements.txt
    python -m pip install --no-deps .
    python -m label_availability results/nsl_kdd_official/label_counts.csv --oracle --convention union

The small package requires NumPy and pandas. Its array interface is
coverage_ceiling(train_labels_per_fold, test_labels_per_fold).
The count interfaces are metric_bounds, oracle_sandwich, union_ceiling and
exact_oracle. See code/label_availability for their implementations.

Count input has one row per fold/class with fold, class, training_rows and
test_rows columns. A missing fold column means one fold. Include every
train-only label with zero test support. Otherwise a missing row means the
vocabulary entry is absent. An optional boolean allowed column restricts outputs
within training labels. Minimum-support diagnostics are hard ceilings only for
classifiers enforcing that vocabulary restriction.

## Verify and reproduce

    python code/check_availability.py
    python code/check_branch_oracle.py results
    python code/verify_cic_archive.py results
    python code/audit_scoring_conventions.py results
    python code/run_solver_shapes.py results/solver_shapes.csv

The row-level check compares both solvers and scoring conventions to exhaustive
legal predictions. The varied-vocabulary solver cases are synthetic, with
recorded node limits and MILP timeouts. A node-budget exception certifies no
optimum. Identical vocabularies are collapsed before search. The sandwich remains
available for valid counts.

    python code/run_unsw_extended.py PATH_TO_DATA results
    python code/summarize_revision.py results
    python code/run_gas_models.py PATH_TO_GAS_ZIP results/gas_model_comparison
    python code/run_nsl_kdd_forest.py PATH_TO_NSL_DIRECTORY results/nsl_model_comparison --seeds 42 43 44 45 46
    python code/summarize_nsl_seeds.py results/nsl_model_comparison
    python code/build_revision_figures.py results PATH_TO_FIGURE_DIRECTORY

PATH_TO_DATA contains the original official UNSW train/test CSVs. The extended
runner reuses 115 recorded fits and resumes missing conditions. The current
36-pair grid is results/unsw_complete_pairs/runs.csv. Original sampled-pair
folders remain historical evidence. New routing fields exist only for freshly
fitted conditions. Oracle-assisted routing uses true availability and is a
counterfactual. The separate confidence policy uses a fixed threshold of 0.5.

All six CICIDS2017 configurations were refitted and are recorded separately in
results/cic_full_replication.csv. Archived aggregates are RESULTS_PARSED.csv.
cic_cv_replication.csv and cic_cv_unweighted_replication.csv are historical
two-arm and one-arm subsets. The fitting entry point is
code/clean_repo/ids_full_study.py. code/reproduce_tbench.py verifies saved
aggregates; it does not refit those forests.

make verify runs core checks. make reproduce DATA=PATH_TO_DATA also regenerates
audits, solver checks and missing UNSW conditions. The Dockerfile is an
environment recipe. Docker was unavailable for a build in this session.

## Evidence boundaries

CLAIMS.md maps manuscript numbers to scripts and files. EXTERNAL-AUDIT.md
documents the targeted source audit and unresolved scoring conventions.

CICIDS2017 uses the local MachineLearningCVE files, which have no timestamps.
No corrected Engelen/Lanvin release was found in the research folder, Documents,
Downloads or Research.rar. A last-30-percent within-day/class row-order split is
retained as historical evidence and has no verified temporal cutoff. Input
hashes and split memberships are in results.

Numeric NaN/Inf values receive training-only median imputation. CIC web-label
spelling variants are normalized. UNSW nominal inputs use ordinal encoding,
whereas NSL-KDD uses one-hot encoding. Comparisons across datasets therefore
retain their original preprocessing differences.

Gas uses adjacent batches. CORAL uses unlabeled target features for covariance
alignment and still predicts only source labels. Row-bootstrap intervals
condition on fixed predictions and the selected batches. Pair fits share test
rows and withheld labels, so they are dependent. Oracle-normalized scores are
not comparable across different inventories or test cohorts.

Permanent DOI, external anonymous hosting and independent reproduction remain
pending. The public repository and MIT copyright identify the author.
Historical forced_assignment_gap fields mean the covered-row-first combined destination penalty C-R. New summaries name it explicitly.

Dataset owner pages:
- [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html)
- [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset)
- [NSL-KDD](https://www.unb.ca/cic/datasets/nsl.html)
- [Gas sensor drift](https://doi.org/10.24432/C5RP6W)

To refit the entire UNSW grid independently of archived predictions, use a new
output folder:

    python code/run_unsw_extended.py PATH_TO_DATA results --fresh --outdir fresh_unsw

Equivalently, make refit DATA=PATH_TO_DATA REFIT_OUT=fresh_unsw starts every fit.
An existing output folder is rejected in fresh mode.
