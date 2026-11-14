# Dataset and outlet investigation (2026-11-15)

Dataset selection followed a scientific question, not a target dataset count.

- NSL-KDD: fresh raw-data model reproduction and an exact-feature overlap control.
  Official file sizes and label counts were checked. Raw files were downloaded
  from the documented public mirror and hashed; only predictions and counts are
  delivered. Train/test overlap used 41 features, excluding difficulty and class.
- Original and corrected CICIDS2017: saved counts, chronology manifests and
  confusion evidence rechecked. Raw multi-gigabyte refits were not repeated.
- UNSW-NB15: existing controlled withholding grid and benign-only diagnostic
  retained; saved verification passed. Not newly refit.
- CICIoT2023: selected as a contemporary IoT contrast with public integer confusion
  matrices, enabling actual independent arithmetic. Official page:
  https://www.unb.ca/cic/datasets/iotdataset-2023.html . The raw download endpoint
  https://cicresearch.ca/IOTDataset/CIC_IOT_Dataset2023/ returned a registration
  form/server error; no new raw-data experiment is claimed. Two published model
  matrices were independently re-scored and checked against the publisher PDF.
- CSE-CIC-IDS2018, CIC-DDoS2019, TON_IoT, Bot-IoT and Edge-IIoTset remain candidate
  raw-data extensions rather than claimed completed experiments. OpenTriIDS uses
  Edge-IIoTset and CICIoT2023, supporting a source-based unknown-output contrast.
  This revision does not claim exhaustive contemporary dataset investigation.

UNB's dataset FAQ permits use/redistribution with required dataset/paper citation:
https://www.unb.ca/cic/datasets/ . The revision avoids redistributing raw data.

## Journal assessment

Primary **scientific-fit candidate**: International Journal of Information Security.
Its information-security scope fits a focused evaluation-methodology article.
The authoritative pages accessed were:

- https://link.springer.com/journal/10207/submission-guidelines
- https://link.springer.com/journal/10207/how-to-publish-with-us

The current publishing page states fully open access, with an APC of GBP 2,690 /
USD 3,690 / EUR 2,990 before applicable taxes. Do not assume a free subscription
route for this journal. Charges can change; this is a dated check, not a quote.
Author-guideline themes include source files, abstract, declarations, references,
tables and artwork. No editorial interest or acceptance is implied.

Subscription-route alternative: Arabian Journal for Science and Engineering,
Computer Science and Engineering section. Current publisher page confirms hybrid
publishing with **no APC for the subscription route**:
https://link.springer.com/journal/13369/how-to-publish-with-us . Its scope:
https://link.springer.com/journal/13369/aims-and-scope . Guidelines:
https://link.springer.com/journal/13369/submission-guidelines . Research articles
are accepted; technical notes have a four-printed-page limit. The present full
article is not a four-page technical note. The abstract should be 150--250 words,
with 4--6 keywords, numeric citations and declarations. LaTeX iicol is recommended;
Word is accepted. The revised PDF uses scholarly Typst typesetting and includes
editable source, but native publisher-class/Word submission compliance is NOT
certified. Native format conversion remains a submission gate, not a passed check.

Computers & Security: direct ScienceDirect author/publishing pages returned 403.
An apparent mirror at computersandsecurity.org had suspicious nonpublisher login
links and was **not used as an authoritative policy source**. No unverified APC
or policy from that site is relied on. JISA is not selected for automatic
resubmission after its desk rejection. No submission or contact was made.

The actual final assessment is below the requested 9/10 readiness threshold.
No journal-specific publication-readiness guarantee is offered.
