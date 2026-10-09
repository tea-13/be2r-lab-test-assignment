#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.local/envs/vlfm/bin/python - <<'PY'
import json
import sys
import torch
import torchvision

result = {"torch": torch.__version__, "torchvision": torchvision.__version__,
          "cuda": torch.version.cuda, "available": torch.cuda.is_available()}
try:
    result.update(gpu=torch.cuda.get_device_name(0),
                  capability=torch.cuda.get_device_capability(0),
                  compiled_arches=torch.cuda.get_arch_list())
    x = torch.ones(32, device="cuda")
    result["sum"] = float((x + 1).sum().item())
    torch.cuda.synchronize()
    assert result["sum"] == 64.0
    result["kernel_ok"] = True
except Exception as exc:
    result.update(kernel_ok=False, error=str(exc))
print(json.dumps(result, indent=2))
sys.exit(0 if result["kernel_ok"] else 1)
PY
