# VLFM: подтверждённый блокер штатного GPU-окружения

2026-10-09, RTX 5060 Ti sm_120. Conda Python 3.9, torch 1.12.1+cu113, torchvision 0.13.1+cu113, numpy 1.26.4 установлены. Это **частичная установка**, не работающий VLFM.

`bash scripts/vlfm-gpu-check.sh` завершился **exit 1**: `CUDA error: no kernel image is available for execution on the device`. `torch.cuda.is_available()` при этом true; wheel содержит sm_37…sm_86. [JSON](gpu-check.json), [предупреждение torch](gpu-check.stderr.txt), [pip check](pip-check.txt).

Habitat, GroundingDINO/LAVIS и модельные серверы не устанавливались после подтверждения блокера. Demo/evaluation не запускались; SR/SPL отсутствуют. Чистый `pip check` относится только к установленной основе.

Точная процедура установки — [environments](../../../environments/stage3.md), описание метода — [VLFM](../../../docs/methods/vlfm.md). Исправление требует отдельной миграции pinned стека на современный CUDA/PyTorch либо другого GPU, поддерживаемого cu113. Исходный pyproject и алгоритмы не изменены.
