"""Validate the saved merged hierarchy and compare it with the original."""
import json
from pathlib import Path
from collections import Counter
import numpy as np
import open3d as o3d
import networkx as nx

root=Path(__file__).resolve().parents[3]
out=root/'results/hovsg/merge-check'
graph=out/'raw/with-import/graph'
levels={}
for level,key in [('floors','floor_id'),('rooms','room_id'),('objects','object_id')]:
    entries={}
    for file in sorted((graph/level).glob('*.json')):
        d=json.loads(file.read_text())
        assert d[key]==file.stem
        pcd=o3d.io.read_point_cloud(str(file.with_suffix('.ply')))
        assert len(pcd.points)>0 and np.isfinite(np.asarray(pcd.points)).all()
        entries[d[key]]=d
    assert entries
    levels[level]=entries
F,R,O=[levels[k] for k in ['floors','rooms','objects']]
for fid,f in F.items():
    assert sorted(f['rooms'])==sorted(k for k,r in R.items() if r['floor_id']==fid)
for rid,r in R.items():
    assert r['floor_id'] in F
    assert len(r['objects'])==len(set(r['objects']))
    assert sorted(r['objects'])==sorted(k for k,o in O.items() if o['room_id']==rid)
for o in O.values():
    assert o['room_id'] in R and np.asarray(o['embedding']).shape==(1024,)
    assert np.isfinite(o['embedding']).all()
nav=nx.node_link_graph(json.loads((graph/'nav_graph/global_nav_graph_graph.json').read_text()))
old=json.loads((root/'results/hovsg/graph-demo/graph-summary.json').read_text())
fixed=json.loads((out/'fixed-input-comparison.json').read_text())
source=root/old['graph_path']
def unique_points(directory):
    arrays=[np.asarray(o3d.io.read_point_cloud(str(f)).points) for f in sorted((directory/'objects').glob('*.ply'))]
    return np.unique(np.concatenate(arrays),axis=0)
before_points=unique_points(source)
after_points=unique_points(graph)
geometry_unchanged=np.array_equal(before_points,after_points)

summary={'graph_path':str(graph.relative_to(root)), 'native_exit_code':1,
 'native_error':"NameError: name 'find_overlapping_ratio' is not defined",
 'workaround':'Import existing hovsg.utils.eval_utils.find_overlapping_ratio into room module at runtime; upstream files unchanged',
 'merge_objects_graph':True,'radius_m':0.1,'overlap_threshold':0.01,
 'baseline_objects':old['objects'],'merged_objects':len(O),
 'fixed_input_objects_before':fixed['before'],'fixed_input_objects_after':fixed['after'],
 'floors':len(F),'rooms':len(R),'parent_links_valid':True,'finite_embeddings':True,
 'nonempty_finite_clouds':True, 'object_label_counts':dict(Counter(o['name'] for o in O.values())),
 'nav_nodes':nav.number_of_nodes(),'nav_edges':nav.number_of_edges(),
 'nav_connected_components':nx.number_connected_components(nav),
 'semantic_accuracy_measured':False,
 'with_import_exit_code':0,'viewer_exit_code':0,
 'unique_object_points_before':len(before_points),'unique_object_points_after':len(after_points),
 'object_geometry_union_preserved':geometry_unchanged}
assert summary['merged_objects']==fixed['after']
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='object_label_counts'},indent=2))
