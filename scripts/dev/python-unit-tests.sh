#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 [backend|compute|packages]" >&2
  echo "  No argument runs all suites sequentially." >&2
  exit 1
}

TARGET="${1:-all}"
case "$TARGET" in
  backend | compute | packages | all) ;;
  *) usage ;;
esac

STATUS=0

run_app() {
  name="$1"
  echo ""
  echo "===== $name unit tests ====="
  if [ ! -x "$ROOT/apps/$name/.venv/bin/python" ]; then
    echo "Missing venv: apps/$name/.venv (run scripts/dev/python-setup.sh)" >&2
    STATUS=1
    return
  fi
  ( cd "$ROOT/apps/$name" && .venv/bin/python -m pytest tests/ -q ) || STATUS=1
}

ensure_package_venv() {
  pip="$ROOT/packages/python/.venv/bin/pip"
  python="$ROOT/packages/python/.venv/bin/python"
  if "$python" -c "import my_python, dotenv" 2>/dev/null; then
    return 0
  fi
  echo "packages/python .venv is missing editable install (only pytest?). Installing .[dev]..." >&2
  (
    cd "$ROOT/packages/python" || exit 1
    "$pip" install -q --upgrade pip
    "$pip" install -e ".[dev]"
  )
}

run_python() {
  echo ""
  echo "===== python (my_python) unit tests ====="
  if [ ! -x "$ROOT/packages/python/.venv/bin/python" ]; then
    echo "Missing venv: packages/python/.venv (run pnpm python:setup packages)" >&2
    STATUS=1
    return
  fi
  ensure_package_venv || {
    echo "Failed to install packages/python dependencies (run pnpm python:setup packages)" >&2
    STATUS=1
    return
  }
  ( cd "$ROOT/packages/python" && .venv/bin/python -m pytest src/tests/unit -q ) || STATUS=1
}

run_target() {
  case "$1" in
    backend | compute) run_app "$1" ;;
    packages) run_python ;;
  esac
}

if [ "$TARGET" = "all" ]; then
  for target in backend compute packages; do
    run_target "$target"
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
