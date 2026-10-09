# Датасеты, веса и минимальные входы

Аудит Этапа 1: 2026-10-08. Обновление Этапа 2: 2026-10-09 — загружены готовая карта DualMap (21,073,974 bytes), MobileCLIP-S2 (398,202,800 bytes), YOLO-World/MobileSAM/FastSAM, автоматически CLIP ViT-B/32, первые 30 кадров Replica и публичный HM3D example. Полный Replica.zip (12,442,855,671 bytes) скачан с согласия пользователя; room0 распакована. Для OneMap получены авторские checkpoints и эпизоды в Docker, pretrained ConvNeXt и Roboflow CLIP/YOLO в локальном кеше. Первоначальная таблица ниже описывает требования, а не отсутствие уже загруженных файлов. Исключение: upstream VLFM сам хранит два PointNav `.pth` примерно по 33 MiB — они пришли с submodule, не добавлены бинарниками в родительский Git. Размеры ниже — порядок объёма для планирования, не измеренный размер загрузки; неизвестные размеры указаны явно. Перед любой загрузкой свыше 5 GB уточнить состав, объём и получить согласование.

## Данные

| Набор / версия | Формат и методы | Доступ / объём / ограничения |
|---|---|---|
| DualMap prebuilt Replica room_0 / iPhone | `map/*.pkl`, `layout.pcd`, `viewpoint.json`; только DualMap offline query. Также нужны class names/colors и та же CLIP-модель | [Авторские ссылки Google Drive/OneDrive и структура](../third_party/DualMap/resources/doc/app_offline_query.md). Replica room0 архив 21,073,974 bytes скачан и проверен Offline Query. Отдельная лицензия готовых карт не указана; Replica-производные сохраняют ограничения исходного набора. Проверено в Этапе 2. |
| Replica RGB-D, подготовка NICE-SLAM | `results/frame*.jpg`, `depth*.png`, `traj.txt` (camera-to-world poses), intrinsics/config; DualMap и HOV-SG | [Архив](https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip), [инструкция](../third_party/DualMap/resources/doc/data_replica_scannet.md). Восемь сцен office0–4, room0–2. Полный архив 12,442,855,671 bytes; скачан, распакована room0. Для минимума room0 либо office0. Это отрендеренные траектории, не исходные meshes. |
| Original Replica v1 | `room_0/habitat/mesh_semantic.ply`, `info_semantic.json`, остальные mesh/texture assets; semantic GT DualMap/HOV-SG | [Источник](https://github.com/facebookresearch/Replica-Dataset), [Research Terms](https://github.com/facebookresearch/Replica-Dataset/blob/main/LICENSE): исследовательское/образовательное некоммерческое использование. Полный набор — большой, >5 GB; точный размер зависит от assets. GT сопоставить по scene ID и координатам, не смешивать room0 и room_0 автоматически. |
| HM3D v0.2 Habitat + semantic annotations/configs | `.basis.glb`, navmesh, semantic `.glb/.txt`, dataset JSON; OneMap и VLFM simulation; исходные сцены HOV-SG | [Matterport release/access](https://github.com/matterport/habitat-matterport-3dresearch). Нужны принятые условия и credentials. Полные train/val — десятки/сотни GB по составу; заранее сверить manifest, 268 GiB свободного диска не гарантируют размещение всех вариантов. OneMap demo требует сцену `00853-5cdEh9F2hJL` и annotated config; наличие в minival не установлено. |
| HM3D ObjectNav v1 / v2 | `.json.gz` эпизоды, не geometry; VLFM — v1; OneMap — v1 и v2 + multiobject | [v1](https://dl.fbaipublicfiles.com/habitat/data/datasets/objectnav/hm3d/v1/objectnav_hm3d_v1.zip), [v2](https://dl.fbaipublicfiles.com/habitat/data/datasets/objectnav/hm3d/v2/objectnav_hm3d_v2.zip). v1 ZIP 138,845,369 bytes, v2 ZIP 260,304,032 bytes; получены авторской сборкой. v1/v2 нельзя подменять без проверки scene IDs и схемы. Для выбранной example 00861 эпизоды нашлись в v2; первые 3 проверяются single-object loader OneMap. Условия исходных HM3D сохраняются. |
| OneMap multiobject episodes | Авторский `multiobject_episodes/` + ObjectNav v2 lookup | [README и Google Drive ID](../third_party/OneMap/README.md): `1lBpYxXRjj8mDSUTI66xv0PfNd-vdSbNj`. Размер и отдельная data license не указаны. Не нужен полный benchmark ради первого demo. |
| HOV-SG hm3dsem_walks | RGB, depth, poses, semantic frames из авторских poses; затем иерархический GT | [README](../third_party/HOV-SG/README.md), [poses](../third_party/HOV-SG/hovsg/data/hm3dsem/metadata/poses). Это производная подготовка, не просто HM3D symlink. Размер зависит от сцен/числа кадров; генерация GT рекомендует 128 GB RAM, на этом хосте отложена. |
| ScanNet / ScanNet200 | `.sens` → color/depth/intrinsic/pose, semantic `.ply`; DualMap и HOV-SG segmentation | [Источник/условия доступа](https://github.com/ScanNet/ScanNet). Нужна заявка/соглашение; полный набор значительно >5 GB, отдельные последовательности тоже уточнять. ScanNet200 — другая таблица классов/подготовка GT. DualMap guide упоминает Python 2.7 SensReader; это отдельный preprocessing, не зависимость основного окружения. |
| TUM RGB-D; MP3D/Gibson | TUM заявлен DualMap; MP3D/Gibson — режимы/эксперименты VLFM | Дополнительные сценарии, не минимальный план. Форматы и загрузки здесь не проверены; у MP3D/Gibson отдельный доступ. Не предполагается общая совместимость с Replica/HM3D. |

Для всех запусков использовать poses датасета или симулятора. Собственный SLAM не нужен.

## Что можно разделить

- DualMap ↔ HOV-SG: одни NICE-SLAM RGB-D/poses и Original Replica GT, если совпадают сцены, intrinsics, единицы depth и coordinate frames. Выходные feature maps/pickle между методами не совместимы.
- OneMap ↔ VLFM: одна HM3D v0.2 geometry/semantics через read-only mount или symlink. Путь эпизодов различается: OneMap `datasets/objectnav_hm3d_v1`, VLFM `data/datasets/objectnav/hm3d/v1`. v2/multiobject хранить отдельно.
- HOV-SG может использовать те же исходные HM3D assets, но требует собственных posed walks и GT. DualMap HM3D_collect — тоже отдельный формат.
- MobileSAM/YOLOv7 между OneMap/VLFM можно разделить только после совпадения конкретного checkpoint и SHA256. SED CLIP, MobileCLIP и HOV-SG CLIP имеют разные feature spaces; их веса и embeddings не подменять.

## Веса и лицензии

Оценки размеров округлены; суммы загрузок, распакованных файлов, кешей и VRAM различаются. Точные revisions/hashes следует записать после разрешённой загрузки.

| Метод | Требуемые артефакты | Порядок объёма и условия |
|---|---|---|
| DualMap query | MobileCLIP-S2 v1, pretrained `datacompdr`; [OpenCLIP checkpoint](https://huggingface.co/apple/MobileCLIP-S2-OpenCLIP) | ~0.4 GB для FP32 ~99M параметров (оценка); Apple AMLR model license. Версия v2 не воспроизводит v1 embeddings. Может скачаться автоматически при первом вызове. |
| DualMap mapping | `model/yolov8l-world.pt`, `model/FastSAM-s.pt`; опционально `model/mobile_sam.pt` | [system_config](../third_party/DualMap/config/system_config.yaml), [Ultralytics](https://github.com/ultralytics/ultralytics). Десятки/сотни MB, точные assets/hashes не проверены. Ultralytics/FastSAM имеют отдельные AGPL/коммерческие условия, Apache-2.0 DualMap их не заменяет. |
| OneMap | `weights/clip.pth` (SED), `yolov7-e6e.pt`, `mobile_sam.pt` | [Точные download URLs в Dockerfile](../third_party/OneMap/Dockerfile). CLIP — порядок GB, YOLO — ~0.3 GB, MobileSAM — ~0.04 GB (оценки); общий объём build не установлен. [SED](https://github.com/xb534/SED), [YOLOv7](https://github.com/WongKinYiu/yolov7) (GPL-3.0 code), [MobileSAM](https://github.com/ChaoningZhang/MobileSAM) (Apache-2.0 code). Отдельная лицензия извлечённого SED checkpoint не подтверждена. |
| VLFM | `data/mobile_sam.pt`, `groundingdino_swint_ogc.pth`, `yolov7-e6e.pt`, `pointnav_weights.pth`; BLIP2/LAVIS downloads | [README](../third_party/vlfm/README.md). GroundingDINO — порядок 0.7 GB, BLIP2 — несколько GB, точный набор кешей не проверен. [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO), [LAVIS](https://github.com/salesforce/LAVIS) — Apache-2.0 code; отдельные модели/данные имеют свои условия. PointNav (~33 MiB) и Spot PointNav уже в upstream Git. |
| HOV-SG | `checkpoints/laion2b_s32b_b79k.bin`, `sam_vit_h_4b8939.pth`; альтернативный OVSeg CLIP | [CLIP model card](https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K) (MIT), [SAM](https://github.com/facebookresearch/segment-anything) (Apache-2.0). CLIP ViT-H 3,944,692,325 bytes + SAM ViT-H 2,564,550,879 bytes: пользователь согласовал оба checkpoint 2026-10-09; загрузка в `data/weights/hovsg/`. Итог проверки — в обзоре HOV-SG. Файл SAM — исходный SAM ViT-H; название `sam_v2` в README не означает SAM 2. |

Лицензии библиотек/кода не автоматически покрывают все веса и датасеты. Неустановленные условия отмечены явно; лицензии не переопределялись.

## План размещения и фактические пути Этапа 2

```text
data/datasets/dualmap-prebuilt/replica_room_0/map/
data/datasets/replica-nice-slam/
data/datasets/replica-original-v1/
data/datasets/hm3d-v0.2/versioned_data/
data/datasets/objectnav-hm3d-v1/
data/datasets/objectnav-hm3d-v2/
data/datasets/onemap-multiobject/
data/weights/{dualmap,onemap,vlfm,hovsg}/
data/cache/
results/<method>/<experiment>/
```

Это договорённость workspace, upstream сам эти пути не читает. Подключать внешними конфигами/overrides, bind mounts или symlinks; результаты каждого запуска сохранять отдельно. `.env.example` — справочник переменных, не готовая интеграция.

## Публичный HM3D example (проверено загрузкой)

По предложению пользователя использован UID `hm3d_example` из [официального downloader v0.2.4](https://github.com/facebookresearch/habitat-sim/blob/v0.2.4/src_python/habitat_sim/utils/datasets_download.py). Он скачивает с GitHub Matterport небольшой пример без credentials. Фактический каталог `data/datasets/onemap-hm3d-example`, ~215 MB.

Доступны `00337-CFVBbU9Rsyb`, `00770-NBg5UqG3di3`, `00861-GLAQ4DNUx5U`; для последней есть semantic mesh/txt. Для неё выбран `example/hm3d_annotated_example_basis.scene_dataset_config.json`. [Инвентарь](../results/onemap/stage2/scene-inventory.json). Это устраняет необходимость закрытого полного HM3D для smoke test, но не заменяет benchmark-сцены/эпизоды.

Готовая карта DualMap фактически распакована в `data/datasets/dualmap-prebuilt/map`; короткий Replica subset — `data/datasets/replica-smoke/Replica/room0`. Карта использует Replica IDs, внешняя таблица в `configs/dualmap/metadata` взята из официального ai-habitat semantic lexicon; исходный gpt_indoor_general.txt не соответствует сохранённым IDs.

Replica.zip получен целиком (12,442,855,671 bytes), SHA256 `dc18265e213f8281444b768eed76f627bde8c3b925654934f84f78a87990a548`. Распакована только room0 (2000 RGB-D кадров + poses) в `data/datasets/replica-nice-slam/Replica`; CRC проверен для всех извлечённых файлов. [Архив](../results/dualmap/stage2/replica-archive.json).

## HOV-SG: фактические assets Этапа 3

Оба согласованных checkpoint ViT-H скачаны в `data/weights/hovsg/`; точные размеры и SHA256 — [инвентарь](../results/hovsg/stage3/weights.json). OpenCLIP revision `1c2b8495b28150b8a4922ee1c8edee224c284c0c`, SHA совпадает с upstream metadata.

Повторно используются `data/datasets/replica-smoke/Replica/room0` и соседний `cam_params.json` из подготовки DualMap. HOV-SG обработал кадры 0, 10, 20 с исходными poses. Original Replica GT, HM3DSem posed walks и полный benchmark не загружались/не выполнялись; NICE-SLAM room0 не подменяет Original Replica room_0 semantic assets. [Результат extraction](../results/hovsg/stage3/README.md).
## Дополнение: RGB-D для графа HOV-SG (2026-10-09)

Для `00861-GLAQ4DNUx5U` из уже скачанного публичного HM3D example отрендерены **83 RGB-D кадра** по авторской траектории HOV-SG (каждая 50-я из 4137 поз). Каталог: `data/datasets/hovsg-hm3d-example/val/00861-GLAQ4DNUx5U/`, около 41 MiB. RGB/depth 640×480, HFOV 90°, глубина uint16 в миллиметрах; poses camera-to-world в системе Habitat, преобразование осей выполняет штатный HM3DSem loader. Соответствие сохранённых поз исходным проверено.

Использованы существующий Docker с Habitat-Sim и helpers HOV-SG; новых загрузок, собственного SLAM или semantic GT нет. [Подготовка и параметры графа](hovsg-graph-demo.md), [проверка входов](../results/hovsg/graph-demo/input-check.json). Это разреженная последовательность для демо, не полный `hm3dsem_walks` benchmark; исходные условия использования HM3D сохраняются.
