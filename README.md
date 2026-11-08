# Label Coverage Bounds Pooled Macro F1: A Reporting Diagnostic for Closed-Set IDS Benchmarks

Release 0.7.0: code, manuscript source and evidence for auditing fold-dependent
legal prediction vocabularies. The repository URL retains its historical name.
The reporting check concerns score attainability; the comparisons are tied to
their declared fixed test cohorts.

On the official original-label NSL-KDD split, 21 of 38 test labels are available
to a training-restricted model. Reaggregating the same five forest prediction
matrices to five categories raises mean macro F1 from 0.23953 (SD 0.00878) to
0.48349 (SD 0.00549) while the ceiling rises from 0.55263 to 1. This changes
the target; it does not improve the model. A targeted review verified a
published NSL-KDD evaluation that maps fine attack types to five categories,
but found no incompatible published score. The broader frozen screen also
found no score conflict, so field-level impact is still unestablished.

## Install and use

    python -m pip install -r code/requirements.txt
    python -m pip install --no-deps .
    python -m label_availability results/nsl_kdd_official/label_counts.csv --oracle --convention union

The small package needs NumPy and pandas. Python 3.13 and the pinned environment
are used for the experiments. Install from source with the command above. The 0.7.0 wheel was not rebuilt in this environment because its setuptools build backend was unavailable and package downloads were blocked; see VALIDATION.json.

```python
from label_availability import coverage_ceiling, count_folds, exact_oracle

coverage_ceiling([[0]], [[0, 1]])                # 0.5: training-restricted outputs
coverage_ceiling([[0]], [[0, 1]], [[0, 1]])      # 1.0: explicit global head
counts = count_folds([[0]], [[0, 1]], [[0, 1]])
exact_oracle(counts, convention="union")
```

Count CSVs use fold, class, training_rows and test_rows. Include every legal
output, including output-only labels with zero training and test support. With
no allowed column, positive training support defines the vocabulary. An optional
boolean allowed column defines legal outputs directly, including training-absent
labels. It is not intersected with training support. CLI output warns when the
coverage ceiling is below one. The main convention averages positive-test-support
labels; scikit-learn's inferred true/predicted union is a separate option.

## Reproduce current tables and figure

    python code/reproduce_release.py --mode saved

This reconstructs scores from released confusion counts, verifies the frozen
50-candidate sample and 180-fit grid, verifies the five-seed NSL label-granularity
reanalysis, regenerates all main tables in
results/manuscript_tables, and exports the CIC hero figure. It does not refit
models. CLAIMS.md maps each table and substantive claim to evidence.

Saved mode rewrites derived CSV tables and may change floating-point serialization.
Use a disposable checkout when preserving the exact frozen file formatting matters.
Primary confusion counts and the frozen sampling frame are retained.

    python code/reproduce_release.py --mode solvers

This exercises both scoring conventions and solvers against exhaustive legal
predictions, checks explicit global heads and vocabulary grouping, and reruns
the branch/MILP shape comparison. Exact-search budgets and MILP timeouts are
recorded; an unfinished search does not certify an optimum. Repeated vocabulary
groups are collapsed before search. The polynomial sandwich remains available.

To refit every fitted comparison in the main manuscript into a new directory:

    python code/reproduce_release.py --mode refit --out fresh_v6 --data PATH_TO_UNSW --cic PATH_TO_CIC --nsl PATH_TO_NSL --gas PATH_TO_GAS_ZIP

This can take many hours. It starts from raw data and keeps new results separate
from the frozen evidence. It fits the six CIC configurations, NSL forest seeds
42--46 and five additional pipelines over the same seed set, the UNSW official
reference and complete 36-pair/five-seed grid, and all gas baselines. The optional digits control is also
rerun. Historical withholding paths and rejection controls have separate entry
points documented in CLAIMS.md. Read the source flags before a large refit.

## Evidence and manuscript

- paper/main.tex and paper/supplementary.tex contain editable LaTeX.
- paper/TBench-Submission.tex and paper/TBench-Anonymous-Submission.tex use the publisher class.
- All six CIC configurations have fresh records in results/cic_full_replication.csv; RESULTS_PARSED.csv contains the corresponding archived aggregates.
- results/unsw_complete_pairs/runs.csv contains the 180 pair/seed scores plus official/path controls. results/rank_audit adds newly refitted covered/unavailable matrices for all 180 pair/seed conditions; full scores match the earlier grid to 1e-12.
- results/nsl_families/seed_metrics.csv and by_seed contain five outputs for each of five additional pipelines, with both scoring conventions. Forest confusion matrices for seeds 42--46 are under results/nsl_model_comparison. The added pipeline comparison uses different preprocessing and is descriptive, not an estimator-only experiment.
- code/audit_nsl_granularity.py reaggregates the same forest confusion matrices to five broad NSL-KDD categories; results/nsl_kdd_official/granularity_reanalysis*.csv retains per-seed and summary scores. This is a target-resolution analysis, not a refit.
- The seed-42 routing control is a scoring-convention illustration in the supplement, not evidence that model rankings change in practice.
- audit/protocol.md was locally frozen before collecting the literature frame. audit/crossref_20261108 contains 385 candidates, the fixed sample of 50, coding and checksums. This is a screening pilot: 3 eligible, 14 excluded, 33 unresolved. It does not estimate field prevalence or document a verified incompatible published score.
- EXTERNAL-AUDIT.md records a separate verified published protocol example (Ayantayo et al., 2023) where NSL-KDD attack subtypes are mapped to five categories. It illustrates target resolution and does not establish a score violation.
- audit/nsl_family_plan.md fixes the additional pipelines before their results were examined. audit/AMENDMENTS.md records screening boundaries. audit/reference_verification.csv checks the cited 2026 records and distinguishes a web report from journal articles.

The public repository identifies the author. The anonymous manuscript omits the
author and personal repository URL, but a blind review needs a separately hosted
anonymous artifact. A permanent DOI and independent reproduction remain pending.
The readable PDFs use a Pandoc/Typst conversion. Native publisher-class compilation
and its final page count remain unverified in this environment.

## Scope and reuse

Code is MIT-licensed. Data owners retain their data terms. Manuscript copyright
remains with the author. The included IEEE citation style retains its own
Creative Commons license metadata. The publisher's class is obtained separately;
its files are not relicensed as MIT. Generative-AI
assistance in the research workflow is disclosed in the manuscript.

CIC uses MachineLearningCVE files without timestamps. No local corrected
Engelen/Lanvin release was found. Historical within-day row order is not a verified
clock-time split. Numeric imputation uses training medians. UNSW uses ordinal
nominal encoding; NSL forests use one-hot encoding; the additional NSL baselines
also standardize numeric features. Pipeline comparisons do not isolate estimator
effects from preprocessing. Gas CORAL uses unlabeled target features.

Pair fits, model pipelines and seeds share test rows. Rank correlations and
reversal counts are descriptive, without iid significance intervals. Historical
forced_assignment_gap means the covered-row-first combined destination penalty
C-R, which includes both unavoidable and model-dependent loss. It is not a claim
that the split forces every part of that penalty. The old bootstrap correlation
script is exploratory historical material, not an inferential analysis.

Dataset sources: [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html),
[UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset),
[NSL-KDD](https://www.unb.ca/cic/datasets/nsl.html),
[gas drift](https://doi.org/10.24432/C5RP6W).
