#!/usr/bin/env bash
# FailPack 5-minute demo: doctor → capture → promote → replay → break → restore
#
# Run from the FailPack repo root:
#   ./examples/five-minute-demo.sh
#
# Requires: Python 3.11+, pip-installed failpack (pip install -e ".[dev]")

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Keep output readable in CI / logs
export NO_COLOR="${NO_COLOR:-1}"

PACK_ID="demo-five-minute"
FIXTURE="fixtures/claude-code-failure.jsonl"
PACK_DIR=".failpack/packs/${PACK_ID}"
ASSERTIONS="${PACK_DIR}/assertions.yaml"

echo "==> 1/8  failpack --version (expect 0.5.x)"
failpack --version

echo
echo "==> 2/8  doctor — env + .failpack/ layout"
failpack doctor

echo
echo "==> 3/8  capture a fixture transcript into a disposable pack"
# --force so re-running the demo is safe
failpack capture "$FIXTURE" --id "$PACK_ID" --force

echo
echo "==> 4/8  promote → golden assertions.yaml"
failpack promote "$PACK_ID"
failpack status "$PACK_ID"

echo
echo "==> 5/8  replay — should PASS"
failpack replay "$PACK_ID"

echo
echo "==> 6/8  intentional break — mutate artifact text, replay should FAIL with diff"
# Save original artifact so we can restore cleanly
ERROR_TXT="${PACK_DIR}/artifacts/error.txt"
cp "$ERROR_TXT" "${ERROR_TXT}.bak"
printf '\nMUTATED_BY_DEMO\n' >> "$ERROR_TXT"

set +e
failpack replay "$PACK_ID"
code=$?
set -e
if [[ "$code" -eq 0 ]]; then
  echo "error: expected replay to fail after intentional break" >&2
  mv "${ERROR_TXT}.bak" "$ERROR_TXT"
  exit 1
fi
echo "(exit ${code} — expected FAIL; check expected/actual/hint/diff above)"

# Also show --no-diff once
echo
echo "==> optional: same failure with --no-diff (no unified diff block)"
set +e
failpack replay "$PACK_ID" --no-diff | head -n 30
set -e

echo
echo "==> 7/8  restore artifact → replay should PASS again"
mv "${ERROR_TXT}.bak" "$ERROR_TXT"
failpack replay "$PACK_ID"

echo
echo "==> 8/8  migrate (should no-op — already current)"
failpack migrate

echo
echo "Done. Demo pack left at ${PACK_DIR} (status=golden)."
echo "Clean up with:  rm -rf ${PACK_DIR}"
