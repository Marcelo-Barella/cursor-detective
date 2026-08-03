# cursor-detective

Cursor plugin that packages the **cursor-detective** skill: deep read-only forensics on local Cursor installs, config, SQLite state, workbench bundles, and project artifacts.

**Linux only.** macOS and Windows are not supported (install/workbench probes are Linux-oriented; other platforms are skipped or unknown).

## What's inside

| Component | Path |
|-----------|------|
| Skill | `skills/cursor-detective/` |
| Probe scripts | `skills/cursor-detective/scripts/` |
| Smoke tests | `skills/cursor-detective/tests/smoke.sh` |
| Path/reference notes | `skills/cursor-detective/reference.md` |

Invoke with `/cursor-detective [theme]` (empty theme → `general-scan`). Reports land at `.cursor/plans/detective-<theme>.plan.md` in the current workspace.

## Requirements

- **Linux only**
- Host tools (not bundled): `bash`, `sqlite3`, `python3`, and common Unix utilities (`find`, `grep`, `sed`, `awk`, `comm`, `stat`)

## Install

### Local (development)

```bash
git clone https://github.com/Marcelo-Barella/cursor-detective.git
ln -s "$(pwd)/cursor-detective" ~/.cursor/plugins/local/cursor-detective
```

Then run **Developer: Reload Window**. Confirm the skill appears under Customize / Skills.

### Marketplace

When published, install from [cursor.com/marketplace](https://cursor.com/marketplace) or Customize → Plugins. Submit updates via [marketplace publish](https://cursor.com/marketplace/publish).

## Usage

```text
/cursor-detective
/cursor-detective persistence
/cursor-detective conversationState
```

The skill runs locate/scan scripts, optional parallel probes (workbench, DBs, project artifacts, compares), and writes a tagged evidence report. It does **not** modify `~/.cursor`, `~/.config/Cursor`, or install trees except the workspace plan file.

## Scripts

| Script | Purpose |
|--------|---------|
| `locate-cursor.sh` | Install root + `WORKBENCH_JS` |
| `scan-paths.sh` | Standard data dir inventory |
| `inspect-state-vscdb.sh` | Global/workspace `state.vscdb` |
| `inspect-store-db.sh` | Chat `store.db` |
| `grep-workbench.sh` | Pattern search in workbench bundle |
| `compare-sqlite-meta.sh` | Schema/rowcount compare |
| `compare-dirs.sh` | Shallow dir file compare |
| `decode-conversation-state.sh` | `conversationState` / `agentKv:blob` decode |

Run smoke tests:

```bash
./skills/cursor-detective/tests/smoke.sh
```

## Related skills (not bundled)

Cross-links only — install separately if needed:

| Skill | When |
|-------|------|
| transport-chat / Cursor Sync Chats | export/import chat transport |
| unravel | flow narrative only |
| research | open-repo code, not Cursor product |
| debugger | repro + fix |

## Daily feature-flag automation (Cloud)

Download and extract a Cursor AppImage, then catalog client feature gates:

```bash
bash scripts/setup-deps.sh
bash scripts/install-pair.sh --first-run   # or --previous-url/--previous-version/--previous-commit
bash scripts/run-pipeline.sh
```

`run-pipeline.sh` extracts the **new** AppImage and catalogs client gates from workbench `kFe` into `workspace/runs/<timestamp>/`. Automation prompt: `prompts/daily-feature-flags.md`.

## Plugin layout

```text
cursor-detective/
├── .cursor-plugin/plugin.json
├── assets/logo.svg
├── prompts/
├── scripts/          # AppImage install + feature-flag catalog
├── skills/cursor-detective/
│   ├── SKILL.md
│   ├── reference.md
│   ├── scripts/
│   └── tests/
├── LICENSE
└── README.md
```

See [Cursor Plugins docs](https://cursor.com/docs/plugins) and the [plugins reference](https://cursor.com/docs/reference/plugins).

## License

MIT. See [LICENSE](./LICENSE).

## Author

Marcelo Barella.
