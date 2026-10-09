# VLFM — выполненная установка и подтверждённый блокер

**Итог:** PARTIAL / GPU BLOCKED, не работающая навигационная система. SHA `584ed56008754fde7997d904983607def8328322`. [Общая подготовка](README.md), [технический обзор](../methods/vlfm.md). У upstream нет environment.yml: использованы Conda/PyTorch команды README и NumPy pin из pyproject.

## 1. Что установлено и почему

Отдельный `.local/envs/vlfm` нужен для проверки **штатного** стека. Проверка старого CUDA kernel выполнена до установки Habitat, LAVIS, GroundingDINO и многогигабайтных моделей, чтобы объективный блокер не задерживал HOV-SG.

```bash
.local/miniforge/bin/conda create --yes \
  --prefix "$PWD/.local/envs/vlfm" \
  --override-channels --channel conda-forge \
  python=3.9 pip
.local/envs/vlfm/bin/python -m pip install \
  'torch==1.12.1+cu113' 'torchvision==0.13.1+cu113' \
  --find-links https://download.pytorch.org/whl/torch_stable.html
.local/envs/vlfm/bin/python -m pip install numpy==1.26.4
bash scripts/vlfm-gpu-check.sh
```

Conda создала Python 3.9.23. Установились torch 1.12.1+cu113 / torchvision 0.13.1+cu113. pip сначала выбрал NumPy 2.0.2; затем явно установлен **1.26.4 из авторского pyproject**, а не произвольная версия. [Conda inventory](../../environments/vlfm-conda-explicit.txt), [pip inventory](../../environments/vlfm-pip-freeze.txt).

## 2. Проверка GPU: команда запуска

Все параметры запуска заданы в [scripts/vlfm-gpu-check.sh](../../scripts/vlfm-gpu-check.sh).

То же через Makefile:

```bash
make vlfm-gpu-check
.local/envs/vlfm/bin/python -m pip check
```

CUDA check — script exit **1**, make exit **2**; это ожидаемый диагностический отказ. `pip check` — чист, но только для частично установленной основы. [JSON](../../results/vlfm/stage3/gpu-check.json), [stderr](../../results/vlfm/stage3/gpu-check.stderr.txt), [pip check](../../results/vlfm/stage3/pip-check.txt).

## 3. Точная ошибка и принятое решение

```text
torch.cuda.is_available(): true
GPU capability: sm_120
compiled_arches: sm_37 sm_50 sm_60 sm_70 sm_75 sm_80 sm_86
CUDA error: no kernel image is available for execution on the device
```

Новый драйвер обнаруживает GPU, но не добавляет отсутствующие kernels в старый wheel. Docker с тем же torch не устраняет причину. CPU import/available=true не были засчитаны как работающий VLFM.

**Решение в этой работе:** зафиксировать ошибку и остановить дальнейшую установку VLFM; продолжить HOV-SG. Замена на современный torch затрагивает pinned pyproject, GroundingDINO extensions, Habitat/LAVIS и не выполнялась. Реальные варианты продолжения: поддерживаемый cu113 GPU либо отдельная миграция стека с повторной проверкой; ни один не объявлен уже сделанным.

## 4. Что не делалось

- `pip install -e .[habitat]`, Habitat/LAVIS/GroundingDINO и YOLOv7 checkout не устанавливались после блокера.
- VLM servers/tmux не запускались; tmux отсутствует в PATH.
- BLIP2/DINO/SAM/YOLO weights специально для VLFM не загружались. PointNav checkpoint уже находится в upstream Git.
- `python -m vlfm.run` не выполнялся; SR/SPL отсутствуют. Default `test_episode_count=-1` запустил бы все эпизоды — такой запуск не выполнялся.
- Имеющаяся HM3D example/v2 выборка OneMap не была автоматически выдана за совместимые VLFM v1 episodes.

Локальные журналы: `results/vlfm/stage3/logs/{conda-create,torch-install,numpy-install}.log`, `make-gpu-check.txt`. Веса/полная модельная среда не нужны для повторения ошибки. [Сводный результат](../../results/vlfm/stage3/README.md).
