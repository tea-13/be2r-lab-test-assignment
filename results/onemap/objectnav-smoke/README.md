# Короткий ObjectNav, 2026-10-09

Штатный `eval_habitat.py`, main SHA `897abb4`, `HM3D ObjectNav v2`, сцена `00861-GLAQ4DNUx5U`. Взяты первые 3 из 28 официальных эпизодов, без изменения start/goal; [manifest и SHA источника](episodes.json). Loader перенумеровывает их в 0/1/2; соответствие исходным IDs сохранено в [summary](summary.json).

| Цель | Шаги | Результат |
|---|---:|---|
| toilet | 200 | FAILURE_OOT |
| sofa | 200 | FAILURE_OOT |
| bed | 154 | SUCCESS |

Exit 0. Штатный `read_results.py`: **SR 33.33%, Average SPL 27.33%** ([вывод](read-results.txt)). Ограничение 200 шагов и три эпизода предназначены для проверки исполнения; результат не сопоставим с paper benchmark. Детектор — штатный YOLOv7, `using_ov: false`. Сохранены [config](config.yaml), `state/`, `trajectories/`, `similarities/`.

Повтор: `make onemap-eval-smoke`; новый output каждый раз в `results/onemap/objectnav-*/raw`.

Подготовка локального subset из уже собранного образа (выполнена):

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

В `configs/onemap` меняются только лимит шагов, путь episodes и пути scene dataset config. Mounts позволяют сохранить исходные episode scene IDs `hm3d_v0.2/val/...`, используя тот же mesh из публичного example. Writable mount `traced_model.pt` нужен авторскому YOLOv7 tracer. Полный HM3D не загружался.
