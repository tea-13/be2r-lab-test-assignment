# HOV-SG: Replica feature-map smoke test

2026-10-09, upstream `d6e65a53c8be6faec3f01f00d1644d967f89e605`, RTX 5060 Ti 16 GB. **INSTALLED / SMOKE_TESTED**. Штатный `application/semantic_segmentation.py` завершился **exit 0**, без правки исходников.

- Вход: первые 30 настоящих RGB-D кадров Replica room0 и предоставленные poses; `skip_frames=10` обрабатывает **0, 10, 20**. [Происхождение subset](../../dualmap/stage2/README.md).
- SAM ViT-H + OpenCLIP ViT-H-14; `points_per_batch=8` вместо 144 для ограничения памяти, `points_per_side=12` сохранён.
- Выход: **79 030 точек**, **30 сохранённых объектов**, full features `[79030,1024]`, mask features `[30,1024]`. Все значения finite; у **3588 точек признаки нулевые**. Это проверка файлов/вычислений, не semantic accuracy.
- Wall time **39.94 с**, max RSS **12 583 936 KiB** (~12 GiB); VRAM peak не измерялся. После fusion было 31 маска, штатная очистка перед сохранением оставила 30.
- Сырые PLY/PT (~326 MiB) остаются локально в `results/hovsg/replica-20261009-015744-1071525/raw/replica` и игнорируются Git.

[Summary](replica-summary.json), [полный Hydra config](replica-config.yaml), [вывод процесса и time](replica-output.txt), [проверка импортов/GPU/FAISS](import-gpu-check.txt), [pip check](pip-check.txt), [веса и размеры](weights.json), [SHA256](weights.sha256).

## Воспроизведение

[Установка](../../../environments/stage3.md), затем из корня workspace:

```bash
make hovsg-replica-smoke
```

Target вызывает проверенный `scripts/hovsg-replica-smoke.sh`, каждый раз создаёт новый каталог вывода. Нужны готовый 30-кадровый subset, оба checkpoint и рабочий X11 `DISPLAY`: upstream `navigation_graph.py` при импорте принудительно выбирает TkAgg даже для extraction. Headless режим не проверен.

## Evaluation

Imports и Hydra overrides штатного evaluator проверены через **`--cfg job`**, exit 0; [разрешённый конфиг](eval-config-check.yaml). Сам evaluator с GT **не выполнялся**: нужны Original Replica `room_0/habitat/info_semantic.json` и `mesh_semantic.ply`. NICE-SLAM RGB-D их не содержит. Перед оценкой необходимо проверить соответствие room0 ↔ room_0 и координат.

Проверенная команда разбора конфига из корня workspace (не запускает оценку):

```bash
MPLCONFIGDIR="$PWD/data/cache/hovsg/matplotlib" .local/envs/hovsg/bin/python \
  third_party/HOV-SG/application/eval/evaluate_sem_seg.py --cfg job \
  main.dataset=replica main.scene_name=room_0 \
  "main.feature_map_path=$PWD/results/hovsg/replica-20261009-015744-1071525/raw/replica" \
  "main.replica_dataset_gt_path=$PWD/data/datasets/replica-original-v1" \
  "main.replica_color_map=$PWD/third_party/HOV-SG/hovsg/labels/class_id_colors.json" \
  "models.clip.checkpoint=$PWD/data/weights/hovsg/laion2b_s32b_b79k.bin"
```

mIoU/FmIoU/mAcc/pAcc отсутствуют. Иерархический HM3DSem graph, OpenAI queries и полный benchmark не запускались. Нельзя интерпретировать этот трёхкадровый запуск как воспроизведение результатов статьи.
