# Detective: `sand_shared_room_box_tools_kill_switch`

Theme: `feature-flag-sand-shared-room-box-tools-kill-switch`  
Flag: `sand_shared_room_box_tools_kill_switch`  
Cursor: **3.15.1** / product commit `41c5e281845de0ce890a8053a3874064bfbdb8b0` (inventory/evidence listed `…bfbdb8bf`)  
Plan path: `/workspace/workspace/runs/20260805T110539Z/plans/detective-feature-flag-sand-shared-room-box-tools-kill-switch.plan.md`

## 1. Objective

Determine how client feature gate `sand_shared_room_box_tools_kill_switch` is registered in Cursor 3.15.1, whether any `checkFeatureGate` / `useFeatureGate` / `wn` / `dr` helpers consult it, what default applies from inventory vs minified registry (`POe` / `xDe`), how it relates to shared-room / box-tools / sand-multiplayer surfaces, and whether a local override is present.

**Success criteria:** registry entry confirmed, call-site vs registry-only classification with Confirmed snippets, modules list, local override status, full Phase 1–5 + 4b report at this path.

**Assumptions**

- Inventory `default: false` matches minified `default:!1`.
- Desktop client gate registry is `POe` (not `kFe`); glass twin is `xDe`.
- Extract under `runs/20260805T110539Z/extract/new` is authoritative when live install is absent.
- Prefer inventory default when Statsig / overrides are unprobeable.

**Unknowns (pre-probe)**

- Live Statsig remote treatment on this host.
- Whether a developer local override exists in `state.vscdb`.
- Whether any non-string / server-only consumer exists outside this AppImage extract.

## 2. Environment

| Item | Value |
|------|--------|
| OS | Linux (cloud agent VM) |
| `locate-cursor.sh` | `install_status=not_found`, `WORKBENCH_JS=` empty (no live Cursor install) |
| Workbench used | `/workspace/workspace/runs/20260805T110539Z/extract/new/usr/share/cursor/resources/app/out/vs/workbench/workbench.desktop.main.js` |
| Glass twin | `…/workbench.glass.main.js` |
| Version / channel | `product.json`: version=**3.15.1**, quality=stable, commit=`41c5e281845de0ce890a8053a3874064bfbdb8b0` |
| User config / `state.vscdb` | Absent (`~/.config/Cursor/User` missing) |
| Inventory | `/workspace/workspace/runs/20260805T110539Z/feature-flags-inventory.json` → `{name, client:true, default:false}`; root `registry_var`=**POe** |
| Manifest category | `other` |
| Precomputed evidence | `/workspace/workspace/runs/20260805T110539Z/plans/_evidence/sand-shared-room-box-tools-kill-switch.json` |

## 3. Scan checklist

| Script / probe | Exit | One-line result |
|----------------|------|-----------------|
| `locate-cursor.sh` | 0 | No install; `WORKBENCH_JS` empty |
| `scan-paths.sh` | 0 | No Cursor User config / global `state.vscdb`; projects root exists (tiny) |
| `grep-workbench.sh` (desktop, flag) | 0 | **1** hit — registry cluster only (`default:!1`) |
| `grep-workbench.sh` (glass, flag) | 0 | **1** hit — same registry entry |
| `grep-workbench.sh` (builtins) | 0 | `toolFormerData` / `composerData` present (bundle healthy) |
| `grep-workbench.sh` (`sand_multiplayer`) | 0 | **1** hit — neighbor registry-only |
| Full-extract `rg` (flag) | 0 | Hits only in desktop, glass, `out/main.js`, `cursor-agent-host`, `cursor-always-local` (registry copies) |
| `checkFeatureGate` / `useFeatureGate` / `wn` / `dr` for flag | 0 | **Zero** call sites in entire extract; also **zero** `checkFeatureGate("sand_*")` in workbench |
| `inspect-state-vscdb.sh` | 1 | Error: `state.vscdb` not found (no local Statsig/override store) |
| `inspect-store-db.sh` | 1 | `--db PATH required` / no chats store |
| Inventory JSON | — | `default: false`, `client: true` |
| Bundle deep extract (Phase 4b) | — | Registry **POe** / **xDe**; neighbors `sand_multiplayer` → flag → `sand_global_search` / `sand_pr_menu`; adjacent wired `shared_chats` / `shared_canvases` / `cursor_shared_session_file_watcher` ungated by this flag |
| Local override probe | — | No User storage → **none** |

## 4. Findings

### Registry (feature-gate map)

- **Confirmed:** Desktop gate registry is minified as **`POe`**, not `kFe`. Assignment: `POe={agent_goal_continuation:…}`; `c_n=Object.keys(POe)`. Flag sits inside `POe` before the keys enumeration (`POe` start < flag < `c_n`). Module header immediately preceding registry: `out-build/vs/platform/experiments/common/experimentConfig.gen.js`.
- **Confirmed:** Glass twin registry is **`xDe`** (`dct=Object.keys(xDe)`).
- **Confirmed:** Exact entry in both bundles (and registry copies in `out/main.js`, `cursor-agent-host`, `cursor-always-local`):  
  `sand_shared_room_box_tools_kill_switch:{client:!0,default:!1}`  
  → client gate, **default false** (`!1`). Matches inventory. Prefer inventory when Statsig uninitialized — `POe[e]?.default??!1` in `ExperimentService._checkGateWithoutOverride`.
- **Confirmed:** Neighbor cluster (sand family inside `POe`/`xDe`):  
  `sand_stale_root_gc` (default false) →  
  `sand_legacy_store_blob_retirement` (default false) →  
  `sand_multiplayer` (default false) →  
  **`sand_shared_room_box_tools_kill_switch`** (default **false**) →  
  `sand_global_search` (default true) →  
  `sand_pr_menu` (default true) →  
  `sand_auto_disk_saver` (default false) → …

### Call sites (active consumers)

- **Confirmed:** Desktop and glass have **zero** `checkFeatureGate("sand_shared_room_box_tools_kill_switch"…)` / `useFeatureGate("sand_shared_room_box_tools_kill_switch"…)`.
- **Confirmed:** Entire AppImage extract has **zero** `checkFeatureGate` / `useFeatureGate` / `wn(` / `dr(` / `checkGate(` / `getDynamicConfig(` string consumers for this flag (searched workbench, `out/main.js`, and `extensions/*/dist/main.js`).
- **Confirmed:** Every mention of `sand_shared_room_box_tools_kill_switch` is **registry-only** (`:{client:!0,default:!1}`); mention counts desktop=1, glass=1 (plus three registry copies elsewhere). Precomputed evidence `modules_near_mentions: []` matches.
- **Confirmed:** Workbench has **zero** `checkFeatureGate("sand_*")` string args at all in 3.15.1 (entire sand gate family is currently dormant at call-site level in client bundles).
- **Confirmed:** No camelCase symbols `SharedRoom` / `sharedRoom` / `BoxTools` / `boxTools` / `RoomBox` exist in the workbench bundles; substrings `shared_room` / `box_tools` appear **only** inside this flag’s registry key.

### Effective value (Statsig / local)

- **Confirmed:** `ExperimentService._checkGateWithoutOverride` falls back to `POe[e]?.default??!1` (desktop) / `xDe[t]?.default??!1` (glass) when Statsig is missing or throws.
- **Confirmed:** Bundled / inventory default for this flag is **false** (prefer inventory).
- **Unknown:** Live Statsig remote value — no running Cursor / no `state.vscdb` / no Statsig cache on disk.
- **Confirmed:** Local feature-flag override: **none** (no `~/.config/Cursor/User`; override storage key exists in bundle as `workbench.experiments.featureFlagOverrides` but nothing persisted here).

### Semantics (what it would change)

- **Confirmed:** In 3.15.1 client bundles, flipping this gate has **no direct UI/runtime effect** — there is no client call site.
- **Confirmed (adjacent “shared” / kill-switch surfaces, ungated by this flag):**
  - Wired client gates **`shared_chats`** and **`shared_canvases`** gate share-feature enablement / context keys (membership + local-mode checks) — separate names, actively consulted via `checkFeatureGate`.
  - Wired gate **`cursor_shared_session_file_watcher`** mirrors into application storage for main-process shared file watchers — unrelated to “room box tools”.
  - Other `*_kill_switch` / `*killswitch*` gates (`limit_hit_ui_kill_switch`, `keybinding_migration_killswitch`, `bugbot_autorun_killswitch`, `admin_command_denylist_enforcement_killswitch`) are wired; this sand kill switch is not among them.
  - Neighbor sand gate **`sand_multiplayer`** (default false) is likewise **registry-only** — naming implies a future multiplayer / shared-room stack that this kill switch would likely disable once hooked.
- **Inferred:** Name `sand_shared_room_box_tools_kill_switch` + placement immediately after `sand_multiplayer` and before UI sand gates (`sand_global_search` / `sand_pr_menu`) imply a **pre-registered / dormant emergency disable** for shared-room “box tools” (tool UI/actions in a sand multiplayer shared room), not yet hooked in the client.
- **Inferred:** Until call sites land, Statsig treatments for this flag would only matter if future client code consults the gate (or if server/agent runtime uses the same Statsig name — not visible as a string consumer in this extract).

### Confidence

**Confirmed** on registry (`POe`/`xDe`), default **false**, full-extract registry-only classification, adjacent wired `shared_*` distinction, modules, and local-override **none**.  
**Inferred** on intended product meaning (dormant kill switch for sand shared-room box tools / multiplayer tool surface).  
**Unknown** only for remote Statsig treatment on a live client.

## 5. Internal code map

### Module table

| Module path | Role vs theme |
|-------------|----------------|
| `out-build/vs/platform/experiments/common/experimentConfig.gen.js` (via `POe`/`xDe`) | Client gate registry including `sand_shared_room_box_tools_kill_switch` |
| `out-build/vs/workbench/services/experiment/browser/experimentService.js` | `checkFeatureGate`, overrides, `POe`/`xDe` default fallback |
| `out/main.js` / `cursor-agent-host` / `cursor-always-local` | Registry copies only (no dedicated call) |
| `workbench.contrib.sharedSessionFileWatcherGateMirror` | Wired consumer of **sibling** gate `cursor_shared_session_file_watcher` only — not this flag |
| (anonymous share helpers) | Wired consumers of **`shared_chats`** / **`shared_canvases`** only — not this flag |

### Entry points

| Symbol / API | Bundle | Role |
|--------------|--------|------|
| `POe` / `xDe` | desktop / glass | Gate map; entry `sand_shared_room_box_tools_kill_switch:{client:!0,default:!1}` |
| `checkFeatureGate("sand_shared_room_box_tools_kill_switch")` | — | **Absent** in 3.15.1 extract |
| `sand_multiplayer` | both | Immediate neighbor sand gate; also registry-only |
| `shared_chats` / `shared_canvases` | both | Separate wired share gates (ungated by this flag) |
| `workbench.experiments.featureFlagOverrides` | both | Override storage key; empty/absent on this host |

### Implementation snippets (Confirmed)

**Registry (desktop `POe`, glass `xDe`):**

```text
sand_stale_root_gc:{client:!0,default:!1},
sand_legacy_store_blob_retirement:{client:!0,default:!1},
sand_multiplayer:{client:!0,default:!1},
sand_shared_room_box_tools_kill_switch:{client:!0,default:!1},
sand_global_search:{client:!0,default:!0},
sand_pr_menu:{client:!0,default:!0},
sand_auto_disk_saver:{client:!0,default:!1},
disable_smart_auto_show_routed_model:{client:!0,default:!1},
```

**Default fallback (`experimentService.js`):**

```text
_checkGateWithoutOverride(e,t){
  if(this._statsig) try { return this._statsig.checkGate(e,t) }
  catch { …; return POe[e]?.default??!1 }  // glass: xDe[t]?.default??!1
  else return … POe[e]?.default??!1
}
```

**Sibling wired share gates (not this flag):**

```text
checkFeatureGate("shared_canvases",{disableExposureLog:!0})
checkFeatureGate("shared_chats",{disableExposureLog:!1})
// SharedSessionFileWatcherGateMirror:
checkFeatureGate(oEh /* cursor_shared_session_file_watcher */,{disableExposureLog:!0})
```

## 6. Diagram

```mermaid
flowchart TD
  subgraph registry [Gate registry POe / xDe]
    SRBT["sand_shared_room_box_tools_kill_switch<br/>client true, default false"]
    SMP["sand_multiplayer<br/>default false — also registry-only"]
    SCH["shared_chats / shared_canvases<br/>WIRED — different names"]
    SSFW["cursor_shared_session_file_watcher<br/>WIRED — different feature"]
  end
  subgraph clients [3.15.1 client extract]
    none["No checkFeatureGate / useFeatureGate / wn / dr<br/>for sand_shared_room_box_tools_kill_switch"]
    shareUI["Share feature / context-key enablement"]
    mirror["SharedSessionFileWatcherGateMirror"]
  end
  SRBT --> none
  SMP -.->|neighbor; no string gate read| none
  SCH -->|checkFeatureGate| shareUI
  SSFW -->|checkFeatureGate| mirror
```

## 7. Gaps & follow-ups

- Live Statsig treatment unprobeable (no `state.vscdb`, no running client).
- Server-side or agent-runtime consumers of Statsig gate `sand_shared_room_box_tools_kill_switch` are outside string-searchable client bundles — not attempted beyond this AppImage extract.
- No `SharedRoom` / `BoxTools` implementation symbols found; intended shared-room box-tools pipeline not reverse-engineered beyond confirming dormancy and neighbor placement after `sand_multiplayer`.
- Neighbor `sand_multiplayer` likewise lacks string consumers; shared-room product surface not yet hooked in this build.
- When future builds add `checkFeatureGate("sand_shared_room_box_tools_kill_switch")`, re-run Phase 4b to locate modules.

## 8. Workspace relevance

Feature-flag inventory + extract under `/workspace/workspace/runs/20260805T110539Z/` are the authoritative inputs for this Notion sync / flag catalog run. Precomputed evidence JSON matched probes (registry-only samples; empty `modules_near_mentions`); deep extract confirmed **POe**/**xDe**, default false, and zero call sites across the full extract.

---

### Verdict summary

| Field | Value |
|-------|--------|
| Confidence | **Confirmed** (registry-only / default false); **Inferred** (intended shared-room box-tools kill switch); **Unknown** (live Statsig) |
| What it changes | **Nothing in 3.15.1 client** — registry-only; no `checkFeatureGate` consumer. Name/neighbors imply a future emergency disable for sand shared-room box tools (distinct from wired `shared_chats` / `shared_canvases` / `cursor_shared_session_file_watcher`). |
| Modules | `experimentConfig.gen.js` (`POe`/`xDe`), `experimentService.js`; registry copies in `out/main.js` / agent-host / always-local; adjacent ungated wired share surfaces (`shared_chats`, `shared_canvases`, SharedSessionFileWatcherGateMirror) |
| Local Override | **none** |
| Inventory default | **false** (`!1`) |
| Registry var | **POe** (desktop); **xDe** (glass) — not `kFe` |
| Call sites | **0** (registry-only) |
