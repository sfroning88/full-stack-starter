#!/bin/sh
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage: $0 {up|down|nuke|status}"
  echo ""
  echo "  up      Start the local Redis container"
  echo "  down    Stop the local Redis container (preserves data)"
  echo "  nuke    Stop and destroy the container + volume"
  echo "  status  Show container status and ping Redis"
  exit 1
}

cmd_up() {
  echo "Starting local Redis..."
  docker compose up -d redis
  echo "Waiting for Redis to be healthy..."
  maxWaitSeconds=30
  elapsed=0
  until docker exec local-redis redis-cli ping > /dev/null 2>&1; do
    elapsed=$((elapsed + 1))
    if [ "$elapsed" -ge "$maxWaitSeconds" ]; then
      echo "Redis did not become ready within ${maxWaitSeconds}s." >&2
      exit 1
    fi
    sleep 1
  done
  echo "Redis is ready at redis://localhost:6379"
}

cmd_down() {
  echo "Stopping local Redis (data preserved)..."
  docker compose stop redis
  echo "Local Redis stopped."
}

cmd_nuke() {
  echo "Destroying Redis container and volume..."
  docker compose down -v
  echo "Local Redis nuked."
}

cmd_status() {
  echo "=== Container Status ==="
  docker compose ps
  echo ""
  echo "=== Redis Ping ==="
  docker exec local-redis redis-cli ping || echo "(container not running)"
}

case "${1:-}" in
  up)     cmd_up ;;
  down)   cmd_down ;;
  nuke)   cmd_nuke ;;
  status) cmd_status ;;
  *)      usage ;;
esac
