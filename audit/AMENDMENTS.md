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
