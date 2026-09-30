# Detective: feature-flag-glass-project-tasks-pill

## Objective

Determine how `glass_project_tasks_pill` exposes project tasks UI in Glass agent chrome and default/off behavior.

## Environment

- Cursor **3.23.5** / commit `a34aa15953a79dfe2ada63f5460efa79005dfbb5`
- Extracted `workbench.glass.main.js` + desktop twin
- `state.vscdb`: missing → local override **none**

## Scan checklist

| Script / probe | Exit | Result |
|----------------|------|--------|
| `locate-cursor.sh` | 0 | Extract path used |
| `scan-paths.sh` | 0 | No state DB |
| `probe-flag.py` | 0 | client=true, default=false; glass call site in `toC` |
| `grep-workbench.sh` | 0 | Registry + `project-tasks-pill` component |

## Findings

### Registry (Confirmed)

- **Confirmed:** `glass_project_tasks_pill:{client:!0,default:!1}` beside other `glass_project_*` flags.

### Agent panel pill (Confirmed)

- **Confirmed:** `toC` in `project-tasks-pill.react.js`:

```javascript
const { notesDocument: s } = ADn(),
      o = i && s,
      a = o_("glass_project_tasks_pill", n && o);
// ...
const g = o && a;
return { id: "project-tasks", content: pill, visible: g };
```

- **Confirmed:** Visible only when **project chat** (`isProjectChat`), **notes document present**, **active surface**, and flag on.
- **Confirmed:** Label `M("glass.agentPanel.projectTasksPill.label", "View Tasks")`; `data-component="project-tasks-pill"`.
- **Confirmed:** Click handler opens editor panel and activates project app with `projectSection: "notes"`.

### Desktop bundle (Confirmed)

- **Confirmed:** Desktop registry entry only (`workbench_count=1`); UI implementation is glass-only.

## Internal code map

| Area | Symbols / modules | Role |
|------|-------------------|------|
| Flag | `o_("glass_project_tasks_pill", n && o)` | Client gate |
| Notes coupling | `ADn()`, `notesDocument` | Requires project notes doc |
| UI | `project-tasks-pill.react.js` (`toC`) | Renders agent chrome pill |
| Navigation | `setEditorPanelVisibility`, `activateApp("project", { projectSection: "notes" })` | Opens tasks/notes section |

## Diagram

```mermaid
flowchart TD
  chat[isProjectChat] --> vis
  notes[notesDocument from ADn] --> vis
  surface[isActiveSurface] --> gate[o_ glass_project_tasks_pill]
  gate --> vis[visible project-tasks pill]
  vis --> click[View Tasks]
  click --> panel[Editor panel + project notes section]
```

## Gaps & follow-ups

- Upstream registration of `toC` return value into agent chrome tab list not fully traced (minified).

## Workspace relevance

None.
