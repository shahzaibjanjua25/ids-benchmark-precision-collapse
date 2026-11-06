# IDS benchmark precision collapse

Reproduction code and aggregate evidence for a study of evaluation protocol and class imbalance on CICIDS2017 and UNSW-NB15. The research manuscript is handled through journal submission.

## Setup

Use Python 3.13. From this repository root, install dependencies with:

    python -m pip install -r code/requirements.txt

Download the official benchmark data separately. Place the UNSW training and testing CSVs in your data directory and the CIC machine-learning CSVs beneath its CICIDS2017 subdirectory.

- [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) and its [dataset paper](https://doi.org/10.5220/0006639801080116)
- [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset) and its [dataset paper](https://doi.org/10.1109/MilCIS.2015.7348942)

## Verify the archived scores

    python -B code/verify_cic_archive.py results

The verifier recomputes six archived CICIDS2017 results from their confusion matrices. The fresh unweighted CICIDS2017 cross-validation replication is in results/cic_cv_unweighted_replication.csv.

## Rerun and audit

Replace PATH_TO_DATA with the directory containing the official CSVs.

    python -B code/rerun_unsw_official.py PATH_TO_DATA results/unsw_reproduction
    python -B code/audit_unsw_overlap.py PATH_TO_DATA results/unsw_overlap_reproduction.csv
    python -B code/audit_cic_day_coverage.py PATH_TO_DATA/CICIDS2017 results/cic_coverage_reproduction.csv
    bash code/run_all.sh PATH_TO_DATA

The standalone figure script can regenerate charts from the archived aggregate data.

    python -B code/release_figures.py

The aggregate results directory excludes raw datasets, console transcripts, and row-level predictions. Two UNSW-NB15 official random forest configurations and one CICIDS2017 shuffled-CV configuration have been reproduced from scratch. Other CICIDS2017 rows are archive results.

## Fixed-test overlap experiment and split manifests

    python -B code/run_unsw_overlap_control.py PATH_TO_DATA results/overlap_reproduction
    python -B code/dataset_manifest.py PATH_TO_DATA
    python -B code/export_cic_membership.py PATH_TO_DATA/CICIDS2017 results/cic_membership_reproduction

The two removal arms retain the same training row count within each class and use the same official test rows. Results and zero-based membership indices are under results/unsw_overlap_control. The CIC test fold arrays are in results/cic_split_manifest and are aligned to the ordered file list in that directory. A fold value of -1 denotes a row used for training only in the single within-day holdout. Benchmark input SHA-256 checksums and archived CIC per-class results are also included.

## CICIDS2017 label-coverage decomposition

    python -B code/decompose_cic_lodo.py results

This splits the pooled archived confusion matrices into test rows whose true labels were seen or unseen in their corresponding training folds. Coverage membership can be reconstructed from the pooled matrix here because no label appears in both groups.

## Five-seed fixed-test experiment

Run code/run_unsw_overlap_control.py with --seed 42 through --seed 46. Use the output folders results/unsw_overlap_seed_42 through results/unsw_overlap_seed_46.

    python -B code/summarize_unsw_overlap_seeds.py results results/unsw_overlap_multiseed
    python -B code/plot_unsw_overlap_seeds.py results/unsw_overlap_multiseed/paired_seed_scores.csv results/overlap_figures

The committed summary includes the seed-paired contrasts, seed-conditional intervals and sign-flip sensitivity calculations. The package includes per-class results and compressed training membership for every seed. The fixed test membership is in results/unsw_overlap_control/test_membership.csv. Both fresh CICIDS2017 cross-validation arms are recorded in results/cic_cv_replication.csv.

## Compute the pre-fit ceiling

    python -B code/label_coverage_bound.py results/cic_lodo_label_counts.csv results/cic_ceiling.csv
    python -B code/label_coverage_bound.py results/unsw_official_label_counts.csv results/unsw_ceiling.csv

The input has one record per fold and class, with class, training_rows and test_rows columns. The output lists pooled support, covered support and the F1 ceiling for each test class. The printed mean is the ceiling for pooled macro F1 with a closed-set classifier.

## Mixed label coverage

    python -B code/run_unsw_partial_coverage.py PATH_TO_DATA results/partial_coverage_reproduction

The demonstration withholds Analysis and Backdoor from official training and preserves the original test rows. The archive includes label counts, test support by coverage stratum, the confusion matrix, and training membership. Use the official test membership already supplied in results/unsw_overlap_control/test_membership.csv. The fresh metrics for all six CICIDS2017 configurations are in results/cic_full_replication.csv. The five-seed overlap study is retained as separate exploratory evidence.

## Withheld-label sensitivity and score shortfall

    python -B code/run_unsw_coverage_sensitivity.py PATH_TO_DATA results/unsw_coverage_sensitivity
    python -B code/summarize_unsw_coverage_sensitivity.py results

The experiment fits 15 forests on the same test partition. It varies the withheld label pair and seed. The run table includes a majority-label reference and a covered-row repair that preserves unseen-row predictions. The summary also computes a single-fold oracle ceiling under unrestricted allocation of unseen false positives to seen labels.

## Additional sampled withheld pairs

    python -B code/run_unsw_coverage_sensitivity.py PATH_TO_DATA results/unsw_coverage_random_pairs --random-pairs
    python -B code/summarize_unsw_coverage_random_pairs.py results

The sampler draws 20 distinct pairs without replacement from the 33 remaining after excluding the three deterministic pairs. Pair-selection seed 2026 and forest seed 42 are fixed. Run records include the selected pair, test support and both shortfall components.

## Pair distribution and repair order

    python -B code/plot_unsw_pair_distribution.py results results/pair_figures

This command regenerates the distribution chart and percentile-bootstrap summaries for the 20 observed pairs. It also verifies the two repair orders on the archived Analysis and Backdoor seed-42 confusion matrix.

## Full sampled grid, rejection scores and digits

    python -B code/run_unsw_coverage_sensitivity.py PATH_TO_DATA results/unsw_random_pairs_extra_seeds --random-pairs --forest-seeds 43 44 45 46
    python -B code/run_unsw_coverage_sensitivity.py PATH_TO_DATA results/unsw_deterministic_rejection --forest-seeds 42
    python -B code/summarize_pair_variation.py results
    python -B code/run_digits_fractional_coverage.py results/digits_fractional_coverage

The original 20 seed-42 runs and 80 additional runs form the balanced grid. The new runs include aggregate unseen prediction destinations. Confidence rejection uses a fixed 0.5 threshold and is scored under both fine-grained and coarse unknown conventions. The digits example uses the data bundled with scikit-learn. Finite-population intervals use exact order-statistic coverage under the declared simple random pair sample at seed 42.

## Published NSL-KDD split

Obtain KDDTrain+.txt and KDDTest+.txt from the [NSL-KDD mirror](https://github.com/jmnwong/NSL-KDD-Dataset). The audit keeps the original fine-grained labels and does not train a model.

    python -B code/audit_nsl_kdd_coverage.py PATH_TO_NSL_KDD results/nsl_kdd_official
    python -B code/bootstrap_pair_correlation.py results

The archive includes input checksums, label counts, and the resampled correlation interval.
