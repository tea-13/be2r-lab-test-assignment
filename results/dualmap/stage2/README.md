# DualMap: проверка 8–9 октября 2026

- Conda Python 3.10.22, PyTorch 2.9.0+cu128, torchvision 0.24.0+cu128, FAISS 1.9.0; [CUDA smoke](gpu-smoke.json).
- Штатный `applications.offline_local_map_query`: загружен 41 объект Replica room0, GUI Open3D работает, запросы выполнены через F и terminal input, выход через Q; exit 0.
- [Результаты запросов](query-results.json): chair → chair, 0.592; sofa → sofa, 0.612. Cosine similarity не является accuracy.
- [Скриншот карты](offline-query.png), [chair](query-chair.png), [sofa с корректными метаданными](query-sofa-corrected.png).
- Исходная карта содержит Replica class IDs. С текущим upstream gpt_indoor_general.txt были неверные текстовые подписи kettle/blanket. Внешний словарь `configs/dualmap/metadata` исправляет только расшифровку IDs, embeddings и алгоритм не менялись.
- Open3D предупреждает о несовпадении размера окна с сохранённым viewpoint: карта видна, запросы работают, точный авторский ракурс не воспроизведён.
- [30 кадров Dataset Mode](../replica-30frames/summary.json): exit 0, 23 объекта, layout, CSV времени. Первые 30 RGB-D кадров и poses взяты из официального NICE-SLAM Replica.zip через HTTP Range; [состав](replica-subset.json). Это smoke test, не оценка полной сцены.
- Первоначальный запуск с 3 keyframes (stride=10) завершился, но после штатной фильтрации не сохранил объектов; переход на 30 keyframes устранил это без изменения порогов.
- [SHA256 карты и checkpoint](assets.sha256). Полные логи находятся локально в игнорируемом `logs/`, карты/бинарники — в `raw/` и `data/`.

- [Вся траектория room0, stride 10](../replica-room0/summary.json): 200/200 кадров, exit 0; 58 объектов и layout; среднее 0.7921 с/кадр, P90 1.1714. [Конфиг](../replica-room0/config.yaml), [CSV](../replica-room0/system_time.csv). Это построение карты на полной траектории с прореживанием, не semantic benchmark. Полный архив скачан, [SHA256/CRC](replica-archive.json).
