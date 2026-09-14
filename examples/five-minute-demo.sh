#!/usr/bin/env bash
# FailPack 5-minute demo: doctor → capture → promote → replay → break → restore
#
# Prefer the built-in command (works after `pip install failpack`):
#   failpack demo
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

echo "==> 1/8  failpack --version (expect 0.8.x)"
failpack --version

echo
echo "==> delegating remaining steps to: failpack demo"
failpack demo --id demo-five-minute
