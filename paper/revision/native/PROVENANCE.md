# Publisher-native manuscript source

Target: International Journal of Information Security. Guidelines checked
2026-11-15: https://link.springer.com/journal/10207/submission-guidelines .
The journal's linked two-column LaTeX package is
https://media.springer.com/full/springer-instructions-for-authors-assets/zip/1633537_svjour3-Latex-package.zip .

`svjour3.cls`, `svglov3.clo`, `spphys.bst` and `readme.txt` are unmodified files
from that publisher package. Their Springer notices apply; the repository's
software license does not relicense these third-party files. The class reports
version 3.3 (2010/11/25), as distributed by the currently linked journal guide.

The bibliography uses the unmodified `sn-mathphys-num.bst` from Springer
Nature's general author package, retaining reference titles and numeric
citations. Official download page:
https://www.springernature.com/us/authors/campaigns/latex-author-support/see-where-our-services-will-take-you/18782940
Downloaded archive SHA-256:
812e76dcaa9c28dc1bff1fb6065d51729b67d4ea140552a05088317414a3ecae.
Its publisher notices apply as well. The older supplied `spphys.bst` is retained
unmodified for provenance but is not selected because it omits article titles.

Build using `python code/build_native_revision.py` from the repository root,
with pdflatex and bibtex available on PATH. The executed build used portable
TinyTeX-1 2026.11 (TeX Live 2026), obtained from its official RStudio release.
The exporter reads the canonical revision prose, math, generated tables and
bibliography. A separate PDF build does not establish scientific acceptance.

The journal is fully open access; an article processing charge may apply.
Funding, authorship, ethics, AI assistance and code/data statements appear in
the manuscript. No manuscript has been submitted or uploaded to the journal.
