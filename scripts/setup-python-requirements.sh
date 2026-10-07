#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "No Docker found in PATH" >&2
  exit 1
fi

compile_requirements() {
  dir="$1"
  echo "Compiling requirements in $dir"
  docker run --rm \
    -v "$ROOT:/repo" \
    -w "/repo/$dir" \
    python:3.13-slim \
    sh -c "pip install -q pip-tools && pip-compile -c constraints.txt -o requirements.txt requirements.in"
}

for d in apps/ai apps/backend apps/trainer; do
  [ -f "$d/requirements.in" ] || continue
  compile_requirements "$d"
done

echo "Python requirements ready."
