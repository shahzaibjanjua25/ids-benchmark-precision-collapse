"""Re-score published CICIoT2023 Tables 7 and 8, without model refitting.

Source: Neto et al., Sensors 23(13):5941, doi:10.3390/s23135941.
Integer cells transcribed from the publisher's HTML tables on 2026-11-15.
Rows are truth; columns are predictions in the shared order below. These are
two model settings in ONE paper, not two independently sampled studies.
"""
import json
import argparse
import hashlib
import re
from pathlib import Path
import numpy as np
import pandas as pd

LABELS = ["Benign", "Brute Force", "DDoS", "DoS", "Mirai", "Recon", "Spoofing", "Web"]
MATRICES = {
    "dnn": [
        [230229,1,7,2,0,9270,3812,1], [1054,438,3,0,0,1216,271,1],
        [23,0,7523853,1012,545,653,65,0], [15,0,4933,1787065,60,61,33,0],
        [10,0,258,41,583283,64,21,0], [18517,2,968,30,1,55656,3455,1],
        [30485,0,17,0,15,10021,67257,3], [1976,0,1,0,0,2028,1221,207]],
    "rf": [
        [234929,4,24,2,4,3192,5159,8], [1342,169,1,0,0,844,626,1],
        [15,0,7525049,557,18,339,173,0], [7,0,1088,1790979,34,12,47,0],
        [5,0,603,18,582921,100,30,0], [11565,6,1418,11,16,60006,5591,17],
        [14618,1,18,6,11,4743,88371,30], [1140,1,3,1,1,1265,2792,230]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    args = parser.parse_args()
    pdf_hash = None
    if args.source_pdf:
        from pypdf import PdfReader
        source = PdfReader(args.source_pdf)
        for name, page in [("dnn", 18), ("rf", 19)]:
            text = source.pages[page].extract_text()
            if name == "dnn":
                text = text[text.index("Table 7."):]
            for label, expected in zip(LABELS, MATRICES[name]):
                # PDF uses the fi ligature in Spoofing.
                pattern = re.escape(label).replace("Spoofing", "Spoo(?:fi|ﬁ)ng")
                matches = re.findall(r"(?<!\w)" + pattern + r"\s+((?:[\d,]+\s+){7}[\d,]+)", text)
                assert len(matches) == 1, (name, label, matches)
                assert [int(x.replace(",", "")) for x in matches[0].split()] == expected
        pdf_hash = hashlib.sha256(args.source_pdf.read_bytes()).hexdigest()
    root = Path(__file__).resolve().parents[1]
    out = root / "results/revision_20261115/ciciot2023_published"
    out.mkdir(parents=True, exist_ok=True)
    pdf_record = out / "pdf_cell_verification.json"
    if pdf_hash:
        pdf_record.write_text(json.dumps({"sha256": pdf_hash, "cells_verified": 128,
                                          "pages": [19, 20], "date": "2026-11-15"}, indent=2), encoding="utf8")
    elif pdf_record.exists():
        pdf_hash = json.loads(pdf_record.read_text())["sha256"]
    rows, perclass = [], []
    for model, raw in MATRICES.items():
        cm = np.array(raw, dtype=np.int64)
        pd.DataFrame(cm, index=LABELS, columns=LABELS).to_csv(out / f"{model}_confusion.csv")
        n, p = cm.sum(1), cm.sum(0)
        f1 = 2 * np.diag(cm) / (n + p)
        assert (n > 0).all() and (np.diag(cm) > 0).all()
        published = {"rf": 0.71928904, "dnn": 0.69726491}[model]
        rows.append({"model": model, "source_table": 8 if model == "rf" else 7,
                     "test_rows": int(cm.sum()), "classes": 8,
                     "recomputed_macro_f1": float(f1.mean()),
                     "published_f1": published, "absolute_difference": abs(float(f1.mean()) - published),
                     "recomputed_weighted_f1": float(np.dot(n, f1) / n.sum()),
                     "recomputed_accuracy": float(np.trace(cm) / cm.sum()),
                     "legal_output_ceiling": 1.0,
                     "classification": "Verified compatible",
                     "score_agreement_1e_7": bool(abs(float(f1.mean()) - published) < 1e-7)})
        for k, support, value in zip(LABELS, n, f1):
            perclass.append({"model": model, "class": k, "support": int(support), "f1": value})
    summary = pd.DataFrame(rows)
    summary.to_csv(out / "summary.csv", index=False)
    pd.DataFrame(perclass).to_csv(out / "per_class.csv", index=False)
    # The table counts come from the publication, not a newly downloaded raw dataset.
    (out / "provenance.json").write_text(json.dumps({
        "doi": "10.3390/s23135941", "url": "https://www.mdpi.com/1424-8220/23/13/5941",
        "retrieved": "2026-11-15", "tables": [7, 8], "row_axis": "true labels",
        "verification": "Each integer cell checked against publisher HTML; metrics independently recomputed",
        "publisher_pdf_sha256": pdf_hash, "pdf_cells_automatically_verified": bool(pdf_hash),
        "pdf_check_record": "pdf_cell_verification.json" if pdf_hash else None,
        "training_counts": "Not reconstructed; all eight legal outputs evidenced by nonzero diagonal cells",
        "limitations": "One paper; two settings; no refit; source does not explicitly name F1 averaging in Eq. 4"}, indent=2), encoding="utf8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
