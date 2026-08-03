#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

FILE=""
PATTERN=""
BUILTIN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file) FILE="$2"; shift 2 ;;
    --pattern) PATTERN="$2"; shift 2 ;;
    --builtin) BUILTIN=true; shift ;;
    -h|--help) echo "Usage: grep-workbench.sh [--file PATH] [--pattern REGEX] [--builtin]"; exit 0 ;;
    *) die "unknown arg: $1" ;;
  esac
done

if [[ -z "$FILE" ]]; then
  wb="$( "${SCRIPT_DIR}/locate-cursor.sh" | awk -F= '/^WORKBENCH_JS=/{print $2}' | tail -n 1 )"
  FILE="$wb"
fi

[[ -f "$FILE" ]] || die "workbench JS not found (pass --file PATH)"

emit_header "grep-workbench.sh" "truncation_max=${TRUNCATE_MAX}"

patterns=()
if [[ "$BUILTIN" == true || -z "$PATTERN" ]]; then
  patterns=(toolFormerData composerData cursorDiskKV store.db composer.composerHeaders createComposer)
elif [[ -n "$PATTERN" ]]; then
  patterns=("$PATTERN")
fi

for pat in "${patterns[@]}"; do
  kv "pattern" "$pat"
  hits="$(grep -oE ".{0,40}${pat}.{0,40}" "$FILE" 2>/dev/null | head -n "${TRUNCATE_MAX}" || true)"
  count="$(grep -c "$pat" "$FILE" 2>/dev/null || echo 0)"
  kv "hit_count" "$count"
  if [[ "$(echo "$hits" | wc -l)" -ge "${TRUNCATE_MAX}" ]]; then
    kv "truncated" "true"
  fi
  echo "$hits" | sed 's/^/snippet=/' || true
done
