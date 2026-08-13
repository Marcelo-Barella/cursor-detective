# Origin visualization UI gates (Cursor 3.16.12)

See full forensic report: this file mirrors `.cursor/plans/detective-origin-visualization.plan.md` (local skill output path; not tracked because `.cursor/` is gitignored).

**Bundle analyzed:** Cursor 3.16.12 (`9d65ef452c6582544b6ae15a61a2e74bd483e1f1`)  
**Extract path:** `workspace/runs/20260813T172251Z/extract/new/` (gitignored runtime artifact)

## Executive conclusion

Origin visualization in the IDE/Glass client is **mostly hard-coded or server-gated**, not controlled by catalog `origin_*` Statsig flags.

1. **IDE “Copy cursor.com link”** uses a **hard-coded owner allowlist** (`anysphere`, `withgraphite`) → `cursorOrigin.codeBrowseAllowed`. Not gated by `limit_origin_ui_to_browse_early_access` or `origin_repos`.
2. **Glass Origin hosted-repo listing** (cloud-agent picker) uses **`cloud_agent_origin_repos`** (Statsig, default OFF) plus server field **`origin_repos_enabled`** from `getRepoSourcePreference`.
3. **Catalog-only flags** have **no `checkFeatureGate` consumers** in 3.16.12.
4. **cursor.com/codebase browser UI** is not embedded in workbench; client builds external URLs only.

## Hard-coded allowlists

| Allowlist | Values | Module | Controls |
|-----------|--------|--------|----------|
| Repo owners | `anysphere`, `withgraphite` | `contrib/cursorOrigin/browser/codeBrowseEligibility.js` | `cursorOrigin.codeBrowseAllowed`, copy-link commands |
| Remote hosts | `origin.cursor.com`, `origin-staging.cursor.com`, `github.com` | `contrib/cursorOrigin/browser/remoteSlug.js` | Slug parsing from git remotes (necessary, not sufficient) |
| Link base | `https://cursor.com/codebase` | `contrib/cursorOrigin/browser/cursorOriginLinks.js` | URL prefix for blob links |

## Client feature gates (registry defaults: client=true, default=false)

| Gate | Wired in 3.16.12? | Effect |
|------|-------------------|--------|
| `cloud_agent_origin_repos` | **Yes (Glass)** | `originClient.listHostedRepos` in cloud-agent / new-project pickers |
| `enable_forge_source_pr_creation_setting` | Yes (IDE+Glass) | PR forge guidance (not browse UI) |
| `marketplace_origin_distribution` | Yes (agent-exec) | Marketplace plugin distribution only |
| `origin_repos` | No | — |
| `limit_origin_ui_to_browse_early_access` | No | — |
| `origin_raw_file_links` | No | — |
| `use_github_pr_links_in_origin_browse` | No | — |
| `codebase_browse_ask_cursor` | No | — |
| `codebase_branches_redesign_in_progress` | No | — |
| `origin_pull_requests_enabled_in_client` | No | — |
| `origin_apps_ga` | No | — |
| `automations_origin_request_reviewers` | No | — |
| `origin_migration_flow` | No | — |

## Server entitlement (not a client flag)

- **`origin_repos_enabled`** on `GetRepoSourcePreferenceResponse` — fetched via `dashboardClient.getRepoSourcePreference` in Glass (`use-preferred-repo-source.react.js`). Enables `originRepoUnificationEnabled` when true.

## Override paths

| Mechanism | Location |
|-----------|----------|
| Statsig evaluation | Remote bootstrap `workbench.experiments.statsigBootstrap` |
| Local overrides | `workbench.experiments.featureFlagOverrides` (24h TTL) |
| API | `experimentService.setFeatureFlagOverride(gate, bool)` |
| Eligibility | Dev build, extension dev, `isDevUser`, or cached server dev flag |
| Debug commands | `workbench.action.dumpFeatureGates`, `workbench.action.clearStatsigCache` |

Overrides can flip `cloud_agent_origin_repos` but **cannot** change the `anysphere|withgraphite` owner allowlist without patching the bundle.

## Enablement recipes

### IDE copy-link → cursor.com/codebase

1. Open a git repo whose remote host is `github.com`, `origin.cursor.com`, or `origin-staging.cursor.com`.
2. Repo owner must be **`anysphere` or `withgraphite`**.
3. No effective feature flag — `limit_origin_ui_to_browse_early_access` is unwired.

### Glass Origin repos in cloud-agent picker

1. Enable **`cloud_agent_origin_repos`** (Statsig or dev override).
2. Authenticated user with **teamId**; server returns Origin namespace.
3. For unified picker UX, server **`origin_repos_enabled: true`**.

```javascript
experimentService.setFeatureFlagOverride("cloud_agent_origin_repos", true)
```

### Flags that do nothing for browse UI in 3.16.12

`origin_repos`, `limit_origin_ui_to_browse_early_access`, `origin_raw_file_links`, `use_github_pr_links_in_origin_browse`, `codebase_browse_ask_cursor`, `codebase_branches_redesign_in_progress`, `origin_pull_requests_enabled_in_client`, `origin_apps_ga`, `automations_origin_request_reviewers`, `origin_migration_flow`

## Evidence modules (workbench bundle paths)

- `out-build/vs/workbench/contrib/cursorOrigin/browser/codeBrowseEligibility.js`
- `out-build/vs/workbench/contrib/cursorOrigin/browser/remoteSlug.js`
- `out-build/vs/workbench/contrib/cursorOrigin/browser/cursorOriginLinks.js`
- `out-build/vs/glass/browser/hooks/use-origin-repositories.react.js`
- `out-build/vs/glass/browser/hooks/use-preferred-repo-source.react.js`

## Hypothesis verdicts

| Hypothesis | Verdict |
|------------|---------|
| Catalog-only origin/codebase_browse flags | Confirmed |
| Browse early access via `limit_origin_ui_to_browse_early_access` | Discarded (unwired) |
| Browse early access via `anysphere\|withgraphite` hard-code | Confirmed for IDE copy-link |
| `cloud_agent_origin_repos` = picker only | Confirmed |
| `origin_pull_requests_enabled_in_client` / `origin_apps_ga` unwired | Confirmed |
