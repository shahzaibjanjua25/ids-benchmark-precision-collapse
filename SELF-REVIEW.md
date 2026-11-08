# Internal review, release 0.8.0

Assessment: **6.5/10**. Recommendation: major revision at a selective Q1 venue;
borderline at an evaluation-methods journal. This is an internal assessment,
not an independent peer review or a TBench decision.

The revision adds a protocol-selection result from CICIDS2017. Reaggregating
the same day-holdout forest predictions gives macro F1 of 0.06030 for 15 fine
labels, 0.15630 for eight declared families, and 0.57972 for benign-versus-
attack; the corresponding legal-output ceilings are 0.06667, 0.25, and 1.
The fine-label score reaches 90.5% of its ceiling because benign F1 is 0.90456
and all attack-class terms are zero. Binary attack recall is only 0.14690.
Thus the fine-label score is nearly fully constrained, while moving to a
feasible binary target does not make the existing multiclass forest a good
detector. The score change comes from a different target on the same
predictions, not a refit or model improvement.

On NSL-KDD, reaggregating the same five forest matrices to five broad categories
changes mean macro F1 from 0.23953 (SD 0.00878) to 0.48349 (SD 0.00549), with
the ceiling changing from 0.55263 to 1. The published Ayantayo et al. study
documents this taxonomy choice in practice: it describes test-only fine attack
subtypes, evaluates five categories, and also excludes unseen-subtype rows in
a secondary test set. That five-category task is internally attainable, so it
is not an incompatible published score. The literature screen still confirms
no published score conflict and does not estimate prevalence across the field.

| Criterion | Internal score |
|---|---:|
| Mathematical soundness | 8/10 |
| Novelty and significance | 5/10 |
| Empirical evidence | 7/10 |
| Reproducibility | 9/10 |
| Clarity | 8/10 |

The results now offer concrete guidance: name the operational target before
choosing the split, report the ceiling for that target, and do not interpret a
coarse-label score as exact attack attribution. Still, the inequality follows
from class recall, the strongest empirical analyses are post-hoc projections
on a small number of fixed benchmarks, and no verified published claim has
been shown to contradict its output vocabulary. A larger independently coded
literature audit or prospective evaluation with naturally fractional label
coverage could change the significance assessment. Without one, I would not
rate the paper 10/10 or recommend acceptance at a selective Q1 journal.

Native TBench-class compilation, final journal pagination, permanent DOI,
external anonymous artifact hosting, and independent reproduction remain
pending. The reading PDFs check content and layout only in the Pandoc/Typst
format. These files do not imply acceptance or guarantee an external score.
