#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
export HF_HOME="$root/data/cache/huggingface" XDG_CACHE_HOME="$root/data/cache"
export PYTHONUNBUFFERED=1 MPLCONFIGDIR="$root/data/cache/matplotlib"
map_dir=${DUALMAP_MAP_DIR:-$root/data/datasets/dualmap-prebuilt/map}
weights="$root/data/weights/dualmap/mobileclip_s2.bin"
[[ -d "$map_dir" && -f "$weights" ]] || { echo 'Missing map/checkpoint; see docs/methods/dualmap.md' >&2; exit 1; }
run_dir="$root/results/dualmap/query-$(date +%Y%m%d-%H%M%S)-$$/raw"
cd "$root/third_party/DualMap"
exec "$root/.local/envs/dualmap/bin/python" -m applications.offline_local_map_query \
  "map_dir=$map_dir" "clip.pretrained=$weights" \
  "output_path=$root/configs/dualmap/metadata" yolo.use_given_classes=false \
  "hydra.run.dir=$run_dir" "$@"
