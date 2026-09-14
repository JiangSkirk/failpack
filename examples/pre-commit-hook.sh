#!/usr/bin/env bash
# FailPack pre-commit tip: fail the commit if any golden pack drifts.
#
# Install (from your repo root):
#   cp examples/pre-commit-hook.sh .git/hooks/pre-commit   # if vendoring this file
#   # or symlink / copy into .git/hooks/pre-commit and chmod +x
#
# Leftover tip: if you use the pre-commit framework instead of raw hooks:
#   - repo: local
#     hooks:
#       - id: failpack-replay
#         name: failpack replay --all
#         entry: failpack replay --all
#         language: system
#         pass_filenames: false
#         always_run: true
#
# Requires: failpack on PATH
#   pip install "git+https://github.com/JiangSkirk/failpack.git"
#   # or: pip install -e .

set -euo pipefail

export NO_COLOR="${NO_COLOR:-1}"

if ! command -v failpack >/dev/null 2>&1; then
  echo 'failpack: not on PATH — skip (install with: pip install "git+https://github.com/JiangSkirk/failpack.git")' >&2
  exit 0
fi

# Only enforce when this repo has a FailPack workspace.
if [[ ! -d .failpack/packs ]]; then
  exit 0
fi

echo "failpack: replaying golden packs…"
failpack replay --all
