# HOV-SG

[Полный журнал развёртывания: команды, настройки, ошибки и решения](../deployment/hovsg.md).
[Paper, RSS 2024](https://arxiv.org/abs/2403.17846), [README](../../third_party/HOV-SG/README.md), SHA `d6e65a53c8be6faec3f01f00d1644d967f89e605`. Точный итог — [status](../status.md).

## Задача и алгоритм

Open-vocabulary 3D mapping и иерархический scene graph для языковых запросов. SAM создаёт class-agnostic masks; OpenCLIP кодирует изображение, crops и masked crops. Признаки объединяются, проецируются через RGB-D/poses в 3D и сливаются между кадрами. Для HM3DSem строится иерархия building → floor → room → object и навигационный граф. Для Replica отдельный режим строит feature map и выполняет semantic segmentation без обязательного многоэтажного графа.

Реализации: [Graph](../../third_party/HOV-SG/hovsg/graph/graph.py), [SAM/CLIP fusion](../../third_party/HOV-SG/hovsg/models/sam_clip_feats_extractor.py), [Replica loader](../../third_party/HOV-SG/hovsg/dataloader/replica.py), [evaluator](../../third_party/HOV-SG/application/eval/evaluate_sem_seg.py).

## Входы, выходы и зависимости

Вход: posed RGB-D, intrinsics и depth scale; Replica использует `frame*.jpg`, `depth*.png`, `traj.txt`, соседний `cam_params.json`. Источник poses — датасет, не собственный SLAM. Semantic evaluation отдельно требует Original Replica `habitat/mesh_semantic.ply` и `info_semantic.json`.

Выход: full/masked point clouds, per-point и per-mask embeddings (`full_feats.pt`, `mask_feats.pt`); graph mode дополнительно сохраняет floors/rooms/objects JSON/PLY и nav graph. Форматы признаков не совместимы с готовой MobileCLIP-картой DualMap без пересчёта.

Штатный [environment.yaml](../../third_party/HOV-SG/environment.yaml): Conda Python 3.9, FAISS GPU, pip Open3D 0.18.0, matplotlib 3.7.3, scipy 1.13.1, SAM/OpenCLIP, Hydra и прочие пакеты. Habitat-Sim устанавливается отдельно для генерации HM3DSem; готовый Replica RGB-D pipeline его не использует. Штатные ViT-H веса: OpenCLIP 3,944,692,325 bytes + SAM 2,564,550,879 bytes. Локальный Conda prefix — `.local/envs/hovsg`.

## Доступные сценарии

- `application/semantic_segmentation.py`: extraction/merge на Replica или ScanNet.
- `application/eval/evaluate_sem_seg.py`: semantic metrics при наличии GT.
- `application/create_graph.py`: иерархический граф HM3DSem; `visualize_graph.py`, `visualize_query_graph.py`: просмотр и запросы.
- Graph evaluation: `application/eval/evaluate_graph.py` с иерархическим GT.

README evaluation-пример содержит плоские overrides, но текущий конфиг использует `main.dataset`, `main.scene_name`, `main.feature_map_path`. Команда evaluator с `--cfg job` проверена (exit 0); это только разбор Hydra config, не вычисление метрик. Original Replica GT отсутствует.

## Проверенный запуск (2026-10-09)

**INSTALLED / SMOKE_TESTED:** официальный Conda YAML установился без изменений requirements. Python 3.9.25, torch 2.8.0+cu128 / torchvision 0.23.0, NumPy 1.26.4, FAISS-GPU 1.11.0, Open3D 0.18.0; `pip check` чист. Graph import, CUDA matmul и CPU FAISS IndexFlatL2 проверены. GPU-индексы FAISS не используются этим pipeline и не проверены. [Установка, загрузки и инвентари](../../environments/stage3.md).

```bash
make hovsg-replica-smoke
```

Штатный `application/semantic_segmentation.py` обработал кадры **0, 10, 20** 30-кадрового Replica room0 subset; poses/intrinsics исходные. Внешние overrides задают пути, `scene_id=room0`, SAM `points_per_batch=8` вместо 144; sampling `points_per_side=12` и fusion/merge сохранены. Новый каталог вывода создаётся при каждом запуске.

Результат: **exit 0**, 79 030 точек, 30 сохранённых объектов; full features `[79030,1024]`, mask features `[30,1024]`, все значения finite. У 3588 точек нулевые признаки. Время 39.94 с, max RSS ~12 GiB, VRAM peak не измерялся. [Config, summary и вывод](../../results/hovsg/stage3/README.md). Это extraction на трёх кадрах, не полный scene graph/semantic benchmark.

## Метрики и ограничения

Semantic evaluator считает mean IoU, frequency-weighted IoU, mean accuracy, pixel accuracy и per-class IoU. Scene-graph evaluator оценивает уровни иерархии; это отдельная задача, не ObjectNav SR/SPL. Без Original Replica GT нельзя выдавать число масок или сохранённую карту за semantic accuracy.

- Штатные модели требуют около 6.51 GB загрузки; runtime VRAM больше суммы весов из-за activations и dense feature tensors.
- Upstream принудительно выбирает TkAgg при импорте navigation_graph; запуск проверен с X11 DISPLAY. Headless режим не проверен.
- Штатный YAML ставит два OpenCV-дистрибутива в общий namespace: runtime cv2 4.11.0, headless metadata 4.8.1.78. В проверенном окружении pipeline работает; частичная переустановка требует повторной проверки.
- Dense 1024-D признаки каждого пикселя и точки нагружают GPU и RAM. Полная последовательность существенно тяжелее короткого smoke test.
- Для полного HM3DSem GT авторы рекомендуют 128 GB RAM, на хосте около 30 GiB; этот режим не обязателен.
- Иерархические natural-language queries используют OpenAI API; ключ и платный внешний вызов не нужны для Replica extraction/evaluation и здесь не настраиваются.
- Original Replica GT отличается от NICE-SLAM RGB-D. Официальный downloader получает многотомный полный архив; он не запускался без согласования большой загрузки.
- README оговаривает академическое использование MIT и обращение к авторам для коммерческого использования; условия моделей и данных отдельные.

## Идеи экспериментов (не выполнены)

1. На одинаковой room0 и моделях менять `pipeline.skip_frames`: время, peak memory, число масок; при наличии GT — mIoU.
2. Сравнить штатные `merge_type=hierarchical/sequential` на одинаковых кадрах: число объектов, fragmentation и semantic metrics; не менять fusion/алгоритмический код.

## Визуальное демо (дополнение 2026-10-09)

`make hovsg-demo` открывает интерактивную 3D-карту с GUI-поиском и top-5. `make hovsg-build-demo` строит расширенную карту на 20 кадрах room0 (`skip_frames=100`): 399 663 точки, 156 сегментов, exit 0 за 308.66 с. Внешний viewer вызывает upstream `load_feature_map` и `text_prompt`; алгоритмы не менялись. Полная иерархия не заявляется: авторский create_graph.py явно пропускает её для Replica.

Первый build упал с CUDA OOM на выделении 3.11 GiB; повтор с `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` прошёл. [Команды, управление, скриншоты](../hovsg-demo.md). Старые результаты трёхкадрового smoke выше сохранены отдельно.

## HM3DSem graph (дополнение 2026-10-09)

`make hovsg-graph-demo` открывает штатный граф публичной сцены 00861, отдельно от Replica GUI. 83 авторские позы → 400 693 точки → 2 этажа, 14 комнат, 683 объектных сегмента. Штатное построение exit 0 за 793.16 с, max RSS ~16.16 GiB. Навигационный граф имеет 1306 узлов / 1440 рёбер и 4 компоненты; крупнейшая соединяет этажи. Его построение не является ObjectNav evaluation. [Подготовка, все настройки, проверки и ограничения](../hovsg-graph-demo.md).

## Проверка дополнительного объединения

`pipeline.merge_objects_graph=true` проверен на сохранённой HM3D-карте. Штатный вызов упал из-за отсутствующего импорта `find_overlapping_ratio`; внешний импорт функции из авторского `eval_utils` позволил завершить построение без правки submodule. Сегментов стало 611 вместо 683, в отдельном опыте на неизменных объектах получено то же сокращение. Это не измерение instance accuracy. [Условия, результаты и визуализация](../../results/hovsg/merge-check/README.md).
