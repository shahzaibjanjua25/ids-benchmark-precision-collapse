#!/usr/bin/env bash
set -euo pipefail
code_dir="$(cd "$(dirname "$0")" && pwd)"
data_dir="$(cd "${1:?Provide the project data directory}" && pwd)"
shift
out="$(mktemp -d "$code_dir/../results/reproduction.XXXXXX")"
python "$code_dir/clean_repo/ids_full_study.py" --unsw-dir "$data_dir" --cic-dir "$data_dir/CICIDS2017" --out "$out" "$@"
python "$code_dir/release_figures.py"

