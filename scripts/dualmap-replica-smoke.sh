#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
export HF_HOME="$root/data/cache/huggingface" XDG_CACHE_HOME="$root/data/cache"
export YOLO_CONFIG_DIR="$root/data/cache/ultralytics" MPLCONFIGDIR="$root/data/cache/matplotlib" PYTHONUNBUFFERED=1
dataset=${REPLICA_ROOT:-$root/data/datasets/replica-smoke/Replica}
[[ -f "$dataset/room0/traj.txt" ]] || { echo 'Replica room0 missing; see docs/methods/dualmap.md' >&2; exit 1; }
run_dir="$root/results/dualmap/replica-$(date +%Y%m%d-%H%M%S)-$$"
cd "$root/third_party/DualMap"
exec "$root/.local/envs/dualmap/bin/python" -m applications.runner_dataset \
  "dataset_path=$dataset" "clip.pretrained=$root/data/weights/dualmap/mobileclip_s2.bin" \
  "yolo.model_path=$root/data/weights/dualmap/yolov8l-world.pt" \
  "sam.model_path=$root/data/weights/dualmap/mobile_sam.pt" \
  "fastsam.model_path=$root/data/weights/dualmap/FastSAM-s.pt" \
  "output_path=$run_dir/raw" "hydra.run.dir=$run_dir/raw/hydra" \
  end=30 stride=1 use_rerun=false use_parallel=false "$@"
