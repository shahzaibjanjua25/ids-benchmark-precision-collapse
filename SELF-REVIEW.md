# Internal re-review, revision 0.9.4

**Self-assessment: 6.5/10.** Major revision remains appropriate for a selective
Q1 journal. This is an internal review, not a TBench decision or a promise of
acceptance.

## New evidence in this revision

- The corrected DistriNet CICIDS2017 archive was downloaded and verified. A
  timestamp-ordered Monday--Thursday to Friday holdout was run with Random
  Forest, Extra Trees and SGD log-loss over three seeds each. The five-label
  test cohort has one class in the training vocabulary, giving a fine-label
  ceiling of 0.20. The released table also reports binary metrics so its
  detection behavior is not confused with exact attack-label attribution.
- A separate benign-only Isolation Forest baseline on UNSW-NB15 supplies an
  open-set binary detector. Its output ceiling is one while attack recall stays
  low, making clear that legal outputs alone do not guarantee useful detection.
- Ten per-seed confusion matrices from one public published IDS artifact were
  independently re-scored. The recomputed mean macro F1 (0.90002) matches the
  paper's 0.900 +/- 0.037 and is compatible with the unit ceiling.
- The Biyouki article's Methods specify binary Normal/Attack scoring for
  CICIDS2017 unless otherwise stated, and Table 4 gives no different target.
  Its LOFO score is compatible with a ceiling of one; predictions are not
  released, so this is a source-based interpretation rather than a re-score.
  No incompatible published score is verified.

## Remaining reasons for major revision

The coverage inequality remains an elementary consequence of recall under a
restricted output set. The empirical work shows the diagnostic on natural
splits and the corrected CICIDS2017 release, but no confirmed published score
violation or change to a prior literature conclusion has been established.
The published artifact re-score covers one paper, not the requested 10--20
papers, and the frozen 50-record screen remains a single-reviewer pilot with
unresolved cases. This is not enough evidence for a field-level significance
claim.

The corrected CICIDS2017 result is one temporal split on one dataset with three
seeds and a per-class training cap. It does not isolate the label correction's
effect from other release changes. The ten external confusion matrices are
repeated seeds from the same study, not ten independent papers. Neither result
supports generalization across networks or studies.

The new evidence raises the practical value, but does not justify a 9.5/10
claim or an acceptance recommendation at a selective Q1 journal. The largest
remaining gain would come from the requested broader artifact-backed literature
audit, particularly if it finds a verified score conflict under an unambiguous
published scoring convention.

The reading PDFs for this revision were rebuilt and visually reviewed. Native
TBench class compilation, independent reproduction, remote CI, permanent DOI
and anonymous artifact hosting remain unverified.
