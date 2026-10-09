# Данные и веса

`datasets/`, `weights/`, `cache/` исключены из Git. На текущем хосте здесь уже находятся Replica room0, HM3D example, ObjectNav subset, готовая карта DualMap и веса методов.
Версии, форматы, доступ и ограничения: [docs/datasets.md](../docs/datasets.md).
Подключать через конфиги, symlinks или read-only bind mounts; исходники upstream не менять.
Одинаковое название датасета не гарантирует совместимость подготовки.

`cache/hovsg/demo-map.txt` после успешного построения указывает на локальную карту для [визуального демо HOV-SG](../docs/hovsg-demo.md). Большие PLY/PT карты находятся в `results/hovsg/*/raw/`, а не в Git.
