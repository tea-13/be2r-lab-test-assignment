# OneMap

[Полный журнал развёртывания: команды, настройки, ошибки и решения](../deployment/onemap.md).
Источники: [paper](https://arxiv.org/abs/2409.11764), [README](../../third_party/OneMap/README.md), commit `897abb4ded745de2c23fe82a606e1ac0d5157089`. Результаты текущего этапа см. [status](../status.md).

## Метод и данные

Задача — zero-shot single-/multi-object navigation с повторным использованием семантической карты между запросами. RGB-D и poses симулятора проецируют dense SED/OpenCLIP признаки в пространственную карту. Обновление учитывает неопределённость наблюдений. Текст сравнивается с признаками карты; navigator выбирает frontier или область высокой similarity и планирует путь. YOLO-World используется для проверки целей.

Ключевые блоки: [feature_map.py](../../third_party/OneMap/mapping/feature_map.py), [navigator.py](../../third_party/OneMap/mapping/navigator.py), [clip_dense.py](../../third_party/OneMap/vision_models/clip_dense.py), [planning](../../third_party/OneMap/planning/). Экспериментальный CuOneMap backend не включается.

Вход: Habitat сцена с navmesh/semantics, RGB-D, camera intrinsics, pose и текстовые цели; evaluation дополнительно требует ObjectNav episodes. Выход: feature/confidence/obstacle map, путь и визуализация Rerun; evaluation сохраняет результаты эпизодов. В демо poses берутся из `sim.get_agent(0).get_state()`.

Режимы upstream: Habitat demo, single-object evaluation, multi-object evaluation и генерация episodes; Spot/реальная платформа не обязательны. Штатное демо — `python3 habitat_test.py --config config/mon/base_conf_sim.yaml` из корня проекта. Наличие этой команды в README не означает успешный запуск здесь.

## Окружение и данные

Выбран авторский [Dockerfile](../../third_party/OneMap/Dockerfile): Ubuntu 22.04, CUDA 12.8.1, Python 3.10; Habitat-sim v0.2.4, Habitat lab/baselines 0.2.420230405, detectron2, SED fork OpenCLIP, planning_cpp. Веса: clip.pth, YOLOv7, MobileSAM; demo также инициализирует YOLO-World и pretrained ConvNeXt CLIP.

Штатный [habitat_test.py](../../third_party/OneMap/habitat_test.py) фиксирует сцену `val/00853-5cdEh9F2hJL` и annotated scene dataset config. Для smoke test пользователь разрешил другую сцену: публичная `example/00861-GLAQ4DNUx5U` из `hm3d_example` содержит semantics. Подготовлена внешняя копия demo с заменой только двух путей сцены/config; [diff](../../results/onemap/stage2/demo-scene-only.diff). Алгоритм и tracked upstream не менялись. Это запуск на другой сцене, а не воспроизведение авторского примера 00853. `HM3D=LOCAL` исключает автоматическую загрузку сцен при сборке, но не скачивание весов и эпизодов. Полный HM3D требует доступа Matterport; публичный example скачан без credentials (~215 MB).

## Проверенные запуски (2026-10-09)

**INSTALLED / SMOKE_TESTED:** собран `be2r-onemap:897abb4`; Habitat-Sim 0.2.4, torch 2.9.0+cu128, torchvision 0.24.0, NumPy 1.26.4, Rerun 0.22.1, inference-gpu 0.15.2. [Установка и исправления окружения](../../environments/onemap-build.md), [версии](../../environments/onemap-pip-freeze.txt). Исходники submodule чистые.

1. `make onemap-habitat-check`: GPU RGB-D render 640×480, navmesh loaded, 908 semantic objects, CUDA matmul finite, exit 0. [JSON](../../results/onemap/stage2/habitat-smoke.json), [RGB](../../results/onemap/stage2/habitat-example-rgb.png).
2. Habitat demo: **317 обновлений карты**, запрос `A Couch`, среднее `add_data` 0.239 с. [Скриншот Rerun](../../results/onemap/stage2/demo-rerun.png), [summary](../../results/onemap/stage2/demo-summary.json). Бесконечный upstream-цикл остановлен SIGINT после smoke (exit 130), естественного «успешного завершения» у него нет.
3. Короткий ObjectNav: подготовлены первые 3 из 28 официальных v2 val эпизодов GLAQ4DNUx5U (toilet, sofa, bed), исходные starts/goals сохранены. Внешний конфиг ограничивает 200 шагов; используется штатный YOLOv7 (`using_ov: false`), тогда как demo напрямую создаёт YOLO-World. [Выбор эпизодов](../../results/onemap/objectnav-smoke/episodes.json). Завершено exit 0: toilet/sofa — лимит 200, bed — успех на 154-м шаге; SR 33.33%, SPL 27.33% по штатному `read_results.py`. [Результаты](../../results/onemap/objectnav-smoke/summary.json).

Данные: `data/datasets/onemap-hm3d-example/versioned_data/hm3d-0.2/hm3d`; pretrained ConvNeXt и Roboflow ONNX/YOLO — `data/cache/onemap`; авторские clip.pth/MobileSAM/YOLOv7 — внутри образа, clip.pth также снаружи в `data/weights/onemap`. [SHA весов](../../results/onemap/stage2/image-weights.sha256). Public example получен официальным standalone downloader v0.2.4 с UID `hm3d_example`, поскольку установленного Habitat-Sim на хосте первоначально не было.

Для EGL нужен read-only mount `/usr/share/glvnd/egl_vendor.d/10_nvidia.json`: NVIDIA-библиотека в контейнере была, vendor JSON отсутствовал. Для Hugging Face выбран `HF_HUB_DISABLE_XET=1`; обычная HTTP-загрузка прошла. В evaluator YOLOv7 пишет `traced_model.pt`, поэтому этот файл вынесен writable mount в кеш. Драйверы хоста не менялись.

Команды из корня (viewer в отдельном терминале):

```bash
make onemap-viewer
make onemap-demo
make onemap-eval-smoke
```

Demo завершать Ctrl+C; `ONEMAP_DEMO_SECONDS=30 make onemap-demo` проверен, возвращает ожидаемый timeout 124 (make 2). Eval сохраняет новый `results/onemap/objectnav-*/raw`; старые результаты не затирает. Для запуска нужны подготовленные три эпизода в `data/datasets/onemap-objectnav-smoke`; [подготовка](../../results/onemap/objectnav-smoke/README.md).

## Метрики и ограничения

Для ObjectNav: SR — доля успешных эпизодов; SPL — успех, взвешенный отношением кратчайшего пути к пройденному. Для multi-object авторские таблицы используют Progress/PR и SPL/PPL; имена в output отличаются от paper, см. README. Короткий тест не воспроизводит paper: другая сцена, ObjectNav v2, main SHA и сокращённый лимит шагов.

- Нужны лицензированные HM3D и согласованные версии эпизодов/semantics.
- `pip check` не чист: LAVIS требует timm 0.4.12 при установленном 1.0.30, decord 0.6.0 помечен unsupported platform. [Вывод](../../results/onemap/stage2/pip-check.txt). BLIP2/видеорежимы не проверены; demo и короткий evaluator работают.
- В исходном Dockerfile `timm>=1.0.7` не quoted; кавычки исправлены только во внешней копии.
- Demo не ограничивает число кадров и работает в цикле; штатный запуск не равен завершённому benchmark.
- Для single-object paper автор рекомендует ветку eval/s_eval; текущий main SHA не выдаётся за её воспроизведение.

## Идеи контролируемых экспериментов (не выполнены)

1. После рабочего demo зафиксировать одну сцену, старт и цели; сравнить повторный поиск с сохранённой картой и после reset: длина пути, шаги, SR.
2. Зафиксировать RGB-D/poses и цели, менять только разрешение карты: память GPU, время обновления, SPL на одинаковом коротком наборе эпизодов. Изменения через конфиг, без правки алгоритма.
