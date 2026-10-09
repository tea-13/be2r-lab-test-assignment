"""Render actual couch-labelled segments before/after, with a shared camera."""
import json
from pathlib import Path
import numpy as np
import open3d as o3d
import pyvista as pv
root=Path(__file__).resolve().parents[3]
out=root/'results/hovsg/merge-check'
old=root/json.loads((root/'results/hovsg/graph-demo/graph-summary.json').read_text())['graph_path']
new=out/'raw/with-import/graph'
p=pv.Plotter(shape=(1,2),window_size=(1600,700),off_screen=True)
colors=['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#a65628','#f781bf','#17becf']
for col,path in enumerate([old,new]):
    p.subplot(0,col); p.set_background('white')
    entries=[json.loads(f.read_text()) for f in sorted((path/'objects').glob('*.json'))]
    entries=[o for o in entries if o['room_id']=='0_2' and o['name']=='couch']
    for i,o in enumerate(entries):
        cloud=o3d.io.read_point_cloud(str(path/'objects'/f"{o['object_id']}.ply"))
        p.add_points(np.asarray(cloud.points),color=colors[i],point_size=6)
    p.add_text(('Before' if col==0 else 'After')+f': {len(entries)} couch-labelled segments',color='black',font_size=16)
    p.view_isometric(); p.camera.up=(0,1,0); p.reset_camera()
p.link_views()
p.show(screenshot=str(out/'couch-comparison.png'))
