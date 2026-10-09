# OneMap — Docker, данные, запуски и ошибки

**Итог:** сборка exit 0, Habitat render, штатное demo на публичной сцене и короткий ObjectNav выполнены. SHA `897abb4ded745de2c23fe82a606e1ac0d5157089`. [Общие условия](README.md), [обзор](../methods/onemap.md).

## 1. Выбор окружения и последовательность исправлений

Основа — авторский Dockerfile: Ubuntu 22.04 / CUDA 12.8.1 cuDNN devel, Python 3.10. Он изолирует сборку Habitat/C++/EGL от хоста Ubuntu 24.04 и подходит RTX 50xx. Режим `HM3D=LOCAL`: сборка получает модели и episodes, но не лицензированные HM3D scenes. Загрузка сборки >5 GB согласована пользователем.

Последовательность попыток сохранена в `results/onemap/stage2/logs/docker-build*.log`:

1. Исходный Dockerfile выбрал torch 2.14.1; resolver остановился: torch требует setuptools>=77.0.3, Spock 3.1.0 — setuptools~=68.1. [Точная ошибка](../../results/onemap/stage2/build-conflict.txt).
2. Во внешней копии закреплены torch 2.9.0 / vision 0.24.0 / audio 2.9.0 с cu128, NumPy 1.26.4 и Rerun 0.22.1. Это также ограничило длительный перебор Rerun.
3. Для scikit-fmm/mesonpy добавлены meson-python, Cython, ninja, wheel и setuptools 68.2.2; requirements ставятся `--no-build-isolation`.
4. `timm>=1.0.7` заключён в кавычки: без них shell воспринимал `>` как redirect. Обновление оставляет конфликт с LAVIS — он не объявлен решённым.
5. Сетевой timeout SED устранён повтором. Зависший gdown CLIP заменён предварительной HTTP-загрузкой и `COPY --from=onemap_weights`.
6. Habitat-Sim 0.2.4 и planning_cpp собраны. Финальная сборка завершилась exit 0.

Все изменения окружения — в [сохранённом diff](../../results/onemap/stage2/docker-environment.diff), исходный Dockerfile и алгоритмы не менялись. Первый незакреплённый torch-слой оставлен для использования build cache: внутри образа остались лишние CUDA 13 библиотеки. Рабочий torch использует cu128; образ не оптимизирован по размеру.

## 2. Команды успешной сборки

Применять patch один раз к свежей копии Dockerfile. Повторять сборку уже имеющегося образа для запуска demo не нужно.

```bash
mkdir -p data/cache/onemap-build data/weights/onemap
cp third_party/OneMap/Dockerfile data/cache/onemap-build/Dockerfile
patch --forward data/cache/onemap-build/Dockerfile < results/onemap/stage2/docker-environment.diff
curl --http1.1 -fL --connect-timeout 20 --speed-time 60 --speed-limit 1024 -C - \
  'https://drive.usercontent.google.com/download?id=1D_RE4lvA-CiwrP75wsL8Iu1a6NrtrP9T&export=download&confirm=t' \
  -o data/weights/onemap/clip.pth

docker build --progress=plain \
  --build-arg HM3D=LOCAL \
  --build-arg HM3D_PATH=/datasets \
  --build-context onemap_weights=./data/weights/onemap \
  --file data/cache/onemap-build/Dockerfile \
  --tag be2r-onemap:897abb4 \
  third_party/OneMap
```

Образ `be2r-onemap:897abb4`, ID `sha256:3f5a665b91e2f6a82be89f22d5f1a981c879ca7895dbb73ff2f88ee81f2c6934`. [Base digest и результат](../../results/onemap/stage2/image.json), [все pip версии](../../environments/onemap-pip-freeze.txt), [SHA весов внутри image](../../results/onemap/stage2/image-weights.sha256).

Отдельно собран `be2r-onemap-env:897abb4` — тот же рецепт, обрезанный до клонирования YOLOv7. Он используется для проверки Habitat и рендера входных кадров HOV-SG. Нормализованный рецепт восстановления этой промежуточной сборки (внешний файл сравнен с сохранённым; Docker build при написании документации повторно не выполнялся):

```bash
python3 - <<'PYENV'
from pathlib import Path
p = Path('data/cache/onemap-build/Dockerfile')
s = p.read_text().split('RUN git clone https://github.com/WongKinYiu/yolov7', 1)[0]
Path('data/cache/onemap-build/Dockerfile.env').write_text(s + '\nCMD ["python3"]\n')
PYENV
docker build --progress=plain \
  --build-arg HM3D=LOCAL \
  --build-arg HM3D_PATH=/datasets \
  --file data/cache/onemap-build/Dockerfile.env \
  --tag be2r-onemap-env:897abb4 \
  third_party/OneMap
```

## 3. Получение публичной сцены вместо закрытой авторской

Авторское demo фиксирует `00853-5cdEh9F2hJL`. Локального HM3D у пользователя не было; официальный полный HM3D перенаправлял на Matterport login. По указанию пользователя использован `hm3d_example`; credentials не вводились.

Habitat-Sim на хосте не был установлен. Вместо `python -m habitat_sim.utils.datasets_download` использован **тот же официальный standalone downloader v0.2.4** в `/tmp/habitat-datasets-download.py`. Нормализованные команды этой процедуры (новая загрузка здесь не выполнялась):

```bash
curl -fL \
  https://raw.githubusercontent.com/facebookresearch/habitat-sim/v0.2.4/src_python/habitat_sim/utils/datasets_download.py \
  -o /tmp/habitat-datasets-download.py
python3 /tmp/habitat-datasets-download.py \
  --uids hm3d_example \
  --data-path "$PWD/data/datasets/onemap-hm3d-example"
sha256sum -c results/onemap/stage2/downloader.sha256
```

Получены сцены 00337, 00770 и **00861-GLAQ4DNUx5U** (~215 MB); последняя содержит semantics. Корень: `data/datasets/onemap-hm3d-example/versioned_data/hm3d-0.2/hm3d`. Demo использует `example/hm3d_annotated_example_basis.scene_dataset_config.json`. [Инвентарь](../../results/onemap/stage2/scene-inventory.json), локальный лог `hm3d-example-download.log`.

## 4. GPU/EGL и минимальный render

Первый GPU render не нашёл CUDA EGL device. NVIDIA-библиотеки были в контейнере, отсутствовал vendor JSON. Решение: read-only bind `/usr/share/glvnd/egl_vendor.d/10_nvidia.json` и `NVIDIA_DRIVER_CAPABILITIES=all`, без изменения драйвера/системы.

```bash
make onemap-habitat-check
```

Все параметры запуска заданы в [scripts/onemap-habitat-check.sh](../../scripts/onemap-habitat-check.sh).

Python-проверка — [scripts/onemap-habitat-check.py](../../scripts/onemap-habitat-check.py). Exit 0: RGB-D 640×480, navmesh, 908 semantic objects, конечный CUDA matmul. [JSON](../../results/onemap/stage2/habitat-smoke.json). Это проверка симулятора, не demo OneMap.

## 5. Demo: сцена, caches и команды

Сгенерирована внешняя копия `habitat_test.py` с **двумя заменами путей**; никакой логики алгоритма не изменялось. [Diff](../../results/onemap/stage2/demo-scene-only.diff). При первом запуске получены дополнительный pretrained ConvNeXt и Roboflow CLIP/YOLO ONNX assets. Xet зависал: выставлен `HF_HUB_DISABLE_XET=1`, обычный HTTP прошёл. Кеши сохранены в `data/cache/onemap/{huggingface,inference}`.

В разных терминалах:

```bash
make onemap-viewer
```

Во втором терминале:

```bash
make onemap-demo
```

Viewer — `.local/envs/dualmap/bin/rerun`, версия 0.22 согласована с SDK контейнера. Demo использует host network для связи с viewer. Все параметры запуска заданы в [scripts/onemap-demo.sh](../../scripts/onemap-demo.sh).

Получено 317 обновлений карты, запрос `A Couch`, mean add_data 0.239 с. Ctrl+C/SIGINT дал 130: upstream loop бесконечный. Дополнительно проверялось `ONEMAP_DEMO_SECONDS=30 make onemap-demo`: 65 обновлений, timeout 124 / make 2 — ожидаемая остановка, не crash. [Скриншот/summary](../../results/onemap/stage2/README.md).

## 6. Подготовка трёх ObjectNav эпизодов

Сцена имеет официальные **v2** episodes. Из image извлечены первые 3 из 28, starts/goals не менялись; исходные IDs 3/0/2, loader переименовывает их в 0/1/2. Выполненная подготовка:

```bash
mkdir -p data/cache/onemap data/datasets/onemap-objectnav-smoke
docker run --rm --network none --entrypoint cat be2r-onemap:897abb4 \
  /onemap/datasets/objectnav_hm3d_v2/val/content/GLAQ4DNUx5U.json.gz \
  > data/cache/onemap/GLAQ4DNUx5U.original.json.gz
python3 - <<'PY'
import gzip, json
from pathlib import Path
src = Path('data/cache/onemap/GLAQ4DNUx5U.original.json.gz')
data = json.loads(gzip.decompress(src.read_bytes()))
data['episodes'] = data['episodes'][:3]
with gzip.open('data/datasets/onemap-objectnav-smoke/GLAQ4DNUx5U.json.gz', 'wt') as f:
    json.dump(data, f)
PY
```

Внешний [eval-smoke.yaml](../../configs/onemap/eval-smoke.yaml): `multi_object=false`, `max_steps=200`, `max_dist=1.0`, `object_nav_path=/episodes/`, `scene_path=datasets/scene_datasets/`, `log_rerun=false`, `use_pointnav=false`, `square_im=true`. Остальные controller/mapping/planning configs штатные. Детектор eval — YOLOv7 (`using_ov=false`); demo создаёт YOLO-World напрямую.

Scene config и mounts сохраняют исходные episode IDs `hm3d_v0.2/val/...`, подключая тот же public example mesh. [Внешний scene JSON](../../configs/onemap/hm3d-example-eval.scene_dataset_config.json).

## 7. Короткая evaluation

```bash
make onemap-eval-smoke
```

Первый запуск упал при записи `traced_model.pt` авторским YOLOv7 tracer. Добавлен writable bind конкретного cache-файла; остальные scene/config mounts read-only. Все параметры запуска заданы в [scripts/onemap-eval-smoke.sh](../../scripts/onemap-eval-smoke.sh).

Штатный `read_results.py` затем прочитал output и сообщил SR/SPL. Нормализованная команда чтения **сохранённых** результатов (эквивалент выполненного чтения; не запускает новые эпизоды):

```bash
docker run --rm --network none --entrypoint python3 \
  -v "$PWD/results/onemap/objectnav-smoke:/onemap/results:ro" \
  -v "$PWD/configs/onemap/eval-smoke.yaml:/onemap/config/mon/eval_smoke.yaml:ro" \
  be2r-onemap:897abb4 \
  read_results.py --config config/mon/eval_smoke.yaml
```

Toilet/sofa: FAILURE_OOT на 200 шагах; bed: SUCCESS на 154. Evaluator/reader exit 0, **SR 33.33%, SPL 27.33%**. [Результаты](../../results/onemap/objectnav-smoke/README.md). Не paper benchmark: другая сцена, v2 episodes, короткий лимит, текущий main вместо рекомендованной paper-ветки.

## 8. Нерешённые ограничения и журналы

- `pip check`: LAVIS требует timm 0.4.12 при фактическом 1.0.30; decord 0.6.0 unsupported platform. [Вывод](../../results/onemap/stage2/pip-check.txt). Demo/eval проходят, BLIP2/video modes не проверялись.
- Matterport доступ к остальным HM3D сценам не подготовлен; полный dataset не получен.
- Image содержит лишний исходный torch/CUDA слой, clean rebuild может выбрать новые версии плавающих зависимостей. Сохранённый image ID/inventory точнее одного Docker tag.
- Локальные логи: `results/onemap/stage2/logs/`: `docker-build.log`, `docker-build-pinned.log`, `docker-build-meson.log`, `docker-build-local-clip.log`, `habitat-smoke.log`, `habitat-smoke-egl.log`, `demo-example.log`, `demo-example-http.log`, `objectnav-smoke.log`, `objectnav-smoke-writable.log`. Они игнорируются Git; ключевые errors/diff/metrics сохранены отдельно.
