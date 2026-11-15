# Final PDF inspection

Both PDFs were compiled with Typst 0.15.2 and every page was rendered to PNG.
The current main article has 10 pages and the supplement 3 pages. The automatic
record in pdf_qa.json checks nonempty extractable text, replacement glyphs and
page bounds, and hashes the inspected PDF bytes.

A visual pass inspected a contact sheet covering all 10 article pages and
enlarged views of the title/abstract, mathematical proof, target-resolution
figure, results tables, and final references. The checked pages showed no
clipping, overlapping content, or missing glyphs. All citations compiled and
referenced figure and table labels resolved. The figure is available as vector
SVG/PDF and a 600-dpi PNG.

This is PDF layout QA, not verification of journal-native format. An editable
Word submission copy was converted from the rebuilt PDF, anonymized, and checked
for text, table presence, replacement glyphs, and identifying metadata. It could
not be rendered with the standard DOCX renderer because LibreOffice was
unavailable. The Word layout therefore still needs a visual check in Word before
upload. Visual inspection of the PDFs was performed
by this automated workflow, not an independent human.
