# HOV-SG: установка и запуск

Проверены карта Replica с текстовым поиском и иерархический граф HM3D. Используется commit `d6e65a53c8be6faec3f01f00d1644d967f89e605`. Команды ниже выполняются из корня репозитория. Сначала требуется [общая подготовка](README.md).

## 1. Создать окружение

Установить авторское Conda-окружение, затем сам пакет:

```bash
.local/miniforge/bin/conda env create \
  --prefix "$PWD/.local/envs/hovsg" \
  --file third_party/HOV-SG/environment.yaml

.local/envs/hovsg/bin/python -m pip install \
  --no-deps \
  --editable third_party/HOV-SG

.local/envs/hovsg/bin/python -m pip check
```

Получены Python 3.9.25, PyTorch 2.8.0/CUDA 12.8, torchvision 0.23.0, NumPy 1.26.4 и Open3D 0.18.0. YAML не менялся. [Conda-пакеты](../../environments/hovsg-conda-explicit.txt), [Python-пакеты](../../environments/hovsg-pip-freeze.txt).

## 2. Скачать веса

OpenCLIP ViT-H и SAM ViT-H занимают вместе 6.51 GB. На подготовленном компьютере они уже скачаны и проверены.

```bash
mkdir -p data/weights/hovsg

curl --http1.1 --fail --location --continue-at - \
  --connect-timeout 20 --speed-time 60 --speed-limit 1024 --retry 3 \
  'https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K/resolve/main/open_clip_pytorch_model.bin' \
  --output data/weights/hovsg/laion2b_s32b_b79k.bin

curl --http1.1 --fail --location --continue-at - \
  --connect-timeout 20 --speed-time 60 --speed-limit 1024 --retry 3 \
  'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth' \
  --output data/weights/hovsg/sam_vit_h_4b8939.pth

sha256sum -c results/hovsg/stage3/weights.sha256
```

[Источники, размеры и контрольные суммы](../../results/hovsg/stage3/weights.json). Установлен SAM первой версии.

## 3. Построить и посмотреть карту Replica

Нужна NICE-SLAM Replica `room0`: RGB, depth, `traj.txt` и `cam_params.json`. [Подготовка данных](dualmap.md). Полная сцена расположена в `data/datasets/replica-nice-slam/Replica`.

Построение карты по 20 кадрам через каждые 100 кадров исходной траектории:

```bash
make hovsg-build-demo
```

Просмотр сохранённой карты:

```bash
make hovsg-demo
```

Вводите текст в поле запроса, выбирайте результат из списка, переключайте RGB, цвета сегментов и сходство с запросом. [Управление](../hovsg-demo.md).

Авторское извлечение признаков завершилось за 308.66 с; получены 156 сегментов. Поиск проверен на `sofa`, `pillow`, `lamp`. Для этой карты используется внешний GUI со штатной функцией `eval_utils.text_prompt`. [Результаты](../../results/hovsg/visual-demo/README.md).

Параметры построения находятся в [hovsg-build-demo.sh](../../scripts/hovsg-build-demo.sh). Ранний запуск на трёх кадрах также сохранён: [конфигурация](../../results/hovsg/stage3/replica-config.yaml), [результат](../../results/hovsg/stage3/replica-summary.json). Режим Replica в авторском приложении не создаёт этажи и комнаты.

## 4. Построить граф HM3D

Нужны публичная сцена `00861-GLAQ4DNUx5U` и образ `be2r-onemap-env:897abb4` из [установки OneMap](onemap.md). Habitat используется из Docker; устанавливать его в Conda HOV-SG не требуется.

Однократно подготовить 83 RGB-D кадра по авторским позам:

```bash
make hovsg-render-hm3d
```

Команда отказывается перезаписывать уже подготовленные данные. Затем построить и открыть граф:

```bash
make hovsg-build-graph
make hovsg-graph-demo
```

В исходном запуске использованы voxel 0.05 м, SAM batch 8 и все подготовленные кадры. Построение заняло 13 мин 13 с. [Полная конфигурация](../../results/hovsg/graph-demo/build-config.yaml), [результаты](../../results/hovsg/graph-demo/README.md), [описание графа](../hovsg-graph-demo.md).

## 5. Дополнительное объединение объектов

Отдельно проверено `pipeline.merge_objects_graph=true` на той же сохранённой карте. Штатный код упал из-за отсутствующего импорта `find_overlapping_ratio`. Во внешнем скрипте подключена функция из самого HOV-SG; алгоритм и файлы submodule не менялись.

Повтор завершился успешно: **683 -> 611 сегментов**. Сохранённый граф и его viewer проверены. Открыть результат:

```bash
make hovsg-graph-merged
```

[Команда повторного построения, сравнение и traceback](../../results/hovsg/merge-check/README.md). Объединение применяется только к одинаково названным пересекающимся сегментам одной комнаты. Уменьшение их числа не является измерением точности физических экземпляров.

## Ошибки и решения

| Проблема | Решение или ограничение |
|---|---|
| CUDA OOM на карте из 20 кадров | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`; повтор прошёл. SAM batch уменьшен до 8 |
| Относительный путь к labels CSV | Запускать авторский код из `third_party/HOV-SG`; рабочие скрипты делают это сами |
| `NameError` при дополнительном объединении | Внешний импорт авторской функции; исходный и исправленный запуски сохранены раздельно |
| После объединения лог показывает старое число объектов | Проверять сохранённые JSON; `self.objects` в памяти не обновляется вместе с `room.objects` |
| Неправильная вертикаль в viewer | Внешний launcher задаёт Y-up, как в Habitat |
| TkAgg требует графическую сессию | Запуски проверены с X11; `MPLCONFIGDIR` вынесен в локальный кеш |
| Два пакета OpenCV в авторском YAML | Runtime работает; пакетная конфигурация сохранена и указана в инвентаре |
| Нет Original Replica semantic GT | mIoU не вычислялся. NICE-SLAM RGB-D не заменяет semantic mesh |

Проверены CUDA, импорт Graph и используемый CPU FAISS IndexFlatL2: [вывод](../../results/hovsg/stage3/import-gpu-check.txt). Навигационный граф HM3D имеет четыре компоненты; движение агента по нему не оценивалось. [Обзор метода и метрики](../methods/hovsg.md).
