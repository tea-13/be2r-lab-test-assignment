#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
export MPLCONFIGDIR="$root/data/cache/hovsg/matplotlib"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
mkdir -p "$MPLCONFIGDIR"
map=${HOVSG_MAP_DIR:-}
if [[ -z "$map" && -f data/cache/hovsg/demo-map.txt ]]; then
  map=$(cat data/cache/hovsg/demo-map.txt)
fi
map=${map:-results/hovsg/replica-20261009-015744-1071525/raw/replica}
[[ -s "$map/mask_feats.pt" ]] || { echo 'Map missing: run make hovsg-build-demo first' >&2; exit 1; }
exec "$root/.local/envs/hovsg/bin/python" scripts/hovsg-demo.py --map "$map" "$@"
