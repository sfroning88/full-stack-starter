#!/bin/sh
set -e
cd "$(dirname "$0")/.."
for d in apps/dashboard apps/backend apps/ai apps/trainer; do
  [ -d "$d" ] && ln -sf ../../../.env "$d/.env"
done
