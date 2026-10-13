#!/usr/bin/env bash
set -euo pipefail

choose_python() {
  if command -v python3 >/dev/null 2>&1; then echo "python3"
  elif command -v python >/dev/null 2>&1; then echo "python"
  else echo "❌ No Python found in PATH" >&2; exit 1; fi
}
PY=$(choose_python)
echo "🔍 Using Python: $PY"

VENV_DIR="${VENV_DIR:-.venv-tools}"
RUFF_VERSION="${RUFF_VERSION:-0.6.9}"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "⛏️  Creating tooling venv at $VENV_DIR"
  "$PY" -m venv "$VENV_DIR"
fi

PIP="$VENV_DIR/bin/pip"
RUFF="$VENV_DIR/bin/ruff"
if ! "$PIP" --version >/dev/null 2>&1; then
  echo "⚠️  Tooling venv stale. Recreating $VENV_DIR"
  rm -rf "$VENV_DIR"
  "$PY" -m venv "$VENV_DIR"
  PIP="$VENV_DIR/bin/pip"
  RUFF="$VENV_DIR/bin/ruff"
fi

"$PIP" install -q --upgrade pip
"$PIP" install -q "ruff==${RUFF_VERSION}"

echo "🔍 Running Ruff (E9 syntax, F821 undefined names)..."
"$RUFF" check . --select E9,F821

echo "✅ CI passed"
