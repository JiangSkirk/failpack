#!/usr/bin/env bash
# Thin wrapper → first-class CLI: failpack demo --cursor-hermetic
#
# Prefer the pip-installed CLI (no clone needed):
#   pip install failpack
#   failpack demo --cursor-hermetic
#
# This script is a checkout convenience alias:
#   ./examples/cursor-latest-hermetic.sh [pack-id] [workspace]
#
# See also: examples/cursor-latest-demo.md, examples/STRANGER_WALKTHROUGH.md

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export NO_COLOR="${NO_COLOR:-1}"

PACK_ID="${1:-cursor-hermetic}"
WORKSPACE="${2:-.}"

echo "==> failpack --version (expect 1.5.9+)"
failpack --version

echo
echo "==> delegating to: failpack demo --cursor-hermetic"
failpack --root "$WORKSPACE" demo --cursor-hermetic --id "$PACK_ID"
