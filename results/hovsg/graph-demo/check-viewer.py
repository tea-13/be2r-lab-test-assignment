"""Exercise upstream viewer; only automate screenshot and window close."""
import importlib.util
import json
import time
from pathlib import Path
import numpy as np
import pyvista as pv
from omegaconf import OmegaConf

root = Path.cwd()
graph = root / (root/'data/cache/hovsg/graph-demo.txt').read_text().strip()
out = root/'results/hovsg/graph-demo'
spec = importlib.util.spec_from_file_location('upstream_viewer',root/'third_party/HOV-SG/application/visualize_graph.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
pv.global_theme.camera['viewup'] = [0, 1, 0]
original_show = pv.Plotter.show
report = {}
def show_and_close(plotter, *args, **kwargs):
    report['actors'] = len(plotter.renderer.actors)
    assert report['actors'] > 3
    result = original_show(plotter, *args, window_size=(1400,1000),
                           interactive_update=True, auto_close=False, **kwargs)
    for _ in range(30):
        plotter.update()
        time.sleep(0.05)
    plotter.screenshot(str(out/'graph-native.png'))
    report['screenshot_saved'] = True
    plotter.close()
    return result

pv.Plotter.show = show_and_close
np.random.seed(0)
module.main.__wrapped__(OmegaConf.create({'graph_path':str(graph)}))
assert report.get('screenshot_saved')
report['upstream_viewer_completed'] = True
(out/'gui-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
