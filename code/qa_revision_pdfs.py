"""Render every current PDF page and record bounds and extractability checks.

Rendering supports visual review; this script does not replace human/agent visual
inspection. Pass an output folder outside the repository for intermediate PNGs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("render_dir", type=Path)
    args = parser.parse_args()
    args.render_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name in ["manuscript", "supplement"]:
        path = ROOT / "paper/revision" / f"{name}.pdf"
        doc = pymupdf.open(path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text()
            assert len(text.strip()) > 50, (name, i)
            assert "\ufffd" not in text, (name, i, "replacement glyph")
            for block in page.get_text("blocks"):
                x0, y0, x1, y1 = block[:4]
                assert x0 >= -0.5 and y0 >= -0.5 and x1 <= page.rect.width + .5 and y1 <= page.rect.height + .5, (name, i, block[:4])
            page.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3)).save(str(args.render_dir / f"{name}-{i+1:02}.png"))
            pages.append({"page": i+1, "characters": len(text), "text_bounds_passed": True})
        records.append({"pdf": path.relative_to(ROOT).as_posix(),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "pages": pages, "all_pages_rendered": True,
                        "visual_review": "See review/revision_20261115/PDF_QA.md; rendering alone is not a visual pass"})
    (ROOT / "review/revision_20261115/pdf_qa.json").write_text(json.dumps(records, indent=2), encoding="utf8")
    print([(r["pdf"], len(r["pages"])) for r in records])


if __name__ == "__main__":
    main()
