# Журнал развёртывания четырёх проектов

Состояние на 2026-10-09. Инструкции собраны по сохранённым scripts, конфигам, inventory и логам работ 8–9 октября. Это последовательность существенных шагов, включая неудачные попытки, а не полный terminal transcript: часть одноразовых shell-команд не сохранилась. Восстановленные рецепты обозначены отдельно; они не выдаются за повторно выполненные загрузки/сборки.

| Проект | Пошаговая инструкция | Итог |
|---|---|---|
| DualMap | [Установка, assets, Query, Replica и ошибки](dualmap.md) | Query и Dataset Mode работают |
| OneMap | [Docker, данные, demo, evaluation и ошибки](onemap.md) | Demo и 3 ObjectNav эпизода работают |
| VLFM | [Conda, проверка CUDA, причина остановки](vlfm.md) | Частичная установка; GPU blocked |
| HOV-SG | [Conda, checkpoint, Replica extraction и ограничения](hovsg.md) | Три кадра обработаны; semantic GT нет |

## 1. Условия хоста

Ubuntu 24.04.3 x86_64, Ryzen 7 7700, 30 GiB RAM, RTX 5060 Ti 16 GB (sm_120), NVIDIA driver 580.178.04. Docker 28.5.1 / Compose 2.40.1, uv 0.9.17, X11 DISPLAY=:1. Системный nvcc 12.0 не обновлялся; CUDA runtime приходит с PyTorch/контейнером. [Исходный аудит](../dependencies.md), [фактическая диагностика](../../results/doctor-stage3.txt).

Все команды ниже и в четырёх инструкциях запускаются **из корня workspace**, если явно не указано иное. Для существующего рабочего окружения переходите к запуску: повторное создание prefix или повторное применение patch не является необходимым шагом. Установка пакетов разрешена внутри изолированных сред; загрузки >5 GB, полный benchmark и системные изменения согласуются по AGENTS.md. В этой сессии согласованы Replica.zip, OneMap build и оба HOV-SG checkpoint.

## 2. Исходники и закрепление SHA

Четыре репозитория добавлены как gitlinks в `third_party/`, nested MobileCLIP инициализирован. [SHA всех checkout](../dependencies.md). Commit родительского репозитория и push не выполнялись. Для уже подготовленного workspace:

```bash
make submodules
git submodule status --recursive
git submodule update --init --recursive
make doctor
make status
```

`make submodules` исполняет [scripts/submodules.sh](../../scripts/submodules.sh): обычный update/init, затем локальный URL MobileCLIP заменяется на HTTPS и выполняется recursive update. Это устраняет требование SSH-ключа; upstream `.gitmodules` не меняется. Не использовать `--remote`: он меняет закреплённую версию.

## 3. Локальный Miniforge (DualMap, VLFM, HOV-SG)

Один установщик, отдельный prefix для каждого проекта. Команды выполненной установки; `mkdir` приведён явно как предварительное условие:

```bash
mkdir -p data/cache/installers
curl -fL https://github.com/conda-forge/miniforge/releases/download/26.7.2-0/Miniforge3-Linux-x86_64.sh -o data/cache/installers/Miniforge3-Linux-x86_64.sh
bash data/cache/installers/Miniforge3-Linux-x86_64.sh -b -p "$PWD/.local/miniforge"
```

После прерывания bootstrap применялся `-u` к этому же установщику/prefix. Conda не добавлялась в shell startup, системный Python не менялся. Отсутствие `conda` в PATH ожидаемо: используется `.local/miniforge/bin/conda`. Доступ к GPU/Docker/сети внутри песочницы был ограничен; проверки повторялись с разрешённым доступом к хосту. Это не устранялось переустановкой драйверов или `sudo`.

## 4. Что хранится где

- `third_party/` — исходники без правок алгоритмов.
- `.local/envs/{dualmap,vlfm,hovsg}` — Conda prefixes; OneMap — два Docker image.
- `data/{datasets,weights,cache}` — данные/веса/кеш, исключены из Git.
- `configs/` — внешние overrides/metadata; `.env.example` справочная и автоматически не подхватывается upstream.
- `results/` — summaries/configs/метрики/скриншоты; большие карты в игнорируемых `raw/`, полные локальные журналы в `logs/`.
- `environments/*-conda-explicit.txt` и `*-pip-freeze.txt` — фактический inventory, не универсальный lockfile. Некоторые freeze entries содержат локальные Conda build URLs.

## 5. Итоговые проверки

Выполнены recursive Git update, `make doctor`, `make status`, проверки shell syntax, local Markdown links, Makefile command expansion, `git diff --check` и `git diff --cached --check`. Все checkout, включая nested MobileCLIP, чисты. GPU checks DualMap и Habitat OneMap повторно прошли на Этапе 3. Новое составление этих инструкций не означает повторной установки или повторного benchmark.

Полные параметры запуска приведены в соответствующих scripts и ниже в инструкциях. [Технические обзоры](../comparison.md) объясняют методы; [status](../status.md) фиксирует границы фактически выполненных экспериментов.
