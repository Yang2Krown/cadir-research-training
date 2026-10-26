#!/usr/bin/env bash
set -euo pipefail
# Coordinator may relay this exact script; no network, downloads or installations.
root=/workspace/hsc-fair-experiment
output=${1:?Usage: container.sh ABSOLUTE_OUTPUT_DIRECTORY COMMAND...}; shift
case "$output" in
 /workspace/hsc-fair-experiment/evidence/*|/workspace/hsc-fair-experiment/cases/nestorowa_hsc/fair-experiment/evidence/*|/workspace/hsc-fair-experiment-data-20261026/*) ;;
 *) echo "Refusing non-experiment output path" >&2; exit 2;;
esac
mkdir -p "$output"
image=sha256:baf71525f92cb9813846199dce68c6190c23d4774b025a7baec85e9688b642c7
exec env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
 docker --host=unix:///var/run/docker.sock run --rm --network none --cpus 2 --memory 8g --read-only --user "$(id -u):$(id -g)" --tmpfs /tmp:rw,nosuid,size=1g \
 --mount type=bind,src=/workspace,dst=/workspace,readonly \
 --mount "type=bind,src=$output,dst=$output" \
 --mount type=bind,src=/workspace/nestorowa-metadata-preparation/reacquired-20261026,dst=/workspace/nestorowa-metadata-preparation/reacquired-20261026,readonly \
 -e R_LIBS_USER=/workspace/.cadir-r-lib/4.4 -e OPENBLAS_NUM_THREADS=2 -e OMP_NUM_THREADS=2 -e MKL_NUM_THREADS=2 -e VECLIB_MAXIMUM_THREADS=2 \
 -w "$root" "$image" "$@"
