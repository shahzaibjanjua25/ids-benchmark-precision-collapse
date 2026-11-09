# Internal re-review, revision 0.9.2

**Assessment: 6/10.** Major revision for a selective Q1 journal; plausible as a
correctness-focused evaluation-methods note after independent review. This is
an internal assessment, not a TBench decision.

## Changes in this revision

- The abstract is shorter and centers the NSL-KDD and CICIDS2017 findings.
- The Biyouki LOFO result is no longer assigned an unsupported 14/15 ceiling.
  The paper's methods say CICIDS metrics are binary unless stated otherwise;
  its Table 4 does not define the LOFO scoring labels or cohort. Conditional
  ceilings are given for separate Web Attack subtypes (12/15), a merged Web
  Attack category (12/13), and binary BENIGN/ATTACK scoring (1). The result
  remains unresolved rather than being called incompatible.
- The NSL-KDD artifact now gives the 40-label train/test union mapping and
  explains why a coherent mixed-resolution score equals the five-category
  score: all four attack families have test-only subtypes. The inferred-union
  and positive-support scores are both 0.48349 (SD 0.00549).
- The natural-protocol table reports F/O, including 0.43343 for the NSL-KDD
  forest mean, and the generator/verifier check the ratios.
- The CIC binary day table states that it is seed 42 only and describes its
  large per-day recall spread. A five-seed refit was not completed; no
  seed-level uncertainty is claimed.
- The binary analysis is explicitly framed as what a unit ceiling does not
  guarantee.

## Remaining reasons for a major revision

The central inequality is an elementary consequence of recall under a
restricted output set. The empirical work is reproducible and the label
resolution examples are useful, but the literature audit still establishes no
published score above its applicable legal-output ceiling. The Biyouki case
does not establish a violation because its scoring convention is ambiguous and
binary scoring is plausible. The broader 50-record screen remains a pilot with
33 unresolved eligibility decisions, not a field-level survey. The manuscript
therefore does not show that reported IDS conclusions are generally invalid or
that the diagnostic has changed prior results.

The revisions improve accuracy, clarity and reproducibility. They do not
justify a 9.5/10 claim or an acceptance recommendation at a selective Q1
journal. The main path to a higher significance rating remains a larger,
independently checked audit with fully specified published scoring targets,
or another empirical finding that changes a defensible literature conclusion.

Reading copies were rebuilt and visually checked. Native publisher-class
compilation, independent reproduction, remote CI, permanent DOI and anonymous
artifact hosting remain unverified.
