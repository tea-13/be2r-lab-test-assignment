#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
output="$root/data/datasets/hovsg-hm3d-example"
mkdir -p "$output"
exec docker run --rm --gpus all --network none --user "$(id -u):$(id -g)" \
  -e NVIDIA_DRIVER_CAPABILITIES=all -e MPLCONFIGDIR=/tmp/matplotlib \
  -e MAGNUM_LOG=quiet -e HABITAT_SIM_LOG=quiet \
  -v /usr/share/glvnd/egl_vendor.d/10_nvidia.json:/usr/share/glvnd/egl_vendor.d/10_nvidia.json:ro \
  -v "$root/data/datasets/onemap-hm3d-example/versioned_data/hm3d-0.2/hm3d:/datasets:ro" \
  -v "$root/third_party/HOV-SG:/hovsg:ro" \
  -v "$output:/output" \
  -v "$root/scripts/hovsg-render-hm3d.py:/tmp/render.py:ro" \
  "${ONEMAP_IMAGE:-be2r-onemap-env:897abb4}" python3 /tmp/render.py
