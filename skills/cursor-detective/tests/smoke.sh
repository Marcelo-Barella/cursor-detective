#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS="${ROOT}/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

STATE="${TMP}/state.vscdb"
sqlite3 "$STATE" <<'SQL'
CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE cursorDiskKV (key TEXT PRIMARY KEY, value TEXT);
INSERT INTO ItemTable VALUES ('composer.composerHeaders', '{"allComposers":[]}');
INSERT INTO cursorDiskKV VALUES ('composerData:00000000-0000-4000-8000-000000000001', '{}');
INSERT INTO cursorDiskKV VALUES ('bubbleId:00000000-0000-4000-8000-000000000001:b1', '{}');
SQL

out="${TMP}/inspect-state.out"
"${SCRIPTS}/inspect-state-vscdb.sh" --db "$STATE" --composer-id '00000000-0000-4000-8000-000000000001' >"$out"
grep -q 'bubble_keys_for_composer=1' "$out"

STORE="${TMP}/store.db"
sqlite3 "$STORE" <<'SQL'
CREATE TABLE meta (key TEXT PRIMARY KEY, value BLOB);
CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB);
INSERT INTO meta VALUES ('k', 'v');
INSERT INTO blobs VALUES ('1', zeroblob(1));
SQL
out="${TMP}/inspect-store.out"
"${SCRIPTS}/inspect-store-db.sh" --db "$STORE" >"$out"
grep -q 'blob_count=1' "$out"

STATE_B="${TMP}/state-b.vscdb"
sqlite3 "$STATE_B" 'CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT);'
out="${TMP}/compare-sqlite.out"
"${SCRIPTS}/compare-sqlite-meta.sh" --a "$STATE" --b "$STATE_B" >"$out"
grep -q 'schema_diff=different' "$out"

mkdir -p "${TMP}/da" "${TMP}/db"
echo x > "${TMP}/da/a.txt"
out="${TMP}/compare-dirs.out"
"${SCRIPTS}/compare-dirs.sh" --a "${TMP}/da" --b "${TMP}/db" >"$out"
grep -q '^diff_line=' "$out"

"${SCRIPTS}/scan-paths.sh" >/dev/null
"${SCRIPTS}/locate-cursor.sh" >/dev/null

# Minimal protobuf-like blob: field 1, len-delimited "hi"
BLOB_HEX="0a026869"
python3 -c "
import binascii, sqlite3
b = binascii.unhexlify('${BLOB_HEX}')
c = sqlite3.connect('${STATE}')
c.execute(
    'INSERT INTO cursorDiskKV VALUES (?,?)',
    ('agentKv:blob:0000000000000000000000000000000000000000000000000000000000000001', b),
)
c.commit()
"
out="${TMP}/decode-blob.out"
"${SCRIPTS}/decode-conversation-state.sh" --db "$STATE" --blob 0000000000000000000000000000000000000000000000000000000000000001 --hex-dump 0 >"$out"
grep -q 'detected_format=protobuf_wire' "$out"
grep -qF "'utf8': 'hi'" "$out"

out="${TMP}/decode-composer.out"
"${SCRIPTS}/decode-conversation-state.sh" --db "$STATE" --composer-id '00000000-0000-4000-8000-000000000001' >"$out"
grep -q 'conversationState_kind=absent' "$out"

out="${TMP}/decode-tilde.out"
sqlite3 "$STATE" "INSERT INTO cursorDiskKV VALUES ('composerData:00000000-0000-4000-8000-000000000002', '{\"conversationState\":\"~CAA=\",\"unifiedMode\":\"agent\"}');"
"${SCRIPTS}/decode-conversation-state.sh" --db "$STATE" --composer-id '00000000-0000-4000-8000-000000000002' >"$out"
grep -q 'conversationState_kind=tilde_base64_protobuf' "$out"
grep -q 'conversationState_blob_ref_count=0' "$out"

echo "smoke: OK"
