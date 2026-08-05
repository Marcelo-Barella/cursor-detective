# Detective: `sand_stale_root_gc`

Theme: `feature-flag-sand-stale-root-gc`  
Flag: `sand_stale_root_gc`  
Cursor: **3.15.1** / product commit `41c5e281845de0ce890a8053a3874064bfbdb8b0` (inventory/evidence listed `…bfbdb8bf`)  
Plan path: `/workspace/workspace/runs/20260805T110539Z/plans/detective-feature-flag-sand-stale-root-gc.plan.md`

## 1. Objective

Determine how client feature gate `sand_stale_root_gc` is registered in Cursor 3.15.1, whether any `checkFeatureGate` / `useFeatureGate` / `wn` / `dr` helpers consult it, what default applies from inventory vs minified registry (`POe` / `xDe`), how it relates to GC / store-blob / disk surfaces (`sand_legacy_store_blob_retirement`, `composerBlobStore`, `disk_usage_monitor`), and whether a local override is present.

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
| Inventory | `/workspace/workspace/runs/20260805T110539Z/feature-flags-inventory.json` → `{name, client:true, default:false}`; root `registry_var`: **POe** |
| Manifest category | `other` (`.new_flags[470]`) |
| Precomputed evidence | `/workspace/workspace/runs/20260805T110539Z/plans/_evidence/sand-stale-root-gc.json` |

## 3. Scan checklist

| Script / probe | Exit | One-line result |
|----------------|------|-----------------|
| `locate-cursor.sh` | 0 | No install; `WORKBENCH_JS` empty |
| `scan-paths.sh` | 0 | No Cursor User config / global `state.vscdb`; projects root exists (tiny) |
| `grep-workbench.sh` (desktop, flag) | 0 | **1** hit — registry cluster only (`default:!1`) |
| `grep-workbench.sh` (glass, flag) | 0 | **1** hit — same registry entry |
| `grep-workbench.sh` (builtins) | 0 | Bundle healthy (`toolFormerData` / `composerData` / related surfaces present) |
| Full-extract `rg` (flag string) | 0 | Hits only in desktop, glass, `out/main.js`, `cursor-agent-host`, `cursor-always-local` (registry copies) |
| `checkFeatureGate` / `useFeatureGate` / `wn` / `dr` for flag | 0 | **Zero** call sites in entire extract; also **zero** `checkFeatureGate("sand_*")` in workbench |
| `inspect-state-vscdb.sh` | 1 | Error: `state.vscdb` not found (no local Statsig/override store) |
| `inspect-store-db.sh` | 1 | `--db PATH required` / no chats store |
| Inventory JSON | — | `default: false`, `client: true`, `registry_var: POe` |
| Bundle deep extract (Phase 4b) | — | Registry **POe** / **xDe**; neighbors `sand_action_audit_logs` / `sand_legacy_store_blob_retirement`; adjacent ungated `composerBlobStore` + wired `disk_usage_monitor` |
| Local override probe | — | No User storage → **none** |

## 4. Findings

### Registry (feature-gate map)

- **Confirmed:** Desktop gate registry is minified as **`POe`**, not `kFe`. Assignment: `POe={agent_goal_continuation:…}`; `c_n=Object.keys(POe)`. Flag sits inside `POe` before the keys enumeration (`POe` start < flag < `c_n`). Module header immediately preceding registry: `out-build/vs/platform/experiments/common/experimentConfig.gen.js`. Inventory root also records `registry_var: POe`.
- **Confirmed:** Glass twin registry is **`xDe`** (`Object.keys(xDe)`).
- **Confirmed:** Exact entry in both bundles (and registry copies in `out/main.js`, `cursor-agent-host`, `cursor-always-local`):  
  `sand_stale_root_gc:{client:!0,default:!1}`  
  → client gate, **default false** (`!1`). Matches inventory. Prefer inventory when Statsig uninitialized — `POe[e]?.default??!1` in `ExperimentService._checkGateWithoutOverride`.
- **Confirmed:** Neighbor cluster (sand family inside `POe`/`xDe`):  
  `sand_enable_pressure_cpu_profiler` (default true) →  
  `sand_action_audit_logs` (default false) →  
  **`sand_stale_root_gc`** (default **false**) →  
  `sand_legacy_store_blob_retirement` (default false) →  
  `sand_multiplayer` (default false) →  
  `sand_shared_room_box_tools_kill_switch` (default false) →  
  `sand_global_search` / `sand_pr_menu` / `sand_auto_disk_saver` …

### Call sites (active consumers)

- **Confirmed:** Desktop and glass have **zero** `checkFeatureGate("sand_stale_root_gc"…)` / `useFeatureGate("sand_stale_root_gc"…)`.
- **Confirmed:** Entire AppImage extract has **zero** `checkFeatureGate` / `useFeatureGate` / `wn(` / `dr(` / `checkGate(` / `getDynamicConfig(` string consumers for this flag (searched workbench, `out/main.js`, and `extensions/*/dist/main.js`). Every mention is **REGISTRY** (`:{client:!0,default:!1}`).
- **Confirmed:** Precomputed evidence `modules_near_mentions: []`, mention counts desktop=1, glass=1 — matches probes.
- **Confirmed:** Workbench has **zero** `checkFeatureGate("sand_*")` string args at all in 3.15.1 (entire sand gate family dormant at call-site level in client bundles).
- **Confirmed:** No camelCase symbols `StaleRoot` / `staleRoot` / `rootGc` / `RootGc` / `staleRoots` / `gcRoots` exist in the workbench bundles. Only the snake_case gate name appears (`stale.?root` → 1 hit = this flag).

### Effective value (Statsig / local)

- **Confirmed:** `ExperimentService._checkGateWithoutOverride` falls back to `POe[e]?.default??!1` (desktop) / `xDe[t]?.default??!1` (glass) when Statsig is missing or throws.
- **Confirmed:** Bundled / inventory default for this flag is **false** (prefer inventory).
- **Unknown:** Live Statsig remote value — no running Cursor / no `state.vscdb` / no Statsig cache on disk.
- **Confirmed:** Local feature-flag override: **none** (no `~/.config/Cursor/User`; override storage key exists in bundle as `workbench.experiments.featureFlagOverrides` but nothing persisted here).

### Semantics (what it would change)

- **Confirmed:** In 3.15.1 client bundles, flipping this gate has **no direct UI/runtime effect** — there is no client call site.
- **Confirmed (adjacent GC / store / disk surfaces, ungated by this flag):**
  - Sibling sand gate **`sand_legacy_store_blob_retirement`** (default false) sits immediately after this key; likewise **registry-only**.
  - Sibling **`sand_auto_disk_saver`** (default false) later in the same sand cluster; also registry-only.
  - Live `out-build/vs/workbench/contrib/composer/browser/composerBlobStore.js` (`YNt="agentKv:blob:"`, checkpoint/artifact prefixes) is ungated by this string.
  - Separate wired gate **`disk_usage_monitor`** → `DiskUsageMonitor` metrics cron (`collectVolumeMetrics` / `collectDirectorySizeMetrics`) — not this flag.
  - Unrelated `cleanupStale*` / CSS `garbageCollect` symbols exist (e.g. `cleanupStaleActiveCanvasForComposer`); none reference this gate.
- **Inferred:** Name `sand_stale_root_gc` + placement beside `sand_legacy_store_blob_retirement` / near disk-saver sand gates imply a **pre-registered / dormant rollout switch** for garbage-collecting stale root data (storage roots / agent store roots), not yet hooked in 3.15.1 client.
- **Inferred:** Until call sites land, Statsig treatments would only matter if future client code consults the gate (or if server/agent runtime uses the same Statsig name — not visible as a string consumer in this extract).

### Confidence

**Confirmed** on registry (`POe`/`xDe`), default **false**, full-extract registry-only classification, adjacent ungated blob/disk surfaces, modules, and local-override **none**.  
**Inferred** on intended product meaning (dormant stale-root GC enablement switch).  
**Unknown** only for remote Statsig treatment on a live client.

## 5. Internal code map

### Module table

| Module path | Role vs theme |
|-------------|----------------|
| `out-build/vs/platform/experiments/common/experimentConfig.gen.js` (via `POe`/`xDe`) | Client gate registry including `sand_stale_root_gc` |
| `out-build/vs/workbench/services/experiment/browser/experimentService.js` | `checkFeatureGate`, overrides, `POe`/`xDe` default fallback |
| `out-build/vs/workbench/contrib/composer/browser/composerBlobStore.js` | Live `agentKv:blob:` / checkpoint blob store — **ungated** by this flag |
| `DiskUsageMonitor` (log-tagged; wired via sibling gate) | Metrics only — gated by `disk_usage_monitor`, not this flag |
| `out/main.js` / `cursor-agent-host` / `cursor-always-local` | Registry copies only (no dedicated call) |

### Entry points

| Symbol / API | Bundle | Role |
|--------------|--------|------|
| `POe` / `xDe` | desktop / glass | Gate map; entry `sand_stale_root_gc:{client:!0,default:!1}` |
| `checkFeatureGate("sand_stale_root_gc")` | — | **Absent** in 3.15.1 extract |
| `YNt="agentKv:blob:"` / `ComposerBlobStore` | both | Adjacent blob KV; not gated by this flag |
| `sand_legacy_store_blob_retirement` / `sand_auto_disk_saver` | both | Neighbor sand gates; also registry-only |
| `disk_usage_monitor` + `DiskUsageMonitor` | both | Separate metrics monitor gated by its own flag |
| `workbench.experiments.featureFlagOverrides` | both | Override storage key; empty/absent on this host |

### Implementation snippets (Confirmed)

**Registry (desktop `POe`, glass `xDe`):**

```text
sand_enable_pressure_cpu_profiler:{client:!0,default:!0},
sand_action_audit_logs:{client:!0,default:!1},
sand_stale_root_gc:{client:!0,default:!1},
sand_legacy_store_blob_retirement:{client:!0,default:!1},
sand_multiplayer:{client:!0,default:!1},
sand_shared_room_box_tools_kill_switch:{client:!0,default:!1},
sand_global_search:{client:!0,default:!0},
sand_pr_menu:{client:!0,default:!0},
sand_auto_disk_saver:{client:!0,default:!1},
```

**Default fallback (`experimentService.js`):**

```text
_checkGateWithoutOverride(e,t){
  if(this._statsig) try { return this._statsig.checkGate(e,t) }
  catch { …; return POe[e]?.default??!1 }  // glass: xDe[t]?.default??!1
  else return … POe[e]?.default??!1
}
```

**Adjacent ungated blob store (`composerBlobStore.js`):**

```text
YNt="agentKv:blob:",Kbn="agentKv:checkpoint:",Qbn="agentKv:bubbleCheckpoint:",KAs="agentKv:artifact:"
…
keyFor(e){return`${YNt}${e_(e)}`}
async getBlob(e,t){… ComposerBlobStore.getBlob …}
```

**Sibling wired gate (not this flag):**

```text
if(!this.experimentService.checkFeatureGate("disk_usage_monitor",{disableExposureLog:!1})){
  this.logService.debug("[DiskUsageMonitor] Skipping: feature flag disabled");return}
```

## 6. Diagram

```mermaid
flowchart TD
  subgraph registry [Gate registry POe / xDe]
    SRGC["sand_stale_root_gc<br/>client true, default false"]
    SLBR["sand_legacy_store_blob_retirement<br/>default false — also registry-only"]
    SADS["sand_auto_disk_saver<br/>default false — also registry-only"]
    DUM["disk_usage_monitor<br/>default false — WIRED"]
  end
  subgraph clients [3.15.1 client extract]
    none["No checkFeatureGate / useFeatureGate / wn / dr<br/>for sand_stale_root_gc"]
    cbs["ComposerBlobStore / agentKv:blob:*<br/>ungated by this flag"]
    mon["DiskUsageMonitor cron metrics"]
  end
  SRGC --> none
  SLBR -.->|neighbor; no string gate read| none
  SADS -.->|neighbor; no string gate read| none
  cbs -.->|name-adjacent infrastructure| SRGC
  DUM -->|checkFeatureGate| mon
```

## 7. Gaps & follow-ups

- Live Statsig treatment unprobeable (no `state.vscdb`, no running client).
- Server-side or agent-runtime consumers of Statsig gate `sand_stale_root_gc` are outside string-searchable client bundles — not attempted beyond this AppImage extract.
- Intended GC pipeline (which “roots”, schedule, relation to blob retirement) not reverse-engineered beyond confirming dormancy and naming adjacency to `sand_legacy_store_blob_retirement` / `composerBlobStore`.
- When future builds add `checkFeatureGate("sand_stale_root_gc")`, re-run Phase 4b to locate modules.

## 8. Workspace relevance

Feature-flag inventory + extract under `/workspace/workspace/runs/20260805T110539Z/` are the authoritative inputs for this Notion sync / flag catalog run. Precomputed evidence JSON matched probes (registry-only samples; empty `modules_near_mentions`); deep extract confirmed **POe**/**xDe**, default false, and zero call sites across the full extract.

---

### Verdict summary

| Field | Value |
|-------|--------|
| Confidence | **Confirmed** (registry-only / default false); **Inferred** (intended stale-root GC); **Unknown** (live Statsig) |
| What it changes | **Nothing in 3.15.1 client** — registry-only; no `checkFeatureGate` consumer. Name/neighbors imply a future stale-root GC switch (distinct from live `ComposerBlobStore` and wired `disk_usage_monitor`). |
| Modules | `experimentConfig.gen.js` (`POe`/`xDe`), `experimentService.js`; registry copies in `out/main.js` / agent-host / always-local; adjacent ungated `composerBlobStore.js` (`agentKv:blob:`) |
| Local Override | **none** |
| Inventory default | **false** (`!1`) |
| Registry var | **POe** (desktop); **xDe** (glass) — not `kFe` |
| Call sites | **0** (registry-only) |
