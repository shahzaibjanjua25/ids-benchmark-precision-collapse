"""Run current verification with a machine-readable log.

This verifies saved predictions; raw model training remains a separate command.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--build-pdf", action="store_true", help="Requires separately held manuscript sources")
    args = parser.parse_args()
    if args.build_pdf and not (ROOT / 'paper/revision/manuscript.typ').exists():
        parser.error('PDF compilation requires the separately held manuscript source package')
    out = ROOT / "review/revision_20261115"
    out.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
    commands = [
        ["code/check_availability.py"], ["code/check_vocabulary_groups.py"],
        ["code/check_certified.py"], ["code/verify_revision_results.py"],
        ["code/audit_ciciot2023_published.py"],
        ["code/verify_rt_iot_audit.py"], ["code/audit_botiot_matrices.py"],
        ["code/verify_rt_iot_fold_varying.py"],
        ["code/verify_release_evidence.py"], ["code/verify_external_artifact_audit.py"],
        ["code/verify_cic_corrected_friday.py"], ["code/verify_cic_binary_lodo.py"],
        ["code/verify_unsw_benign_ood.py"], ["code/verify_published_score_audit.py"],
        ["code/verify_cic_archive.py", "results"], ["code/audit_revision_inventory.py"]]
    if args.build_pdf and not args.skip_pdf:
        commands.append(["code/build_revision_paper.py"])
    records = []
    for command in commands:
        start = time.perf_counter()
        proc = subprocess.run([sys.executable, "-B", *command], cwd=ROOT,
                              text=True, encoding="utf8", errors="replace", capture_output=True)
        records.append({"command": "python " + " ".join(command), "returncode": proc.returncode,
                        "seconds": time.perf_counter() - start,
                        "stdout": proc.stdout, "stderr": proc.stderr})
        (out / "verification_run.json").write_text(json.dumps(records, indent=2), encoding="utf8")
        print(f"{command[0]}: {'PASS' if proc.returncode == 0 else 'FAIL'}", flush=True)
        if proc.returncode:
            print(proc.stderr)
            raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
