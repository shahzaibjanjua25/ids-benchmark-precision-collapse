# Final PDF inspection

Both PDFs were compiled with Typst 0.15.2 and every page was rendered to PNG.
The current main article has 10 pages and the supplement 4 pages. The automatic
record in pdf_qa.json checks nonempty extractable text, replacement glyphs and
page bounds, and hashes the inspected PDF bytes.

A visual pass inspected contact sheets for all 10 article pages and all four
supplement pages, including the title/abstract, main mathematical results,
proof appendix, target-resolution figure, results tables, and references. No
clipping, overlap, or missing glyphs was apparent. The abstract follows the
journal-specific headings; citations use alphabetized Harvard author-date
format. The figure is available as vector SVG/PDF and a 600-dpi PNG.

This is PDF layout QA, not verification of journal-native format. An editable
Word submission copy was converted from the rebuilt PDF, anonymized, and checked
for visible text, tables, replacement glyphs, metadata, and four native Word
equation objects. Equation 4 has explicit nested superscript structures for
both exponents. Its layout could not be rendered here because LibreOffice and a
working Word window were unavailable, so the DOCX still needs a visual check in
Microsoft Word before upload. No independent human replication of the research
results has been performed.
