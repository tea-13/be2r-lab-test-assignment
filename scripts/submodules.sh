#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
git submodule update --init
# Upstream использует SSH. Меняем только локальный config, не .gitmodules upstream.
git -C third_party/DualMap submodule init
git -C third_party/DualMap config submodule.3rdparty/mobileclip.url https://github.com/apple/ml-mobileclip.git
git submodule update --init --recursive
