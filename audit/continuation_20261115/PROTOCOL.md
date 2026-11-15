# Targeted source audit, continuation

The ledger contains 23 distinct IDS study records: the previous 12 plus eleven
purposefully chosen anomaly, open-set and IoT benchmark studies. This is a
targeted methodological audit, not a systematic review, prevalence sample, or
23 independent reproductions. Twenty published records have a completed target-level classification; two published records retain insufficient information, and one preprint is excluded from the published count. Three studies have confusion counts independently
re-scored (18 matrices); one of those uses its author-manuscript version.

Selection follows the research question: does an evaluated target require exact
unseen-label naming, a known category, a binary alarm, or aggregated unknown
recognition? Each row records the inspected source location, legal outputs,
metric, verdict and remaining uncertainty. Missing aggregation details remain
missing; a binary or weighted score is never silently relabeled macro F1.
The primary class of interest is pooled arithmetic-mean classwise F1. Other
targets are retained to test the applicability boundary and explicitly marked.

Searches used publisher pages, author manuscripts, cited references, and a
Consensus discovery query for open-set IDS. Consensus full-text paid features
were not used. Date: 2026-11-15. Search strings included "open set intrusion
recognition fine grained", "unknown intrusion traffic OpenMax", "macro F1 upper
bound quantification", and the exact titles and DOIs in the ledger. Downloaded
PDF hashes are retained, while copyrighted full papers remain outside Git.

Nearest mathematical prior inspected in full: Balikas et al., IDA 2015,
doi:10.1007/978-3-319-24465-5_3, author PDF
https://aptikal.imag.fr/~amini/Publis/Quantification_IDA15.pdf. Its bounds support
regularized model selection with unlabeled samples using estimated class priors,
prediction proportions, IID concentration and quantification assumptions. It
does not specify the fold-vocabulary allocation polytope used here. The basic
existence of bounds on F1 is therefore prior work, not a novelty claim.

Cruz et al. (IEEE HST 2017) already distinguish exact exploit categorization,
coarser families, binary detection and explicit unknown recognition. The present
paper must not claim to originate that distinction. Its narrower contribution
is the exact attainable pooled score with routing certificates, conditional on
declared counts and legal outputs. Absence of an equivalent construction among
these inspected sources is not proof of mathematical priority.
