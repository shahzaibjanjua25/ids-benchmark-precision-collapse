# Illustrative source audit

These targeted checks are separate from the release-0.5.0 frozen 50-candidate
screening pilot in audit/crossref_20261108. They are retained as source-specific
compatibility notes and are not the denominator of that pilot.

Access dates: 2026-11-08 through 2026-11-11, Asia/Karachi. This is a targeted compatibility audit,
not a systematic review and not a prevalence estimate. Four sources were carried
forward from the preceding revision. The new search inspected the gas protocol,
official CICDDoS2019 documentation, and published CICIDS2017 target definitions.
The coding sheet includes excluded and unresolved cases.

Search service: available web search, followed by publisher, author or dataset-owner
pages. The search covered source material available on the access date. There was
no database-complete date restriction or claim of exhaustive screening.

Queries included:

- CICIDS2017 day-level temporal holdout macro F1
- CICIDS2018 chronological split binary F1
- The dashboard says perfect seven harmonized classes
- One-Class Drift Compensation for an Electronic Nose Setting 1 Table 4
- CIC DDoS2019 dataset training testing attacks official

Coding fields are source type, protocol, reported metric, reported value, compatible
test-support ceiling, status, and evidence. The reported values are transcriptions.
The ceilings are derived only under the stated output restriction.

## Friday report

Source: https://www.pcboss.me/projects/network-intrusion-detection/

The report lists 5688 benign and 30704 unavailable attack rows, benign-only recall
0.9967, and macro F1 0.0435. With rounding to four decimal places, even the smallest
compatible true-positive count gives benign F1 above 0.269. A four-label average
must exceed 0.067. An unweighted class-F1 denominator must be at least seven if all
numbers describe the same predictions. This is compatible with label union, but
also with an explicitly wider label list. The prose alone does not resolve it.
The linked source archive returned HTTP 403 on this access date.

## Gas study

Source: https://doi.org/10.3390/chemosensors9080208

The paper's Table 3 specifies adjacent-batch setting 1. Table 4 gives source-5 to
target-6 accuracy of 72.91, 78.78, 78.95 and 78.42 percent for CCPCA, TCTL, TMTL and
ODCM. These are below the source-label-only cap 1833/2300 = 0.7969565. TMTL+ reports
96.00 percent. The method comparisons include target calibration information.
Compatibility requires its effective labels and permitted outputs, which have not
been independently reconstructed. A numerical exceedance alone is not coded as a
violation. The reported average across batch tasks is not a pooled row accuracy.

## CICDDoS2019

Source: https://www.unb.ca/cic/datasets/ddos-2019.html

The official page's prose and table disagree on PortMap/PortScan naming and the
first/second-day ordering. Actual file labels and the selected protocol are needed
before computing a fine-grained ceiling. No benchmark score or ceiling is inferred.

## Published label-resolution example: NSL-KDD

Source: Ayantayo et al., *Network intrusion detection using feature fusion with
deep learning*, Journal of Big Data 10, 167 (2023),
https://doi.org/10.1186/s40537-023-00834-0.

The article states that 17 fine-grained attack subtypes in KDDTest+ do not appear
in KDDTrain+, then maps the target to Normal, DoS, Probe, R2L and U2R. It also
constructs a second test set excluding rows with those unseen subtypes. Under
the stated five-output task, all five categories have training support and the
coverage ceiling is 1. The article's broad-category scores are therefore not
incompatible with the ceiling. They also do not establish exact recognition of
the unseen subtypes. This is a verified published example of a task-resolution
choice, not evidence that a published score violated its declared vocabulary.

Our paired NSL-KDD reaggregation uses the released five forest confusion
matrices and the dataset's five-category mapping. Mapping both true and predicted
labels gives macro-F1 0.23953 +/- 0.00878 for fine subtypes and 0.48349 +/-
0.00549 for broad categories; the corresponding ceilings are 0.55263 and 1.
This is a post-hoc change of target on the same predictions, not a refit or a
comparison between models trained for different taxonomies. It demonstrates
that label resolution can materially change both score and attainable ceiling,
while leaving the absent published-score conflict unresolved.

## Published CICIDS2017 day-holdout score: binary target

Source: Alsaadi et al., *Dataset-Calibrated Perturbation Budgets for Adversarial
Robustness Evaluation of Machine-Learning Network Intrusion Detection Systems*,
Technologies 14(10), 647 (2026), Table 2,
https://doi.org/10.3390/technologies14100647.

Table 2 reports macro F1 = 0.619 for a random forest under whole-day holdout.
The table explicitly identifies the task as binary. The article's discussion
notes that the held-out day's fine-grained attack types are absent from training,
but the binary output labels (BENIGN and ATTACK) both occur in training. The
positive-support ceiling for this reported target is therefore 1, so the score
is compatible with the target's legal vocabulary. It is not a score for exact
attack-type attribution and is not a violation of the 15-label CICIDS2017
ceiling.

The companion follow-up fit in this release trains a 100-tree random forest on
the same MachineLearningCVE cohort, maps all non-BENIGN labels to ATTACK, trains
on Monday through Thursday and tests on Friday. It yields macro F1 = 0.61754
and attack recall = 0.27894 for seed 42. The close value is a cross-study
consistency check, not an exact reproduction: the original paper's complete
preprocessing and hyperparameters are not asserted to match this pipeline.
This case shows why protocol reports must name both the split and output target.

## Published CICIDS2017 leave-one-family-out result: binary task is stated in methods

Source: Biyouki et al., *An Enhanced Deep Learning Framework for Intrusion
Classification Enterprise Network Using Multi-Branch CNN-Attention Architecture*,
Scientific Reports 16, 3962 (2026), https://doi.org/10.1038/s41598-025-34166-1.

Table 4 reports 98.55% macro F1 for the CICIDS2017 leave-one-family-out
experiment, with Web Attack withheld from training. The Methods section states
that CICIDS2017 is evaluated as binary Normal/Attack and that its metrics use
that configuration unless otherwise stated. Table 4 does not specify a
different label inventory, so we interpret its target as binary. Both legal
outputs remain in training because other attack families are retained. The
reported score is therefore compatible with a ceiling of 1. This is a
source-based target interpretation, not an independent re-score; predictions
are not released. A 15-label ceiling of 0.80 or 13-label ceiling of 0.9231
would apply only under an unstated multiclass target and is not the reading
supported by the methods.

The Nuako technical report lists macro F1 0.0435 against the conservative
comparison ceiling 0.25. That score is below the ceiling and therefore cannot
be a ceiling violation. The scored denominator and target inventory remain
unresolved.

## Public prediction-artifact re-score: corrected CICIDS2017 five-superclass task

Franco-Valiente et al. publish per-seed 5 by 5 confusion matrices for a
connection-grouped CICIDS2017 evaluation, along with code and curated results:
https://doi.org/10.3390/electronics15184074 and
https://github.com/josemifv/distributed-nids-mlops. Their target is the five
superclasses Normal, DoS, Probe, R2L and U2R. Table 2 reports nonzero training
support for each, including 65 U2R rows. We downloaded the ten baseline
connection-grouped matrices for seeds 42--51 and recomputed macro F1 from
counts. The mean is 0.90002 (sample SD 0.05143; t-based 95% CI half-width
0.03679), matching the reported 0.900 ± 0.037. All five test classes have
support, and all five outputs have training support, so the applicable ceiling
is 1. The result is compatible. It checks one published paper, one model and one
protocol; it is not a re-score of 10--20 papers or a prevalence estimate.
Matrices and recomputed seed values are archived in
`audit/external/franco_valiente_2026/` and checked by
`code/verify_external_artifact_audit.py`.
