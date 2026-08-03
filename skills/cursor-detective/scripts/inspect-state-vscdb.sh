#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

DB=""
WS_ID=""
COMPOSER_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db) DB="$2"; shift 2 ;;
    --workspace-storage-id) WS_ID="$2"; shift 2 ;;
    --composer-id) COMPOSER_ID="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: inspect-state-vscdb.sh [--db PATH] [--workspace-storage-id ID] [--composer-id UUID]"
      exit 0 ;;
    *) die "unknown arg: $1" ;;
  esac
done

require_cmd sqlite3

if [[ -z "$DB" && -n "$WS_ID" ]]; then
  DB="$(workspace_state_db "$WS_ID")"
elif [[ -z "$DB" ]]; then
  DB="$(global_state_db)"
fi

[[ -f "$DB" ]] || die "state.vscdb not found: $DB"

emit_header "inspect-state-vscdb.sh" "read-only"
kv "db" "$DB"

sqlite3 "file:${DB}?mode=ro" <<'SQL'
.headers off
.mode list
SELECT 'table=' || name FROM sqlite_master WHERE type='table' ORDER BY 1;
SQL

composer_keys="$(sqlite3 "file:${DB}?mode=ro" "SELECT COUNT(*) FROM ItemTable WHERE key LIKE 'composer.%';" 2>/dev/null || echo 0)"
kv "itemtable_composer_key_count" "$composer_keys"

sqlite3 "file:${DB}?mode=ro" <<'SQL' || true
.headers on
.mode csv
SELECT key, length(value) AS value_len FROM ItemTable WHERE key LIKE 'composer.%' LIMIT 10;
SQL

kv "cursorDiskKV_total" "$(sqlite3 "file:${DB}?mode=ro" "SELECT COUNT(*) FROM cursorDiskKV;" 2>/dev/null || echo 0)"

sqlite3 "file:${DB}?mode=ro" <<'SQL' || true
.headers on
.mode csv
SELECT substr(key,1,instr(key||':',':')-1) AS prefix, COUNT(*) AS n
FROM cursorDiskKV
GROUP BY 1
ORDER BY n DESC
LIMIT 10;
SQL

if [[ -n "$COMPOSER_ID" ]]; then
  kv "composer_id" "$COMPOSER_ID"
  n="$(sqlite3 "file:${DB}?mode=ro" "SELECT COUNT(*) FROM cursorDiskKV WHERE key LIKE 'bubbleId:${COMPOSER_ID}:%';")"
  kv "bubble_keys_for_composer" "$n"
  sqlite3 "file:${DB}?mode=ro" "SELECT key FROM cursorDiskKV WHERE key='composerData:${COMPOSER_ID}' OR key LIKE 'bubbleId:${COMPOSER_ID}:%' LIMIT 5;"
fi
