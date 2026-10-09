#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
dataset="$root/data/datasets/hovsg-hm3d-example"
scene=00861-GLAQ4DNUx5U
test -s "$dataset/val/$scene/render-summary.json"
output="$root/results/hovsg/hm3d-graph-$(date +%Y%m%d-%H%M%S)-$$/raw"
mkdir -p "$output" "$root/data/cache/hovsg/matplotlib"
export MPLCONFIGDIR="$root/data/cache/hovsg/matplotlib"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 HYDRA_FULL_ERROR=1
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
cd "$root/third_party/HOV-SG"
"$root/.local/envs/hovsg/bin/python" application/create_graph.py \
  main.dataset=hm3dsem main.split=val "main.scene_id=$scene" \
  "main.dataset_path=$dataset" "main.save_path=$output" \
  "main.package_path=$root/third_party/HOV-SG/hovsg" \
  "models.clip.checkpoint=$root/data/weights/hovsg/laion2b_s32b_b79k.bin" \
  "models.sam.checkpoint=$root/data/weights/hovsg/sam_vit_h_4b8939.pth" \
  models.sam.points_per_batch=8 pipeline.skip_frames=1 pipeline.voxel_size=0.05 \
  "hydra.run.dir=$output/hydra" hydra.job.chdir=false
test -d "$output/hm3dsem/$scene/graph/rooms"
printf '%s\n' "${output#"$root/"}/hm3dsem/$scene/graph" > "$root/data/cache/hovsg/graph-demo.txt"
printf 'Graph ready: %s/hm3dsem/%s/graph\n' "$output" "$scene"
