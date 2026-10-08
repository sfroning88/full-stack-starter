#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "No Python found in PATH" >&2
  exit 1
fi

setup_backend_venv() {
  dir="$1"
  echo "Setting up .venv in $dir"
  (
    cd "$ROOT/$dir" || exit 1
    rm -rf .venv
    "$PY" -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -r requirements.txt
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
  )
}

for d in apps/*; do
  [ -f "$d/requirements.txt" ] || continue
  setup_backend_venv "$d"
done

[ -d packages/python ] && setup_package_venv

echo "Python venvs ready."
