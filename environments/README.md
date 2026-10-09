# Проверенные команды установки DualMap

Выполнялись 8–9 октября 2026 из корня workspace. Окружение хранится в `.local/` и не попадает в Git. Miniforge не добавлялся в shell startup; системный Python не менялся.

```bash
curl -fL https://github.com/conda-forge/miniforge/releases/download/26.7.2-0/Miniforge3-Linux-x86_64.sh -o data/cache/installers/Miniforge3-Linux-x86_64.sh
bash data/cache/installers/Miniforge3-Linux-x86_64.sh -b -p "$PWD/.local/miniforge"
.local/miniforge/bin/conda create -y -p "$PWD/.local/envs/dualmap" --override-channels -c conda-forge python=3.10 pip 'numpy<2' faiss-cpu=1.9.0 mkl 'blas=1.0=mkl' cmake
uv pip install --python .local/envs/dualmap/bin/python 'torch==2.9.0+cu128' 'torchvision==0.24.0+cu128' --index-url https://download.pytorch.org/whl/cu128
uv pip install --python .local/envs/dualmap/bin/python -r environments/dualmap-requirements.txt
uv pip install --python .local/envs/dualmap/bin/python --no-deps -e third_party/DualMap/3rdparty/mobileclip
uv pip install --python .local/envs/dualmap/bin/python 'git+https://github.com/ultralytics/CLIP.git'
make dualmap-gpu-check
```

Установщик требует существующего `data/cache/installers/`; после прерывания установки использовался его `-u`. В песочнице нужны разрешения на сеть и служебный `~/.conda`. CLIP разрешился в SHA `7ffa84b3bfa40c42ecc1c77147a855e69cb2dd40`; закреплять этот SHA при повторной установке.

`dualmap-conda-explicit.txt` фиксирует Conda-пакеты; `dualmap-pip-freeze.txt` — инвентарь фактической среды, **не единый автоматически разрешимый lockfile**: MobileCLIP metadata требует старый torchvision, обходится штатным `--no-deps`. Пакеты clip-benchmark/datasets для обучения не установлены. Smoke tests inference выполнены с современной CUDA 12.8 парой torch/vision.

Данные/checkpoints и команды запуска описаны в [DualMap](../docs/methods/dualmap.md); установка пакетов не скачивает Replica автоматически. OneMap устанавливается отдельно в Docker, его статус — в [методе](../docs/methods/onemap.md).
