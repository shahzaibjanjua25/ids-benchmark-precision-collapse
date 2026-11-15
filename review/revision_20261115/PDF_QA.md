# Final PDF inspection

Both PDFs were compiled with Typst 0.15.2 and every page was rendered to PNG.
The final main article has 9 pages and the supplement 3 pages. The automatic
record in pdf_qa.json checks nonempty extractable text, replacement glyphs and
page bounds, and hashes the inspected PDF bytes.

A Codex visual pass inspected a contact sheet covering all rendered pages and
larger views of mathematical proofs, the target-resolution figure, tables and
the final references. The earlier one-reference final page was eliminated by
adjusting reference spacing. The title's awkward word break was removed. The
final equation/figure/table views showed no clipping, overlapping content or
missing glyphs. All citations compiled; all referenced figure and table labels
resolved. The figure is available as vector SVG/PDF and a 600-dpi PNG.

This is layout QA, not verification of journal-native format. The publisher-class
or Word submission gate in the journal assessment remains unresolved. Visual
inspection was performed by this automated workflow, not an independent human.
