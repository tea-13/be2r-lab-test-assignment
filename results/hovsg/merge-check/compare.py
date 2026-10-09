"""Inspect saved graphs and repeat only Room.merge_objects on fixed inputs."""
import json
from pathlib import Path
from collections import Counter
import numpy as np
import open3d as o3d
import hovsg.graph.room as room_module
from hovsg.graph.room import Room
from hovsg.graph.object import Object
from hovsg.utils.eval_utils import find_overlapping_ratio

root=Path(__file__).resolve().parents[3]
out=root/'results/hovsg/merge-check'
source=root/json.loads((root/'results/hovsg/graph-demo/graph-summary.json').read_text())['graph_path']
room_module.find_overlapping_ratio=find_overlapping_ratio
report={'source_graph':str(source.relative_to(root)), 'upstream_import_workaround':True, 'rooms':[]}
for p in sorted((source/'rooms').glob('*.json')):
    meta=json.loads(p.read_text())
    room=Room(meta['room_id'], meta['floor_id'])
    room.load(str(source/'rooms'))
    for oid in meta['objects']:
        obj=Object(oid, room.room_id)
        obj.load(str(source/'objects'))
        room.add_object(obj)
    before=len(room.objects)
    labels=Counter(obj.name for obj in room.objects)
    room.merge_objects()
    report['rooms'].append({'room':room.room_id,'before':before,'after':len(room.objects),
        'labels_before':dict(labels),'labels_after':dict(Counter(o.name for o in room.objects)),
        'unique_python_objects':len({id(o) for o in room.objects}),
        'unique_object_ids':len({o.object_id for o in room.objects}),
        'finite_embeddings':all(np.isfinite(o.embedding).all() for o in room.objects)})
report['before']=sum(x['before'] for x in report['rooms'])
report['after']=sum(x['after'] for x in report['rooms'])
report['duplicate_ids']=any(x['after']!=x['unique_object_ids'] for x in report['rooms'])
(out/'fixed-input-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rooms'},indent=2))
