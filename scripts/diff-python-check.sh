#!/bin/sh
set -e

BASE="${BASE_SHA:-origin/staging}"
HEAD="${HEAD_SHA:-HEAD}"
CHANGED=$(git diff --name-only "$BASE"...$HEAD 2>/dev/null || true)
[ -z "$CHANGED" ] && exit 0

BACKEND=0
AI=0
TRAINER=0
PACKAGES=0

for path in $CHANGED; do
  case "$path" in
    apps/backend/*) BACKEND=1 ;;
    apps/ai/*) AI=1 ;;
    apps/trainer/*) TRAINER=1 ;;
    packages/python/*) PACKAGES=1 ;;
  esac
done

[ "$BACKEND" = 1 ] && echo "backend"
[ "$AI" = 1 ] && echo "ai"
[ "$TRAINER" = 1 ] && echo "trainer"
[ "$PACKAGES" = 1 ] && echo "packages"
