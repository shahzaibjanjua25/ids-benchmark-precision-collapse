# Prospective local audit protocol v1

Recorded 2026-11-08, Asia/Karachi, before collecting the audit search frame.
This is a locally frozen protocol, not an externally registered review.

## Question and estimand

Among a reproducible sample of indexed IDS candidates, how often can vocabulary
availability and the reported score convention be checked? Among confirmed
eligible studies, which protocols have a verified ceiling below one, and are any
reported scores incompatible with that ceiling?

The search frame is bounded and relevance-ranked. Its proportions do not estimate
prevalence across the entire IDS literature. Missing evidence is a checkability
outcome and is not treated as evidence of a ceiling violation.

## Search frame

Use Crossref's public works API with query.bibliographic, rows=100, relevance
ordering, and publication dates 2017-01-01 through 2026-11-08. Record full raw
responses and retrieval timestamps. Use these six queries exactly:

1. intrusion detection temporal evaluation
2. intrusion detection chronological split
3. intrusion detection leave one day out
4. intrusion detection group holdout
5. intrusion detection unseen attacks evaluation
6. network intrusion detection concept drift benchmark

Deduplicate by lowercase DOI. Retain records whose title contains "intrusion" and
"detect" (case-insensitive, substring matching). Do not filter on the presence of
an open-access copy, dataset name, reported score or suspected availability issue.
Save the complete retained frame and its SHA-256 checksum.

## Sample and screening

Sort the frame by DOI. Select 50 records without replacement using NumPy
default_rng(20261108). If fewer than 50 records exist, inspect all and report that
shortfall. Preserve the selected DOI list before substantive coding.

Eligible studies report an empirical network/IoT intrusion-detection evaluation
using a temporal, capture-day, device/site/scenario or group holdout, including
streaming concept-drift evaluations with stated train/test timing. Random-only
studies, reviews without original evaluations, non-network anomaly tasks, and
dataset papers without an empirical compatible protocol are ineligible. If
eligibility cannot be established, mark it unresolved. Do not replace sampled
records based on accessibility or outcome.

## Evidence and coding

Use publisher full text, an author manuscript, or the paper's linked code/results.
Record source URL, section/table/code location, and brief evidence. Metadata alone
cannot establish a score convention or an output vocabulary. Record inaccessible
full text and unresolved facts explicitly.

For every sampled record, code eligibility and reason, dataset/version, split,
prediction target, allowed outputs, per-fold support availability, pooling,
scored-label inventory, reported metric/value and artifact availability. Separate
training labels from legal outputs. A global neural head can permit labels absent
from a training sample, giving legal coverage one despite poor learnability.

Classify the audit result as verified ceiling below one, verified ceiling one,
unresolved vocabulary, unresolved support, unresolved scoring, ineligible or
unresolved eligibility. Multiple missingness flags are permitted. A reported
score is called incompatible only if cohort, vocabulary, metric, averaging and
inventory are verified and its value exceeds a valid bound after allowing its
stated rounding. No score value will be inferred from an ambiguous F1 label.

## Analysis and deviations

Report screening/retrieval flow, missingness counts, eligible/checkable counts,
and exact sampled proportions with their denominators. Any sampling interval
refers to this bounded frame and not the whole field. Correlations across reused
test rows or label pairs are descriptive, without iid significance claims.

Record protocol amendments and their timing. Freeze original selection and keep
excluded/unresolved cases. Verify newly cited DOIs against primary metadata and
distinguish journal articles, proceedings, preprints and technical reports.
