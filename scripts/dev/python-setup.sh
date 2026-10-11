#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "No Python found in PATH" >&2
  exit 1
fi

usage() {
  echo "Usage: $0 [ai|backend|trainer|packages]" >&2
  echo "  No argument runs full setup (compile requirements, venvs, pytest)." >&2
  exit 1
}

TARGET="${1:-all}"
case "$TARGET" in
  ai | backend | trainer | packages | all) ;;
  *) usage ;;
esac

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "No Docker found in PATH" >&2
    exit 1
  fi
}

compile_requirements() {
  dir="$1"
  require_docker
  echo "Compiling requirements in $dir"
  docker run --rm \
    -v "$ROOT:/repo" \
    -w "/repo/$dir" \
    python:3.13-slim \
    sh -c "pip install -q pip-tools && pip-compile -c constraints.txt -o requirements.txt requirements.in"
}

setup_backend_venv() {
  dir="$1"
  echo "Setting up .venv in $dir"
  (
    cd "$ROOT/$dir" || exit 1
    rm -rf .venv
    "$PY" -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -r requirements.txt
    .venv/bin/pip install -q "pytest>=8.0.0"
  )
}

setup_package_venv() {
  echo "Setting up .venv in packages/python"
  (
    cd "$ROOT/packages/python" || exit 1
    rm -rf .venv
    "$PY" -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -e ".[dev]"
    .venv/bin/pip install -q "pytest>=8.0.0"
  )
}

setup_app() {
  name="$1"
  dir="apps/$name"
  if [ -f "$dir/requirements.in" ]; then
    compile_requirements "$dir"
  fi
  if [ -f "$dir/requirements.txt" ]; then
    setup_backend_venv "$dir"
  fi
}

if [ "$TARGET" = "all" ]; then
  for d in apps/*; do
    [ -f "$d/requirements.in" ] || continue
    compile_requirements "$d"
  done
  for d in apps/*; do
    [ -f "$d/requirements.txt" ] || continue
    setup_backend_venv "$d"
  done
  [ -d packages/python ] && setup_package_venv
else
  case "$TARGET" in
    ai | backend | trainer) setup_app "$TARGET" ;;
    packages) [ -d packages/python ] && setup_package_venv ;;
  esac
fi

echo "Python setup complete."
