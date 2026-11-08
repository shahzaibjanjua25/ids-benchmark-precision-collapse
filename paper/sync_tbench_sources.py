"""Keep both publisher sources on the body in main.tex."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
main = (ROOT / "main.tex").read_text(encoding="utf-8")
abstract = re.search(r"\\begin\{abstract\}\s*(.*?)\s*\\end\{abstract\}", main, re.S)
body_start = main.index("\\section{Introduction}")
body_end = main.index("\\bibliographystyle{IEEEtran}")
if not abstract:
    raise SystemExit("main.tex abstract was not found")
abstract_text = abstract.group(1).strip()
body = main[body_start:body_end].rstrip()

title = "Label Coverage Bounds Pooled Macro F1: A Reporting Diagnostic for Closed-Set IDS Benchmarks"
keywords = "Macro F1, label coverage, benchmark protocols, intrusion detection, reproducibility"
common = r"""\documentclass[namedate,webpdf,contemporary,large]{TBench-template}
\usepackage[english]{babel}
\usepackage{graphicx}
\usepackage{amsmath}
\begin{document}
\journaltitle{BenchCouncil Transactions on Benchmarks, Standards and Evaluations}
\DOI{}
\appnotes{Research Article}
\firstpage{1}
"""

def write_source(path: Path, anonymous: bool) -> None:
    if anonymous:
        author = r"""\author{Author withheld for review}
\authormark{Anonymous submission}
"""
    else:
        author = r"""\author[1,$\ast$]{Shah Zaib Sajid}
\authormark{Sajid}
\address[1]{\orgname{Independent Researcher}}
\corresp[$\ast$]{Correspondence: shahzaibjanjua25@gmail.com}
"""
    document = (
        common
        + rf"\title[Label coverage bounds]{{{title}}}" + "\n"
        + author
        + rf"\abstract{{{abstract_text}}}" + "\n"
        + rf"\keywords{{{keywords}}}" + "\n"
        + "\\maketitle\n\n"
        + body
        + "\n\\bibliographystyle{TBench}\n\\bibliography{references}\n\\end{document}\n"
    )
    path.write_text(document, encoding="utf-8")


write_source(ROOT / "TBench-Submission.tex", anonymous=False)
write_source(ROOT / "TBench-Anonymous-Submission.tex", anonymous=True)
print("Synchronized publisher sources to main.tex body")
