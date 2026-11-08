# Historical revision v4 status (superseded)

This file preserves the preceding revision's state. Current release 0.5.0 is
documented in README.md, CLAIMS.md, SELF-REVIEW.md and VALIDATION.json. It adds a
natural NSL pipeline winner reversal, same-cohort destination controls, complete
180-fit ranking matrices and vocabulary-parameterized grouping. The older
statements below about absent natural inversions and main-paper layout describe
v4 only. The current literature pilot is under audit/crossref_20261108.

## Theory and interpretation

| Roadmap item | Outcome |
| --- | --- |
| Formal setup and notation | Training labels, permitted outputs, counts, coverage ceiling C, oracle O, repairs R and Q defined. Repair, convexity, vertex and tightness arguments separated. |
| Polynomial sandwich | Implemented, proved and compared with row-level search. |
| Closed forms | One uncovered fold and identical vocabularies implemented. The old 3^20 stress case is identified as trivial after this reduction. |
| Complexity | Set Cover proof in main text; concave-cost assignment, count-grid MILP, XP scope and absent approximation guarantee explicit. |
| Other conventions | Union ceiling/oracle, fold averages, weighted/micro/balanced-accuracy ceilings, harmonic macro-P/R bound, abstention and unknown outputs. Sharp MCC and kappa bounds remain open. |
| Minimum-support sensitivity | Thresholds 1,2,5,10,20,50,100,500,1000 computed. A hard ceiling requires the output restriction to be enforced. |
| Group split design | Leave-one-group-out zero/one proposition proved and constrained assignment objective posed. No split optimizer claimed. |
| Decomposition | Both orders and an order-averaged formula in main text. Minimum vocabulary penalty reported separately. |

## Experiments

| Roadmap item | Outcome |
| --- | --- |
| Natural binding fractional IDS example | Remains an empirical gap. Natural gas coverage is weakly binding in the pooled score. No published ranking reversal claimed. |
| Timestamped CIC blocks | Current files and Research.rar have no timestamps. Broader search of research folder, Documents and Downloads found no candidate release. |
| Granularity | CIC original/web-merged/declared-family/binary and NSL original/five-category ceilings regenerated. |
| Corrected-label sensitivity | Corrected Engelen/Lanvin data absent locally. No corrected-version result synthesized. |
| Full pair grid and official reference | Runner completes 36 pairs at five seeds, five official reference fits, and seed-42 alphabetical withholding sizes 1,3,4,5. summarize_revision.py asserts completed counts. |
| Models | Gas forest, logistic, SVM, kNN, MLP, histogram boosting and CORAL/logistic; five NSL forest seeds. Archived IDS boosting comparisons distinguished from fresh fits. |
| Uncertainty | Seed SDs, gas fold scores and conditional row-bootstrap intervals for gas and NSL. No inference across independent networks. |
| Routing | Oracle-assisted and fixed-confidence controls for newly fitted UNSW conditions. Cached fits lack added controls. |
| Ranking inversion | Constructed example fully specified. No natural benchmark inversion claimed. |
| Official versus shuffled UNSW | Archived context retained. Changing cohorts cannot isolate shift, imbalance and capacity causally. |
| Other metrics | Standardized counts and macro/weighted/micro/balanced-accuracy ceilings for primary cases, plus fold and union conventions. |

## Audit, artifact and writing

- Illustrative audit with six coded sources, query strings, access date and exclusions. No prevalence claim. Nuako source download returned HTTP 403.
- Friday arithmetic establishes a denominator of at least seven under its assumptions. It does not uniquely establish label union.
- Gas literature scores are recorded against a source-only cap with a calibration compatibility caveat. Numerical exceedance alone is not coded as a violation.
- Related work adds pooling, macro-F1 definitions, time-aware evaluation and open-set recognition, checked against primary sources.
- Pip package and CLI, environment pins, MIT license, Docker recipe, make targets, claim map and CI workflow supplied. Local package installation and CLI execution succeeded. Docker and remote CI require separate verification.
- Digits and historical splits defined in the main text, repair orders included, uncertainty targets named, broader impact separated, research questions answered.
- Case summary, stacked repair components, withholding-size curve and reporting flowchart added. Gas unavailability uses pattern coding.
- Official TBench class and style downloaded for the paper package. Native compilation and page-limit verification remain pending after TeX server HTTP errors. Automatic approval review rejected starting a local cache helper because its required approval category was disabled. Reading-copy PDFs are checked separately.
- Permanent DOI, external anonymous hosting and independent reproduction remain pending. Public code and MIT notice identify the author.

## Corrections to roadmap claims

1. Polynomial time at fixed fold count is XP, not by itself FPT.
2. Minimum-training-count thresholds cannot cap an unrestricted classifier's attainable score.
3. The denominator inference is not unique to label union.
4. The exact digits gap rounds to 0.02824. Subtracting separately rounded values gives 0.02823.

The remaining significance question is the material external natural case.
