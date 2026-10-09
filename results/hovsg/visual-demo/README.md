# HOV-SG — визуальная карта и интерактивный поиск

2026-10-09. Upstream SHA `d6e65a53c8be6faec3f01f00d1644d967f89e605`, алгоритмы не изменены. Внешний Open3D GUI использует штатные `load_feature_map` и `text_prompt(..., templates=True)`.

## Карта

20 кадров 0,100,…,1900 из уже скачанной Replica room0, исходные poses/intrinsics, SAM batch 8, штатный extraction. **399 663 точки, 156 сегментов, features [156,1024], finite, exit 0**. Время **308.66 с**, max RSS **12 941 944 KiB**. [Summary](build-summary.json), [Hydra config](build-config.yaml).

Первый запуск завершился CUDA OOM на normalize dense pixel features (3.11 GiB allocation). [Ошибка](build-first-error.txt). Повтор с `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` прошёл; веса/исходники/алгоритм не менялись. Сырые PLY/PT остаются вне Git; точный путь в summary и локальном `data/cache/hovsg/demo-map.txt`.

## Проверенный GUI

```bash
make hovsg-demo
```

[Полная инструкция управления](../../../docs/hovsg-demo.md). `make hovsg-build-demo` повторяет построение в новый output; для просмотра уже подготовленной карты это не нужно.

Выполнены два автоматических GUI-прогона на реальном X11/OpenGL: первый выявил слабую читаемость сплошного серого фона, после улучшения GUI повторно прошёл exit 0. Проверялись RGB, цветные сегменты, similarity heatmap, selected object, три запроса, выбор второго результата, отключение ceiling filter, reset camera, screenshots и закрытие. Это проверки настоящего окна и функций его callbacks; не benchmark и не ручная проверка всех возможных мышиных жестов. [Вывод](gui-check.txt), [query JSON](queries.json).

| Запрос | Top-1 segment ID | Cosine similarity |
|---|---|---|
| sofa | 154 | 0.3375 |
| pillow | 60 | 0.3572 |
| lamp | 105 | 0.3431 |

ID соответствует файлу `objects/pcd_<id>.ply`; категории GT не присваивались. Score не вероятность и не измерение accuracy. Наличие top-1 для любого текста не гарантирует присутствия предмета в сцене.

## Скриншоты

- [Окно с поиском и панелью управления](window.png).
- [RGB-карта](rgb.png), [цветные сегменты](instances.png).
- [Sofa](query-sofa.png), [pillow](query-pillow.png), [lamp](query-lamp.png).
- [Similarity heatmap](similarity.png), [потолок без display filter](ceiling-visible.png).

Иерархический graph не создавался: upstream прямо пропускает его для Replica/ScanNet. Демо показывает реальные feature-map segments и штатную оценку запросов; OpenAI API не вызывается. Нет GT, mIoU и полной оценки сцены.
