#!/bin/sh
set -e

echo "Checking Python formatting (black)..."
black --check apps/backend apps/ai apps/trainer packages/python
