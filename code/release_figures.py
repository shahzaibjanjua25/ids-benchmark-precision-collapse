from pathlib import Path
import hashlib, json, re, shutil
from datetime import datetime, timezone
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def render(release):
    r = release / "results"
    figs = release / "manuscript" / "figures"
    data = r / "figures_data"
    for folder in (figs, data, release / "submission"):
        folder.mkdir(parents=True, exist_ok=True)
    a = pd.read_csv(r / "RESULTS_PARSED.csv")
    keys = ["dataset", "variant", "protocol", "model", "arm"]
    summary = a.groupby(keys)["macro_f1"].agg(["count", "mean", "std"]).reset_index()
    summary.to_csv(r / "macro_f1_summary.csv", index=False)
    series = [
        ("cic_protocols", summary.query("dataset == 'cic' and protocol != 'time'"), ["protocol", "arm"], "mean", "Macro F1"),
        ("unsw_official", summary.query("dataset == 'unsw' and protocol == 'official' and model == 'rf'"), ["variant", "arm"], "mean", "Mean macro F1 across seeds"),
        ("class_duplicates", pd.read_csv(r / "data_audit.csv").query("dataset == 'unsw'"), ["cls"], "dup_fraction", "Exact duplicate fraction"),
    ]
    for name, values, columns, metric, axis in series:
        values.to_csv(data / (name + ".csv"), index=False)
        fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
        labels = values[columns].astype(str).agg(" / ".join, axis=1)
        ax.barh(labels, values[metric], color="#24678a")
        ax.invert_yaxis()
        ax.set(xlabel=axis, xlim=(0, 1))
        ax.grid(axis="x", alpha=.25)
        ax.set_axisbelow(True)
        fig.savefig(figs / (name + ".png"), dpi=300)
        fig.savefig(figs / (name + ".pdf"))
        if name == "cic_protocols":
            ax.set_title("CICIDS2017 random forest evaluation by protocol")
            fig.savefig(release / "submission" / "graphical_abstract.png", dpi=300)
        plt.close(fig)

def collect(root, release):
    log = (root / "command.txt").read_bytes()
    (release / "results" / "command_original.txt").write_bytes(log)
    raw = log.decode("utf-8-sig", errors="replace")
    blocks = re.split(r" {12,}|\r?\n", raw)
    (release / "results" / "command_readable.txt").write_text("\n".join(x.strip() for x in blocks if x.strip()), encoding="utf-8")
    records = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if rel.parts[0].startswith("PUBLISHABLE_PAPER") or rel.parts[0] == ".git" or not path.is_file():
            continue
        with path.open("rb") as stream:
            sha1 = hashlib.file_digest(stream, "sha1").hexdigest()
        s = path.stat()
        ext = path.suffix.lower()
        role = "data" if rel.parts[0] == "CICIDS2017" or path.name.startswith("UNSW_NB15") else {".py":"source", ".pyc":"scratch", ".png":"plot", ".txt":"log", ".csv":"result", ".json":"result", ".docx":"other", ".rar":"other"}.get(ext, "other")
        records.append(dict(path=rel.as_posix(), size=s.st_size, ext=ext, last_modified=datetime.fromtimestamp(s.st_mtime, timezone.utc).isoformat(), sha1=sha1, guessed_role=role))
    (release / "docs" / "inventory.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    r = release / "results"
    for name in ["aggregate.csv","data_audit.csv","per_class_long.csv","per_class_summary.csv","threshold.csv","fp_sources.csv","report.txt","done.txt"]:
        shutil.copy2(root / "study_out" / name, r / name)
    shutil.copy2(r / "aggregate.csv", r / "RESULTS_PARSED.csv")
    for source in ["outputs_cic", "outputs_unsw", "out_cv", "out_dedup", "out_official"]:
        shutil.copytree(root / source, r / source)
    for name in ["ids_full_study.py", "cic_ids_pipeline.py", "unsw_nb15_pipeline.py", "unsw_ablation.py"]:
        shutil.copy2(root / name, release / "code" / "clean_repo" / name)
    render(release)
    summary = pd.read_csv(r / "macro_f1_summary.csv")
    lines = ["# Archived experimental results", "", "The structured CSV reproduces study_out/aggregate.csv. Each row represents one saved run. The original console transcript is preserved separately, with a line-split reading copy. The standalone pipeline outputs and ablation exports are also included. Console-only values have not been individually reconciled.", "", "| Dataset | Variant | Protocol | Model | Arm | Runs | Mean macro F1 | Seed SD |", "|---|---|---|---|---|---:|---:|---:|"]
    for row in summary.itertuples(index=False):
        sd = f"{row.std:.5f}" if pd.notna(row.std) else "Unavailable"
        lines.append(f"| {row.dataset} | {row.variant} | {row.protocol} | {row.model} | {row.arm} | {row.count} | {row.mean:.5f} | {sd} |")
    (r / "RESULTS_PARSED.md").write_text("\n".join(lines)+"\n", encoding="utf-8")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", type=Path)
    args = parser.parse_args()
    release = Path(__file__).resolve().parents[1]
    if args.collect:
        collect(args.collect, release)
    else:
        render(release)

