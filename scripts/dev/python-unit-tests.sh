#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 [backend|packages]" >&2
  echo "  No argument runs all suites sequentially." >&2
  exit 1
}

TARGET="${1:-all}"
case "$TARGET" in
  backend | packages | all) ;;
  *) usage ;;
esac

STATUS=0

run_app() {
  name="$1"
  echo ""
  echo "===== $name unit tests ====="
  if [ ! -x "$ROOT/apps/$name/.venv/bin/python" ]; then
    echo "Missing venv: apps/$name/.venv (run scripts/dev/setup-python-venvs.sh)" >&2
    STATUS=1
    return
  fi
  ( cd "$ROOT/apps/$name" && .venv/bin/python -m pytest tests/ -q ) || STATUS=1
}

run_python() {
  echo ""
  echo "===== python (my_python) unit tests ====="
  if [ ! -x "$ROOT/packages/python/.venv/bin/python" ]; then
    echo "Missing venv: packages/python/.venv (run scripts/dev/setup-python-venvs.sh)" >&2
    STATUS=1
    return
  fi
  ( cd "$ROOT/packages/python" && .venv/bin/python -m pytest src/tests/unit -q ) || STATUS=1
}

run_target() {
  case "$1" in
    backend ) run_app "$1" ;;
    packages) run_python ;;
  esac
}

if [ "$TARGET" = "all" ]; then
  for t in backend packages; do
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
