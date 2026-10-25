#!/usr/bin/env bash
set -euo pipefail
review_base="$(cd "$(dirname "$0")/.." && pwd)"
case_base="$(cd "$review_base/../.." && pwd)"
python "$review_base/scripts/cluster_review.py" > "$review_base/logs/cluster_review.log" 2>&1
bash "$case_base/scripts/run-r.sh" "$review_base/scripts/annotation_review.R" "$review_base" > "$review_base/logs/annotation_review.log" 2>&1
python "$review_base/scripts/build_report.py"
python "$review_base/scripts/verify_acceptance.py"
# Source checks are separate and bounded; this offline review does not repeat HTTP requests.
