#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Cleaning build artifacts under $ROOT ..."

echo "  - node_modules, .next, .turbo, dist directories"
find . -type d \
  \( -name node_modules -o -name .next -o -name .turbo -o -name dist \) \
  -prune -exec rm -rf {} +

echo "  - .tsbuildinfo files"
find . -type f -name "*.tsbuildinfo" \
  -not -path "*/node_modules/*" \
  -exec rm -f {} +

echo "  - Prisma generated client (packages/db/prisma/src/generated)"
rm -rf packages/db/prisma/src/generated

echo "  - macOS Finder duplicates from iCloud sync"
find . -type f \
  \( \
    -name "* [0-9].*"   -o -name "* [0-9]"  -o \
    -name "* [0-9][0-9].*"   -o -name "* [0-9][0-9]" \
  \) \
  -not -path "*/node_modules/*" \
  -not -path "*/.next/*" \
  -exec rm -f {} +

echo ""
echo "Done!"
echo "Next: pnpm install && pnpm --filter @fiery/db db:generate"
