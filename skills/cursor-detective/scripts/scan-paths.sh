#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

[[ "${1:-}" == "--help" || "${1:-}" == "-h" ]] && { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

emit_header "scan-paths.sh"

cfg="$(cursor_config_root)"
path_stat_line "cursor_user_config" "$cfg"
path_stat_line "global_state_vscdb" "$(global_state_db)"
path_stat_line "projects_root" "$(projects_root)"
path_stat_line "chats_root" "$(chats_root)"

ws_root="${cfg}/workspaceStorage"
if [[ -d "$ws_root" ]]; then
  count=0
  while IFS= read -r d; do
  [[ -z "$d" ]] && continue
  kv "workspace_storage_dir" "$d"
  path_stat_line "workspace_state" "${d}/state.vscdb"
  count=$((count + 1))
  [[ "$count" -ge 5 ]] && { kv "workspace_storage_truncated" "true"; break; }
  done < <(find "$ws_root" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | head -n 6)
fi

pr="$(projects_root)"
if [[ -d "$pr" ]]; then
  kv "projects_count" "$(find "$pr" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
fi

cr="$(chats_root)"
if [[ -d "$cr" ]]; then
  kv "chats_workspace_keys" "$(find "$cr" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
fi
