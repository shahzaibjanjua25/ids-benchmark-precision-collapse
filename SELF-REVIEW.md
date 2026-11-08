# Internal review, release 0.9.1

Assessment: **7/10**. Recommendation: major revision at a selective Q1 venue;
potentially suitable for a focused evaluation-methods venue after independent
review. This is an internal assessment, not an external referee report or a
TBench decision.

The manuscript now gives a more useful account of task choice on CICIDS2017.
The same multiclass day-holdout predictions produce macro F1 0.06030 at 15
labels, 0.15630 at eight declared families, and 0.57972 at binary resolution.
The corresponding ceilings are 0.06667, 0.25 and 1; binary attack recall is
only 0.14690. A separate binary refit on the Monday-to-Thursday/Friday split
scores 0.61754 with attack recall 0.27894, close to a published binary score of
0.619. The five-fold binary pooled refit still has only 0.14782 attack recall.
This supports a practical point: changing the target removes the structural
ceiling, but a more attainable score does not establish good detection.

The external audit also identifies a concrete, unresolved reporting ambiguity.
Biyouki et al. report 0.9855 macro F1 for a CICIDS2017 leave-one-family-out
experiment with Web Attack excluded from training. If the score averages all 15
closed-set labels, the ceiling is at most 14/15 = 0.9333; if it excludes the
unseen class or uses a binary task, that conclusion does not follow. The article
does not identify the LOFO scoring vocabulary, and its discussion does not map
known-class performance and held-out-family ranking to separate metric cohorts,
so the paper does not label the score incompatible. This makes the diagnostic
useful for specifying what a published zero-day score must disclose, while
falling short of proving that a
published result is wrong or changing a literature-level conclusion.

| Criterion | Internal score |
|---|---:|
| Mathematical soundness | 8/10 |
| Novelty and significance | 6/10 |
| Empirical evidence | 7/10 |
| Reproducibility | 9/10 |
| Clarity | 8/10 |

The central bound remains an elementary corollary of recall under a restricted
output set. The exact oracle is more informative but has limited effect in the
natural examples. The external audit is small and the new publication's scoring
convention is unresolved. The broader 50-record search is a screening pilot
(3 eligible, 14 excluded, 33 unresolved), not a confirmed survey of temporal
IDS evaluations. No verified incompatible published score is established, and
the analysis does not demonstrate field-wide prevalence or adoption. The
manuscript should not be presented as a new learning method or as evidence that
existing headline scores are generally invalid.

The revised result improves the practical significance over release 0.8.0, but
the evidence does not justify a 9.5/10 claim or an accept recommendation at a
selective Q1 journal. A verified published score with a fully specified target
that exceeds its legal-output ceiling, or a broader preregistered audit that
shows how often the missing vocabulary changes interpretation, would be needed
for a substantial significance increase. Such evidence must be found, not
inferred from an ambiguous report.

Reading-copy page counts and text checks passed before this revision. Rebuild
the reading PDFs and update VALIDATION.json after the current sources are final.
Native publisher-class compilation, pixel-level page inspection, remote CI,
permanent DOI, anonymous artifact hosting and independent reproduction remain
unverified.
