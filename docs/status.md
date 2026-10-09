# Текущий статус

**Обновлено:** 2026-10-09. **Этапы 2–3 и запрошенная итоговая проверка выполнены. VLFM имеет подтверждённый GPU-блокер; полный benchmark не воспроизведён.**

| Метод | Окружение | Проверено запуском | Ограничения |
|---|---|---|---|
| DualMap | INSTALLED: локальный Conda Python 3.10, torch 2.9/cu128 | GPU; Offline Query; Replica Dataset Mode | Нет semantic GT/benchmark |
| OneMap | INSTALLED: Docker на авторской основе с внешней фиксацией зависимостей | Habitat GPU render; штатный demo на HM3D example; 3 ObjectNav эпизода | Другая сцена, v2 episodes, лимит 200; не paper benchmark |
| VLFM | PARTIAL / GPU BLOCKED: Conda Python 3.9, штатный torch/cu113 | CUDA kernel: exit 1, no kernel image | Политика/Habitat/серверы не установлены, navigation не запускался |
| HOV-SG | INSTALLED: штатный Conda Python 3.9, torch 2.8/cu128 | Replica feature map/query; HM3DSem graph; дополнительное объединение: 683 -> 611 сегментов; авторский viewer, exit 0 | Без GT/graph accuracy; nav graph имеет 4 компоненты; ObjectNav по нему не запускался |

SMOKE_TESTED означает фактический ограниченный запуск, не воспроизведение результатов статьи. Хост: Ubuntu 24.04.3, RTX 5060 Ti 16 GB, драйвер 580.178.04; системный CUDA/драйверы не менялись. Все четыре Git submodules и nested MobileCLIP сохраняют закреплённые SHA, tracked upstream чистый.

## Реальные результаты

- **DualMap Offline Query:** 41 объект, `chair → chair, 0.592`, `sofa → sofa, 0.612`; GUI Open3D и выход Q — exit 0. Исправлены только внешние Replica class metadata. [Результаты/скриншоты](../results/dualmap/stage2/README.md).
- **DualMap Dataset:** 30 кадров → 23 объекта; полная траектория room0 со stride 10 → 200 кадров, 58 объектов + layout, exit 0. Среднее 0.7921 с/кадр, P90 1.1714. [CSV/config/summary](../results/dualmap/replica-room0/summary.json). mIoU не измерялся.
- **OneMap Habitat:** example `00861-GLAQ4DNUx5U`, RGB-D render, navmesh, 908 semantic objects, CUDA matmul; exit 0. [JSON](../results/onemap/stage2/habitat-smoke.json).
- **OneMap demo:** 317 обновлений карты, запрос A Couch, среднее add_data 0.239 с; [Rerun](../results/onemap/stage2/demo-rerun.png). Остановлен SIGINT (130), поскольку upstream-цикл бесконечный. Дополнительная проверка make-target: 65 обновлений за ограниченный запуск, timeout 124 / make 2 — ожидаемо.
- **OneMap ObjectNav:** первые 3 официальных v2 эпизода на той же сцене, максимум 200 шагов. Toilet/sofa — FAILURE_OOT, bed — SUCCESS на 154-м шаге; evaluator и штатный reader exit 0. **SR 33.33%, SPL 27.33%**. [Артефакты](../results/onemap/objectnav-smoke/README.md). Это smoke test, не полный benchmark.

- **VLFM:** штатный torch 1.12.1+cu113 видит RTX 5060 Ti, но реальный kernel падает `no kernel image is available for execution on the device`. Wheel содержит sm_37…sm_86, GPU — sm_120. Установлены только Python/torch/vision/NumPy и их зависимости; продолжение тяжёлой установки остановлено. [Ошибка и JSON](../results/vlfm/stage3/README.md). SR/SPL отсутствуют.
- **HOV-SG:** официальный YAML установился без правок; Graph import, CUDA и CPU FAISS IndexFlatL2 проверены. Штатный Replica pipeline на кадрах 0/10/20 завершился exit 0: **79 030 точек, 30 объектов**, full features `[79030,1024]`, mask features `[30,1024]`; значения finite, у 3588 точек нулевые features. **39.94 с**, max RSS ~12 GiB. [Артефакты/config](../results/hovsg/stage3/README.md). SAM batch 8 вместо 144 — внешний конфиг. mIoU не измерялся; evaluator проверен только с `--cfg job`.

## Подготовка и команды

- DualMap: `.local/miniforge`, `.local/envs/dualmap`; [установка/версии](../environments/README.md). Работают `make dualmap-gpu-check`, `make dualmap-query`, `make dualmap-replica-smoke`.
- OneMap: `be2r-onemap:897abb4`, отдельный образ проверки Habitat `be2r-onemap-env:897abb4`; [сборка и image ID](../environments/onemap-build.md). `make onemap-viewer`, `make onemap-demo`, `make onemap-habitat-check`; `make onemap-eval-smoke` вызывает проверенный `scripts/onemap-eval-smoke.sh`.
- Пользователь согласовал Replica.zip и загрузки Docker >5 GB. Replica скачан целиком (12,442,855,671 bytes), SHA256 сохранён, CRC извлечённой room0 проверен. Публичный HM3D example получен вместо недоступной авторской сцены; Matterport credentials не использовались.
- VLFM: `make vlfm-gpu-check` воспроизводит блокер (script 1 / make 2). HOV-SG: `make hovsg-replica-smoke` вызывает проверенный upstream pipeline; [Conda установка](../environments/stage3.md). Оба ViT-H checkpoint HOV-SG согласованы и скачаны (6.51 GB), SHA256 сохранены; CLIP SHA совпал с metadata источника.
- Веса/кеш/сырые карты и логи остаются вне Git. Небольшие JSON/CSV, trajectories и скриншоты сохранены в `results/`.

## Обнаруженные проблемы

- DualMap MobileCLIP metadata требует старый torchvision и training-only пакеты; штатный `--no-deps` сохранён, inference проверен с torch 2.9/cu128. Open3D ракурс не совпал с авторским viewport, поиск работает.
- Авторская OneMap-сборка без pins выбирала torch 2.14.1 и конфликтовала со Spock по setuptools. Во внешней копии ограничены torch/vision, NumPy/Rerun, добавлен meson-python. Проблемы сети SED/gdown/Xet устранены повтором, локальным checkpoint и HTTP transport.
- Habitat EGL потребовал read-only host `10_nvidia.json`; YOLOv7 tracer — writable mount файла. Сцена demo заменена только двумя путями в генерируемой копии; алгоритмы не редактировались.
- `pip check` OneMap сообщает LAVIS/timm и decord platform; [вывод](../results/onemap/stage2/pip-check.txt). Это остающиеся ограничения непроверенных режимов, а не блокеры выполненных demo/eval. Образ содержит лишний исходный CUDA 13 слой ради сохранения build cache; он не минимален.
- VLFM заблокирован штатным CUDA 11.3/PyTorch 1.12 wheel. Docker не добавляет отсутствующие GPU kernels; нужен другой поддерживаемый GPU либо отдельная миграция всего pinned стека. Она здесь не выполнялась.
- HOV-SG `pip check` чист, но YAML устанавливает два OpenCV-дистрибутива в один namespace; runtime 4.11.0 при headless metadata 4.8.1.78. Проверенный pipeline работает. FAISS GPU indexes не проверены — код использует CPU IndexFlatL2. Upstream Graph импортирует TkAgg, поэтому проверка выполнена с X11, не headless.
- Original Replica semantic GT отсутствует: его официальный downloader получает многотомный полный архив. GT и полный benchmark не запускались/не скачивались. Полный HM3D/Matterport и иерархический GT остаются вне выполненных сценариев. Граф одной публичной сцены позднее построен — см. дополнение ниже.

## Изменённые файлы и проверки

Обновлены `.gitignore`, README, Makefile, `docs/{dependencies,datasets,status,implementation_plan}.md`; подготовлены обзоры всех четырёх методов в `docs/methods/`, сравнение `docs/comparison.md`, инструкции/инвентари `environments/`, внешние metadata/configs `configs/`, простые scripts и перечисленные results. Предыдущие пользовательские шаблоны/изменения не сбрасывались; commit/push не выполнялись.

Проверки: `git submodule update --init --recursive`, `make doctor`, `make status`, shell syntax, локальные Markdown links, Makefile command expansion, `git diff --check`, `git diff --cached --check`, Git gitlinks/recursive submodules и чистота upstream. Отсутствие Conda в PATH ожидаемо: используется локальный prefix. Успех doctor отдельно не подтверждает методы; они проверены перечисленными реальными запусками.

Повторно проверены `make dualmap-gpu-check` и `make onemap-habitat-check`: оба exit 0. Полные GUI/навигационные запуски Этапа 2 повторно не выполнялись: их команды и результаты уже проверены; новые окружения изолированы. HOV-SG script выполнен реально, Makefile вызывает ту же команду. [Диагностика хоста](../results/doctor-stage3.txt).

**Следующий шаг:** для semantic metrics DualMap/HOV-SG подготовить согласованный Original Replica GT и проверить координаты/классы. Для VLFM выбрать поддерживаемый старым стеком GPU либо отдельно спланировать миграцию. Контролируемые ablations из [сравнения](comparison.md) не выполнялись. Текущая работа завершена на smoke pipelines, без полного benchmark и без изменения алгоритмов.


## Дополнение: подробный журнал развёртывания

По запросу пользователя добавлены [общая подготовка и четыре инструкции](deployment/README.md): команды окружений, данные/checkpoints, все параметры wrappers, последовательность ошибок и решений, результаты и неустранённые ограничения. Сохранённые команды отделены от восстановленных рецептов; неполнота исторических transfer URLs DualMap явно отмечена. Ссылки добавлены в README и каждый обзор метода.

При этой доработке менялась только документация. Повторные установки, загрузки и benchmark не запускались. Проверены ссылки, bash/Python-синтаксис примеров, соответствие копий wrappers действующим scripts и восстановленного Dockerfile.env сохранённому файлу. Статусы методов не изменились.


## Дополнение: визуальное демо HOV-SG

По отдельному запросу пользователя подготовлен рабочий `make hovsg-demo`: внешний GUI с 3D-картой, RGB/instance/similarity modes, текстовым полем, top-5, выбором сегмента, screenshot и camera reset. Query math и загрузка features взяты из upstream eval_utils; исходный HOV-SG не менялся. [Запуск и управление](hovsg-demo.md), [скриншоты и доказательства](../results/hovsg/visual-demo/README.md).

`make hovsg-build-demo` вызывает штатный Replica extraction на 20 кадрах по всей траектории room0: **399 663 точки, 156 сегментов, 308.66 с, exit 0**. Первый запуск упал с CUDA OOM на выделении 3.11 GiB; включение `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` позволило повтору завершиться. Новые данные/веса не скачивались, полный benchmark не выполнялся.

GUI реально открывался на X11/OpenGL, два прогона завершились exit 0. Проверены запросы sofa/pillow/lamp, выбор второго результата, режимы/ceiling/reset, изображения и закрытие. Интерфейс не имитирует этажи/комнаты: авторский create_graph.py явно пропускает иерархию для Replica. Semantic accuracy не измерена.

Добавлены scripts/hovsg-{build-demo.sh,demo.sh,demo.py}, docs/hovsg-demo.md, results/hovsg/visual-demo; обновлены Makefile, README, обзор и deployment HOV-SG, data/README.md и этот статус. Остальные методы не изменялись. Для наблюдения результатов следующий шаг — `make hovsg-demo`; отдельная настройка больше не нужна на текущем хосте.

## Дополнение: настоящий граф HOV-SG на HM3D example

По отдельному запросу пользователя построен штатный **HM3DSem graph**, без изменения upstream. Из уже скачанной сцены 00861-GLAQ4DNUx5U отрендерены 83 RGB-D кадра по каждой 50-й авторской позе (4137 poses). Habitat-Sim взят из существующего OneMap environment image, рендер без сети; новые зависимости/веса/данные не скачивались.

`application/create_graph.py`: **exit 0, 793.16 с, max RSS 16 942 056 KiB**. Параметры: 640×480/FOV90, voxel 0.05 м, SAM batch 8, skip_frames 1 по подготовленным 83 кадрам, остальные алгоритмы штатные. Результат: 400 693 точки; 694 mask embeddings; **2 этажа, 14 комнат, 683 object nodes**. Логическая иерархия с building-root: 700 узлов / 699 рёбер. Это сегменты, не 683 гарантированно целых физических объекта.

Навигационный граф: **1306 узлов / 1440 рёбер, 4 связные компоненты** (1140/148/14/4). Крупнейшая соединяет оба этажа одним межэтажным ребром; остальные участки изолированы. Проход агента, collision checking, graph accuracy и SR/SPL не проверялись. Ограничения зафиксированы, искусственные связи не добавлялись.

Авторский PyVista viewer реально открыт дважды, screenshot сохранён; exit 0. Внешний launcher задаёт только Y-up камеру. Непустые PLY, embeddings, parent links и компоненты проверены; `make doctor` exit 0, Makefile/shell/Python и локальные ссылки проверены. Upstream HOV-SG tracked/untracked чист. Другие методы не изменялись.

Команды: `make hovsg-graph-demo` — просмотр готового графа; `make hovsg-build-graph` — повтор построения; `make hovsg-render-hm3d` — однократный рендер (отказывается перезаписывать существующий набор). [Инструкция](hovsg-graph-demo.md), [результаты](../results/hovsg/graph-demo/README.md).

Добавлены scripts/hovsg-{render-hm3d.py,render-hm3d.sh,build-graph.sh,graph-demo.sh,graph-view.py}, docs/hovsg-graph-demo.md, results/hovsg/graph-demo; обновлены README, Makefile, docs/status, datasets, methods/hovsg, deployment/hovsg, comparison и ссылка из Replica demo. Следующий шаг для пользователя — просмотр графа; для исследования — оценка фрагментации и связности на фиксированных данных. Полный benchmark и API-запросы не запускались.

## Дополнение: научно-технический отчёт README

По запросу пользователя README переработан под тему «Устойчивое согласование объектных наблюдений в семантических картах для поиска по пространственным отношениям»: 11 разделов, сравнение четырёх методов, формальная кандидатная гипотеза, условия опровержения и план контролируемой проверки. Основная экспериментальная работа относится к DualMap/OneMap/HOV-SG; VLFM представлен подтверждённым GPU-блокером.

Добавлены четыре существующих скриншота и таблица подтверждений выполненных pipelines с прямыми ссылками на JSON, evaluator output и GUI checks. Числа сверены с сохранёнными результатами. Уточнено, что DualMap уже использует `on`, OneMap — неопределённость, HOV-SG — объединение сегментов; graph run имел `merge_objects_graph=false`. Дополнительный поиск выявил близкие работы OVIP-SG и TRACKGRAPH: новизна не заявлена установленной. Гипотеза пока не реализована и не проверена; наблюдения фрагментации не заменяют instance GT и контролируемый эксперимент.

В этой задаче менялись только README и этот статус. Новые эксперименты, установки, загрузки датасетов и изменение upstream не выполнялись. Проверены существование всех локальных ссылок/изображений, структура отчёта, команды через `make -n` и `git diff --check`. Следующий научный шаг — разметка, проверка штатных вариантов HOV-SG и калибровка предлагаемого свидетельства на данных, отделённых от теста.

## Дополнение: компактное мини-исследование и материалы README

README перестроен по цепочке «тема → методы → реальные запуски → наблюдаемая проблема → гипотеза → воспроизведение». Формальная модель перенесена в docs/research-proposal.md. Иллюстрации и компактные подтверждения README собраны в assets/ как точные копии существующих результатов; оригиналы results/, конфиги, скрипты и upstream сохранены без изменений. Причина отказа VLFM уточнена: старый PyTorch/CUDA wheel не поддерживает новый GPU, системный драйвер не устаревший.

Подготовлены отдельные списки файлов и команды коммитов вне репозитория; индекс Git, commits и push не изменялись. Промпты и шаблон обзора исключены из рекомендуемого набора; реальные результаты и инструкции сохранены. Проверены ссылки, идентичность assets исходникам, команды Makefile в dry-run и отсутствие крупных данных в предлагаемом составе. Новые эксперименты не запускались.

## Дополнение: проверка объединения объектов HOV-SG

По запросу пользователя фактически проверен `pipeline.merge_objects_graph=true` на карте тех же 83 кадров HM3D. Повторное извлечение SAM/CLIP не выполнялось; авторский `Graph.build_graph` загрузил сохранённые облака и признаки. Штатный запуск из директории проекта завершился exit 1: в `Room.merge_objects` отсутствует импорт `find_overlapping_ratio`. Первый диагностический вызов из корня также выявил зависимость от относительного пути labels CSV.

Во внешнем скрипте подключена существующая функция из `hovsg.utils.eval_utils`; алгоритм и upstream-файлы не менялись. Повтор построения завершился exit 0: **683 -> 611 сегментов**, 2 этажа и 14 комнат. Отдельный вызов того же объединения на неизменных объектах исходного графа дал также 611. Метка `couch`: 8 -> 6 сегментов. Проверены уникальность ID, родительские ссылки, непустые конечные облака и embeddings. Авторский viewer открыл сохранённый граф, скриншот и закрытие — exit 0. Навигационный граф сохранил четыре компоненты; навигация и instance accuracy не оценивались.

Обнаружена дополнительная особенность: итоговый stdout печатает старый `len(self.objects)=683`, тогда как сохранённый граф собирается из обновлённых `room.objects` и содержит 611 объектов. Для запросов по результату следует загрузить сохранённый граф заново. [Эксперимент, команды и подтверждения](../results/hovsg/merge-check/README.md).

Добавлен `make hovsg-graph-merged`, старый результат сохранён. README переписан с описанием методов, запущенных сценариев и содержания скриншотов. Гипотеза теперь учитывает проверенное штатное объединение; математическая постановка сокращена до решения по уверенности и проверяемого компромисса ошибок. В deployment-документах длинные команды разбиты на строки, копии скриптов заменены ссылками; HOV-SG инструкция приведена к текущим рабочим режимам.

Изменения: README, Makefile, docs/research-proposal.md, docs/deployment/{dualmap,onemap,hovsg,vlfm}.md, docs/hovsg-graph-demo.md, docs/methods/hovsg.md, docs/status.md, assets и results/hovsg/merge-check. Новых загрузок и установок не было. Commit/push не выполнялись. Следующий исследовательский шаг — разметка физических экземпляров и сравнение качества слияний и поиска; сам факт сокращения числа сегментов гипотезу не подтверждает.

Проверки этой доработки: повторное чтение сохранённого графа и сравнение геометрии (все 154 952 уникальные точки сохранены), настоящий GUI-прогон, локальные Markdown-ссылки, синтаксис команд и Python, раскрытие Makefile targets, `make status`, `git diff --check` и неизменность HOV-SG submodule. Списки файлов для будущих коммитов обновлены; крупных данных в них нет.

## Дополнение: ссылки README и состав коммита

По запросу пользователя из README убраны ссылки на отдельные технические обзоры. Краткие описания работ, демонстрации и инструкции запуска сохранены. Файлы обзоров не удалялись. Состав рекомендуемого коммита проверен через Git; явные команды добавления приведены в ответе, без файлов со списками. Индекс и commits не изменялись. Альтернативные исследовательские идеи обсуждаются отдельно; новая гипотеза пока не выбрана.

## Дополнение: обратная связь между картой и видеосегментацией

По запросу пользователя исследовательская проблема и гипотеза заменены в README. Там же описаны механизм повторной сегментации с подсказками из проекций карты, проверка видимости и глубины, защита от закрепления ошибок карты, ограничения и сравнение с простой фильтрацией. Обзоры методов, результаты и команды запуска сохранены. Отдельный файл прежней формализации `docs/research-proposal.md` удалён по прямому запросу; исторические упоминания выше относятся к предыдущей редакции.

Новый механизм не реализован, эксперименты не запускались. Следующий шаг — выбрать видеосегментатор и подготовить последовательность с разметкой экземпляров для контролируемого сравнения. Изменены только README и этот статус, удалён файл прежней постановки. Проверены локальные ссылки и сохранность остальных разделов README.
