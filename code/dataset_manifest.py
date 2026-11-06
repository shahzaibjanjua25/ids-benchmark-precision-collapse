"""Report the data-file identities used by the benchmark loaders."""
import argparse
import hashlib
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("data", type=Path)
args = parser.parse_args()
root = args.data.resolve()
files = list((root / "CICIDS2017").rglob("*.csv"))
files.extend(root.glob("UNSW_NB15_*ing-set.csv"))
for path in sorted(files):
    with path.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    print(f"{checksum}  {path.relative_to(root).as_posix()}")

