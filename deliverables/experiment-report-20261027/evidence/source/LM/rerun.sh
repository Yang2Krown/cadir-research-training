#!/usr/bin/env bash
set -euo pipefail
case_base="$(cd "$(dirname "$0")/.." && pwd)"
output_root="$case_base/runs"
config="$case_base/config/case.json"
audit_only=false
remaining=("$@")
while (($#)); do
  case "$1" in
    --output-root) output_root="$2"; shift 2 ;;
    --output-root=*) output_root="${1#*=}"; shift ;;
    --config) config="$2"; shift 2 ;;
    --config=*) config="${1#*=}"; shift ;;
    --audit-only) audit_only=true; shift ;;
    *) shift ;;
  esac
done
python "$case_base/scripts/check_environment.py" --output-root "$output_root" --config "$config"
python "$case_base/scripts/run_case.py" "${remaining[@]}" --output-root "$output_root"
if "$audit_only"; then exit 0; fi
case_run_dir="$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' "$output_root/latest-case.json")"
bash "$case_base/scripts/run-r.sh" "$case_base/scripts/verify_results.R" "$case_run_dir" > "$case_run_dir/verification.log" 2>&1
python "$case_base/scripts/collect_outputs.py" --output-root "$output_root"
