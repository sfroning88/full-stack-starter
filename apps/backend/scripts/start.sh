#!/bin/bash
set -e
if [[ "$SERVICE_TYPE" == "api" ]]; then
  exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
else
  exec python -m src/worker_runner.py
fi
