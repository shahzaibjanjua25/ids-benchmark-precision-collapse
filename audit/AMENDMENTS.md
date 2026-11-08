# Audit amendments and boundaries

The local protocol was committed at f8258a47e8e302608b206642c308b5065d735537
before fetching its six Crossref responses on 2026-11-08. This is a prospective
local freeze, not external preregistration.

Public response snapshots omit abstracts and reference lists. Original snapshot
hashes are retained; source copies stay outside the release. The selection uses
only titles, DOIs and the declared random seed, so this redaction changes no
selected DOI. The public frame checksum identifies the redacted CSV schema.
The earlier unredacted-frame checksum was
b073eac32d4f81d08458ada6fa3bf2f0d9e5af106337e70d3cdc96ebd45d864a.

The sample is 50 candidates, not 50 confirmed eligible papers. Temporal neural
coding, temporal layers, split learning and grouped feature selection do not
establish a held-out temporal or group evaluation. Target-scenario fine-tuning
on 70% of that same target scenario is not a whole-scenario holdout. The latter
clarification excludes A16 after its complete experimental protocol was read.

An explicit publisher-deposited forward-replay abstract can establish screening
eligibility (A47), but cannot establish vocabulary, supports or score convention.
Unavailable facts remain unresolved. A retracted original article is retained
with its status and unresolved protocol; it is not removed based on its results.

The public coding sheet is a single-reviewer, AI-assisted screening pilot.
It contains no independently adjudicated prevalence estimate. No authors were
contacted. A broader review of 40--60 confirmed eligible studies remains future
work; the pilot is not presented as completing that review.

The NSL family-plan file was written before the new fits. Its first commit attempt
failed because Git identity was unset; the successful commit followed runner
launch and preceded inspection of its first result. The destination rerouting
analysis is explicitly post hoc and was not part of that baseline plan.

Public CSV line endings were canonicalized to LF before release so Git checkouts preserve the frozen frame checksum across operating systems. Selected DOIs and coding decisions are unchanged.

# 2026-11-08: NSL pipeline seed expansion

After an external referee questioned the seed-42-only comparison, the five
additional prespecified pipelines were evaluated on the same official NSL-KDD
train/test files with seeds 42--46. The existing forest's five seed outputs
were retained. The parameters and preprocessing were not retuned; the added
pipelines remain complete-pipeline comparisons because their preprocessing
differs from the forest. GaussianNB was refit for each seed and produced
identical scores. kNN is deterministic under its specified settings; its one
saved prediction matrix is reused for the other seed labels rather than
refitting an identical estimator. Full-cohort and covered-row results are
reported under both positive-test-support and inferred-union scoring. The
original seed-42 leader-change claim was removed after the mean results showed
kNN first on both metrics.

The external referee also identified that the literature pilot did not
establish a published score conflict. No incompatible published result was
added or inferred; the revised paper states this as an unresolved impact gap.

# 2026-11-08: Target-resolution example and paired NSL reanalysis

In response to the significance concern, a targeted primary-source search was
conducted after the frozen 50-record literature sample had been coded. This
search is supplementary and is not counted as another sampled or eligible
study. Ayantayo et al. (2023), *Journal of Big Data*, DOI
10.1186/s40537-023-00834-0, explicitly describe test-only fine attack
subtypes in NSL-KDD, map the task to five broad categories, and construct an
additional test subset without those subtypes. All five category outputs occur
in training, so this is not an incompatible-score case.

To quantify what the taxonomy choice does, code/audit_nsl_granularity.py maps
both true and predicted labels in each of the existing five forest confusion
matrices to those five categories. No model was fit and no test cohort changed.
The paired scores and ceilings are saved in
results/nsl_kdd_official/granularity_reanalysis*.csv and are included in saved
release verification. Fine-label macro F1 is 0.23953 (sample SD 0.00878) with
ceiling 0.55263; the five-category projection is 0.48349 (sample SD 0.00549)
with ceiling 1. This is a target-resolution illustration on one fixed split,
not an estimate of field prevalence, a claim of model improvement, or proof
that published conclusions are generally invalid.

# 2026-11-08: CICIDS2017 target-resolution analysis

To answer the protocol-selection question without changing the fitted model,
code/audit_cic_target_resolution.py aggregates both axes of the saved
unweighted CICIDS2017 day-holdout forest confusion matrix under the released
fine-label, eight-family and benign-versus-attack maps. Fold-level mapped
support is reconstructed from the retained day/class counts. The three
ceilings are 0.06667, 0.25 and 1; the same predictions score macro F1 0.06030,
0.15630 and 0.57972, respectively. Binary attack recall is 0.14690. These are
different targets, not a score ranking or binary refit. Fine-label F1 is
90.5% of its ceiling because it is supported almost entirely by the benign
term; all attack-class F1 terms are zero. The binary result is included to
show that removing a structural ceiling does not guarantee useful detection.
Reproduction and assertions are in the saved release command.
