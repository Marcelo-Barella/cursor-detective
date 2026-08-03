# cursor-detective reference

Read-only path tables and chat-layer examples. Not playbooks — use `SKILL.md` for the investigation pipeline.

## Platform paths

| Artifact | Linux | macOS | Windows |
|----------|-------|-------|---------|
| Cursor `User/` config | `~/.config/Cursor/User/` | `~/Library/Application Support/Cursor/User/` | `%APPDATA%/Cursor/User/` |
| Global `state.vscdb` | `.../globalStorage/state.vscdb` | same relative under User | same relative under User |
| Workspace `state.vscdb` | `.../workspaceStorage/<hash>/state.vscdb` | same | same |
| Agent transcripts / project metadata | `~/.cursor/projects/<projectKey>/` | same | same |
| Chat store trees | `~/.cursor/chats/<workspaceKey>/` | same | same |
| Import activation staging | `~/.cursor/import-activation/` (`pending.json`, `result.json`) | same | same |

Global backup used by transport: `globalStorage/state.vscdb.sync.backup`.

## `state.vscdb`

SQLite with at least:

| Table | Role |
|-------|------|
| `ItemTable` | Key/value sidebar state. Composer list: `composer.composerHeaders`, `composer.composerData`. |
| `cursorDiskKV` | Per-composer blobs. Keys like `composerData:<uuid>` and `bubbleId:<uuid>:<bubbleId>` drive Composer UI (tool cards, MCP blocks). |

Probe with `inspect-state-vscdb.sh` (read-only `file:...?mode=ro`). Default DB is global; pass `--workspace-storage-id` or `--db`.

### `conversationState` and `agentKv:blob:*`

| Field / key | Format | Decode |
|-------------|--------|--------|
| `composerData:<uuid>` → `conversationState` | `~` + base64(protobuf index of 32-byte blob hashes) + `blobEncryptionKey` | `decode-conversation-state.sh --composer-id UUID` lists `agentKv:blob:*` refs; `--blob HASH` decodes payload |
| `cursorDiskKV` → `agentKv:blob:<64-hex>` | Protobuf wire (agent loop state) | `decode-conversation-state.sh --blob HASH` |

Examples:

```bash
./decode-conversation-state.sh --composer-id <uuid>
./decode-conversation-state.sh --list-blobs 10
./decode-conversation-state.sh --blob <64-hex> --hex-dump 256 --out /tmp/blob.bin
```

## Workbench bundle

Typical relative path under install root:

`resources/app/out/vs/workbench/workbench.desktop.main.js`

Linux may ship as AppImage; mount or extract before grepping. `locate-cursor.sh` searches common roots and lists `cursor*.AppImage` candidates when no install tree is found.

**Mandatory fallback (Linux):** when `WORKBENCH_JS` is empty but Cursor is running, use the live mount:

`/tmp/.mount_cursor*/usr/share/cursor/resources/app/out/vs/workbench/workbench.desktop.main.js`

Deep extract: `grep -oE 'out-build/vs/workbench/[^"]+' workbench.desktop.main.js | grep -iE '<theme-keywords>' | sort -u`

macOS/Windows v1: `probe_status=skipped` — tag **Unknown** in reports after documenting attempts; cite canonical paths from this table.

## Examples (not playbooks): four chat persistence layers

From transport-chat / Cursor Sync (condensed):

| Layer | Location | Consumer |
|-------|----------|----------|
| 1 — Transcripts | `~/.cursor/projects/<projectKey>/agent-transcripts/*.jsonl` | Archival, export bundles |
| 2 — `store.db` | Under `~/.cursor/chats/<workspaceKey>/.../store.db` | CLI import/export (Merkle `meta` + `blobs`) |
| 3 — Sidebar `state.vscdb` | Global + workspace `ItemTable` | Chat list / headers in IDE |
| 4 — IDE activation | `cursorDiskKV` + `composer.*` APIs | Opening a chat in Composer; extension writes activation, not always all of layer 3 |

**Confirmed vs inferred:** JSONL alone does not restore tool/MCP UI — **Confirmed** when `cursorDiskKV` keys exist for the composer UUID. `store.db` is often written by Python during import; IDE reads `cursorDiskKV` for bubble rendering.

Two-phase transport: Phase A (disk + `state.vscdb` merge, Cursor quit) vs Phase B (`composer.createComposer`, `pending.json` watcher). See cursor-sync `docs/chat-import-activate.md`.

## `grep-workbench.sh` defaults

Built-in patterns (when no `--pattern`):

- `toolFormerData`
- `composerData`
- `cursorDiskKV`
- `store.db`
- `composer.composerHeaders`
- `createComposer`

Output is truncated to `TRUNCATE_MAX` snippets per pattern.

## cursor-sync cross-link

When the open workspace is [cursor-sync](https://github.com/Marcelo-Barella/cursor-sync):

- Bundled transport reference: `resources/transport-chat/reference.md`
- Activation flow: `docs/chat-import-activate.md`
- Extension Chats tab replaces deprecated `/transport-chat` skill install (v0.7.0+)

Use **cursor-detective** for read-only forensics; use **Cursor Sync Chats** or transport scripts for export/import.
