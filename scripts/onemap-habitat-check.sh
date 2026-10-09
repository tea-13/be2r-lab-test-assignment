#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
exec docker run --rm --gpus all --network none --user "$(id -u):$(id -g)" \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -v /usr/share/glvnd/egl_vendor.d/10_nvidia.json:/usr/share/glvnd/egl_vendor.d/10_nvidia.json:ro \
  -v "$root/data/datasets/onemap-hm3d-example/versioned_data/hm3d-0.2/hm3d:/datasets:ro" \
  -v "$root/results/onemap/stage2:/results" \
  -v "$root/scripts/onemap-habitat-check.py:/tmp/smoke.py:ro" \
  "${ONEMAP_IMAGE:-be2r-onemap-env:897abb4}" python3 /tmp/smoke.py
