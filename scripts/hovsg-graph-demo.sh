#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
if [[ -n "${HOVSG_GRAPH_DIR:-}" ]]; then
  graph=$HOVSG_GRAPH_DIR
else
  graph=$(cat "$root/data/cache/hovsg/graph-demo.txt")
fi
[[ "$graph" = /* ]] || graph="$root/$graph"
test -d "$graph/floors"
test -d "$graph/rooms"
test -d "$graph/objects"
export MPLCONFIGDIR="$root/data/cache/hovsg/matplotlib"
mkdir -p "$MPLCONFIGDIR" "$root/data/cache/hovsg/graph-viewer"
cd "$root/third_party/HOV-SG"
exec "$root/.local/envs/hovsg/bin/python" "$root/scripts/hovsg-graph-view.py" \
  "graph_path=$graph" "hydra.run.dir=$root/data/cache/hovsg/graph-viewer" hydra.job.chdir=false
