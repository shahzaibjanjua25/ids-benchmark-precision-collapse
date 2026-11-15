# Current article source

- manuscript.typ / manuscript.pdf: rewritten research draft.
- supplement.typ / supplement.pdf: mathematical and reproduction notes.
- references.bib: selected current bibliography.
- generated/: tables and vector/raster figure from result CSVs.

Compile from the repository root with `python code/build_revision_paper.py` after
installing requirements-revision.txt. This generates tables and the figure before
compiling both PDFs with Typst. `python code/qa_revision_pdfs.py RENDER_DIRECTORY`
renders all pages for inspection. The generated files are intentionally committed.

The older files in paper/ are historical and were not overwritten. Current claims
are mapped in review/revision_20261115/EVIDENCE.md. This is not certified
publication-ready or a claim of independent journal peer review.

The primary delivery is now native/manuscript.pdf and native/supplement.pdf,
compiled in the journal-linked two-column Springer class. Run
`python code/build_native_revision.py` with pdflatex/bibtex on PATH after the
Typst build generates tables/figures. Style provenance and notices are in
native/PROVENANCE.md. Native visual inspection: review/continuation_20261115/NATIVE_PDF_QA.md.
