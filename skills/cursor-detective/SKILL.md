---
name: cursor-detective
description: >-
  Deep read-only forensics on Cursor local install, config, SQLite state,
  workbench bundles, and project artifacts. Always probes to maximum depth
  in one pass (workbench modules, DBs, transcripts) without asking permission.
  Writes .cursor/plans/detective-<theme>.plan.md. Use when the user invokes
  /cursor-detective or asks to reverse-engineer Cursor internals, scan
  state.vscdb, inspect AppImage/workbench, or compare on-disk behavior.
disable-model-invocation: true
mode: true
icon: cursor-logo
color: brand
reminder: Cursor Detective — read-only forensics only; probe to max depth in one pass; write .cursor/plans/detective-<theme>.plan.md; never modify ~/.cursor or install trees.
---

# cursor-detective

Read-only investigation skill. **Do not modify** `~/.cursor`, `~/.config/Cursor`, or install trees except writing the report under the **current workspace**.

## Depth policy (mandatory)

Every run goes **as deep as evidence allows in one pass**. Do not stop at inventory or high-level summaries when the workbench bundle, DBs, or project artifacts are reachable.

**Always do without asking:**

- Resolve `workbench.desktop.main.js` (extracted install **or** running AppImage mount under `/tmp/.mount_cursor*`) and grep theme-relevant patterns plus built-ins.
- List embedded module paths (`out-build/vs/workbench/...`, `../packages/...`) for the theme; extract at least one confirming snippet per major subsystem named in findings.
- Run theme-matched scripts from Phase 4 even when Phase 2 alone would suffice.
- Launch parallel subagents (Phase 3) whenever the theme is broad **or** workbench/DB/project probes are independent — not only for `general-scan`.

**Never:**

- Ask whether to go deeper, trace a subsystem, or run extra probes.
- End the user-facing reply with permission prompts ("say the word", "want me to…", "if you want…").
- Defer workbench/module analysis to **Gaps & follow-ups** without attempting mount-path resolution and grep first.

Record unattempted or blocked probes under **Gaps & follow-ups** with what was tried — not as invitations for the user to approve the next step.

## Invocation

`/cursor-detective [theme]`

If theme is empty, use `general-scan`.

## Theme normalization

Same rules as unravel: trim, lowercase, spaces/underscores → `-`, strip non `[a-z0-9-]`, collapse `-`, fallback `general-scan`.

Output file: `.cursor/plans/detective-<theme>.plan.md` (create `.cursor/plans/` if missing).

## Pipeline

### Phase 1 — Frame

1. Normalize theme.
2. Set `PLAN_PATH=".cursor/plans/detective-<theme>.plan.md"`.
3. One paragraph: objective, scope, success criteria.
4. Bullet testable assumptions and unknowns.

### Phase 2 — Discover (scripts, in order)

Resolve this skill's directory (plugin install or `~/.cursor/skills/cursor-detective`), then run from its `scripts/` folder:

1. `./locate-cursor.sh`
2. `./scan-paths.sh`

If a script exits non-zero, record exit code in the plan and continue only when the failure is non-fatal (missing install); stop if `sqlite3` is missing and DB scripts are required.

### Phase 3 — Delegate (parallel probes)

When theme is broad (`general-scan`, `cursor-storage-inventory`), user gave compare targets, **or** Phase 4 includes workbench + DB + project artifacts, launch up to four parallel subagents:

| Agent | Scope |
|-------|--------|
| Install/bundle | AppImage/squashfs, `workbench.desktop.main.js`, `grep-workbench.sh` defaults |
| State DBs | `inspect-state-vscdb.sh` global + latest workspace DB |
| Project artifacts | `~/.cursor/projects/**`, transcripts, `inspect-store-db.sh` on a sample `store.db` |
| Compare | User UUIDs/paths: `compare-dirs.sh` / `compare-sqlite-meta.sh` |

Subagents must paste script output; tag every finding.

### Phase 4 — Extract (by theme)

| Theme signal | Scripts |
|--------------|---------|
| persistence, storage, vscdb, composer | `inspect-state-vscdb.sh`, `inspect-store-db.sh` |
| UI, composer, sidebar, workbench | `grep-workbench.sh` |
| compare, diff, broken vs working | `compare-dirs.sh`, `compare-sqlite-meta.sh` |
| inventory / general | all inspect scripts with default limits |
| agent, composer, runtime, "how does X work" | above + workbench module list + `grep-workbench.sh` for entry points (`createComposer`, `submitChat`, `runAgent`, `agentKv`, theme keywords) |
| conversationState, agentKv blob, decode blob | `decode-conversation-state.sh` (`--composer-id`, `--blob`, `--list-blobs`) |

### Phase 4b — Workbench deep extract (mandatory when bundle reachable)

1. If `locate-cursor.sh` leaves `WORKBENCH_JS` empty, resolve from `/tmp/.mount_cursor*/usr/share/cursor/resources/app/out/vs/workbench/workbench.desktop.main.js` or AppImage extract path; record which path was used.
2. Grep built-ins and theme-specific patterns via `grep-workbench.sh`.
3. Enumerate unique `out-build/vs/workbench/contrib/...` and `../packages/...` module paths matching the theme (`grep -oE` on the bundle file).
4. For each major subsystem in findings, cite at least one **Confirmed** bundle snippet (module header or API string such as `submitChatMaybeAbortCurrent`, `agentKv:blob:`, `TranscriptStore`).

If the bundle is truly unreachable after mount + extract attempts, tag **Unknown** and document every path tried — do not skip this phase silently.

### Phase 5 — Synthesize

Write `PLAN_PATH` using **Report template** below. Run scripts **before** any **Confirmed** finding. Include **Internal code map** whenever Phase 4b ran or the theme concerns runtime/UI/persistence behavior.

## Evidence model

| Tag | Use when |
|-----|----------|
| **Confirmed** | Script stdout or cited path + snippet |
| **Inferred** | Pattern in bundle/DB without runtime proof |
| **Unknown** | Probe ran; no evidence; say what was tried |

Forbidden: inventing keys, APIs, or paths not seen in probes.

## Report template (required section order)

1. **Objective**
2. **Environment** (OS; `locate-cursor.sh`; workbench path used; version/channel if detected)
3. **Scan checklist** (table: script, exit code, one-line result)
4. **Findings** (by subsystem; tagged bullets)
5. **Internal code map** (module table, entry points, implementation snippets — required for runtime/UI/persistence themes and whenever workbench was probed)
6. **Diagram** (mermaid: persistence and/or request flow when in scope)
7. **Gaps & follow-ups** (blocked probes only — no "ask user to approve deeper dive")
8. **Workspace relevance** (optional; e.g. cursor-sync transport)

## Script index

| Script | Purpose |
|--------|---------|
| `locate-cursor.sh` | Install + `WORKBENCH_JS` |
| `scan-paths.sh` | Standard data dir inventory |
| `inspect-state-vscdb.sh` | `--db`, `--workspace-storage-id`, `--composer-id` |
| `inspect-store-db.sh` | `--db PATH` |
| `grep-workbench.sh` | `--pattern`, `--file`, or built-ins |
| `compare-sqlite-meta.sh` | `--a` `--b` |
| `compare-dirs.sh` | `--a` `--b` |
| `decode-conversation-state.sh` | `--composer-id`, `--blob HASH`, `--list-blobs N`, `--db` |

See [reference.md](reference.md) for paths and chat-layer examples.

## Related skills

| Skill | Use instead when |
|-------|------------------|
| transport-chat / Cursor Sync Chats | export/import transport |
| unravel | flow narrative only |
| research | open-repo code, not Cursor product |
| debugger | repro + fix |
