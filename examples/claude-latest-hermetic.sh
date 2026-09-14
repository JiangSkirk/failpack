#!/usr/bin/env bash
# Thin wrapper → first-class CLI: failpack demo --claude-hermetic
#
# Prefer the pip-installed CLI (no clone needed):
#   pip install failpack
#   failpack demo --claude-hermetic
#
# This script remains for docs / checkout convenience and accepts the same
# optional positional args as before:
#   ./examples/claude-latest-hermetic.sh [pack-id] [workspace]
#
# See also: examples/claude-latest-demo.md, examples/STRANGER_WALKTHROUGH.md

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export NO_COLOR="${NO_COLOR:-1}"

PACK_ID="${1:-claude-hermetic}"
WORKSPACE="${2:-.}"

echo "==> failpack --version (expect 1.5.9+)"
failpack --version

echo
echo "==> delegating to: failpack demo --claude-hermetic"
failpack --root "$WORKSPACE" demo --claude-hermetic --id "$PACK_ID"
