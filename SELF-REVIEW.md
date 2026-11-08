# Internal review, release 0.7.0

Assessment: **6/10**. Recommendation: major revision at a selective Q1 venue;
borderline for a correctness-focused journal. This is an internal assessment,
not an independent peer review or a TBench decision.

The main improvement is a reproducible label-resolution analysis on NSL-KDD.
Using the same five saved forest confusion matrices, mapping both true and
predicted labels to five broad categories changes mean macro F1 from 0.23953
(SD 0.00878) to 0.48349 (SD 0.00549); the ceiling changes from 0.55263 to 1.
This quantifies how a published score's target taxonomy can change its
interpretation without any new fit. The analysis is explicitly a post-hoc
projection, not a comparison of separately trained models.

A primary-source check of Ayantayo et al. (2023) verified a published NSL-KDD
evaluation that describes 17 test-only fine attack subtypes, reports a five-
category task, and creates a second test set without those subtypes. Under its
five-category output vocabulary, the ceiling is one; its score is not a
verified violation. The literature screen still has no confirmed published
score incompatible with its declared outputs. This improves the practical
positioning, but does not establish field-wide prevalence or impact.

The five-seed pipeline comparison remains descriptive across complete
pipelines with different preprocessing. kNN has the highest point estimate;
its full-score margin over the decision tree is smaller than the tree's seed
SD. The manuscript now states that explicitly. Both scoring conventions are
shown, the natural NSL table uses the five-seed mean, the oracle and sandwich
bounds are defined in the main text, and the UNSW disagreement counts are
restored with their denominators.

| Criterion | Internal score |
|---|---:|
| Mathematical soundness | 8/10 |
| Novelty and significance | 4/10 |
| Empirical evidence | 6/10 |
| Reproducibility | 9/10 |
| Clarity | 7/10 |

The central inequality remains elementary, and the main contribution remains
a reporting diagnostic. The external published example supports the relevance
of target resolution but is not an incompatible-score case. A broader
independently coded audit or a natural published example where the ceiling
changes a substantive conclusion is still needed for a stronger Q1 novelty
case.

Native TBench-class compilation, final journal pagination, permanent DOI,
external anonymous artifact hosting, and independent reproduction remain
pending. The reading PDFs check content and layout only in the Pandoc/Typst
format. These files do not imply acceptance or guarantee an external score.
