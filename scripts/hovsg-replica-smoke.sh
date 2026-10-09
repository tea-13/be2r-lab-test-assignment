#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
python="$root/.local/envs/hovsg/bin/python"
dataset="$root/data/datasets/replica-smoke/Replica/room0"
weights="$root/data/weights/hovsg"
for file in "$python" "$dataset/traj.txt" "$dataset/../cam_params.json" \
  "$weights/laion2b_s32b_b79k.bin" "$weights/sam_vit_h_4b8939.pth"; do
  [[ -f "$file" ]] || { printf 'Missing: %s\n' "$file" >&2; exit 1; }
done
# This prefix contains the first 30 authentic frames; use poses 0, 10, 20.
[[ $(find "$dataset/results" -maxdepth 1 -name 'frame*.jpg' | wc -l) -eq 30 ]] || {
  echo 'Expected the prepared 30-frame Replica subset' >&2; exit 1;
}
output="$root/results/hovsg/replica-$(date +%Y%m%d-%H%M%S)-$$/raw"
mkdir -p "$output" "$root/data/cache/hovsg/matplotlib"
export MPLCONFIGDIR="$root/data/cache/hovsg/matplotlib"
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export HYDRA_FULL_ERROR=1
cd "$root/third_party/HOV-SG"
exec "$python" application/semantic_segmentation.py \
  main.dataset=replica main.scene_id=room0 \
  "main.dataset_path=$dataset" "main.save_path=$output" \
  "models.clip.checkpoint=$weights/laion2b_s32b_b79k.bin" \
  "models.sam.checkpoint=$weights/sam_vit_h_4b8939.pth" \
  models.sam.points_per_batch=8 pipeline.skip_frames=10 \
  "hydra.run.dir=$output/hydra" hydra.job.chdir=false
