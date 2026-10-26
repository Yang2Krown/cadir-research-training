#!/usr/bin/env bash
set -euo pipefail
source /workspace/cadir-env/activate.sh
exec Rscript --vanilla "$@"
