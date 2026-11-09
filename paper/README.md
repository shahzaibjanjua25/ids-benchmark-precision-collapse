# Manuscript sources for release 0.9.2

main.tex is the editable primary manuscript source. Run
`python paper/sync_tbench_sources.py` to regenerate the named and anonymous
publisher-class sources from its body. supplementary.tex contains the
vocabulary-oracle proofs, repair accounting,
solver details and
optional historical controls. The public repository and its main source identify
the author; the anonymous manuscript needs a separate anonymous artifact host
for blind review.

Obtain the publisher class, bibliography style and logo through the
[TBench author guide](https://press-t.benchcouncil.org/journals/TBench/pages/Guide-for-Authors).
Those third-party files are not included in the MIT code release. The downloaded
bundle's README and class header contain different licensing statements; their
original notices are retained in the local submission package.

manuscript.pdf, anonymous.pdf and supplement.pdf are reading copies converted
through Pandoc/Typst. The current copies have 14, 14 and 5 pages. They were
rendered with Poppler at 80 dpi; contact sheets and the NSL/CIC tables were
visually checked for clipping, overlap and unreadable layout. Native
publisher-class compilation and journal pagination have not been verified. To
rebuild reading copies with Pandoc and Typst on PATH:

    python paper/build_reading.py

These PDFs do not certify compliance with the journal's native layout. The
manuscript includes an accurate statement of generative-AI assistance. The author
must review the final submission and supply any submission-system information
that the journal requests. No acceptance or external review score is guaranteed.
