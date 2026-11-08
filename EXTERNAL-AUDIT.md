# Illustrative source audit

These targeted checks are separate from the release-0.5.0 frozen 50-candidate
screening pilot in audit/crossref_20261108. They are retained as source-specific
compatibility notes and are not the denominator of that pilot.

Access date: 2026-11-08, Asia/Karachi. This is a targeted compatibility audit,
not a systematic review and not a prevalence estimate. Four sources were carried
forward from the preceding revision. The new search inspected the gas protocol
and official CICDDoS2019 documentation. Six sources are retained in the coding
sheet, including excluded and unresolved cases.

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
