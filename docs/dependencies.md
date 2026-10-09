# Зависимости и выбор окружений

Первичный аудит: 2026-10-08. Таблицы хоста и исходных решений ниже описывают состояние **до установки**. Последующие фактические установки и ограничения: [status](status.md), [DualMap](methods/dualmap.md), [OneMap](methods/onemap.md), [VLFM](methods/vlfm.md), [HOV-SG](methods/hovsg.md). Свободное место и версии плавающих зависимостей меняются; исходные рекомендации не заменяют результаты запусков.

## Хост

| Проверка | Результат |
|---|---|
| ОС | Ubuntu 24.04.3 LTS, x86_64, kernel 7.0.0-28-generic, не WSL |
| CPU / RAM | Ryzen 7 7700, 8 ядер / 16 потоков; 30 GiB RAM, ~22 GiB доступно; swap 8 GiB |
| Диск workspace | 268 GiB свободно из 915 GiB; `/tmp` на том же разделе |
| GPU | GeForce RTX 5060 Ti, 16311 MiB VRAM, ~15104 MiB свободно при аудите |
| Драйвер | NVIDIA open kernel module 580.178.04; `nvidia-smi` сообщает CUDA 13.0 |
| Toolkit | `/usr/bin/nvcc` 12.0.140 — отдельная версия, не CUDA 13.0 |
| Docker | 28.5.1, Compose 2.40.1; daemon доступен вне песочницы |
| GPU в Docker | `--gpus all` + `nvidia-smi` успешно на уже локальном CUDA 12.2 образе; вычисления CUDA/EGL не проверены |
| Python / менеджеры | Системный Python 3.12.3; uv 0.9.17; Conda нет в PATH и стандартных проверенных каталогах |
| Сборка / GUI | gcc, cmake, ninja доступны; tmux нет в PATH; X11, DISPLAY=:1; Open3D/Rerun rendering не проверен |

Сбой `nvidia-smi` и отказ Docker socket внутри песочницы не были неисправностью хоста: повтор вне неё успешен. Список Docker runtimes содержит runc без отдельного `nvidia`, но реальный GPU passthrough работает.

RTX 5060 Ti — Blackwell, compute capability 12.0 ([NVIDIA](https://developer.nvidia.com/cuda/gpus)). Поддержка Blackwell появилась в готовых PyTorch 2.7 wheels CUDA 12.8 ([релиз](https://pytorch.org/blog/pytorch-2-7/)). Кандидат для новых окружений — согласованная пара torch 2.7.1 / torchvision 0.22.1 cu128; это ещё не проверенная конфигурация методов. Старый torch/cu113 нельзя считать подходящим только из-за нового драйвера. Для сборки CUDA extensions под sm_120 системный nvcc 12.0 не подходит; toolkit при необходимости размещать в изолированном окружении/контейнере, без изменения системы.

## Зафиксированные исходники

SHA записаны в gitlinks индекса родительского репозитория; commit родительского репозитория не создавался.

| Submodule | SHA |
|---|---|
| DualMap | `157235ec49e6a1f439babbc571c4c02ad1f06aa9` |
| DualMap/3rdparty/mobileclip | `1140b8d197e4ed7d56b3a92216ded98bb1c2ac87` |
| OneMap | `897abb4ded745de2c23fe82a606e1ac0d5157089` |
| vlfm | `584ed56008754fde7997d904983607def8328322` |
| HOV-SG | `d6e65a53c8be6faec3f01f00d1644d967f89e605` |

Единственный объявленный вложенный submodule — MobileCLIP. `make submodules` задаёт ему локальный HTTPS URL вместо upstream SSH. YOLOv7, GroundingDINO, Habitat и pip git-зависимости не объявлены submodules этих проектов; их установка отложена, версии дополнительных checkout нужно фиксировать при установке. Upstream не изменён.

## Решения

| Метод | Выбор | Причина и ограничения |
|---|---|---|
| DualMap (P0) | Отдельный Conda, Python 3.10, штатный environment.yml | FAISS CPU 1.9.0 + MKL уже описаны автором; переход на uv потребовал бы перевода Conda-зависимостей. Установить Conda позже локально. Выбрать Blackwell wheels для незакреплённого torch. ROS не нужен для offline query / Dataset Mode. |
| OneMap (P0) | Авторский Dockerfile, Ubuntu 22.04 / CUDA 12.8.1 cuDNN devel / Python 3.10 | GPU passthrough подтверждён, автор адаптировал образ к RTX 50xx. Изолирует Habitat/C++/EGL от Ubuntu 24.04. Сборка Habitat длительная, но локальная установка требует тех же компиляторов и библиотек. Не собирать в Этапе 1. |
| VLFM (P1) | Штатный Conda Python 3.9 как исходный рецепт; GPU-запуск BLOCKED | torch 1.12.1+cu113 / torchvision 0.13.1 жёстко закреплены в README и pyproject; подходящего штатного GPU-окружения для RTX 5060 Ti нет. Docker этого не исправит. Нужен отдельный согласованный порт стека либо хост с поддерживаемой старым torch GPU. |
| HOV-SG (P1) | Отдельный Conda Python 3.9, основа environment.yaml | FAISS/Habitat имеют штатный Conda-путь; меньше изменений, чем uv. Torch не закреплён: нужен Blackwell wheel и проверка FAISS. Полный HM3DSem GT не подходит RAM хоста; начинать с Replica segmentation. |

uv доступен, но не выбран: не устраняет зависимости FAISS/Habitat и системную сборку; готовый авторский путь здесь предпочтительнее. Гарантировать рабочую установку без установки и smoke test невозможно.

## Источники, режимы, минимальные сценарии

Ниже — исходный обзор upstream-команд Этапа 1; фактические проверенные процедуры находятся в обзорах методов. Выполнять из каталога соответствующего submodule только после установки и подготовки [данных](datasets.md). Не добавлены как рабочие make-цели.

### DualMap

Источники: [README](../third_party/DualMap/README.md), [environment.yml](../third_party/DualMap/environment.yml), [offline guide](../third_party/DualMap/resources/doc/app_offline_query.md), [dataset guide](../third_party/DualMap/resources/doc/app_runner_dataset.md), [query implementation](../third_party/DualMap/applications/offline_local_map_query.py).

Версии: Python 3.10; faiss-cpu 1.9.0; numpy<2; ultralytics 8.3.103; supervision 0.25.1; rerun-sdk 0.22.1; record3d 1.4.1; torch/open_clip не закреплены. MobileCLIP v1 устанавливается автором через `pip install -e . --no-deps` в его каталоге. Полный Conda YAML включает необязательные iPhone-пакеты; их Linux-совместимость ещё проверить.

Первый сценарий: готовая Replica room_0 карта, MobileCLIP-S2, Open3D GUI, `python -m applications.offline_local_map_query`. Вход — `.pkl`, `layout.pcd`, `viewpoint.json`, согласованные class names/colors; выход — визуальный поиск по тексту. Путь `map_dir` задавать Hydra override во внешней команде, не редактировать upstream. Проверить class list и `_id_colors.json`: они загружаются до карты. Затем `python -m applications.runner_dataset`: RGB-D + intrinsics + готовые poses → карта объектов, PCD, CSV времени. Для каждого запуска отдельный output_path: runner может очищать каталог вывода. ROS/Record3D/online navigation доступны автором, вне минимального сценария. Лицензия кода Apache-2.0; MobileCLIP и модели имеют отдельные условия.

### OneMap

Источники: [README](../third_party/OneMap/README.md), [Dockerfile](../third_party/OneMap/Dockerfile), [requirements](../third_party/OneMap/requirements.txt), [demo](../third_party/OneMap/habitat_test.py).

Habitat-sim v0.2.4 собирается из source; habitat-lab/baselines 0.2.420230405; ultralytics 8.2.73; protobuf 3.20.1; spock-config 3.1.0; torch, numpy, rerun и ряд Git dependencies плавающие. Нужны planning_cpp, YOLOv7, SED/OpenCLIP, MobileSAM, detectron2, LAVIS. Команда `pip ... timm>=1.0.7` в Dockerfile не заключает спецификатор в кавычки: shell трактует `>` как redirect; требование нижней версии так не закрепляется. Также проверить совместимость старого LAVIS с новым torch/timm.

План: `HM3D=LOCAL`, read-only mount `versioned_data`, внешний Compose env-file. Даже LOCAL скачивает веса и navigation episodes при build; сначала уточнить объём и согласовать большие загрузки. MINI поддержан Dockerfile, но наличие нужной демо-сцены в minival не подтверждено. `habitat_test.py` жёстко задаёт `val/00853-5cdEh9F2hJL/5cdEh9F2hJL.basis.glb` и `hm3d_annotated_basis.scene_dataset_config.json`, использует semantics. Поэтому одного произвольного HM3D mesh недостаточно.

Демо: `python3 habitat_test.py --config config/mon/base_conf_sim.yaml`, Rerun viewer на хосте. Вход — simulator RGB-D/pose, цели; выход — карта и траектория в Rerun. Single/multi-object evaluation (`eval_habitat.py`, `eval_habitat_multi.py`) сохраняет results/results_multi; полный benchmark вне разрешения. Для paper single-object автор рекомендует отдельную ветку eval/s_eval, текущий SHA не равнозначен ей. Экспериментальный CuOneMap не устанавливать для исходного сценария. Код MIT.

### VLFM

Источники: [README](../third_party/vlfm/README.md), [pyproject](../third_party/vlfm/pyproject.toml), [servers](../third_party/vlfm/scripts/launch_vlm_servers.sh).

Дополнительно: transformers 4.26.0, timm 0.4.12, numpy 1.26.4, OpenCV 4.5.5.64, LAVIS 1.0.2, GroundingDINO `eeba084341aaa454ce13cb32fa7fd9282fc73a67`; Habitat как OneMap. Четыре VLM-сервера (GroundingDINO, BLIP2, SAM, YOLOv7) требуют tmux/Flask и совместного бюджета VRAM, пиковая память не измерена. README предупреждает об отсутствии активной поддержки.

После устранения GPU-блокера: `bash scripts/launch_vlm_servers.sh`, затем `python -m vlfm.run` — авторская evaluation, не короткий smoke test. Для минимума сначала выбрать ограничение эпизодов в конфиге. Вход — HM3D v0.2 + ObjectNav v1 + веса; выход — navigation evaluation/логи. Режим Spot не нужен. Код MIT.

### HOV-SG

Источники: [README](../third_party/HOV-SG/README.md), [environment](../third_party/HOV-SG/environment.yaml), [config](../third_party/HOV-SG/config/semantic_segmentation.yaml).

Python 3.9; faiss-gpu (версия не закреплена); Open3D 0.18.0; scipy 1.13.1; matplotlib 3.7.3; openai 1.3.7; OpenCV headless 4.8.1.78 одновременно с незакреплённым opencv-python. Нужно согласовать NumPy/ABI и torch в отдельном окружении. Использование FAISS в graph_utils.py — CPU IndexFlatL2; возможная замена пакета на faiss-cpu требует проверки, сейчас не выполнена.

Первый сценарий: `python application/semantic_segmentation.py main.dataset=replica main.dataset_path=Replica/office0 main.save_path=data/sem_seg/office0`, затем `python application/eval/evaluate_sem_seg.py main.dataset=replica main.scene_name=office0 main.feature_map_path=data/sem_seg/office0`. Пути и checkpoints задавать внешними Hydra overrides. RGB-D/poses → feature point cloud → semantic metrics; GT Replica нужен отдельно. SAM ViT-H + CLIP ViT-H велики, пригодность 16 GB VRAM не проверена. HM3DSem graphs/queries доступны отдельно; GT construction рекомендует 128 GB RAM. README-команда `data/habitat/gen_hm3dsem_from_poses.py` устарела: фактический файл `hovsg/data/hm3dsem/gen_hm3dsem_walks_from_poses.py`. Языковые graph queries требуют API, Replica segmentation — нет. LICENSE — MIT, но README дополнительно просит связаться с авторами для коммерческого применения; это расхождение сохранено как ограничение.

## Фактическое окружение Этапа 2

DualMap установлен отдельно в `.local/envs/dualmap` (Miniforge в `.local/miniforge`, без изменения shell startup). Python 3.10.22, torch 2.9.0+cu128 / torchvision 0.24.0+cu128: CUDA kernels на sm_120 и оба режима проверены. FAISS CPU 1.9.0, Open3D 0.19.0, MobileCLIP установлен editable с `--no-deps`. [Команды и инвентарь](../environments/README.md). Зависимости ROS/Record3D и обучения исключены; metadata MobileCLIP сохраняет конфликт со старым torchvision, не влияющий на проверенные inference-запуски.

OneMap: собран Docker на авторской основе `HM3D=LOCAL`; [внешние изменения и команды](../environments/onemap-build.md), [inventory](../environments/onemap-pip-freeze.txt). Незакреплённый torch 2.14.1 конфликтовал со Spock по setuptools; выбран проверенный torch 2.9.0+cu128. Habitat-Sim 0.2.4 собран, GPU render и demo проверены. EGL требует read-only host vendor JSON; HTTP вместо HF Xet устранил остановку загрузки. Эти настройки не меняют код метода.

## Фактические окружения Этапа 3

- **VLFM:** создан Conda Python 3.9.23, torch 1.12.1+cu113, torchvision 0.13.1+cu113, NumPy 1.26.4. CUDA kernel завершился `no kernel image is available` на sm_120; установку остального стека остановили. Это подтверждённый GPU-блокер, не полный установленный VLFM.
- **HOV-SG:** официальный environment.yaml + editable package, Python 3.9.25, torch 2.8/cu128, torchvision 0.23, NumPy 1.26.4, FAISS-GPU 1.11.0, Open3D 0.18.0; без правки YAML, pip check чист. CPU FAISS IndexFlatL2 и CUDA проверены; Replica extraction на трёх кадрах exit 0. Habitat-Sim не нужен этому режиму и не устанавливался.
- [Команды установки и ограничения namespace OpenCV](../environments/stage3.md), [точные результаты](status.md). Никакие системные CUDA/драйверы и исходные алгоритмы не изменялись.
