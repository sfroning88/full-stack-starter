#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

install_pytest() {
  dir="$1"
  pip="$ROOT/$dir/.venv/bin/pip"
  if [ ! -x "$pip" ]; then
    echo "Missing venv: $dir/.venv (run scripts/setup-python-venvs.sh first)" >&2
    exit 1
  fi
  echo "Installing pytest in $dir/.venv"
  "$pip" install -q "pytest>=8.0.0"
}

for d in apps/*; do
  [ -f "$d/requirements.txt" ] || continue
  install_pytest "$d"
done

[ -d packages/python ] && install_pytest packages/python

echo "Pytest installed in Python venvs."
