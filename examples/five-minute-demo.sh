#!/usr/bin/env bash
# FailPack wow demo: prefer the ~60s path, or the full break/restore path.
#
# Prefer the built-in command (works after git install):
#   pip install "git+https://github.com/JiangSkirk/failpack.git"
#   failpack demo --fast          # ~60s stranger path (recommended)
#   failpack demo                 # full path with doctor + break/restore
#
# Or run this script from the FailPack repo root:
#   ./examples/five-minute-demo.sh
#
# Requires: Python 3.11+, pip-installed failpack (pip install -e ".[dev]")

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Keep output readable in CI / logs
export NO_COLOR="${NO_COLOR:-1}"

MODE="${1:---fast}"

echo "==> failpack --version (expect 1.5.x)"
failpack --version

echo
if [[ "$MODE" == "--full" ]]; then
  echo "==> delegating to: failpack demo  (full path)"
  failpack demo --id demo-five-minute
else
  echo "==> delegating to: failpack demo --fast  (~60s)"
  failpack demo --fast --id demo-five-minute
fi
