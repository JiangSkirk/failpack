#!/usr/bin/env bash
# Prove FailPack's Claude Code one-shot without a live Claude install.
#
# Uses a fake HOME + fixtures/claude-code-failure.jsonl so strangers and CI
# can run: capture --claude-latest → promote → replay.
# Never points at a real ~/.claude tree.
#
# From a FailPack checkout (editable install recommended):
#   pip install -e ".[dev]"
#   ./examples/claude-latest-hermetic.sh
#
# See also: examples/claude-latest-demo.md, examples/STRANGER_WALKTHROUGH.md

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export NO_COLOR="${NO_COLOR:-1}"

FIXTURE="${ROOT}/fixtures/claude-code-failure.jsonl"
if [[ ! -f "$FIXTURE" ]]; then
  echo "error: missing fixture: $FIXTURE" >&2
  exit 1
fi

FAKE_HOME="$(mktemp -d "${TMPDIR:-/tmp}/failpack-claude-hermetic.XXXXXX")"
cleanup() { rm -rf "$FAKE_HOME"; }
trap cleanup EXIT

PROJECT="${FAKE_HOME}/.claude/projects/hermetic-demo"
mkdir -p "$PROJECT"
cp "$FIXTURE" "${PROJECT}/session.jsonl"

# Path.home() (used by --claude-latest) follows HOME. Keep the real user-site /
# venv import path so `failpack` still resolves after HOME is faked.
ORIG_HOME="${HOME}"
if [[ -z "${VIRTUAL_ENV:-}" && -z "${PYTHONUSERBASE:-}" ]]; then
  export PYTHONUSERBASE="${ORIG_HOME}/.local"
fi
export HOME="$FAKE_HOME"

PACK_ID="${1:-claude-hermetic}"
WORKSPACE="${2:-.}"

echo "==> failpack --version (expect 1.5.7+)"
failpack --version

echo
echo "==> hermetic Claude one-shot (HOME=${FAKE_HOME})"
echo "    layout: ~/.claude/projects/<name>/*.jsonl"
echo "    fixture → ~/.claude/projects/hermetic-demo/session.jsonl"
failpack --root "$WORKSPACE" capture --claude-latest --id "$PACK_ID" --force

echo
echo "==> promote → golden"
failpack --root "$WORKSPACE" promote --suggest --write "$PACK_ID"

echo
echo "==> replay — should PASS"
failpack --root "$WORKSPACE" replay "$PACK_ID"

echo
echo "Done. Hermetic Claude one-shot pack: ${WORKSPACE}/.failpack/packs/${PACK_ID}"
echo "Clean up with:  failpack --root ${WORKSPACE} rm ${PACK_ID} --force"
echo "Real machine (after a Claude Code failure): failpack capture --claude-latest --id my-failure"
