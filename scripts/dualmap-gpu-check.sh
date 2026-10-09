#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.local/envs/dualmap/bin/python - <<'PY'
import json
import torch, torchvision, faiss
x = torch.randn(512, 512, device="cuda")
y = x @ x.T
torch.cuda.synchronize()
assert bool(torch.isfinite(y).all())
print(json.dumps({"torch": torch.__version__, "torchvision": torchvision.__version__,
                 "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
                 "capability": torch.cuda.get_device_capability(0),
                 "finite_matmul": True, "faiss": faiss.__version__}, indent=2))
PY
