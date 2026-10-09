# OneMap: проверка 2026-10-09

- Docker собран exit 0; воспроизведение внешнего Dockerfile из diff проверено `patch` + `cmp`; [image ID](image.json), [pip inventory](../../../environments/onemap-pip-freeze.txt), [внешние изменения окружения](docker-environment.diff).
- Публичный `hm3d_example`: выбрана `00861-GLAQ4DNUx5U`, [файлы](scene-inventory.json). Исходный demo жёстко задаёт другую сцену; [diff только двух путей](demo-scene-only.diff), [SHA исходника/копии](demo-source.json).
- Habitat-Sim GPU render и CUDA matmul: exit 0, navmesh загружен, 908 semantic objects. [JSON](habitat-smoke.json), [RGB](habitat-example-rgb.png). Проверенная команда `make onemap-habitat-check`.
- OneMap demo: 317 обновлений карты, среднее add_data 0.239 с, запрос A Couch. [Rerun](demo-rerun.png), [summary](demo-summary.json). Бесконечный цикл остановлен SIGINT (exit 130). Дополнительно проверен `ONEMAP_DEMO_SECONDS=30 make onemap-demo`: 65 обновлений, ожидаемый timeout 124 / make 2.
- [ObjectNav на 3 эпизодах](../objectnav-smoke/README.md): exit 0, 1 успех, 2 лимита шагов; SR 33.33%, SPL 27.33%. Не benchmark статьи.
- [Контрольные суммы авторских весов](image-weights.sha256); веса, датасеты и полные логи исключены из Git.

Устранены: конфликт torch 2.14.1 / Spock по setuptools, mesonpy для scikit-fmm, сетевой timeout SED, остановка gdown, отсутствие NVIDIA EGL vendor JSON, Xet download и запрет записи YOLOv7 traced_model.pt. [Первая точная ошибка resolver](build-conflict.txt), [оставшиеся metadata-конфликты](pip-check.txt). Алгоритмы не менялись.
