# RT-IoT2022 experiment plan

Prepared after raw-file/count inspection and before any model fit in this
continuation. This is a locally recorded plan, not external preregistration.

Question: on a contemporary public IoT corpus, how much can mandatory
false-positive destinations lower the exact fine-label oracle, and how does a
separately fitted binary alarm differ from exact withheld-label attribution?

Source: UCI dataset 942, DOI 10.24432/C5P338, public archive
https://archive.ics.uci.edu/static/public/942/rt-iot2022.zip (CC BY 4.0).
The actual file contains 123,117 rows and 12 observed labels. It differs from
some descriptive website label/count text; use actual verified file counts.

Features: drop row index Unnamed: 0, label Attack_type, id.orig_p and id.resp_p.
Retain 81 behavioral/protocol features. Label mapping: Thing_Speak,
MQTT_Publish and Wipro_bulb are BENIGN; the other nine observed labels ATTACK.
Publish the exact mapping. Do not infer timestamps from file order.

Split: StratifiedGroupKFold(5, shuffle=True, random_state=20261115), using exact
feature vectors as groups. Hash-group cardinality is verified against exact
drop_duplicates cardinality. Use fold zero, fixed before model results. Its
31,061 test rows contain all 12 labels; the other 92,056 rows form the source
training pool. No exact feature group crosses partitions. This is one grouped
holdout, not pooled five-fold CV or a verified chronological split. Counts for
the other four folds are a pre-fit inventory check, not extra fitted experiments.

Conditions: all-label baseline and each of the nine attack labels withheld from
the training pool in turn. Every condition retains exactly the same full test
cohort. Exhaust the nine labels; do not select cases by resulting model score.

Model: ExtraTreesClassifier(100 trees, min_samples_leaf=2, n_jobs=4), seeds
42,43,44. Fit training-only numeric median imputation and categorical one-hot
encoding (unknown categories ignored). No model tuning, threshold selection,
feature selection or early stopping on test data. Cap at 1,000 rows per original
fine label with the seed; remove a withheld label from this precomputed capped
sample, keeping remaining rows matched across conditions. For each condition and
seed fit (a) the fine-label model and (b) a binary model on exactly those rows,
using the same preprocessing recipe and seed. This makes 60 actual fits.

Compute fine macro F1 on the fixed 12-class test inventory, its support oracle,
binary-projected scores and attack recall, separately fitted binary macro F1 and
attack recall, and per-class recall. Save truth, predictions, confusion matrices,
fit/test membership, legal vocabularies, coverage counts, exact rational oracle
certificates and hashes. Check test-group disjointness and prediction legality.

Analysis: descriptive mean/sample SD over the three seeds; this includes capped
sampling and model initialization variation. Shared test rows and feature-group
dependencies preclude iid significance claims. Do not call score differences
across targets model improvements. Test truth may enter the oracle and metrics,
but not model fitting or hyperparameter decisions. The purpose is evaluation
diagnosis rather than an estimator leaderboard or a new unknown-attack detector.
