# Detective: `sand_spotlight`

Theme: `feature-flag-sand-spotlight`  
Flag: `sand_spotlight`  
Cursor: **3.15.1** / product commit `41c5e281845de0ce890a8053a3874064bfbdb8b0` (inventory/evidence listed `…bfbdb8bf`)  
Plan path: `/workspace/workspace/runs/20260805T110539Z/plans/detective-feature-flag-sand-spotlight.plan.md`

## 1. Objective

Determine how client feature gate `sand_spotlight` is registered in Cursor 3.15.1, whether any `checkFeatureGate` / `useFeatureGate` / `wn` / `dr` helpers consult it, what default applies from inventory vs minified registry (`POe` / `xDe`), how it relates to Spotlight / sand-family surfaces, and whether a local override is present.

**Success criteria:** registry entry confirmed, call-site vs registry-only classification with Confirmed snippets, modules list, local override status, full Phase 1–5 + 4b report at this path.

**Assumptions**

- Inventory `default: true` matches minified `default:!0`.
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
| Inventory | `/workspace/workspace/runs/20260805T110539Z/feature-flags-inventory.json` → `{name, client:true, default:true}`; `registry_var: POe` |
| Manifest category | `other` |
| Precomputed evidence | `/workspace/workspace/runs/20260805T110539Z/plans/_evidence/sand-spotlight.json` |

## 3. Scan checklist

| Script / probe | Exit | One-line result |
|----------------|------|-----------------|
| `locate-cursor.sh` | 0 | No install; `WORKBENCH_JS` empty |
| `scan-paths.sh` | 0 | No Cursor User config / global `state.vscdb`; projects root exists (tiny) |
| `grep-workbench.sh` (desktop, `sand_spotlight`) | 0 | **1** hit — registry cluster only (`default:!0`) |
| `grep-workbench.sh` (glass, flag) | 0 | **1** hit — same registry entry |
| `grep-workbench.sh` (builtins) | 0 | `toolFormerData` / `composerData` present (bundle healthy) |
| Full-extract `rg` (`sand_spotlight`) | 0 | Hits only in desktop, glass, `out/main.js`, `cursor-agent-host`, `cursor-always-local` (registry copies) |
| `checkFeatureGate` / `useFeatureGate` / `wn` / `dr` for flag | 0 | **Zero** call sites in entire extract; also **zero** `checkFeatureGate("sand_*")` in workbench |
| `inspect-state-vscdb.sh` | 1 | Error: `state.vscdb` not found (no local Statsig/override store) |
| `inspect-store-db.sh` | — | `--db PATH required` / no chats store |
| Inventory JSON | — | `default: true`, `client: true` |
| Bundle deep extract (Phase 4b) | — | Registry **POe** / **xDe**; unrelated Sentry `SpotlightBrowser` / `feSpotLight` SVG strings present; no gate wiring |
| Local override probe | — | No User storage → **none** |

## 4. Findings

### Registry (feature-gate map)

- **Confirmed:** Desktop gate registry is minified as **`POe`**, not `kFe`. Assignment: `POe={agent_goal_continuation:…}`; `c_n=Object.keys(POe)`. Flag sits inside `POe` before the keys enumeration (`POe` start < flag < `c_n`). Module header immediately preceding registry: `out-build/vs/platform/experiments/common/experimentConfig.gen.js`.
- **Confirmed:** Glass twin registry is **`xDe`** (`Object.keys(xDe)` / `dct=Object.keys(xDe)`).
- **Confirmed:** Exact entry in both bundles (and registry copies in `out/main.js`, `cursor-agent-host`, `cursor-always-local`):  
  `sand_spotlight:{client:!0,default:!0}`  
  → client gate, **default true** (`!0`). Matches inventory. Prefer inventory when Statsig uninitialized — `POe[e]?.default??!1` in `ExperimentService._checkGateWithoutOverride`.
- **Confirmed:** Neighbor cluster (immediate keys inside `POe`/`xDe`):  
  `sand_auto_review` (default false) →  
  `sand_mcp_oauth_loopback` (default false) →  
  **`sand_spotlight`** (default **true**) →  
  `smart_mode_classifier_shadow_mode` (default false) →  
  `ext_host_document_memory_estimates` …  
  Later sand sibling in full sand-ordered list: `sand_renderer_heap_metrics` (default false).

### Call sites (active consumers)

- **Confirmed:** Desktop and glass have **zero** `checkFeatureGate("sand_spotlight"…)` / `useFeatureGate("sand_spotlight"…)`.
- **Confirmed:** Entire AppImage extract has **zero** `checkFeatureGate` / `useFeatureGate` / `wn(` / `dr(` / `checkGate(` string consumers for this flag (searched workbench, `out/main.js`, and `extensions/*/dist/main.js`).
- **Confirmed:** Every mention of `sand_spotlight` is **registry-only** (`:{client:!0,default:!0}`); mention counts desktop=1, glass=1 (plus three registry copies elsewhere). Precomputed evidence `modules_near_mentions: []` matches.
- **Confirmed:** Workbench has **zero** `checkFeatureGate("sand_*")` string args at all in 3.15.1 (entire sand gate family is currently dormant at call-site level in client bundles).

### Effective value (Statsig / local)

- **Confirmed:** `ExperimentService._checkGateWithoutOverride` falls back to `POe[e]?.default??!1` (desktop) / `xDe[t]?.default??!1` (glass) when Statsig is missing or throws.
- **Confirmed:** Bundled / inventory default for this flag is **true** (prefer inventory).
- **Unknown:** Live Statsig remote value — no running Cursor / no `state.vscdb` / no Statsig cache on disk.
- **Confirmed:** Local feature-flag override: **none** (no `~/.config/Cursor/User`; override storage key exists in bundle as `workbench.experiments.featureFlagOverrides` but nothing persisted here).

### Semantics (what it would change)

- **Confirmed:** In 3.15.1 client bundles, flipping this gate has **no direct UI/runtime effect** — there is no client call site.
- **Confirmed (adjacent “spotlight” strings, ungated by this flag):**
  - Bundled **Sentry Spotlight** integration: `node_modules/@sentry/browser/.../integrations/spotlight.js`, `SpotlightBrowser`, `spotlightBrowserIntegration`, sidecar URL docs (`spotlightjs.com`), and log lines `[Spotlight] Disabled Sentry -> Spotlight integration…`. Sentry client `init()` can force `_setupIntegrations()` when an integration name `startsWith("Spotlight")`. None of these paths reference the string `sand_spotlight` or `checkFeatureGate`.
  - Unrelated SVG/DOM allowlist tokens `feSpotLight` (and similar) appear in HTML sanitizer lists — not product UI.
  - No `out-build/...Spotlight...` workbench contrib module path exists; theme-adjacent modules are experiment services + generic Quick Access (`anythingQuickAccess`, `editorQuickAccess`) with no link to this gate string.
- **Inferred:** Name `sand_spotlight` + placement after other sand rollout gates (`sand_auto_review` / `sand_mcp_oauth_loopback`) and default **true** imply a **pre-registered / dormant sand-family switch** (possibly intended to gate a Spotlight-named product or Sentry Spotlight enablement) that is **not yet hooked** into client `checkFeatureGate`. Default-on is unusual for dormant sand gates (most neighbors default off) but is Confirmed in both inventory and `POe`/`xDe`.
- **Inferred:** Until call sites land, Statsig treatments for `sand_spotlight` would only matter if future client code consults the gate (or if server/agent runtime uses the same Statsig name — not visible as a string consumer in this extract).

### Confidence

**Confirmed** on registry (`POe`/`xDe`), default **true**, full-extract registry-only classification, adjacent ungated Sentry Spotlight distinction, modules, and local-override **none**.  
**Inferred** on intended product meaning (dormant sand Spotlight rollout switch).  
**Unknown** only for remote Statsig treatment on a live client.

## 5. Internal code map

### Module table

| Module path | Role vs theme |
|-------------|----------------|
| `out-build/vs/platform/experiments/common/experimentConfig.gen.js` (via `POe`/`xDe`) | Client gate registry including `sand_spotlight` |
| `out-build/vs/workbench/services/experiment/browser/experimentService.js` | `checkFeatureGate`, overrides, `POe`/`xDe` default fallback |
| `out/main.js` / `cursor-agent-host` / `cursor-always-local` | Registry copies only (no dedicated call) |
| `node_modules/@sentry/browser/.../integrations/spotlight.js` | Sentry SpotlightBrowser integration — **ungated** by this flag |
| Quick Access contrib (`anythingQuickAccess.js`, `editorQuickAccess.js`, …) | Theme-adjacent search UI modules; no `sand_spotlight` string |

### Entry points

| Symbol / API | Bundle | Role |
|--------------|--------|------|
| `POe` / `xDe` | desktop / glass | Gate map; entry `sand_spotlight:{client:!0,default:!0}` |
| `checkFeatureGate("sand_spotlight")` | — | **Absent** in 3.15.1 extract |
| `SpotlightBrowser` / `spotlightBrowserIntegration` | both | Sentry sidecar integration; not wired to this gate |
| `workbench.experiments.featureFlagOverrides` | both | Override storage key; empty/absent on this host |

### Implementation snippets (Confirmed)

**Registry (desktop `POe`, glass `xDe`):**

```text
sand_auto_review:{client:!0,default:!1},
sand_mcp_oauth_loopback:{client:!0,default:!1},
sand_spotlight:{client:!0,default:!0},
smart_mode_classifier_shadow_mode:{client:!0,default:!1},
ext_host_document_memory_estimates:{client:!0,default:!1},
```

**Default fallback (`experimentService.js`):**

```text
_checkGateWithoutOverride(e,t){
  if(this._statsig) try { return this._statsig.checkGate(e,t) }
  catch { …; return POe[e]?.default??!1 }  // glass: xDe[t]?.default??!1
  else return … POe[e]?.default??!1
}
```

**Adjacent ungated Sentry Spotlight (not this flag):**

```text
init(){(this._isEnabled()||this._options.integrations.some(({name:e})=>e.startsWith("Spotlight")))&&this._setupIntegrations()}
…
node_modules/@sentry/browser/.../integrations/spotlight.js → SpotlightBrowser
…
[Spotlight] Disabled Sentry -> Spotlight integration due to too many failed requests…
```

## 6. Diagram

```mermaid
flowchart TD
  subgraph registry [Gate registry POe / xDe]
    SS["sand_spotlight<br/>client true, default true"]
    SAR["sand_auto_review<br/>default false — also registry-only"]
    SMO["sand_mcp_oauth_loopback<br/>default false — also registry-only"]
  end
  subgraph clients [3.15.1 client extract]
    none["No checkFeatureGate / useFeatureGate / wn / dr<br/>for sand_spotlight"]
    sentry["Sentry SpotlightBrowser / sidecar<br/>ungated by this flag"]
  end
  SS --> none
  SAR -.->|neighbor; no string gate read| none
  SMO -.->|neighbor; no string gate read| none
  sentry -.->|name collision only| SS
```

## 7. Gaps & follow-ups

- Live Statsig treatment unprobeable (no `state.vscdb`, no running client).
- Server-side or agent-runtime consumers of Statsig gate `sand_spotlight` are outside string-searchable client bundles — not attempted beyond this AppImage extract.
- Intended product surface for “spotlight” (Sentry vs in-app UI) cannot be proven without a call site; only naming + neighbor sand cluster + default-true registry entry are Confirmed.
- When future builds add `checkFeatureGate("sand_spotlight")`, re-run Phase 4b to locate modules.

## 8. Workspace relevance

Feature-flag inventory + extract under `/workspace/workspace/runs/20260805T110539Z/` are the authoritative inputs for this Notion sync / flag catalog run. Precomputed evidence JSON matched probes (registry-only samples; empty `modules_near_mentions`); deep extract confirmed **POe**/**xDe**, default **true**, and zero call sites across the full extract.

---

### Verdict summary

| Field | Value |
|-------|--------|
| Confidence | **Confirmed** (registry-only / default true); **Inferred** (intended sand Spotlight rollout); **Unknown** (live Statsig) |
| What it changes | **Nothing in 3.15.1 client** — registry-only; no `checkFeatureGate` consumer. Name/neighbors imply a future sand Spotlight switch (distinct from ungated Sentry SpotlightBrowser). |
| Modules | `experimentConfig.gen.js` (`POe`/`xDe`), `experimentService.js`; registry copies in `out/main.js` / agent-host / always-local; adjacent ungated Sentry `spotlight.js` |
| Local Override | **none** |
| Inventory default | **true** (`!0`) |
| Registry var | **POe** (desktop); **xDe** (glass) — not `kFe` |
| Call sites | **0** (registry-only) |
