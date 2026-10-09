#!/usr/bin/env bash
# Только диагностика: без установки, скачивания и запуска контейнеров.
set -euo pipefail
cd "$(dirname "$0")/.."
printf 'Kernel: %s\n' "$(uname -sr)"
if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  printf 'OS: %s\n' "$PRETTY_NAME"
fi
if [[ $(uname -r) == *[Mm]icrosoft* ]]; then echo 'WSL: yes'; else echo 'WSL: no'; fi
lscpu | sed -n '/Model name:/p; /^CPU(s):/p'
free -h
df -h .
for tool in git python3 conda uv docker nvcc cmake gcc ninja tmux; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s: %s\n' "$tool" "$(command -v "$tool")"
  else
    printf 'WARN %s: unavailable in PATH\n' "$tool"
  fi
done
if [[ -x .local/miniforge/bin/conda ]]; then
  printf 'Workspace Conda: '
  .local/miniforge/bin/conda --version
fi
for method in dualmap vlfm hovsg; do
  if [[ -x ".local/envs/$method/bin/python" ]]; then
    printf 'Workspace Python (%s): ' "$method"
    ".local/envs/$method/bin/python" --version
  fi
done
python3 --version
if command -v uv >/dev/null 2>&1; then uv --version; fi
if command -v nvcc >/dev/null 2>&1; then nvcc --version; fi
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader || echo 'WARN GPU: unavailable here; check host outside sandbox'
else
  echo 'WARN nvidia-smi: unavailable'
fi
if command -v docker >/dev/null 2>&1; then
  docker --version
  docker compose version || echo 'WARN Docker Compose: unavailable'
  docker info --format 'Docker server: {{.ServerVersion}}' || echo 'WARN Docker daemon: unavailable here; check permissions/sandbox'
fi
printf 'GUI: DISPLAY=%s WAYLAND_DISPLAY=%s SESSION=%s (rendering not tested)\n' "${DISPLAY:-unset}" "${WAYLAND_DISPLAY:-unset}" "${XDG_SESSION_TYPE:-unset}"
echo 'Git submodules:'
modules=$(git submodule status --recursive)
printf '%s\n' "$modules"
if [[ $(git ls-files --stage third_party | awk '$1 == "160000" {n++} END {print n+0}') != 4 ]] || [[ -z "$modules" ]] || printf '%s\n' "$modules" | rg -q '^[-+U]'; then
  echo 'ERROR submodules: missing, uninitialized or SHA mismatch'
  exit 1
fi
echo 'Doctor completed; warnings do not confirm method readiness. GPU compute and demos require separate checks.'
