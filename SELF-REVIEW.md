# Internal critical review, release 0.5.0

Assessment: approximately 8/10. Recommendation: major revision as a full research
article. This is an internal assessment of work revised in this session, not an
independent peer review or a TBench editorial decision. No journal acceptance
threshold or official scoring rubric is assumed.

The strongest addition is a natural, consequential comparison on the official
fine-grained NSL-KDD split. The forest leads full macro F1, while kNN leads the
covered-row target. A post-hoc counterfactual also reverses their full-score order
on unchanged test rows without adding true positives: forest 0.25456 -> 0.26914;
kNN 0.25160 -> 0.29839. The reversal survives inferred-union scoring. These are
six declared local pipelines, not a reversal of an already-published comparison.
Preprocessing differences and the oracle's use of true availability are explicit.

The full UNSW experiment now saves covered and unavailable confusion matrices
for every one of 36 pairs and five seeds. All 180 full scores match the previous
grid within 1e-12. Rank correlations, within-pair reversals and pair means are
descriptive; no iid confidence interval is attached to dependent fits. The gas
comparison retains its null result: all 19 fitted-model rankings agree.

Theory includes the general NP-hardness result and an implemented grouping
algorithm that is fixed-parameter tractable in the number of destination labels.
The elementary recall ceiling is identified as such. The legal-vocabulary API
accepts global heads without falsely excluding training-absent labels. Minimum
training support remains sensitivity analysis unless enforced as an output rule.

The main manuscript is substantially shorter, with three data tables and one
hero figure. Repair accounting, optional controls and solver detail are in the
included supplement. All headline interpretation is present in the main text.
MIT code licensing, citation metadata, CI checks and one-command evidence/table
regeneration are supplied. The wheel builds and its installed interfaces work.

Remaining acceptance concerns:

1. The literature work is a 50-candidate screening pilot: three confirmed
   eligible, fourteen excluded and thirty-three unresolved. It is not the
   requested survey of 40--60 verified eligible temporal IDS studies, and yields
   no field prevalence estimate or verified incompatible published score.
2. The natural winner reversal is demonstrated on local baseline pipelines and
   one established split. Broader independent networks, contemporary protocols
   and externally published conclusions remain unverified.
3. The theoretical oracle correction is small in the natural cases; the grouping
   bound still grows quickly with destination-label count. No approximation
   guarantee, deployment benefit, sharp MCC/kappa extension or adoption evidence
   is claimed.
4. Native publisher-class compilation and final journal pagination, a permanent
   DOI, external anonymous artifact hosting and independent reproduction remain
   pending. Readable PDF layout verification is not native-template verification.

Indicative sub-scores: correctness 9, novelty 7, empirical evidence 8,
reproducibility 8.5, writing/focus 8.5. The improvements support a substantially
stronger methodology note. They do not justify a guaranteed 9/10 rating or an
acceptance claim for a full journal article.
