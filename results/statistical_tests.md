# Statistical evidence

Seed SD is computed descriptively with sample standard deviation on repeated runs. Repeated seeds on one official test set do not measure sampling uncertainty. Single-seed settings have no seed SD. The archived class exports include Wilson intervals for supported denominators. Full paired prediction-level comparisons and an independently justified resampling unit are needed before presenting confirmatory intervals or p-values.


## Full-size UNSW-NB15 verification

The two raw official-split random forests at seed 42 were rerun with 200 trees. Both macro-F1 values matched the archived values exactly at saved precision. See results/rerun_unsw_official/metrics.csv and paired_predictions.csv. The correctness table includes 4,123 rows correct only for the unweighted arm and 1,407 correct only for the weighted arm. These are descriptive paired counts. Flow-level independence is unverified, so no independence-based p-value or confidence interval is supplied. The overlap audit counts matching pandas hashes of the loaded feature vectors and of the feature-label combinations. It does not identify capture sessions or independent groups.

- The CICIDS2017 day coverage audit found 14 attack classes with no training support in their held-out day folds, totaling 557,646 test rows. See cic_day_coverage.csv. This is a deterministic coverage check.
