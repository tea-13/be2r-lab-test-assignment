# Conda-окружения VLFM и HOV-SG

Команды выполняются из корня workspace через локальный Miniforge; системные CUDA/драйверы не меняются. Инвентари `*-pip-freeze.txt` и `*-conda-explicit.txt` описывают фактическую установку, а не обещают переносимость на другие платформы.

## VLFM — частичная установка, GPU заблокирован

В upstream нет environment.yml: использованы команды Python/torch из README и NumPy из pyproject.

```bash
.local/miniforge/bin/conda create -y -p "$PWD/.local/envs/vlfm" --override-channels -c conda-forge python=3.9 pip
.local/envs/vlfm/bin/python -m pip install 'torch==1.12.1+cu113' 'torchvision==0.13.1+cu113' -f https://download.pytorch.org/whl/torch_stable.html
.local/envs/vlfm/bin/python -m pip install numpy==1.26.4
bash scripts/vlfm-gpu-check.sh
```

Последняя команда проверена: **exit 1**, `no kernel image is available` на sm_120. Пакеты устанавливаются, но CUDA kernels не работают. Дальнейшая установка Habitat/моделей остановлена; не выдавать этот prefix за полный VLFM. [Результат](../results/vlfm/stage3/README.md).

## HOV-SG — штатный Conda рецепт

Первоначальная команда (статус последующих проверок — [HOV-SG](../docs/methods/hovsg.md)):

```bash
.local/miniforge/bin/conda env create -p "$PWD/.local/envs/hovsg" -f third_party/HOV-SG/environment.yaml
.local/envs/hovsg/bin/python -m pip install --no-deps -e third_party/HOV-SG
.local/envs/hovsg/bin/python -m pip check
```

Для Replica используется существующий RGB-D subset с poses. Habitat-Sim нужен отдельному HM3DSem data generation, поэтому не входит в минимальную установку. Checkpoints согласованы пользователем; оригинальный `environment.yaml` сохраняется без изменений.

Установка завершилась exit 0 без изменения requirements: Python 3.9.25, torch 2.8.0+cu128 / torchvision 0.23.0+cu128, NumPy 1.26.4, FAISS-GPU 1.11.0 (Conda CUDA 12.1.1), Open3D 0.18.0. Graph import, CUDA matmul и используемый HOV-SG **CPU** FAISS `IndexFlatL2` проверены; GPU-индексы FAISS не проверялись. `pip check` чист. [Вывод](../results/hovsg/stage3/import-gpu-check.txt).

Официальный YAML одновременно ставит opencv-python и headless: runtime `cv2.__version__=4.11.0`, metadata headless=4.8.1.78. Эти дистрибутивы разделяют namespace; установка воспроизводится целиком, не следует удалять один поверх другого без повторной проверки. Это ограничение рецепта, не обнаруженная ошибка smoke test. Автоматический выбор версий зафиксирован в инвентарях; SAM Git dependency разрешился в `dca509fe793f601edb92606367a655c15ac00fdf`.

Оба checkpoint скачаны следующими командами (суммарно 6.51 GB; требуется предварительное согласование большой загрузки):

```bash
mkdir -p data/weights/hovsg
curl --http1.1 -fL -C - --connect-timeout 20 --speed-time 60 --speed-limit 1024 --retry 3 https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K/resolve/main/open_clip_pytorch_model.bin -o data/weights/hovsg/laion2b_s32b_b79k.bin
curl --http1.1 -fL -C - --connect-timeout 20 --speed-time 60 --speed-limit 1024 --retry 3 https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth -o data/weights/hovsg/sam_vit_h_4b8939.pth
sha256sum -c results/hovsg/stage3/weights.sha256
```

CLIP `main` разрешился в revision `1c2b8495b28150b8a4922ee1c8edee224c284c0c`; SHA256 совпал с `x-linked-etag` источника. Размеры обоих файлов совпали с HTTP metadata. [Инвентарь](../results/hovsg/stage3/weights.json). Веса не добавляются в Git.
