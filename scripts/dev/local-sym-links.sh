#!/bin/sh
set -e
cd "$(dirname "$0")/.."
for dir in apps/frontend apps/backend apps/compute; do
  [ -d "$dir" ] && ln -sf ../../../.env "$dir/.env"
done
