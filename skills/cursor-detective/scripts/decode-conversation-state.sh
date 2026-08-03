#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

DB=""
COMPOSER_ID=""
BLOB=""
LIST_BLOBS=""
HEX_DUMP="128"
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db) DB="$2"; shift 2 ;;
    --workspace-storage-id) DB="$(workspace_state_db "$2")"; shift 2 ;;
    --composer-id) COMPOSER_ID="$2"; shift 2 ;;
    --blob) BLOB="$2"; shift 2 ;;
    --list-blobs) LIST_BLOBS="$2"; shift 2 ;;
    --hex-dump) HEX_DUMP="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    -h|--help)
      cat <<'EOF'
Usage: decode-conversation-state.sh [options]

Read-only decode of Cursor agent conversation blobs in state.vscdb.

  --composer-id UUID     Show composerData + conversationState metadata
  --blob HASH            Decode agentKv:blob:<HASH> (protobuf wire + strings)
  --list-blobs N         List N largest agentKv:blob keys by size
  --db PATH              state.vscdb (default: global)
  --workspace-storage-id ID  Workspace state.vscdb
  --hex-dump BYTES       Trailing hex dump (default 128, 0=off)
  --out PATH             Write raw blob bytes when using --blob

Notes:
  composerData.conversationState often starts with "~" (encrypted ref).
  Offline decrypt is not supported; decode raw blobs via --blob instead.
EOF
      exit 0
      ;;
    *) die "unknown arg: $1" ;;
  esac
done

require_cmd python3

args=()
[[ -n "$DB" ]] && args+=(--db "$DB")
[[ -n "$COMPOSER_ID" ]] && args+=(--composer-id "$COMPOSER_ID")
[[ -n "$BLOB" ]] && args+=(--blob "$BLOB")
[[ -n "$LIST_BLOBS" ]] && args+=(--list-blobs "$LIST_BLOBS")
args+=(--hex-dump "$HEX_DUMP")
[[ -n "$OUT" ]] && args+=(--out "$OUT")

exec python3 "${SCRIPT_DIR}/decode_conversation_state.py" "${args[@]}"
