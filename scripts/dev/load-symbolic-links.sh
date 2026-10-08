#!/bin/sh
set -e
cd "$(dirname "$0")/.."
for d in apps/frontend apps/backend; do
  [ -d "$d" ] && ln -sf ../../../.env "$d/.env"
done
