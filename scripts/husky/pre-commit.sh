#!/usr/bin/env sh
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1

pnpm lint-staged
pnpm type-check
pnpm check:migration-safety
pnpm check:unit-tests
