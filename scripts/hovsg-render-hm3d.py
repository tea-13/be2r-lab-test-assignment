"""Render one public scene at the upstream HOV-SG camera poses (no navigation)."""
import hashlib
import json
import sys
from pathlib import Path

import habitat_sim
import numpy as np

sys.path.insert(0, "/hovsg/hovsg/data/hm3dsem")
from habitat_utils import load_poses_from_file, make_sensor_spec, save_obs

scene = "00861-GLAQ4DNUx5U"
pose_file = Path(f"/hovsg/hovsg/data/hm3dsem/metadata/poses/{scene}.txt")
output = Path("/output") / "val" / scene
if output.exists():
    raise SystemExit(f"Refusing to overwrite existing sequence: {output}")
poses = load_poses_from_file(str(pose_file))
indices = list(range(0, len(poses), 50))
backend = habitat_sim.SimulatorConfiguration()
backend.scene_id = f"/datasets/example/{scene}/GLAQ4DNUx5U.basis.glb"
backend.scene_dataset_config_file = "/datasets/example/hm3d_annotated_example_basis.scene_dataset_config.json"
agent_cfg = habitat_sim.agent.AgentConfiguration()
agent_cfg.sensor_specifications = [
    make_sensor_spec(name, kind, 480, 640, [0, 0, 0])
    for name, kind in [("color_sensor", habitat_sim.SensorType.COLOR),
                       ("depth_sensor", habitat_sim.SensorType.DEPTH)]
]
settings = dict(scene=backend.scene_id, lidar_sensor=False,
                depth_sensor=True, semantic_sensor=False)
sim = habitat_sim.Simulator(habitat_sim.Configuration(backend, [agent_cfg]))
depth_stats = []
try:
    agent = sim.initialize_agent(0)
    for frame_id, source_id in enumerate(indices):
        pose = poses[source_id]
        state = agent.get_state()
        for name in ["color_sensor", "depth_sensor"]:
            state.sensor_states[name].position = pose[:3]
            state.sensor_states[name].rotation = pose[3:]
        agent.set_state(state, reset_sensors=True, infer_sensor_states=False)
        obs = sim.get_sensor_observations(0)
        assert np.isfinite(obs["depth_sensor"]).all()
        assert obs["depth_sensor"].max() < 65.535, "uint16 mm overflow"
        save_obs(str(output), settings, obs, pose, frame_id)
        depth_stats.append(float((obs["depth_sensor"] > 0).mean()))
        print(f"Rendered {frame_id + 1}/{len(indices)} (source pose {source_id})", flush=True)
finally:
    sim.close()
summary = dict(scene=scene, habitat_sim=habitat_sim.__version__,
               source_pose_sha256=hashlib.sha256(pose_file.read_bytes()).hexdigest(),
               source_pose_count=len(poses), source_indices=indices,
               frames=len(indices), width=640, height=480, hfov_degrees=90,
               depth_unit="millimetres, uint16", poses="upstream Habitat camera-to-world; loader applies diag(1,-1,-1,1)",
               minimum_valid_depth_fraction=min(depth_stats), semantic_gt_rendered=False)
(output / "render-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
