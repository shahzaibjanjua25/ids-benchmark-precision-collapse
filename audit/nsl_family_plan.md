# NSL family comparison, frozen before fitting

2026-11-08. Use the official KDDTrain+ and KDDTest+ files, all original
fine-grained labels and every test row. Reuse the existing seed-42 200-tree
forest as the reference. Fit five additional pipelines once, without score-based
selection: ExtraTrees (200 trees, leaf 2, split 5), DecisionTree (leaf 2, split 5),
GaussianNB (default variance smoothing), SGDClassifier (log_loss, alpha 0.0001,
max_iter 1000, tol 0.001), and uniform five-neighbor kNN. Seed 42 where applicable.

For these additional models, one-hot encode columns 1, 2, 3 with unknown levels
ignored and standardize the remaining numeric columns using training values.
The forest retains its released preprocessing. This compares declared pipelines,
not an isolated estimator effect. Predict only classes observed in training.

Save covered and unavailable confusion matrices, all legal labels, fit timing
and parameters. Full macro F1 uses the 38 positive-test-support labels; covered
macro F1 uses that subset's positive-support labels. Report all pipelines and
pairwise rank reversals, whether present or absent. These are fixed-cohort
descriptions, with no iid p-values or bootstrap intervals across model families.
