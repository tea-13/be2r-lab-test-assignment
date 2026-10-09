#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
dataset="$root/data/datasets/replica-nice-slam/Replica/room0"
weights="$root/data/weights/hovsg"
[[ -f "$dataset/traj.txt" ]] || { echo 'Missing full Replica room0' >&2; exit 1; }
output="$root/results/hovsg/demo-map-$(date +%Y%m%d-%H%M%S)-$$/raw"
mkdir -p "$output" "$root/data/cache/hovsg/matplotlib"
export MPLCONFIGDIR="$root/data/cache/hovsg/matplotlib"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 HYDRA_FULL_ERROR=1
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
cd "$root/third_party/HOV-SG"
"$root/.local/envs/hovsg/bin/python" application/semantic_segmentation.py \
  main.dataset=replica main.scene_id=room0 \
  "main.dataset_path=$dataset" "main.save_path=$output" \
  "models.clip.checkpoint=$weights/laion2b_s32b_b79k.bin" \
  "models.sam.checkpoint=$weights/sam_vit_h_4b8939.pth" \
  models.sam.points_per_batch=8 pipeline.skip_frames=100 \
  "hydra.run.dir=$output/hydra" hydra.job.chdir=false
test -s "$output/replica/mask_feats.pt"
test -s "$output/replica/full_pcd.ply"
printf '%s\n' "${output#"$root/"}/replica" > "$root/data/cache/hovsg/demo-map.txt"
printf 'Demo map ready: %s/replica\n' "$output"
