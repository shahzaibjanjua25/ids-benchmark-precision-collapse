# Release 0.9.1 artifact entry point

README.md gives installation and one-command saved-table, solver and raw-data
refit modes. CLAIMS.md maps the three result datasets (the NSL pipeline table is
shown in separate score-convention tables), the figure and substantive results
to scripts and data. paper/ contains the exact manuscript
sources for this release, including the supplement.

The revised external audit includes a published CICIDS2017 leave-one-family-out
score of 0.9855 whose scored label inventory is unspecified. Under the specific
15-label closed-set convention including the withheld class, its ceiling would
be at most 14/15; alternate scoring vocabularies remove the contradiction. The
case is therefore recorded as unresolved and verified by
code/verify_published_score_audit.py, not as a confirmed incompatible result.

The current scope is a reporting diagnostic for vocabulary-constrained pooled
scoring. Full and covered-row scores are treated as different tasks, not as
competing rankings. The NSL pipeline comparison uses all five seeds for
randomized pipelines and reports both positive-support and inferred-union scores;
the seed-42 pipeline leader change does not persist in the mean scores. Original
15-pair and 20-pair subsets remain historical evidence; current rank analysis
uses all 36 pairs and five seeds with saved confusion matrices.
All six CIC forest configurations were freshly replicated, separately from the
archived aggregates. Historical one-arm/two-arm files are subsets, not a competing
statement of the current replication scope.

The NSL-KDD label-resolution analysis maps both truth and prediction axes from
the same five forest confusion matrices to the five broad categories. It raises
mean macro F1 from 0.23953 to 0.48349 while the ceiling changes from 0.55263 to
1. This is a paired change in the scoring target, not a refit or a claim of
improved fine-grained recognition.

The CICIDS2017 day-holdout analysis likewise reaggregates a fixed forest
prediction matrix at fine-label, eight-family, and binary resolution. Its
macro-F1 values are 0.06030, 0.15630, and 0.57972 against ceilings 0.06667,
0.25, and 1. The fine-label score is 90.5% of its ceiling because benign F1 is
0.90456 and the 14 attack-class F1 terms are zero. Binary attack recall is
0.14690. This identifies an attainable binary task, but it does not turn the
existing multiclass model into a useful attack detector or stand in for a
separately trained binary model.

The 50-record literature artifact is a candidate-screening pilot. It contains
three confirmed eligible studies, not fifty eligible temporal IDS papers. No
verified incompatible published score is established; unresolved support,
output vocabularies and scoring are not violations. The pilot therefore does
not establish field-level impact. The targeted Ayantayo et al. (2023) case is a
verified published example of five-category mapping with test-only fine-grained
subtypes; it is not a score incompatible with the stated output vocabulary.

The readable PDFs are converted reading copies. Native TBench-class compilation,
final journal pagination, permanent DOI and external blind-review artifact hosting
remain separate release requirements. The public repository is author-identifying.
