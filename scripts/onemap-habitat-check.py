import json
from pathlib import Path
import numpy as np
import torch
import habitat_sim
from PIL import Image
out=Path('/results')
b=habitat_sim.SimulatorConfiguration()
b.scene_id='/datasets/example/00861-GLAQ4DNUx5U/GLAQ4DNUx5U.basis.glb'
b.scene_dataset_config_file='/datasets/example/hm3d_annotated_example_basis.scene_dataset_config.json'
sensors=[]
for name,kind in [('rgb',habitat_sim.SensorType.COLOR),('depth',habitat_sim.SensorType.DEPTH)]:
 s=habitat_sim.CameraSensorSpec();s.uuid=name;s.sensor_type=kind;s.resolution=[480,640];s.position=[0,0.88,0];sensors.append(s)
a=habitat_sim.agent.AgentConfiguration();a.sensor_specifications=sensors
sim=habitat_sim.Simulator(habitat_sim.Configuration(b,[a]));sim.seed(0)
state=habitat_sim.AgentState();state.position=sim.pathfinder.get_random_navigable_point();sim.get_agent(0).set_state(state)
obs=sim.get_sensor_observations();Image.fromarray(obs['rgb']).save(out/'habitat-example-rgb.png')
x=torch.randn(256,256,device='cuda');y=x@x;torch.cuda.synchronize()
categories=sorted(set(o.category.name() for o in sim.semantic_scene.objects if o is not None and o.category is not None))
r={'habitat_sim':habitat_sim.__version__,'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'cuda_matmul_finite':bool(torch.isfinite(y).all()),'scene':'00861-GLAQ4DNUx5U','navmesh_loaded':sim.pathfinder.is_loaded,'semantic_objects':len(sim.semantic_scene.objects),'categories':categories,'agent_position':state.position.tolist(),'rgb_shape':list(obs['rgb'].shape),'depth_shape':list(obs['depth'].shape),'depth_min':float(obs['depth'].min()),'depth_max':float(obs['depth'].max())}
(out/'habitat-smoke.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sim.close()
