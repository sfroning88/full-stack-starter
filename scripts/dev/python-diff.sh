#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 [check|format|tests]" >&2
  echo "  check   List affected Python targets (BASE_SHA..HEAD_SHA, default origin/staging..HEAD)" >&2
  echo "  format  Run black --check on Python apps and packages/python" >&2
  echo "  tests   Run unit tests for staged Python changes (default)" >&2
  exit 1
}

MODE="${1:-tests}"
case "$MODE" in
  check | format | tests) ;;
  *) usage ;;
esac

if [ "$MODE" = "format" ]; then
  echo "Checking Python formatting (black)..."
  black --check apps/backend apps/ai apps/trainer packages/python
  exit 0
fi

AI=0
BACKEND=0
TRAINER=0
PACKAGES=0

mark_path() {
  case "$1" in
    apps/ai/*) AI=1 ;;
    apps/backend/*) BACKEND=1 ;;
    apps/trainer/*) TRAINER=1 ;;
    packages/python/*) PACKAGES=1 ;;
  esac
}

if [ "$MODE" = "check" ]; then
  BASE="${BASE_SHA:-origin/staging}"
  HEAD="${HEAD_SHA:-HEAD}"
  CHANGED=$(git diff --name-only "$BASE"...$HEAD 2>/dev/null || true)
  [ -z "$CHANGED" ] && exit 0
  for path in $CHANGED; do
    mark_path "$path"
  done
  [ "$BACKEND" = 1 ] && echo "backend"
  [ "$AI" = 1 ] && echo "ai"
  [ "$TRAINER" = 1 ] && echo "trainer"
  [ "$PACKAGES" = 1 ] && echo "packages"
  exit 0
fi

STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
[ -z "$STAGED" ] && exit 0

for path in $STAGED; do
  mark_path "$path"
done

if [ "$PACKAGES" = 1 ]; then
  AI=1
  BACKEND=1
  TRAINER=1
fi

TARGETS=""
[ "$AI" = 1 ] && TARGETS="${TARGETS} ai"
[ "$BACKEND" = 1 ] && TARGETS="${TARGETS} backend"
[ "$TRAINER" = 1 ] && TARGETS="${TARGETS} trainer"
[ "$PACKAGES" = 1 ] && TARGETS="${TARGETS} packages"
TARGETS=$(echo "$TARGETS" | xargs)

[ -z "$TARGETS" ] && exit 0

echo "Running Python unit tests for: $TARGETS"

STATUS=0
for target in $TARGETS; do
  ./scripts/dev/python-unit-tests.sh "$target" || STATUS=1
done

echo ""
if [ "$STATUS" -eq 0 ]; then
  echo "Python unit tests passed (1)."
else
  echo "Python unit tests failed (0). Commit blocked." >&2
fi
exit "$STATUS"
