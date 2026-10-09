#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
run_dir="$root/results/onemap/objectnav-$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$run_dir/raw/trajectories" "$run_dir/raw/similarities" "$run_dir/raw/state"
touch "$root/data/cache/onemap/traced_model.pt"
echo "Results: $run_dir"
exec docker run --rm --gpus all --network host --user "$(id -u):$(id -g)" --entrypoint timeout \
 -e NVIDIA_DRIVER_CAPABILITIES=all -e HF_HOME=/cache/huggingface -e HF_HUB_DISABLE_XET=1 \
 -e MODEL_CACHE_DIR=/cache/inference -e XDG_CACHE_HOME=/cache -e MPLCONFIGDIR=/cache/matplotlib \
 -e YOLO_CONFIG_DIR=/cache/ultralytics -e PYTHONUNBUFFERED=1 \
 -v /usr/share/glvnd/egl_vendor.d/10_nvidia.json:/usr/share/glvnd/egl_vendor.d/10_nvidia.json:ro \
 -v "$root/data/datasets/onemap-hm3d-example/versioned_data/hm3d-0.2/hm3d/example:/onemap/datasets/scene_datasets/hm3d_v0.2/val:ro" \
 -v "$root/data/datasets/onemap-hm3d-example/versioned_data/hm3d-0.2/hm3d/example:/onemap/datasets/scene_datasets/hm3d:ro" \
 -v "$root/configs/onemap/hm3d-example-eval.scene_dataset_config.json:/onemap/datasets/scene_datasets/hm3d/hm3d_annotated_basis.scene_dataset_config.json:ro" \
 -v "$root/configs/onemap/eval-smoke.yaml:/onemap/config/mon/eval_smoke.yaml:ro" \
 -v "$root/data/datasets/onemap-objectnav-smoke:/episodes:ro" \
 -v "$root/data/cache/onemap:/cache" \
 -v "$root/data/cache/onemap/traced_model.pt:/onemap/traced_model.pt" \
 -v "$run_dir/raw:/onemap/results" \
 be2r-onemap:897abb4 --signal=INT --kill-after=15s 600s \
 python3 eval_habitat.py --config config/mon/eval_smoke.yaml
