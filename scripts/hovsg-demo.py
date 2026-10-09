"""Small GUI for HOV-SG Replica artifacts; extraction/query math stays upstream."""
import argparse
import colorsys
import json
from pathlib import Path

import numpy as np
import open3d as o3d
from open3d.visualization import gui, rendering
import open_clip

from hovsg.utils.eval_utils import load_feature_map, text_prompt

ROOT = Path(__file__).resolve().parents[1]


class Demo:
    def __init__(self, map_path, smoke_output=None):
        self.map_path = map_path
        # Keep numeric PLY IDs aligned with feature rows; upstream otherwise skips gaps.
        self.cloud = o3d.io.read_point_cloud(str(map_path / "full_pcd.ply"))
        self.objects, self.features = load_feature_map(str(map_path))
        if not self.objects or len(self.objects) != len(self.features):
            raise ValueError("Empty map or object/embedding count mismatch")
        for i in range(len(self.features)):
            if not (map_path / "objects" / f"pcd_{i}.ply").is_file():
                raise ValueError(f"Missing pcd_{i}.ply: cannot preserve object IDs")
        if self.cloud.is_empty() or not np.isfinite(self.features).all():
            raise ValueError("Invalid saved map")
        print("Loading local OpenCLIP ViT-H for HOV-SG text queries...", flush=True)
        self.model, _, _ = open_clip.create_model_and_transforms(
            "ViT-H-14", pretrained=str(ROOT / "data/weights/hovsg/laion2b_s32b_b79k.bin"),
            device="cuda",
        )
        self.model.eval()
        self.scores = None
        self.ranking = []
        self.selected = 0
        self.query_records = []
        self.smoke_output = smoke_output
        self.smoke_stage = 0
        self.ticks = 0
        self.bounds = self.cloud.get_axis_aligned_bounding_box()
        self.window = gui.Application.instance.create_window("HOV-SG — Replica map and text search", 1400, 900)
        self.scene = gui.SceneWidget()
        self.scene.scene = rendering.Open3DScene(self.window.renderer)
        self.scene.scene.set_background([0.055, 0.065, 0.085, 1.0])
        self.scene.scene.show_axes(True)
        em = self.window.theme.font_size
        self.panel = gui.Vert(0.5 * em, gui.Margins(em, em, em, em))
        self.panel.add_child(gui.Label("HOV-SG | Replica room0"))
        self.panel.add_child(gui.Label(f"{len(self.cloud.points):,} points | {len(self.objects)} segments"))
        self.panel.add_child(gui.Label("Drag: orbit | Wheel: zoom\nCtrl+drag: pan"))
        self.panel.add_child(gui.Label("Text query (English)"))
        self.query = gui.TextEdit()
        self.query.text_value = "sofa"
        self.panel.add_child(self.query)
        self.button("Search", self.search)
        self.mode = gui.Combobox()
        for name in ("RGB", "Instances", "Similarity", "Selected object"):
            self.mode.add_item(name)
        self.mode.set_on_selection_changed(lambda _name, _index: self.redraw())
        self.panel.add_child(self.mode)
        self.cut = gui.Checkbox("Hide ceiling (display only)")
        self.cut.checked = True
        self.cut.set_on_checked(lambda _checked: self.redraw())
        self.panel.add_child(self.cut)
        self.button("Reset view", self.reset_view)
        self.panel.add_child(gui.Label("Top 5 segments (cosine similarity)"))
        self.listing = gui.ListView()
        self.listing.set_max_visible_items(5)
        self.listing.set_items(["Run Search to rank objects"])
        self.listing.set_on_selection_changed(self.select_result)
        self.panel.add_child(self.listing)
        self.note = gui.Label("Similarity is not probability.\nReplica feature map; no floor/room graph.")
        self.panel.add_child(self.note)
        self.button("Save screenshot", self.save_screenshot)
        self.button("Quit", self.window.close)
        self.window.add_child(self.scene)
        self.window.add_child(self.panel)
        self.window.set_on_layout(self.layout)
        self.redraw()
        self.reset_view()
        if smoke_output:
            smoke_output.mkdir(parents=True, exist_ok=True)
            self.window.set_on_tick_event(self.smoke_tick)
        print("GUI ready. Enter a query and click Search; select any of the top 5 segments.", flush=True)

    def button(self, text, callback):
        button = gui.Button(text)
        button.set_on_clicked(callback)
        self.panel.add_child(button)

    def layout(self, _context):
        rect = self.window.content_rect
        width = min(360, rect.width // 3)
        self.scene.frame = gui.Rect(rect.x, rect.y, rect.width - width, rect.height)
        self.panel.frame = gui.Rect(rect.get_right() - width, rect.y, width, rect.height)

    def display_cloud(self, cloud, color=None):
        # Replica room0 is Z-up. This clips only rendered geometry, never the map.
        if self.cut.checked:
            z = np.asarray(cloud.points)[:, 2]
            cloud = cloud.select_by_index(np.flatnonzero(z < self.bounds.max_bound[2] - 0.25))
        else:
            cloud = o3d.geometry.PointCloud(cloud)
        if color is not None:
            cloud.paint_uniform_color(color)
        return cloud

    def add_cloud(self, name, cloud, color=None, size=3):
        cloud = self.display_cloud(cloud, color)
        if cloud.is_empty():
            return
        material = rendering.MaterialRecord()
        material.shader = "defaultUnlit"
        material.point_size = size
        self.scene.scene.add_geometry(name, cloud, material)

    def redraw(self):
        self.scene.scene.clear_geometry()
        mode = self.mode.selected_index
        if mode == 0:
            self.add_cloud("rgb", self.cloud)
        elif mode == 1:
            for i, cloud in enumerate(self.objects):
                self.add_cloud(str(i), cloud, colorsys.hsv_to_rgb((i * 0.618034) % 1, 0.7, 0.95))
        elif mode == 2 and self.scores is not None:
            low, high = float(self.scores.min()), float(self.scores.max())
            for i, cloud in enumerate(self.objects):
                value = (float(self.scores[i]) - low) / max(high - low, 1e-8)
                self.add_cloud(str(i), cloud, colorsys.hsv_to_rgb((1 - value) * 0.66, 0.85, 0.95))
        else:
            background = o3d.geometry.PointCloud(self.cloud)
            background.colors = o3d.utility.Vector3dVector(
                np.asarray(self.cloud.colors) * 0.45 + 0.025)
            self.add_cloud("background", background, size=3)
        if self.scores is not None and mode in (0, 3):
            self.add_cloud("selected", self.objects[self.selected], [1.0, 0.4, 0.05], size=6)
            box = self.objects[self.selected].get_axis_aligned_bounding_box()
            box.color = [1.0, 0.65, 0.1]
            material = rendering.MaterialRecord()
            material.shader = "unlitLine"
            material.line_width = 2
            self.scene.scene.add_geometry("box", o3d.geometry.LineSet.create_from_axis_aligned_bounding_box(box), material)
        self.scene.force_redraw()

    def reset_view(self):
        center = self.bounds.get_center()
        radius = np.linalg.norm(self.bounds.get_extent())
        self.scene.setup_camera(60, self.bounds, center)
        self.scene.look_at(center, center + np.array([0.65, -0.8, 0.85]) * radius * 0.8, [0, 0, 1])

    def search(self):
        query = self.query.text_value.strip()
        if not query:
            self.note.text = "Enter a non-empty English query."
            return
        # Exact upstream semantic-evaluation text encoder/templates and cosine function.
        scores = text_prompt(self.model, 1024, self.features, [query], templates=True)[:, 0]
        if not np.isfinite(scores).all():
            raise ValueError("Non-finite text similarities")
        self.scores = scores
        self.ranking = np.argsort(-scores, kind="stable")[:5].tolist()
        self.selected = self.ranking[0]
        self.listing.set_items([f"#{i}   {scores[i]:.3f}" for i in self.ranking])
        self.listing.selected_index = 0
        self.mode.selected_index = 3
        self.note.text = f'Query: {query}\nOrange: #{self.selected}, score {scores[self.selected]:.3f}\nScore is not confidence or accuracy.'
        record = {"query": query, "top5": [{"id": i, "similarity": float(scores[i])} for i in self.ranking]}
        self.query_records.append(record)
        print(json.dumps(record), flush=True)
        self.redraw()

    def select_result(self, _text, _double_click):
        i = self.listing.selected_index
        if self.ranking and 0 <= i < len(self.ranking):
            self.selected = self.ranking[i]
            self.mode.selected_index = 3
            self.note.text = f'Selected #{self.selected}: {self.scores[self.selected]:.3f}\nOrange = selected segment\nScore is cosine similarity.'
            self.redraw()

    def capture(self, path, done=None):
        def save(image):
            if not o3d.io.write_image(str(path), image):
                raise RuntimeError(f"Could not save {path}")
            print(f"Screenshot: {path}", flush=True)
            if done:
                gui.Application.instance.post_to_main_thread(self.window, done)
        self.scene.scene.scene.render_to_image(save)

    def save_screenshot(self):
        from datetime import datetime
        folder = ROOT / "results/hovsg/screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        self.capture(folder / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".png"))

    def smoke_tick(self):
        self.ticks += 1
        if self.ticks < 15:
            return False
        self.ticks = 0
        stage = self.smoke_stage
        self.smoke_stage += 1
        if stage == 0:
            self.capture(self.smoke_output / "rgb.png")
        elif stage == 1:
            self.mode.selected_index = 1
            self.redraw()
        elif stage == 2:
            self.capture(self.smoke_output / "instances.png")
        elif stage in (3, 5, 7):
            self.query.text_value = {3: "sofa", 5: "pillow", 7: "lamp"}[stage]
            self.search()
        elif stage in (4, 6, 8):
            self.capture(self.smoke_output / f"query-{self.query.text_value}.png")
            if stage == 8:
                from PIL import ImageGrab
                rect = self.window.os_frame
                ImageGrab.grab(bbox=(rect.x, rect.y, rect.get_right(), rect.get_bottom())).save(
                    self.smoke_output / "window.png")
        elif stage == 9:
            self.listing.selected_index = 1
            self.select_result("", False)
            assert self.selected == self.ranking[1]
            self.mode.selected_index = 2
            self.redraw()
        elif stage == 10:
            self.capture(self.smoke_output / "similarity.png")
        elif stage == 11:
            self.cut.checked = False
            self.redraw()
            self.reset_view()
            (self.smoke_output / "queries.json").write_text(json.dumps({
                "map": str(self.map_path), "points": len(self.cloud.points),
                "segments": len(self.objects), "queries": self.query_records,
                "second_result_selection_checked": True,
            }, indent=2) + "\n")
            self.capture(self.smoke_output / "ceiling-visible.png", self.window.close)
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--smoke-output", type=Path, help="Run GUI checks, capture frames, then close")
    args = parser.parse_args()
    gui.Application.instance.initialize()
    demo = Demo(args.map.resolve(), args.smoke_output)
    gui.Application.instance.run()
    # Keep GUI callbacks alive for the entire event loop.
    del demo


if __name__ == "__main__":
    main()
