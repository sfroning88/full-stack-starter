#!/usr/bin/env bash
set -euo pipefail

# Generates a new migration SQL file using `prisma migrate diff` (no shadow DB).
# `migrate dev --create-only` needs a shadow database which cannot replay
# Supabase-managed schemas (auth.*), so we diff schema files directly instead.
#
# From repo root: pnpm db:migrate <name>
# Example: pnpm db:migrate add_expense_tables

NAME="${1:-}"
if [[ -z "$NAME" || "$NAME" == *"/"* || "$NAME" == *".."* ]]; then
  echo "error: invalid or missing migration name (first argument)" >&2
  echo "usage: pnpm db:migrate <migration_name>" >&2
  echo "example: pnpm db:migrate init" >&2
  exit 1
fi
shift

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRISMA_DIR="$(dirname "$SCRIPT_DIR")"
MIGRATIONS_DIR="$PRISMA_DIR/migrations"

TIMESTAMP="$(date -u '+%Y%m%d%H%M%S')"
MIGRATION_DIR="$MIGRATIONS_DIR/${TIMESTAMP}_${NAME}"

sql="$(prisma migrate diff \
  --from-config-datasource \
  --to-schema "$PRISMA_DIR/schema" \
  --script)"

if [[ -z "$sql" || "$sql" == "-- This is an empty migration." ]]; then
  echo "No schema changes detected — nothing to migrate."
  exit 0
fi

mkdir -p "$MIGRATION_DIR"
printf '%s\n' "$sql" > "$MIGRATION_DIR/migration.sql"
echo "Created migration: ${TIMESTAMP}_${NAME}"
echo "  → $MIGRATION_DIR/migration.sql"
