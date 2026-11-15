# Final native PDF inspection

The primary article uses the journal-linked svjour3 two-column class. The final
manuscript has ten pages; the supplementary notes have four. Every page was
rendered at 1.3x and inspected in page contact sheets, with full-size checks of
the final reference pages. Equations, table columns, captions, the vector figure,
headers, footnotes, and reproduction commands are legible within the page.

The initial long count definition was split into aligned lines. An initial
bibliography omitted titles; it was replaced by the publisher's numbered style,
with explicit compatibility definitions. URL wrapping was repaired. Reference
text uses nine-point type, removing an otherwise nearly empty eleventh page.
No overfull boxes, undefined citations/references or missing-character messages
remain in the final LaTeX logs. Final page text bounds and replacement-glyph
checks pass. Rendering alone was not treated as visual inspection.

The final first eight article pages and all four supplement pages are
pixel-identical to the fully inspected preceding render; final article pages
nine and ten were then viewed separately at full size. Native formula displays
were checked against the canonical definitions/proofs; compilation alone was
not taken as proof of a correct math conversion.

`native_pdf_qa.json` hashes the exact final native PDFs. `native_build.json`
records the compiler and successful command sequence. No later PDF rebuild
may be delivered without refreshing these hashes and reviewing changed pages.
The Typst derivative is retained as editable-source evidence and has separately
refreshed automated rendering checks; the delivered primary PDF is native.
