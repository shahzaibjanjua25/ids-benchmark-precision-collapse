# Internal critical review, release 0.6.0

Assessment: **5.5/10**. Recommendation: major revision; I would not accept this
as a full research article at a Q1 venue in its current form. This is an
internal referee-style assessment, not an independent peer review or a TBench
editorial decision. No official TBench scoring rubric is assumed.

The mathematical statement is correct and easy to verify: if a legal output
cannot name a test label, its recall is zero, and the class-level F1 term is
bounded accordingly. NSL-KDD's official fine-grained split has natural partial
coverage, while CICIDS2017 leave-one-day-out gives an extreme, already-known
case. The paper now treats the inequality as a reporting corollary rather than
a new method.

The revised NSL pipeline comparison fits the randomized pipelines over seeds
42--46, reports seed SDs, and includes both positive-test-support and
inferred-union scoring. The original seed-42 forest/kNN leader-change claim was
withdrawn: kNN has the highest mean under both scoring conventions, and the
forest is third on full positive-support F1. The fixed-test comparisons remain
descriptive; they do not establish model-family ranking stability or a
statistically significant advantage. The deterministic GaussianNB/kNN rows
have zero seed variation by construction.

The main paper now separates the full cohort from the covered-row task, moves
the oracle complexity proofs into the supplement, removes the unexplained
65-condition routing headline, and calls the routing example a scoring
convention control. The gas denominator and test-row wording are explicit. The
pipeline table shows both scoring conventions. The repository claim map and
README describe the current experiments.

Reproducibility remains a strength: source hashes, fold manifests, confusion
matrices, claim-to-file mapping and saved verification are included. The
complete literature evidence is still a 50-candidate screening pilot: three
eligible, fourteen excluded and thirty-three unresolved. It found **no
verified incompatible published score** and cannot establish field-level
impact. No such case is asserted.

Indicative sub-scores: mathematical soundness 8/10, novelty 3/10, empirical
significance 5/10, reproducibility 9/10, writing/focus 6/10. The ceiling is an
elementary but useful reporting check; its practical adoption and effect on
published conclusions have not been demonstrated. A confirmed external case
and a broader, independently coded literature audit remain the main scientific
gaps.

Native TBench-class compilation and final journal pagination, a permanent DOI,
external anonymous artifact hosting and independent reproduction remain
pending. The reading PDFs verify content and layout only for the Pandoc/Typst
reading format. These materials do not imply journal acceptance or guarantee a
9/10 rating.
