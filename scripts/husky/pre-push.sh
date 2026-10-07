#!/usr/bin/env sh
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1

pnpm run check:python-format
pnpm build

if [ -f scripts/husky/pre-push-extra.sh ]; then
    sh scripts/husky/pre-push-extra.sh
fi
