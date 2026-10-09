"""Rebuild the hierarchy from the saved upstream feature map."""
from pathlib import Path
import sys
import os
from datetime import datetime
from omegaconf import OmegaConf
from hovsg.graph.graph import Graph

root = Path(__file__).resolve().parents[3]
cfg = OmegaConf.load(root / 'results/hovsg/graph-demo/build-config.yaml')
source = Path(cfg.main.save_path) / cfg.main.dataset / cfg.main.scene_id
provide_import = '--provide-missing-import' in sys.argv
if provide_import:
    import hovsg.graph.room as room_module
    from hovsg.utils.eval_utils import find_overlapping_ratio
    room_module.find_overlapping_ratio = find_overlapping_ratio
label = 'with-import' if provide_import else 'native'
default_output = root / 'results/hovsg/merge-check/raw' / (label + '-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
out = Path(os.environ.get('HOVSG_MERGE_OUTPUT', str(default_output))).resolve()
if out.exists():
    raise FileExistsError(f'Choose a new HOVSG_MERGE_OUTPUT directory: {out}')
out.mkdir(parents=True, exist_ok=True)
cfg.main.save_path = str(out)
cfg.main.dataset_path = str(Path(cfg.main.dataset_path) / cfg.main.split / cfg.main.scene_id)
cfg.pipeline.merge_objects_graph = True
OmegaConf.save(cfg, out / 'config.yaml')
graph = Graph(cfg)
graph.load_full_pcd(str(source))
graph.load_full_pcd_feats(str(source), normalize=False)
graph.load_masked_pcds(str(source))
graph.build_graph(str(out))

print(f'Saved graph: {out / "graph"}')
