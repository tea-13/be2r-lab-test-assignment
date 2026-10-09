#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
mkdir -p data/cache/onemap-demo data/cache/onemap
python3 - <<'PY'
from pathlib import Path
s=Path('third_party/OneMap/habitat_test.py').read_text()
changes={
 '/val/00853-5cdEh9F2hJL/5cdEh9F2hJL.basis.glb':'/example/00861-GLAQ4DNUx5U/GLAQ4DNUx5U.basis.glb',
 '/hm3d_annotated_basis.scene_dataset_config.json':'/example/hm3d_annotated_example_basis.scene_dataset_config.json',
}
for old,new in changes.items():
    assert s.count(old)==1, f'Unexpected upstream scene path: {old}'
    s=s.replace(old,new)
Path('data/cache/onemap-demo/habitat_test_example.py').write_text(s)
PY
exec docker run --rm --gpus all --network host --user "$(id -u):$(id -g)" --entrypoint timeout \
 -e NVIDIA_DRIVER_CAPABILITIES=all -e HF_HOME=/cache/huggingface -e HF_HUB_DISABLE_XET=1 \
 -e MODEL_CACHE_DIR=/cache/inference -e XDG_CACHE_HOME=/cache -e MPLCONFIGDIR=/cache/matplotlib \
 -e YOLO_CONFIG_DIR=/cache/ultralytics -e PYTHONUNBUFFERED=1 \
 -v /usr/share/glvnd/egl_vendor.d/10_nvidia.json:/usr/share/glvnd/egl_vendor.d/10_nvidia.json:ro \
 -v "$root/data/datasets/onemap-hm3d-example/versioned_data/hm3d-0.2/hm3d:/onemap/datasets/scene_datasets/hm3d:ro" \
 -v "$root/data/cache/onemap:/cache" \
 -v "$root/data/cache/onemap-demo/habitat_test_example.py:/onemap/habitat_test_example.py:ro" \
 be2r-onemap:897abb4 --signal=INT --kill-after=15s "${ONEMAP_DEMO_SECONDS:-0}s" \
 python3 habitat_test_example.py --config config/mon/base_conf_sim.yaml
