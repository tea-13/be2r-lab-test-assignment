.DEFAULT_GOAL := help
.PHONY: help doctor status submodules

help:
	@printf '%s\n' 'make doctor       Check host prerequisites' 'make status       Show current reproduction status' 'make submodules   Initialize pinned sources recursively (HTTPS)' 'make dualmap-gpu-check      Check PyTorch CUDA and FAISS' 'make dualmap-query          Open verified offline query GUI' 'make dualmap-replica-smoke  Run 30 Replica frames' 'make onemap-habitat-check   Check Habitat GPU render (not OneMap demo)' 'make onemap-viewer          Open Rerun 0.22 viewer' 'make onemap-demo            Run OneMap on public HM3D example' 'make onemap-eval-smoke      Run 3 ObjectNav episodes, max 200 steps' 'make vlfm-gpu-check         Reproduce official torch incompatibility on sm_120' 'make hovsg-replica-smoke    Extract HOV-SG map from 3 Replica frames' 'make hovsg-build-demo       Build a 20-frame Replica demo map' 'make hovsg-demo             Open Replica feature map and text search' 'make hovsg-render-hm3d      Render 83 author camera poses (once)' 'make hovsg-build-graph      Build native HM3DSem hierarchy and nav graph' 'make hovsg-graph-demo       Open native floor/room/object graph viewer' 'make hovsg-graph-merged     Open graph after verified object merging'

doctor:
	@bash scripts/doctor.sh

status:
	@cat docs/status.md

submodules:
	@bash scripts/submodules.sh

# Add project-specific targets only after confirming upstream commands.

.PHONY: dualmap-gpu-check
dualmap-gpu-check:
	@bash scripts/dualmap-gpu-check.sh

.PHONY: dualmap-query
dualmap-query:
	@bash scripts/dualmap-query.sh

.PHONY: dualmap-replica-smoke
dualmap-replica-smoke:
	@bash scripts/dualmap-replica-smoke.sh

.PHONY: onemap-habitat-check
onemap-habitat-check:
	@bash scripts/onemap-habitat-check.sh

.PHONY: onemap-viewer onemap-demo
onemap-viewer:
	@.local/envs/dualmap/bin/rerun

onemap-demo:
	@bash scripts/onemap-demo.sh

.PHONY: onemap-eval-smoke
onemap-eval-smoke:
	@bash scripts/onemap-eval-smoke.sh

.PHONY: vlfm-gpu-check
vlfm-gpu-check:
	@bash scripts/vlfm-gpu-check.sh

.PHONY: hovsg-replica-smoke
hovsg-replica-smoke:
	@bash scripts/hovsg-replica-smoke.sh

.PHONY: hovsg-demo hovsg-build-demo
hovsg-demo:
	@bash scripts/hovsg-demo.sh

hovsg-build-demo:
	@bash scripts/hovsg-build-demo.sh

.PHONY: hovsg-render-hm3d hovsg-build-graph hovsg-graph-demo
hovsg-render-hm3d:
	@bash scripts/hovsg-render-hm3d.sh

hovsg-build-graph:
	@bash scripts/hovsg-build-graph.sh

hovsg-graph-demo:
	@bash scripts/hovsg-graph-demo.sh

.PHONY: hovsg-graph-merged
hovsg-graph-merged:
	@HOVSG_GRAPH_DIR="$(CURDIR)/results/hovsg/merge-check/raw/with-import/graph" bash scripts/hovsg-graph-demo.sh
