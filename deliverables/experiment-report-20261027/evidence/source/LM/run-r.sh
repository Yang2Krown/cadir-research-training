#!/usr/bin/env bash
set -euo pipefail
# Authorized by continuation-task.md: reuse the verified preserved Conda runtime.
source /workspace/cadir-env/activate.sh
exec Rscript --vanilla "$@"
