#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

A="" B=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --a) A="$2"; shift 2 ;;
    --b) B="$2"; shift 2 ;;
    -h|--help) echo "Usage: compare-sqlite-meta.sh --a PATH --b PATH"; exit 0 ;;
    *) die "unknown arg: $1" ;;
  esac
done

[[ -f "$A" && -f "$B" ]] || die "both --a and --b must exist"
require_cmd sqlite3

emit_header "compare-sqlite-meta.sh"
kv "a" "$A"
kv "b" "$B"

schema_a="$(sqlite3 "file:${A}?mode=ro" ".schema")"
schema_b="$(sqlite3 "file:${B}?mode=ro" ".schema")"
if [[ "$schema_a" == "$schema_b" ]]; then
  kv "schema_diff" "identical"
else
  kv "schema_diff" "different"
  echo "--- schema_a ---"
  echo "$schema_a"
  echo "--- schema_b ---"
  echo "$schema_b"
fi

while IFS= read -r tbl; do
  [[ -z "$tbl" ]] && continue
  ca="$(sqlite3 "file:${A}?mode=ro" "SELECT COUNT(*) FROM \"${tbl}\";" 2>/dev/null || echo NA)"
  cb="$(sqlite3 "file:${B}?mode=ro" "SELECT COUNT(*) FROM \"${tbl}\";" 2>/dev/null || echo NA)"
  kv "rowcount_${tbl}" "a=${ca} b=${cb}"
done < <(sqlite3 "file:${A}?mode=ro" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1;")
