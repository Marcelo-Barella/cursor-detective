#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_lib.sh
source "${SCRIPT_DIR}/_lib.sh"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

[[ "${1:-}" == "--help" || "${1:-}" == "-h" ]] && usage

emit_header "locate-cursor.sh"

sys="$(uname -s)"
kv "platform" "$sys"

search_roots=()
case "$sys" in
  Linux)
    search_roots+=(
      "${HOME}/Applications/cursor"
      "/usr/share/cursor"
      "/usr/share/cursor/resources"
      "/opt/Cursor"
      "${HOME}/.local/share/cursor"
      "${HOME}/.local/share/Cursor"
    )
    ;;
  Darwin)
    kv "probe_status" "skipped"
    kv "probe_note" "macOS install search not implemented in v1; paths listed in reference.md"
    search_roots+=("/Applications/Cursor.app/Contents")
    ;;
  *)
    kv "probe_status" "skipped"
    kv "probe_note" "Windows install search not implemented in v1"
    ;;
esac

best_install=""
best_workbench=""

for root in "${search_roots[@]}"; do
  [[ -d "$root" ]] || continue
  kv "candidate_install" "$root"
  wb="$(find "$root" -type f -name 'workbench.desktop.main.js' 2>/dev/null | head -n 1 || true)"
  if [[ -n "$wb" && -f "$wb" ]]; then
    best_install="$root"
    best_workbench="$wb"
    break
  fi
done

if [[ "$sys" == "Linux" && -z "$best_workbench" ]]; then
  while IFS= read -r -d '' img; do
    kv "appimage_candidate" "$img"
  done < <(find "${HOME}" -maxdepth 4 -type f -name 'cursor*.AppImage' -print0 2>/dev/null || true)
fi

if [[ -n "$best_workbench" ]]; then
  kv "INSTALL_ROOT" "$best_install"
  kv "WORKBENCH_JS" "$best_workbench"
  kv "workbench_size" "$(human_bytes "$(stat -c '%s' "$best_workbench" 2>/dev/null || stat -f '%z' "$best_workbench")")"
else
  kv "WORKBENCH_JS" ""
  kv "install_status" "not_found"
fi

if [[ -n "$best_install" ]]; then
  pj="$(find "$best_install" -type f -path '*/resources/app/product.json' 2>/dev/null | head -n 1 || true)"
  if [[ -f "${pj:-}" ]]; then
    ver="$(grep -E '"version"' "$pj" | head -n 1 | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
    kv "cursor_version" "${ver:-unknown}"
  fi
fi
