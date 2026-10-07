#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
[ -z "$STAGED" ] && exit 0

AI=0
BACKEND=0
TRAINER=0
PACKAGES=0

for path in $STAGED; do
  case "$path" in
    apps/ai/*) AI=1 ;;
    apps/backend/*) BACKEND=1 ;;
    apps/trainer/*) TRAINER=1 ;;
    packages/python/*) PACKAGES=1 ;;
  esac
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
for t in $TARGETS; do
  ./scripts/python-unit-tests.sh "$t" || STATUS=1
done

echo ""
if [ "$STATUS" -eq 0 ]; then
  echo "Python unit tests passed (1)."
else
  echo "Python unit tests failed (0). Commit blocked." >&2
fi
exit "$STATUS"
