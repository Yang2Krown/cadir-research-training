#!/usr/bin/env bash
set -euo pipefail
case_base="$(cd "$(dirname "$0")/.." && pwd)"
python "$case_base/scripts/check_environment.py"
python "$case_base/scripts/run_case.py" "$@"
case_run_dir="$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' "$case_base/latest-case.json")"
bash "$case_base/scripts/run-r.sh" "$case_base/scripts/verify_results.R" "$case_run_dir" > "$case_run_dir/verification.log" 2>&1
python "$case_base/scripts/collect_outputs.py"
