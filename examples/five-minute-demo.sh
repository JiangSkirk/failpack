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

echo "==> 1/7  failpack --version (expect 0.3.x)"
failpack --version

echo
echo "==> 2/7  doctor — env + .failpack/ layout"
failpack doctor

echo
echo "==> 3/7  capture a fixture transcript into a disposable pack"
# --force so re-running the demo is safe
failpack capture "$FIXTURE" --id "$PACK_ID" --force

echo
echo "==> 4/7  promote → golden assertions.yaml"
failpack promote "$PACK_ID"
failpack status "$PACK_ID"

echo
echo "==> 5/7  replay — should PASS"
failpack replay "$PACK_ID"

echo
echo "==> 6/7  intentional break — mutate a substring assertion, replay should FAIL"
# Save original assertions so we can restore cleanly
cp "$ASSERTIONS" "${ASSERTIONS}.bak"
python3 - <<'PY'
from pathlib import Path
import yaml

path = Path(".failpack/packs/demo-five-minute/assertions.yaml")
data = yaml.safe_load(path.read_text(encoding="utf-8"))
assert data.get("substrings"), "expected substring assertions"
data["substrings"][0]["contains"] = "THIS_STRING_DOES_NOT_EXIST_IN_ARTIFACTS"
path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
print("mutated substring assertion")
PY

set +e
failpack replay "$PACK_ID"
code=$?
set -e
if [[ "$code" -eq 0 ]]; then
  echo "error: expected replay to fail after intentional break" >&2
  mv "${ASSERTIONS}.bak" "$ASSERTIONS"
  exit 1
fi
echo "(exit ${code} — expected FAIL; check expected/actual/hint above)"

# Also show machine-readable output once
echo
echo "==> optional: same failure as --json"
set +e
failpack replay "$PACK_ID" --json | head -n 40
set -e

echo
echo "==> 7/7  restore assertions → replay should PASS again"
mv "${ASSERTIONS}.bak" "$ASSERTIONS"
failpack replay "$PACK_ID"

echo
echo "Done. Demo pack left at ${PACK_DIR} (status=golden)."
echo "Clean up with:  rm -rf ${PACK_DIR}"
