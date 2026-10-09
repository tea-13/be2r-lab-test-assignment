import json
import re
from collections import Counter
from pathlib import Path
import networkx as nx
import numpy as np
import open3d as o3d
import torch
root=Path.cwd(); out=root/'results/hovsg/graph-demo'
graph=root/(root/'data/cache/hovsg/graph-demo.txt').read_text().strip()
levels={}
for level,key in [('floors','floor_id'),('rooms','room_id'),('objects','object_id')]:
    levels[level]={}
    for f in sorted((graph/level).glob('*.json')):
        d=json.loads(f.read_text()); assert f.stem==d[key]
        p=o3d.io.read_point_cloud(str(f.with_suffix('.ply')))
        assert len(p.points)>0 and np.isfinite(np.asarray(p.points)).all()
        levels[level][d[key]]=d
    assert levels[level]
F,R,O=[levels[x] for x in ['floors','rooms','objects']]
for key,d in F.items():
    assert sorted(d['rooms'])==sorted(k for k,v in R.items() if v['floor_id']==key)
for key,d in R.items():
    assert d['floor_id'] in F
    assert sorted(d['objects'])==sorted(k for k,v in O.items() if v['room_id']==key)
    assert np.isfinite(np.asarray(d['embeddings'])).all()
for d in O.values():
    assert d['room_id'] in R
    assert np.asarray(d['embedding']).shape==(1024,)
    assert np.isfinite(d['embedding']).all()
nav_json=json.loads((graph/'nav_graph/global_nav_graph_graph.json').read_text())
nav=nx.node_link_graph(nav_json)
assert nav.number_of_nodes()>0 and nav.number_of_edges()>0
pcd=o3d.io.read_point_cloud(str(graph.parent/'full_pcd.ply'))
features=torch.load(graph.parent/'mask_feats.pt',map_location='cpu',weights_only=True)
assert torch.isfinite(features).all()
log=(out/'logs/build.log').read_text()
summary=dict(graph_path=str(graph.relative_to(root)),full_pcd_points=len(pcd.points),mask_features_shape=list(features.shape),floors=len(F),rooms=len(R),objects=len(O),parent_links_valid=True,finite_object_embeddings=True,nonempty_ply_files=True,hierarchy_nodes_including_building=1+len(F)+len(R)+len(O),hierarchy_edges=len(F)+len(R)+len(O),rooms_per_floor={k:len(v['rooms']) for k,v in F.items()},objects_per_room={k:len(v['objects']) for k,v in R.items()},object_label_counts=dict(Counter(v['name'] for v in O.values())),nav_nodes=nav.number_of_nodes(),nav_edges=nav.number_of_edges(),nav_connected_components=nx.number_connected_components(nav),nav_largest_component_nodes=len(max(nx.connected_components(nav),key=len)),build_exit_zero='Exit status: 0' in log)
assert summary['build_exit_zero']
summary['nav_components']=[{'nodes':len(c),'floors':sorted({int(nav.nodes[n]['floor_id']) for n in c})} for c in sorted(nx.connected_components(nav),key=len,reverse=True)]
summary['nav_interfloor_edges']=sum(nav.nodes[a]['floor_id']!=nav.nodes[b]['floor_id'] for a,b in nav.edges)
timing=re.search(r'Elapsed .*: ([0-9:.]+)$',log,re.M).group(1)
seconds=0.0
for value in timing.split(':'):
    seconds=60*seconds+float(value)
summary['elapsed_seconds']=round(seconds,2)
summary['max_rss_kib']=int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',log).group(1))
(out/'graph-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# Small inspectable hierarchy without copying embeddings or binary maps.
(out/'hierarchy.json').write_text(json.dumps({'floors':[{k:v for k,v in d.items() if k in ['floor_id','name','rooms']} for d in F.values()],'rooms':[{k:v for k,v in d.items() if k in ['room_id','name','floor_id','objects']} for d in R.values()],'objects':[{k:v for k,v in d.items() if k in ['object_id','name','room_id']} for d in O.values()]},indent=2)+'\n')
print(json.dumps(summary,indent=2))
