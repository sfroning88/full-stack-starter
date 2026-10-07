#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 [ai|backend|trainer|packages]" >&2
  echo "  No argument runs all suites sequentially." >&2
  exit 1
}

TARGET="${1:-all}"
case "$TARGET" in
  ai | backend | trainer | packages | all) ;;
  *) usage ;;
esac

STATUS=0

run_app() {
  name="$1"
  echo ""
  echo "===== $name unit tests ====="
  if [ ! -x "$ROOT/apps/$name/.venv/bin/python" ]; then
    echo "Missing venv: apps/$name/.venv (run scripts/setup-python-venvs.sh)" >&2
    STATUS=1
    return
  fi
  ( cd "$ROOT/apps/$name" && .venv/bin/python -m pytest tests/ -q ) || STATUS=1
}

run_python() {
  echo ""
  echo "===== python (fiery_python) unit tests ====="
  if [ ! -x "$ROOT/packages/python/.venv/bin/python" ]; then
    echo "Missing venv: packages/python/.venv (run scripts/setup-python-venvs.sh)" >&2
    STATUS=1
    return
  fi
  ( cd "$ROOT/packages/python" && .venv/bin/python -m pytest src/tests/unit -q ) || STATUS=1
}

run_target() {
  case "$1" in
    ai | backend | trainer) run_app "$1" ;;
    packages) run_python ;;
  esac
}

if [ "$TARGET" = "all" ]; then
  for t in ai backend trainer packages; do
    run_target "$t"
  done
else
  run_target "$TARGET"
fi

echo ""
if [ "$STATUS" -eq 0 ]; then
  echo "All requested unit tests passed."
else
  echo "Some unit tests failed." >&2
fi
exit "$STATUS"
