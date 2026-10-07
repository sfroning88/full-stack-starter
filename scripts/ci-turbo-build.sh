#!/usr/bin/env bash
set -euo pipefail

EVENT_NAME="${CI_EVENT_NAME:?CI_EVENT_NAME is required}"
BASE_REF="${CI_BASE_REF:-}"
BEFORE="${CI_EVENT_BEFORE:-}"
EMPTY_SHA="0000000000000000000000000000000000000000"

case "$EVENT_NAME" in
pull_request)
  if [ -z "$BASE_REF" ]; then
    echo "ci-turbo-build: CI_BASE_REF is required for pull_request" >&2
    exit 1
  fi
  pnpm exec turbo run build --filter="...[origin/${BASE_REF}]"
  ;;
push)
  if [ -z "$BEFORE" ] || [ "$BEFORE" = "$EMPTY_SHA" ]; then
    pnpm exec turbo run build
  else
    pnpm exec turbo run build --filter="...[${BEFORE}]"
  fi
  ;;
*)
  pnpm exec turbo run build
  ;;
esac
