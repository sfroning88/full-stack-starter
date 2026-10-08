#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 {up|down|nuke|status}"
  echo ""
  echo "  up      Start the local Postgres container"
  echo "  down    Stop the local Postgres container (preserves data)"
  echo "  nuke    Stop and destroy the container + volume"
  echo "  status  Show container status and Postgres readiness"
  exit 1
}

cmd_up() {
  echo "Starting local Postgres..."
  docker compose up -d postgres
  echo "Waiting for Postgres to be healthy..."
  maxWaitSeconds=60
  elapsed=0
  until docker exec local-postgres pg_isready -U admin -d postgres > /dev/null 2>&1; do
    elapsed=$((elapsed + 1))
    if [ "$elapsed" -ge "$maxWaitSeconds" ]; then
      echo "Postgres did not become ready within ${maxWaitSeconds}s." >&2
      exit 1
    fi
    sleep 1
  done
  echo "Postgres is ready at postgresql://admin:admin@localhost:5432/postgres"
}

cmd_down() {
  echo "Stopping local Postgres (data preserved)..."
  docker compose stop postgres
  echo "Local Postgres stopped."
}

cmd_nuke() {
  echo "Destroying Postgres container and volume..."
  docker compose down -v
  echo "Local Postgres nuked."
}

cmd_status() {
  echo "=== Container Status ==="
  docker compose ps
  echo ""
  echo "=== Postgres Readiness ==="
  docker exec local-postgres pg_isready -U admin -d postgres || echo "(container not running)"
}

case "${1:-}" in
  up)     cmd_up ;;
  down)   cmd_down ;;
  nuke)   cmd_nuke ;;
  status) cmd_status ;;
  *)      usage ;;
esac
