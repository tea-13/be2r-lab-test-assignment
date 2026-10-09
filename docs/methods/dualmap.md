# DualMap

[Полный журнал развёртывания: команды, настройки, ошибки и решения](../deployment/dualmap.md).
Источники: [paper](https://arxiv.org/abs/2506.01950), [README](../../third_party/DualMap/README.md), commit `157235ec49e6a1f439babbc571c4c02ad1f06aa9`. Результаты текущего этапа см. [status](../status.md).

## Метод и данные

Задача — online open-vocabulary mapping в изменяющихся сценах и поиск объектов естественным языком. RGB-D и известные poses поступают в detector: YOLO-World задаёт классы, SAM/FastSAM — маски, MobileCLIP — признаки. Объектные наблюдения объединяются в конкретную локальную карту; отдельная абстрактная глобальная карта хранит более устойчивое представление. Обновление учитывает видимость, соответствие наблюдений и мобильность объектов. Навигационные функции используют layout/navigation graph, но не нужны offline query.

Ключевые блоки: [core.py](../../third_party/DualMap/dualmap/core.py), [detector](../../third_party/DualMap/utils/object_detector.py), [tracker](../../third_party/DualMap/utils/tracker.py), [local](../../third_party/DualMap/utils/local_map_manager.py) / [global](../../third_party/DualMap/utils/global_map_manager.py) map managers. Собственный SLAM не добавлен.

- Dataset Mode: RGB, depth, intrinsics, готовые camera-to-world poses → объекты `.pkl`, layout `.pcd`, CSV времени, при отдельной оценке semantic metrics.
- Offline Query: готовые объектные карты и текст → cosine similarity MobileCLIP и подсветка наиболее подходящего объекта в Open3D.
- Также upstream поддерживает ROS1/ROS2, Record3D и online simulation; эти режимы в данном этапе не проверяются.

## Проверенный запуск (2026-10-09)

**SMOKE_TESTED:** Offline Query и Dataset Mode. Conda `.local/envs/dualmap`: Python 3.10.22, torch 2.9.0+cu128 / torchvision 0.24.0+cu128, FAISS 1.9.0, Open3D 0.19.0, OpenCLIP 2.32.0. uv используется только как pip installer внутри Conda, с кешем хоста. Точные версии: [Conda explicit](../../environments/dualmap-conda-explicit.txt), [pip inventory](../../environments/dualmap-pip-freeze.txt).

Из корня workspace:

```bash
make dualmap-gpu-check
make dualmap-query
# В окне F, в терминале chair/sofa, затем Q в окне.
make dualmap-replica-smoke
```

Query использует `data/datasets/dualmap-prebuilt/map` и `data/weights/dualmap/mobileclip_s2.bin`. Карту из [авторского архива](https://drive.google.com/file/d/15O8pWAD4qUXLq0N9Ji0UFhxdzUJpXZTH/view) (21,073,974 bytes) распаковывать непосредственно в `data/datasets/dualmap-prebuilt`. Checkpoint — [фиксированный revision](https://huggingface.co/apple/MobileCLIP-S2-OpenCLIP/resolve/8e8a808316aeb7c24d0400e1cf8f74b6937832aa/open_clip_pytorch_model.bin). Внешняя metadata исправляет несовпадение Replica IDs с текущим gpt_indoor_general, а не результаты модели.

Dataset target обрабатывает первые 30 кадров room0 со stride=1, sequential, без Rerun. По умолчанию данные в `data/datasets/replica-smoke/Replica`; для полной распаковки задать `REPLICA_ROOT=/absolute/path/Replica`. Нужны `room0/results/{frame*.jpg,depth*.png}` и исходный `traj.txt`, camera intrinsics берутся из upstream Replica config. В `data/weights/dualmap` нужны `yolov8l-world.pt`, `mobile_sam.pt`, `FastSAM-s.pt` из [Ultralytics assets v8.3.0](https://github.com/ultralytics/assets/releases/tag/v8.3.0). YOLO-World также загрузил CLIP ViT-B/32 в `~/.cache/clip/ViT-B-32.pt`; этот кеш не в Git. Каждый запуск target получает новый output в `results/dualmap/replica-*/raw`.

Результаты: 41 объект в готовой карте; chair 0.592, sofa 0.612; Dataset Mode сохранил 23 объекта и layout, среднее 0.4549 с/кадр на 30 кадрах. [Артефакты и оговорки](../../results/dualmap/stage2/README.md), [CSV](../../results/dualmap/replica-30frames/system_time.csv). Дополнительно вся траектория room0 (2000 исходных кадров, stride=10 → 200 обработанных): exit 0, 58 объектов + layout, среднее 0.7921 с/кадр, P90 1.1714. [Результаты](../../results/dualmap/replica-room0/summary.json). Проверенная команда:

```bash
REPLICA_ROOT="$PWD/data/datasets/replica-nice-slam/Replica" bash scripts/dualmap-replica-smoke.sh end=-1 stride=10
```

Semantic GT не загружен, mIoU/FmIoU/mAcc не измерялись.

Установка использует Dataset/Query subset [requirements](../../environments/dualmap-requirements.txt), без ROS/Record3D. MobileCLIP установлен штатно `--no-deps`: `uv pip check` сообщает отсутствующие training-only clip-benchmark/datasets и старое требование torchvision==0.14.1; понижение torchvision нарушит Blackwell-стек. Этот конфликт metadata зафиксирован, проверенные inference-сценарии работают. Полная environment.yml не объявляется воспроизведённой.

## Метрики и границы проверки

Upstream semantic evaluation вычисляет mIoU (среднее IoU классов), FmIoU (IoU с весами по частотам), mAcc (средняя точность классов); [реализация](../../third_party/DualMap/evaluation/sem_seg_eval.py). Для этого нужен Original Replica semantic GT отдельно от NICE-SLAM RGB-D.

Cosine similarity в Offline Query — оценка соответствия запроса объекту, не accuracy и не доказательство воспроизведения paper. В query-коде надпись «Top 5» при `top_k=1`: фактически выводится один объект. Short Dataset Mode — smoke test, не полная оценка сцены.

## Ограничения

- Query имеет жёсткие `.to("cuda")` в callback; CPU override сам по себе недостаточен.
- Объектные embeddings должны соответствовать той же модели MobileCLIP; заменять её версией v2 нельзя без пересчёта карты.
- Open3D требует работающего дисплея; карта требует согласованных class names/colors.
- Runner использует предоставленные poses; ошибки poses/depth непосредственно влияют на геометрию.
- Некоторые каталоги output очищаются upstream при запуске: каждый запуск должен иметь новый путь.

## Идеи контролируемых экспериментов (не выполнены)

1. На одной сцене и фиксированных весах сравнить stride 5/10/20: время на кадр, число объектов; после подготовки GT — mIoU. Зафиксировать одинаковый диапазон исходных кадров.
2. На одной готовой карте сравнить синонимы и описания одного предмета: top-1 UID, cosine similarity и ручное соответствие. Фиксировать class metadata, карту и модель; не менять алгоритм.
