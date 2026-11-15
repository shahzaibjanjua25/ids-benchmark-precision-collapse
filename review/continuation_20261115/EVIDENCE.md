# Continuation evidence map

This record supersedes the earlier snapshot's incomplete-work status where
specified. Earlier logs, errors and subjective reviews remain for provenance.

| Claim | Executed source/evidence |
|---|---|
| 60 RT-IoT fits, three seeds and ten conditions | code/run_rt_iot_audit.py; results/continuation_20261115/rt_iot/runs.csv and manifest.json |
| Fixed test cohort, capped paired memberships | split.npz and 30 condition NPZs; verify_rt_iot_audit.py |
| 18,272 exact input groups, no cross-split identity | raw CSV SHA in manifest; optional --data verifier reconstructs hashes and SGKF |
| Oracle 0.84260594 for dominant attack omission | exact rational certificate plus independent destination enumeration |
| Binary mean 0.986803, ARP held alarm recall 0.163656 | scores independently reconstructed from predictions; generated RT table |
| Six additional Bot-IoT matrices | audit_botiot_matrices.py --source-pdf; source_verification.json records 24 checked cells and author-version scope |
| 23 targeted records, 20 completed published target classifications | audit/continuation_20261115/sources.csv; two insufficient + one preprint excluded |
| Balikas/Cruz relevant prior | PROTOCOL.md, references.bib and narrowed related-work text |
| Publisher-native source | paper/revision/native; unmodified journal-linked svjour3 styles with PROVENANCE.md |
| Large-count correctness repair | core._prepare normalizes exact validated counts before grouping; check_certified.py adds float-aggregate and Fraction regressions |
| Verifier does not repair NSL membership evidence | verify_revision_results.py asserts existing split arrays |

All RT fits completed before the saved-string dtype was normalized from object
to Unicode for pickle-free loading. This changes serialization, not labels,
predictions or numeric results. The runner now emits Unicode directly.

The initial native build compiled but had an overwide definition; it was split
into aligned lines. A fallback Tectonic attempt failed DNS; portable pdflatex
from official TinyTeX subsequently compiled the actual publisher class. These
dependency failures are not experimental successes and do not affect fitted
evidence. Native rendering/visual checks and final delivery import are separate
gates recorded after final compilation.

No journal submission, remote push, independent human peer review, or journal
acceptance is claimed. A script performs an ordinary branch push when run by
the user with working GitHub authentication.
