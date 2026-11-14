# Adversarial review history

These are sequential automated perspective passes by one Codex agent. They are
not four independent people, external journal reviews, or evidence of acceptance.
Scores are subjective rubric assessments, not scientific measurements.

## Pass 1: initial manuscript

Mathematics: the elementary bound is correct but thin as a primary novelty claim;
the most substantial oracle results are relegated to supplementary material.
Experiments: fixed-cohort evidence is useful, but estimator comparisons mix
preprocessing, literature breadth is weak, and saved results need rerunning.
Writing: excessive qualifications, repeated target distinctions and seven tables
obscure a coherent central question. Reproducibility: extensive artifacts exist,
but historical versus newly reproduced evidence must be distinguished.

Decision: major revision; not ready for submission. No numerical score was used
to force an outcome.

## Pass 2: after proof restructuring, rational verifier and fresh refits

- Mathematical reviewer: rederived repair, convex vertex allocation, tightness,
  vocabulary grouping, fixed/union objectives and Set Cover reduction. A zero-C
  union boundary case was explicitly corrected before delivery. The rational
  implementation matches row-level enumeration; novelty remains incompletely
  established. Do not advertise priority.
- Cybersecurity reviewer: the new matched-preprocessing arm fixes one comparison
  weakness. The feature audit reveals 654 distinct overlaps, so an official-split
  rerun alone is insufficient as clean evidence. Require the control arm and
  avoid causal claims across original/corrected CIC releases.
- Writing reviewer: the full rewrite is substantially more coherent. Retain
  concise RQs, integrate proofs into the main text, generate tables, and remove
  duplicated seed tables. Require a readable figure and no one-reference orphan
  page at the end.
- Reproducibility reviewer: validate PDF cells independently of transcription,
  save fresh predictions and membership, rerun original-commit checks in an
  isolated worktree, and test the packaged wheel and Git delivery.

Repairs implemented: overlap-controlled six additional fits; independent exact
pandas merge; twelve saved prediction matrices independently scored; three old
forest matrices reproduced exactly; PDF-cell validation; figure and generated
tables; separate original-commit worktree; clean-target wheel import; final
verification and packaging checks recorded alongside this file.

## Pass 3: final adversarial assessment

| Perspective | Weight | Score / 10 | Reason for remaining deduction |
|---|---:|---:|---|
| Mathematics and methods | 0.30 | 8.4 | Correct, tested characterization; priority not conclusively established and broad novelty remains modest |
| Cybersecurity and experiments | 0.30 | 7.0 | Better controlled evidence, but limited external operational impact and no completed twenty-paper audit |
| Writing and communication | 0.20 | 8.2 | Coherent focused draft; final journal-native formatting remains a gate |
| Reproducibility and integrity | 0.20 | 8.0 | Traceable current evidence and honest limits; not every historical raw fit or independent human replication completed |

Weighted value = 7.86, reported as **7.9/10**. The required 9/10 threshold is NOT
achieved and no reviewer perspective is artificially raised to pass it.

## Editorial screening decision

The revision is a defensible research draft with meaningful software and
experimental repairs. It should not be labeled publication-ready. The remaining
major concerns are demonstrated originality/impact and literature audit breadth;
native publisher submission compliance is also uncertified. These are substantive
gates, not a suggestion to disguise the work with stronger prose. A final PDF
and reproducible committed branch are delivered with this mandatory disclosure.
