"""Generate manuscript tables from verified result files and compile with Typst."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import pandas as pd
import typst

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/revision"


def table(name, headers, rows, caption, label):
    # Inputs are controlled artifact strings; brackets are escaped defensively.
    def cell(value):
        return "[" + str(value).replace("[", r"\[").replace("]", r"\]") + "]"
    content = '#figure(table(columns: (' + ', '.join(['1fr'] * len(headers)) + '),\n'
    content += 'inset: 5pt, stroke: 0.4pt,\ntable.header(' + ','.join(cell(x) for x in headers) + '),\n'
    for row in rows:
        content += ','.join(cell(x) for x in row) + ',\n'
    content += '), kind: table, caption: [' + caption + ']) <' + label + '>\n'
    (PAPER / "generated" / name).write_text(content, encoding="utf8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PAPER)
    parser.add_argument("--tables-only", action="store_true")
    args = parser.parse_args()
    (PAPER / "generated").mkdir(exist_ok=True)
    runs = pd.read_csv(ROOT / "results/revision_20261115/nsl_matched/runs.csv")
    assert len(runs) == 6 and set(runs.seed) == {42, 43, 44}
    assert not runs.duplicated(["model", "seed"]).any()
    rows = []
    for name, group in runs.groupby("model", sort=False):
        f = lambda key: f'{group[key].mean():.3f} ({group[key].std(ddof=1):.3f})'
        rows.append([name.replace("_", " ").title(), f("fine_macro_f1"), f("union_macro_f1"), f("category_macro_f1")])
    table("nsl_table.typ", ["Pipeline", "Fine / support", "Fine / union", "Five categories"], rows,
          "Fresh NSL-KDD fits with matched preprocessing. Mean macro F1 (sample SD) over seeds 42--44; all six fits share the official test cohort. Fine support ceiling 0.553; five-category ceiling one.", "tab-nsl")
    control = pd.read_csv(ROOT / "results/revision_20261115/nsl_no_feature_overlap/runs.csv")
    assert len(control) == 6
    rows = []
    for name, group in control.groupby("model", sort=False):
        f = lambda key: f'{group[key].mean():.3f} ({group[key].std(ddof=1):.3f})'
        rows.append([name.replace("_", " ").title(), f("fine_macro_f1"), f("union_macro_f1"), f("category_macro_f1")])
    table("overlap_table.typ", ["Pipeline", "Fine / support", "Fine / union", "Five categories"], rows,
          "NSL-KDD overlap-controlled refits: 658 training rows removed by exact feature identity, full test cohort retained. Mean macro F1 (sample SD) across three seeds. Vocabulary ceilings are unchanged.", "tab-overlap")
    targets = pd.read_csv(ROOT / "results/cic_lodo_target_resolution.csv")
    rows = [[r.resolution, str(r.target_classes), f"{r.coverage_ceiling:.3f}", f"{r.macro_f1:.3f}"] for r in targets.itertuples()]
    table("target_table.typ", ["Target", "Classes", "Coverage bound", "Macro F1"], rows,
          "Original CICIDS2017 day-holdout predictions mapped to three targets. All rows re-score the same pooled predictions, without refitting.", "tab-target")
    external = pd.read_csv(ROOT / "results/revision_20261115/ciciot2023_published/summary.csv")
    rows = [[r.model.upper(), f"{r.recomputed_macro_f1:.5f}", f"{r.published_f1:.5f}", f"{r.absolute_difference:.5f}"] for r in external.itertuples()]
    table("external_table.typ", ["Model", "Matrix macro F1", "Summary F1", "Absolute gap"], rows,
          "CICIoT2023 eight-class F1 computed from published Tables 7 and 8 versus the corresponding Table 6 entry. Both matrices contain 10,340,161 observations. Summary reconciliation is unresolved; these are not ceiling violations.", "tab-external")
    if args.tables_only:
        return
    subprocess.run([sys.executable, str(ROOT / "code/plot_revision_targets.py")], check=True)
    args.output.mkdir(parents=True, exist_ok=True)
    for filename in ["manuscript", "supplement"]:
        result = typst.compile(str(PAPER / f"{filename}.typ"), root=str(PAPER))
        (args.output / f"{filename}.pdf").write_bytes(result)
        print(f"Compiled {filename}: {len(result)} bytes")
    (PAPER / "generated/table_sources.json").write_text(json.dumps({
        "nsl": "results/revision_20261115/nsl_matched/runs.csv",
        "overlap": "results/revision_20261115/nsl_no_feature_overlap/runs.csv",
        "target": "results/cic_lodo_target_resolution.csv",
        "external": "results/revision_20261115/ciciot2023_published/summary.csv"}, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
