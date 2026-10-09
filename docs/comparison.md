# Сопоставление методов

Методы решают разные задачи: общая таблица SR или mIoU для всех четырёх была бы некорректна. Подробности и первичные источники: [DualMap](methods/dualmap.md), [OneMap](methods/onemap.md), [VLFM](methods/vlfm.md), [HOV-SG](methods/hovsg.md). Фактические результаты — [status](status.md).

| Метод | Задача / представление | Вход → выход | Данные минимального сценария | Метрики / ограничения |
|---|---|---|---|---|
| DualMap | Open-vocabulary mapping; объекты и layout с MobileCLIP embeddings | Posed RGB-D → 3D map; текст + готовая карта → найденный объект | NICE-SLAM Replica; готовая авторская карта | mIoU/FmIoU/mAcc требуют отдельного semantic GT; cosine query score не accuracy |
| OneMap | Zero-shot ObjectNav; переиспользуемая dense feature/confidence map | Simulator RGB-D/pose + цель → путь/действия | Публичная HM3D 00861 с semantics, ObjectNav v2 | SR/SPL; короткие 3 эпизода с 200 шагами не benchmark статьи |
| VLFM | Zero-shot ObjectNav; occupancy + language-conditioned value map | RGB-D/pose + цель → frontier/PointNav actions | HM3D и согласованные ObjectNav episodes | SR/SPL; torch/cu113 и модельные серверы ограничивают перенос на Blackwell |
| HOV-SG | Open-vocabulary 3D map и иерархический building/floor/room/object graph | Posed RGB-D → feature clouds; graph mode → иерархия и query results | Replica RGB-D для extraction; HM3D example + авторские poses для графа; GT для оценки отдельно | mIoU/FmIoU/mAcc/pAcc; графовые метрики отдельно; память зависит от числа точек и dense 1024-D features |

Ни один сценарий не требует собственного SLAM: используются poses датасета или симулятора. Карты и embeddings разных моделей не взаимозаменяемы. Штатные Replica extraction/evaluation HOV-SG не требуют OpenAI API; иерархические языковые запросы — отдельный сценарий.

## Контролируемые эксперименты

Следующие сравнения **не выполнены**. Выполненные smoke tests подтверждают работоспособность отдельных режимов, но не являются ablation study.

1. **Плотность кадров в DualMap/HOV-SG.** Одинаковые исходные кадры room0, intrinsics, poses и веса; менять только stride. Сравнивать время, память и число объектов внутри каждого метода. mIoU сравнивать только после подготовки одного GT, одинаковой таблицы классов и области оценки.
2. **Переиспользование карты OneMap.** Фиксированные сцена, starts, цели и лимит; сравнить повторный поиск с сохранённой картой и после reset. Измерить шаги, длину пути, SR/SPL. Нужна проверка штатного multi-object режима; текущий single-object smoke этого эффекта не измеряет.
3. **Формулировка текстовой цели.** Для неизменной карты DualMap — синонимы/описания, top-1 UID и ручное соответствие. Для VLFM — те же starts/goals и набор формулировок, SR/SPL и frontiers; возможно только после устранения GPU-блокера. Сходство embeddings не считать навигационным успехом.
