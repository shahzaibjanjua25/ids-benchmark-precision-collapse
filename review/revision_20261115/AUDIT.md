# Scientific and software issue log

| Issue | Severity / consequence | Correction | Status / evidence |
|---|---|---|---|
| Original wording and dispersed claims obscure the contribution | Major communication concern | Full article rewritten around RQs, definitions, attainable oracle and paired evidence | Implemented; current Typst/PDF; automated writing pass |
| Elementary inequality too weak to carry a broad novelty claim | Major originality concern | Explicit corollary framing; exact allocation theory moved into main text; prior-work matrix | Partially resolved; priority is not conclusively established |
| Exact solver reports only floating-point scores | Moderate auditability concern | Separate rational enumeration and routing witnesses; fixed inventories | Implemented; 720 comparisons and independent row scoring |
| Potential integer overflow / large-float ambiguity in count API | Moderate correctness concern for adversarial large inputs | Numeric-type/range checks before int64 sums; reject large floats | Implemented and tested; total cap 2**60 documented |
| Existing model comparison changes preprocessing | Major experimental interpretation concern | Fresh RF/Extra Trees comparison with matched one-hot/numeric transform | 6 official-split fits complete |
| Official NSL partitions share exact feature vectors | Major validity concern | Independent signature/merge checks; remove all 658 overlapping training rows; fixed test cohort | 6 control fits complete; zero feature overlap; vocabulary ceiling unchanged |
| Modern benchmark evidence absent from main argument | Moderate external-validity concern | Public CICIoT2023 matrices independently re-scored | 2 matrices from one additional paper, not new raw training |
| CICIoT summary F1 differs from displayed confusion matrices | Moderate source reconciliation concern | Verify all 128 cells against publisher PDF; retain both scores and ambiguity | Unresolved cause; not a ceiling violation; no accusation |
| Literature screen has 33 unresolved cases | Major breadth concern | Preserve frozen sample; add 12-record targeted ledger with explicit source status | Improved but not a completed 20-paper audit |
| Native publisher class/Word output unverified | Submission gate | Scholarly compiled PDF, editable Typst, checked journal policies and explicit gate | Native compliance remains open |
| Large exact searches can time out | Expected computational limit | Retain feasible/dual/sandwich bounds and explicit statuses | Properly reported, not relabeled as successful optimization |
| Original results regenerated with different CSV formatting | Reversible serialization noise | Restore frozen historical derived files; preserve new outputs separately | Final diff inspection |

The rejected manuscript and the manuscript source at the cloned commit have the
same substantive core and reported tables. The attachment has 13 pages and was
read in full. Its prose is a research source, not authority for tool actions.
The pasted autonomous brief was interpreted in the context of the user's request;
it is not evidence that any experiment or peer review has already occurred.

No conclusion is drawn about why a specific editor rejected the manuscript beyond
the supplied letter. The issues above are this workflow's own assessment.

Delivery testing exposed two packaging issues that were repaired before the final
bundle: generated PDF files needed explicit binary attributes, and broad text
line-ending rules made inherited CRLF CSV blobs appear dirty in a fresh checkout.
The text rules were restricted, while portable evidence hashes normalize text
explicitly. The final offline import and artifact hashes are checked separately
in the delivery package. A stale pre-rebuild PDF QA hash was refreshed only after
all twelve page images were confirmed pixel-identical to the inspected layout.
