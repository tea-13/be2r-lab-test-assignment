"""Run the upstream viewer with a Y-up camera matching Habitat coordinates."""
from pathlib import Path
import runpy

import pyvista as pv

pv.global_theme.camera["viewup"] = [0, 1, 0]
runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "third_party/HOV-SG/application/visualize_graph.py"),
    run_name="__main__",
)
