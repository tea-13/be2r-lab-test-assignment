# VLFM

[Полный журнал развёртывания: команды, настройки, ошибки и решения](../deployment/vlfm.md).
[Paper, ICRA 2024](https://arxiv.org/abs/2312.03275), [upstream README](../../third_party/vlfm/README.md), SHA `584ed56008754fde7997d904983607def8328322`. Точный итог запуска — [status](../status.md).

## Задача и алгоритм

Zero-shot ObjectNav: найти объект заданной категории в незнакомой сцене. Depth формирует occupancy map и границы исследованного пространства. BLIP-2 image–text matching оценивает RGB-наблюдения относительно текстовой цели; оценки проецируются в value map. Политика выбирает перспективный frontier, PointNav ведёт к waypoint. Детектор и маска локализуют целевой объект и переключают поиск на подход к нему.

Основные реализации: [value_map](../../third_party/vlfm/vlfm/mapping/value_map.py), [obstacle_map](../../third_party/vlfm/vlfm/mapping/obstacle_map.py), [ITM policy](../../third_party/vlfm/vlfm/policy/itm_policy.py), [BLIP2ITM](../../third_party/vlfm/vlfm/vlm/blip2itm.py). Это карта ценности для навигации, а не объектный scene graph.

## Входы, выходы и зависимости

Входы: RGB-D, параметры камеры, pose/GPS/compass симулятора, целевая категория; для evaluation — сцена/navmesh и официальные ObjectNav episodes. Выходы: действия/waypoints, occupancy/value/object maps, episode metrics, опционально видео. Собственный SLAM не требуется.

Штатный способ — Conda Python 3.9, torch 1.12.1+cu113 / torchvision 0.13.1+cu113; в репозитории нет environment.yml, команды находятся в README. Habitat-Sim 0.2.4, Habitat-Lab/Baselines 0.2.420230405; GroundingDINO на SHA `eeba084…`, LAVIS 1.0.2, transformers 4.26.0, timm 0.4.12. Отдельные Flask servers BLIP2ITM/GroundingDINO/MobileSAM/YOLOv7 запускаются через tmux. PointNav checkpoint уже включён в Git submodule; остальные веса не следует подменять похожими моделями других методов.

## Минимальный pipeline и границы проверки

Авторский pipeline после полной установки: `scripts/launch_vlm_servers.sh`, затем `python -m vlfm.run` из корня upstream. Это **reference-команды**, их успешность на текущем хосте не предполагается. Стандартный конфиг использует `test_episode_count: -1` (все эпизоды); короткий тест требует внешнего Hydra override и доступных сцен/эпизодов. [Конфиг](../../third_party/vlfm/config/experiments/vlfm_objectnav_hm3d.yaml).

В Этапе 3 установлен штатный torch в отдельном `.local/envs/vlfm`: Python 3.9, torch 1.12.1+cu113, torchvision 0.13.1+cu113, numpy 1.26.4. **GPU BLOCKED подтверждён запуском:** `make vlfm-gpu-check` возвращает ошибку `no kernel image is available for execution on the device` (script exit 1 / make exit 2). RTX 5060 Ti имеет sm_120; wheel содержит архитектуры до sm_86. При этом `torch.cuda.is_available()` true. [Точный результат](../../results/vlfm/stage3/README.md), [установка](../../environments/stage3.md). Политика, Habitat и серверы не установлены; навигационный pipeline не запускался. Миграция на современный torch затрагивает закреплённые requirements, GroundingDINO extensions и Habitat/LAVIS; не объявляется выполненной автоматически.

## Метрики и ограничения

ObjectNav: SR (доля успехов), SPL (успех с учётом длины пути), distance-to-goal и число шагов по Habitat evaluation. Реальные SR/SPL VLFM в этой работе пока не измерены.

- Полная политика зависит от нескольких модельных серверов; один успешно импортированный модуль не означает работающую навигацию.
- Нужны согласованные версии HM3D и эпизодов. Имеющаяся example 00861 имеет ObjectNav v2; штатный VLFM ориентирован на v1, подмена без проверки конфигурации недопустима.
- Четыре одновременно загруженные модели ограничивают VRAM; перенос на CPU меняет производительность и не подтверждает GPU-сценарий.
- README указывает отсутствие активного сопровождения. Реальный Spot/ROS-путь в задачу не входит. Лицензия кода MIT; данные и веса имеют отдельные условия.

## Идеи экспериментов (не выполнены)

1. На фиксированных эпизодах сравнить формулировки цели при неизменных моделях: SR/SPL, выбранные frontiers и число шагов.
2. В пределах авторских конфигов сравнить порог детектора: ложные остановки, SR/SPL; фиксировать сцены, starts и лимит шагов.
