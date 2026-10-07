#!/usr/bin/env sh
set -e

die() {
  printf '%s\n' "$1" >&2
  printf '%s\n' "→ Fix using the migration-safety skill: .cursor/skills/migration-safety/SKILL.md" >&2
  exit 1
}

STAGED=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
[ -z "$STAGED" ] && exit 0

migration_files=$(printf '%s\n' $STAGED | grep -E '^packages/db/prisma/migrations/[^/]+/migration\.sql$' | sort -u || true)
[ -z "$migration_files" ] && exit 0

echo "Migration safety checks (staged migration.sql; see .cursor/skills/migration-safety/SKILL.md)..."

check_drop_add_needs_update() {
  content=$1
  display=$2
  if ! grep -q 'DROP COLUMN' "$content" || ! grep -q 'ADD COLUMN' "$content"; then
    return 0
  fi
  drop_line=$(grep -n 'DROP COLUMN' "$content" | head -1 | cut -d: -f1)
  update_line=$(grep -nE '^[[:space:]]*UPDATE[[:space:]]' "$content" | head -1 | cut -d: -f1)
  if [ -z "$update_line" ]; then
    die "FAIL: $display — DROP COLUMN and ADD COLUMN without an UPDATE to backfill/rename. Add UPDATE before DROP (see SKILL.md)."
  fi
  if [ "$update_line" -ge "$drop_line" ]; then
    die "FAIL: $display — first UPDATE must appear before first DROP COLUMN when both DROP and ADD COLUMN are present."
  fi
}

check_create_has_if_not_exists() {
  content=$1
  display=$2
  line_no=0
  while IFS= read -r line || [ -n "$line" ]; do
    line_no=$((line_no + 1))
    trimmed=$(printf '%s\n' "$line" | sed 's/^[[:space:]]*//')
    [ -z "$trimmed" ] && continue
    case "$trimmed" in
      '--'*) continue ;;
    esac
    case "$line" in
      *[Cc][Rr][Ee][Aa][Tt][Ee][[:space:]]*[Uu][Nn][Ii][Qq][Uu][Ee][[:space:]]*[Ii][Nn][Dd][Ee][Xx][[:space:]]*)
        case "$line" in
          *'IF NOT EXISTS'*) ;;
          *) die "FAIL: $display:$line_no — CREATE UNIQUE INDEX without IF NOT EXISTS: ${line}" ;;
        esac
        ;;
      *[Cc][Rr][Ee][Aa][Tt][Ee][[:space:]]*[Ii][Nn][Dd][Ee][Xx][[:space:]]*)
        case "$line" in
          *'IF NOT EXISTS'*) ;;
          *) die "FAIL: $display:$line_no — CREATE INDEX without IF NOT EXISTS: ${line}" ;;
        esac
        ;;
      *[Cc][Rr][Ee][Aa][Tt][Ee][[:space:]]*[Tt][Aa][Bb][Ll][Ee][[:space:]]*)
        case "$line" in
          *'IF NOT EXISTS'*) ;;
          *) die "FAIL: $display:$line_no — CREATE TABLE without IF NOT EXISTS: ${line}" ;;
        esac
        ;;
    esac
  done <"$content"
}

check_banned_partial_index_names() {
  content=$1
  display=$2
  for name in \
    idx_quickbooks_online_customer_qbo_parent_id \
    idx_quickbooks_online_invoice_qbo_customer_id
  do
    if grep -qF "$name" "$content"; then
      die "FAIL: $display — disallowed index name \"$name\" (partial / stray index list; see SKILL.md)."
    fi
  done
}

check_does_not_contain_mlflow_schema() {
  content=$1
  display=$2
  line_no=0
  while IFS= read -r line || [ -n "$line" ]; do
    line_no=$((line_no + 1))
    trimmed=$(printf '%s\n' "$line" | sed 's/^[[:space:]]*//')
    [ -z "$trimmed" ] && continue
    case "$trimmed" in
      '--'*) continue ;;
    esac
    case "$line" in
      *[Mm][Ll][Ff][Ll][Oo][Ww]*)
        die "FAIL: $display:$line_no — Prisma migrations must not touch schema mlflow (Alembic-owned): ${line}"
        ;;
    esac
  done <"$content"
}

for f in $migration_files; do
  tmp=$(mktemp)
  if ! git show ":$f" >"$tmp" 2>/dev/null; then
    rm -f "$tmp"
    die "FAIL: could not read staged contents of $f (git show :path)."
  fi
  check_drop_add_needs_update "$tmp" "$f"
  check_create_has_if_not_exists "$tmp" "$f"
  check_banned_partial_index_names "$tmp" "$f"
  check_does_not_contain_mlflow_schema "$tmp" "$f"
  rm -f "$tmp"
done

echo "Migration safety: OK."