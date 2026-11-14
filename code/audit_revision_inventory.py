"""Record a non-executing repository inventory and current evidence hashes."""
import ast
import hashlib
import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only",
                                     "33f16a6cd72506f5c9fe816af36f9f6908331ad4"], cwd=ROOT, text=True).splitlines()
    records = []
    syntax_errors = []
    # Include newly added Python sources as well as the original tracked tree.
    python_files = subprocess.check_output(["git", "ls-files", "--cached", "--others",
                                            "--exclude-standard", "--", "*.py"], cwd=ROOT, text=True).splitlines()
    python_paths = sorted({ROOT / path for path in python_files})
    for path in python_paths:
        if ".git" in path.parts:
            continue
        record = {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            record.update(functions=sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)),
                          classes=sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)),
                          imports=sorted({n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}))
        except SyntaxError as exc:
            record["syntax_error"] = str(exc)
            syntax_errors.append(record["path"])
        records.append(record)
    out = ROOT / "review/revision_20261115"
    out.mkdir(parents=True, exist_ok=True)
    (out / "source_inventory.json").write_text(json.dumps({
        "original_commit": "33f16a6cd72506f5c9fe816af36f9f6908331ad4",
        "original_tracked_file_count": len(files), "python_sources": records,
        "syntax_errors": syntax_errors,
        "scope": "Complete path and Python syntax inventory; semantic inspection focused on metrics, oracle, reproduction, new refit and manuscript evidence. Not an execution of every historical script.",
        "python": platform.python_version(), "platform": platform.platform()}, indent=2), encoding="utf8")
    paths = sorted(p for p in (ROOT / "results/revision_20261115").rglob("*") if p.is_file())
    (out / "result_hashes.json").write_text(json.dumps({p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, indent=2), encoding="utf8")
    assert not syntax_errors, syntax_errors
    print(f"Parsed {len(records)} Python sources; original tracked inventory {len(files)} files")


if __name__ == "__main__":
    main()
