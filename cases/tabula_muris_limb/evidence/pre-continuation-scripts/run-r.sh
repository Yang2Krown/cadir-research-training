#!/usr/bin/env bash
set -euo pipefail
# Require the Docker runtime specified by the attached task. Do not silently
# substitute the restored legacy Conda runtime.
launcher=/workspace/.cadir-setup/run-r.sh
repo=/workspace/cadir-research-training
if [[ ! -f "$launcher" ]]; then
  echo "BLOCKED: required Docker launcher missing: $launcher" >&2
  exit 69
fi
mapped=()
for arg in "$@"; do
  case "$arg" in
    "$repo"/*) mapped+=("/repo/${arg#"$repo"/}") ;;
    *) mapped+=("$arg") ;;
  esac
done
cd "$repo"
exec bash "$launcher" Rscript --vanilla "${mapped[@]}"
