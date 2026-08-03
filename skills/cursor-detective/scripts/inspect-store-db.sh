#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

DB=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --db) DB="$2"; shift 2 ;;
    -h|--help) echo "Usage: inspect-store-db.sh --db PATH"; exit 0 ;;
    *) die "unknown arg: $1" ;;
  esac
done

[[ -n "$DB" ]] || die "--db PATH required"
[[ -f "$DB" ]] || die "store.db not found: $DB"
require_cmd sqlite3

emit_header "inspect-store-db.sh"
kv "db" "$DB"

sqlite3 "file:${DB}?mode=ro" ".schema"

if sqlite3 "file:${DB}?mode=ro" "SELECT name FROM sqlite_master WHERE type='table' AND name='meta';" | grep -q meta; then
  kv "meta_table" "present"
  sqlite3 "file:${DB}?mode=ro" "SELECT key, length(value) FROM meta LIMIT 20;"
else
  kv "meta_table" "absent"
  kv "schema_warning" "not Merkle-style store (no meta table)"
fi

if sqlite3 "file:${DB}?mode=ro" "SELECT name FROM sqlite_master WHERE type='table' AND name='blobs';" | grep -q blobs; then
  kv "blob_count" "$(sqlite3 "file:${DB}?mode=ro" "SELECT COUNT(*) FROM blobs;")"
fi
