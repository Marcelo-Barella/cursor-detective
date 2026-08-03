# Feature Flags Notion sync — Daily Automation

Detect new Cursor **client feature flags** (`kFe` gates), run one full Cursor Detective per new flag, and upsert Done rows in the **Cursor Feature Flags** Notion database with the detective plan on the page body.

## Memory keys

Store and read these from Automation Memory (local runs: `workspace/automation-memory.json`):

- `version` — last processed Cursor version
- `commit_sha` — last processed commit
- `download_url` — last processed download URL
- `known_flag_names` — newline-separated catalog of flags already processed (optional backup; Notion Keys are authoritative for "new")

**First run** (version fields empty): `install-pair.sh --first-run` (dev vs stable baseline for skip detection).

**Subsequent runs**: reinstall previous from Memory URL; skip if `commit_sha` unchanged.

## Pipeline

1. Run `bash scripts/setup-deps.sh`
2. Install pair:
   - First run: `bash scripts/install-pair.sh --first-run`
   - Else: `bash scripts/install-pair.sh --previous-url "$download_url" --previous-version "$version" --previous-commit "$commit_sha"`
3. Parse stdout. If `skip=true`, log "No new Cursor build" and exit 0.
4. Run `bash scripts/run-pipeline.sh` (optionally `--previous-names` from Memory `known_flag_names` written to a temp file). This extracts the **new** AppImage and catalogs `kFe`.
5. Read the latest `workspace/runs/*/manifest.json` and `feature-flags-inventory.json`.
6. Query Notion **Cursor Feature Flags** (data source under Cursor Internal — Agent). Build `new_flags` = catalog names **missing** from Notion `Key` (Notion is source of truth for already-done work; do not rely only on Memory names).
7. If `new_flags` is empty, update Memory version/commit/download_url from the new build, refresh `known_flag_names`, and exit 0.
8. Spawn **one Cursor Detective subagent per new flag** (parallel waves of up to **4**, same depth as the Ralph feature-flag run). Each subagent must:
   - Follow `skills/cursor-detective/SKILL.md` fully (Phases 1–5 + 4b)
   - Theme: `feature-flag-<kebab-flag-name>`
   - Use extracted `workbench_js` from the manifest (and glass twin if present under the same extract)
   - Prefer inventory `client` / `default` from `feature-flags-inventory.json` over misreads
   - Write plan to `workspace/runs/<timestamp>/plans/detective-feature-flag-<kebab>.plan.md`
9. For each completed detective, create or update the Notion row:
   - Properties: Name, Key, Category, Client, Bundled Default, Local Override, What it changes, Confidence, Evidence, Modules, Detective Plan, Status=`Done`, Cursor Version, Last Verified
   - **Page body**: full detective plan markdown (plan content lives on the Notion page, not only a local file path)
10. Update Memory: `version`, `commit_sha`, `download_url` from the new build; `known_flag_names` = full catalog names.
11. Write backup summary to `workspace/runs/<timestamp>/feature-flags-sync.md`

## Detective subagent prompt (per flag)

```
You are running a COMPLETE Cursor Detective investigation.
Theme: feature-flag-<kebab>

MANDATORY: Follow skills/cursor-detective/SKILL.md fully (Phases 1–5 + 4b). Do NOT shortcut.

Flag under study: `<flag_name>`

Fixed paths from parent:
- Skill scripts: skills/cursor-detective/scripts/
- Workbench: <workbench_js from manifest>
- Inventory: workspace/runs/<timestamp>/feature-flags-inventory.json
- Output plan: workspace/runs/<timestamp>/plans/detective-feature-flag-<kebab>.plan.md

Confirm kFe registry entry, checkFeatureGate call sites (or registry-only), Statsig/local effective value when probeable, modules touched, and Confirmed/Inferred/Unknown tags. Prefer inventory default (!0=true, !1=false).
```

## Notion notes

- Prefer create over noisy search when inserting truly new Keys.
- Prefer update when the Key already exists as a stub (Not started).
- Put the detective plan markdown in the page content; also set Detective Plan / Evidence properties to the plan filename.
- Database name: **Cursor Feature Flags**. If missing, stop and report (do not recreate unless Memory says first-run recreate is allowed).

## Constraints

- Do not commit or push to git.
- Use `scripts/` for install/extract/catalog; do not modify install trees outside `versions/` and `workspace/`.
- Do not re-detect flags already Done in Notion unless the catalog entry itself disappeared/reappeared with different defaults (optional; default = skip Done Keys).
