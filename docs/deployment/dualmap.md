# DualMap — шаги развёртывания и журнал решений

**Итог:** Offline Query и Replica Dataset Mode проверены. SHA `157235ec49e6a1f439babbc571c4c02ad1f06aa9`; nested MobileCLIP `1140b8d197e4ed7d56b3a92216ded98bb1c2ac87`. Сначала [общая подготовка/Miniforge](README.md). [Обзор метода](../methods/dualmap.md).

## 1. Изолированное окружение

Выбран Conda для FAISS/MKL, uv использован как pip installer внутри prefix. Полный upstream YAML с ROS/iPhone extras не устанавливался: использован Dataset/Query subset. Выполненные команды:

```bash
.local/miniforge/bin/conda create --yes \
  --prefix "$PWD/.local/envs/dualmap" \
  --override-channels --channel conda-forge \
  python=3.10 pip 'numpy<2' faiss-cpu=1.9.0 mkl 'blas=1.0=mkl' cmake
uv pip install \
  --python .local/envs/dualmap/bin/python \
  'torch==2.9.0+cu128' 'torchvision==0.24.0+cu128' \
  --index-url https://download.pytorch.org/whl/cu128
uv pip install \
  --python .local/envs/dualmap/bin/python \
  -r environments/dualmap-requirements.txt
uv pip install \
  --python .local/envs/dualmap/bin/python \
  --no-deps -e third_party/DualMap/3rdparty/mobileclip
uv pip install \
  --python .local/envs/dualmap/bin/python \
  'git+https://github.com/ultralytics/CLIP.git'
make dualmap-gpu-check
```

Итог: Python 3.10.22, torch 2.9.0+cu128 / torchvision 0.24.0, NumPy 1.26.4, FAISS CPU 1.9.0, Open3D 0.19.0, OpenCLIP 2.32.0, Ultralytics 8.3.103, Rerun 0.22.1. [Полный список pip требований](../../environments/dualmap-requirements.txt), [pip inventory](../../environments/dualmap-pip-freeze.txt), [Conda inventory](../../environments/dualmap-conda-explicit.txt). Git CLIP разрешился в `7ffa84b3bfa40c42ecc1c77147a855e69cb2dd40`.

`make dualmap-gpu-check` проверил CUDA matmul/finite и FAISS import: exit 0. [JSON](../../results/dualmap/stage2/gpu-smoke.json). Полный metadata resolver MobileCLIP не считается исправленным: `--no-deps` — авторский способ, старая vision-зависимость не понижалась.

## 2. Готовая карта и веса

| Полученный файл | Источник/назначение |
|---|---|
| `data/cache/replica_room_0.zip` | Авторский Google Drive folder из [offline guide](../../third_party/DualMap/resources/doc/app_offline_query.md), файл ID `15O8pWAD4qUXLq0N9Ji0UFhxdzUJpXZTH`, 21 073 974 bytes |
| `data/datasets/dualmap-prebuilt/map/` | Распакованная карта: 41 объект, layout и viewpoint |
| `data/weights/dualmap/mobileclip_s2.bin` | Apple MobileCLIP-S2 v1 / OpenCLIP, datacompdr; не MobileCLIP v2 |
| `data/weights/dualmap/yolov8l-world.pt` | YOLO-World detector |
| `data/weights/dualmap/mobile_sam.pt` | MobileSAM |
| `data/weights/dualmap/FastSAM-s.pt` | FastSAM |
| `~/.cache/clip/ViT-B-32.pt` | Дополнительный CLIP cache, появившийся при работе detector |

Карта и checkpoints скачаны; были медленные/прерывавшиеся HTTP-передачи, продолженные через curl `-C -`. Точные исходные shell-команды загрузок DualMap в логах не сохранились, поэтому ссылки на guessed release assets здесь не выдаются за выполненные команды. Источники моделей/лицензии собраны в [datasets](../datasets.md); точная идентичность полученных файлов фиксируется [SHA256](../../results/dualmap/stage2/assets.sha256).

Восстановленный рецепт получения именно авторской карты (не повторно скачивался при написании этой инструкции):

```bash
mkdir -p data/cache data/datasets/dualmap-prebuilt data/weights/dualmap
curl --http1.1 -fL -C - \
  'https://drive.usercontent.google.com/download?id=15O8pWAD4qUXLq0N9Ji0UFhxdzUJpXZTH&export=download&confirm=t' \
  -o data/cache/replica_room_0.zip
python3 -m zipfile -e data/cache/replica_room_0.zip data/datasets/dualmap-prebuilt
sha256sum -c results/dualmap/stage2/assets.sha256
```

Последняя команда требует также все четыре checkpoint по путям таблицы. Для весов точные transfer URLs не восстановлены; это оставшийся пробел истории загрузки, а не признак отсутствия весов на текущем хосте.

## 3. Исправление class metadata для Offline Query

Готовая карта содержит Replica IDs, а текущий `gpt_indoor_general.txt` давал неверные подписи (kettle/blanket). Созданы внешние `configs/dualmap/metadata/replica_room_0/classes_info/` с именами из официального ReplicaCAD semantic lexicon и детерминированными HSV-цветами. Цвета — только визуализация, не GT. [SOURCE и SHA исходника](../../configs/dualmap/metadata/replica_room_0/classes_info/SOURCE.txt). При повторном запуске используются уже сохранённые JSON, генерировать их заново не нужно. Embeddings/объекты карты не изменялись.

## 4. Offline Query: запуск поиска

```bash
make dualmap-query
```

F в окне -> `chair` или `sofa` в терминале; Q в окне завершает процесс. Все параметры запуска заданы в [scripts/dualmap-query.sh](../../scripts/dualmap-query.sh).

Итог: 41 объект; chair score 0.592, sofa 0.612, exit 0. [Конфиг/скриншоты/результаты](../../results/dualmap/stage2/README.md). Score — similarity, не accuracy. `DUALMAP_MAP_DIR` позволяет выбрать другую совместимую готовую карту.

## 5. Replica: полный архив и короткий subset

С согласия пользователя скачан `https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip`, **12 442 855 671 bytes**. SHA256 `dc18265e213f8281444b768eed76f627bde8c3b925654934f84f78a87990a548`. Извлечена только room0: 2000 RGB-D кадров, traj.txt и cam_params. CRC проверен для извлечённых members. [Manifest](../../results/dualmap/stage2/replica-archive.json).

До завершения большой загрузки первые 30 кадров извлечены HTTP Range (28 803 269 переданных bytes) с проверкой CRC. Сохранены кадры 0…29 и исходный полный traj.txt; поэтому индекс кадра совпадает с индексом pose. [Список файлов](../../results/dualmap/stage2/replica-subset.json). Ниже более простой **восстановленный рецепт из уже полного ZIP**, без специального сетевого reader; при подготовке документации повторно не распаковывался:

```bash
curl --http1.1 -fL -C - \
  https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip \
  -o data/cache/Replica.zip
python3 - <<'PYDATA'
from pathlib import Path
from zipfile import ZipFile
with ZipFile('data/cache/Replica.zip') as archive:
    wanted = {f'{kind}{i:06d}' for kind in ('frame', 'depth') for i in range(30)}
    for name in archive.namelist():
        common = name == 'Replica/cam_params.json'
        scene = name.startswith('Replica/room0/')
        if common or scene:
            archive.extract(name, 'data/datasets/replica-nice-slam')
        if common or name == 'Replica/room0/traj.txt' or (scene and '/results/' in name and Path(name).stem in wanted):
            archive.extract(name, 'data/datasets/replica-smoke')
PYDATA
```

Original Replica semantic GT — другой набор файлов, здесь не скачан.

## 6. Dataset Mode: выполненные запуски

```bash
make dualmap-replica-smoke
REPLICA_ROOT="$PWD/data/datasets/replica-nice-slam/Replica" \
  bash scripts/dualmap-replica-smoke.sh end=-1 stride=10
```

Все параметры запуска заданы в [scripts/dualmap-replica-smoke.sh](../../scripts/dualmap-replica-smoke.sh).

Первый неудачный по содержимому результат: 3 keyframes, после штатной фильтрации 0 объектов. Увеличен только объём входа: 30 кадров/stride 1 -> 23 объекта. Полная траектория со stride 10 -> 200 кадров, 58 объектов, среднее 0.7921 с/кадр; оба запуска exit 0. [30 кадров](../../results/dualmap/replica-30frames/summary.json), [200 кадров/config/CSV](../../results/dualmap/replica-room0/summary.json).

## 7. Ошибки, решения и оставшиеся ограничения

| Симптом | Что сделано | Итог |
|---|---|---|
| Прерван Miniforge bootstrap | Повтор installer с `-u` в том же prefix | Окружение создано |
| Старый torchvision в MobileCLIP metadata | Авторский editable `--no-deps`, современная согласованная torch/vision cu128 пара | Inference работает; training-only clip-benchmark/datasets отсутствуют |
| Медленная/прерванная загрузка | Возобновление curl `-C -`, проверка размеров/SHA | Assets получены |
| Неверные имена объектов карты | Внешний Replica ID->name JSON, `yolo.use_given_classes=false` | Подписи исправлены без изменения features |
| Open3D viewpoint/window mismatch | Использован работающий GUI; точный авторский ракурс не объявлен воспроизведённым | Поиск работает |
| 0 объектов после 3 keyframes | 30 последовательных кадров, без изменения порогов алгоритма | 23 объекта |
| Риск очистки upstream output | Новый каталог с timestamp/PID при каждом запуске | Старые результаты сохраняются |
| Нет semantic GT | mIoU/FmIoU/mAcc не вычислялись | Остающийся предел проверки |

Локальные журналы: `results/dualmap/stage2/logs/{conda-create,python-deps,torch-install,offline-query-corrected,replica-30frames,replica-room0-full}.log`. Логи/бинарники игнорируются Git; небольшие доказательства результата сохранены по ссылкам выше. ROS/Record3D/онлайн-робот не устанавливались.
