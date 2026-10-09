# OneMap: выполненная установка (2026-10-09)

Собран локальный `be2r-onemap:897abb4`, [image ID](../results/onemap/stage2/image.json), [pip inventory](onemap-pip-freeze.txt). Основа — авторский Dockerfile; [внешний diff](../results/onemap/stage2/docker-environment.diff) фиксирует необходимые изменения окружения. Исходники метода не редактировались. Это inventory успешной сборки, не гарантия работоспособности всех режимов; [статус запусков](../docs/methods/onemap.md).

Причины изменений: конфликт torch 2.14.1/setuptools со Spock 3.1.0; длительный перебор Rerun; отсутствующий mesonpy для scikit-fmm; зависание gdown на CLIP. Выбраны torch 2.9.0+cu128, torchvision 0.24.0, torchaudio 2.9.0, NumPy 1.26.4, Rerun 0.22.1, setuptools 68.2.2. Сохранился авторский конфликт LAVIS/timm после отдельного обновления timm; `pip check` также отмечает decord unsupported platform. [Вывод](../results/onemap/stage2/pip-check.txt). Проверенные режимы проходят. Первый незакреплённый torch-слой оставлен ради кеша уже выполненной сборки; образ содержит лишние CUDA 13 пакеты, поэтому не является минимальным по размеру.

Подготовка внешней копии: скопировать `third_party/OneMap/Dockerfile` в `data/cache/onemap-build/Dockerfile` и применить указанный diff только к копии. CLIP в `data/weights/onemap/clip.pth` получен командой (при прерывании повторить с тем же `-C -`):

```bash
mkdir -p data/cache/onemap-build data/weights/onemap
cp third_party/OneMap/Dockerfile data/cache/onemap-build/Dockerfile
patch --forward data/cache/onemap-build/Dockerfile < results/onemap/stage2/docker-environment.diff
curl --http1.1 -fL --connect-timeout 20 --speed-time 60 --speed-limit 1024 -C - \
  'https://drive.usercontent.google.com/download?id=1D_RE4lvA-CiwrP75wsL8Iu1a6NrtrP9T&export=download&confirm=t' \
  -o data/weights/onemap/clip.pth

docker build --progress=plain --build-arg HM3D=LOCAL --build-arg HM3D_PATH=/datasets \
  --build-context onemap_weights=./data/weights/onemap \
  -f data/cache/onemap-build/Dockerfile -t be2r-onemap:897abb4 third_party/OneMap
```

Эта build-команда завершилась exit 0. BuildKit нужен для cache mount и дополнительного контекста. Сборка скачивает больше 5 GB; согласие пользователя получено. Сцены HM3D она не скачивает. Author weights/episodes находятся внутри образа; CLIP дополнительно сохранён снаружи для возобновления загрузок.

Отдельный `be2r-onemap-env:897abb4` экспортирован из того же Dockerfile, обрезанного перед `RUN git clone https://github.com/WongKinYiu/yolov7`, с `CMD ["python3"]`. Он содержит Habitat-Sim 0.2.4 и используется проверенной целью `make onemap-habitat-check`. Для EGL требуется host-файл `/usr/share/glvnd/egl_vendor.d/10_nvidia.json` (read-only bind в скрипте). Изменения системного CUDA/драйвера не делались.
