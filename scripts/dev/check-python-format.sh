#!/bin/sh
set -e

echo "Checking Python formatting (black)..."
black --check apps/backend packages/python
