#!/usr/bin/env bash
# shellcheck disable=SC2034
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

emit_header() {
  local script="$1"
  local note="${2:-}"
  echo "script=${script}"
  echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ -n "$note" ]]; then
    echo "note=${note}"
  fi
}

kv() { printf '%s=%s\n' "$1" "$2"; }

die() {
  echo "error: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

human_bytes() {
  local n="$1"
  if (( n < 1024 )); then echo "${n}B"; return; fi
  if (( n < 1048576 )); then echo "$(( n / 1024 ))KB"; return; fi
  echo "$(( n / 1048576 ))MB"
}

path_stat_line() {
  local label="$1"
  local p="$2"
  if [[ -e "$p" ]]; then
    local sz mt
    sz=$(stat -c '%s' "$p" 2>/dev/null || stat -f '%z' "$p")
    mt=$(stat -c '%y' "$p" 2>/dev/null || stat -f '%Sm' "$p")
    kv "${label}_exists" "true"
    kv "${label}_path" "$p"
    kv "${label}_size" "$(human_bytes "$sz")"
    kv "${label}_mtime" "$mt"
  else
    kv "${label}_exists" "false"
    kv "${label}_path" "$p"
  fi
}

cursor_config_root() {
  local home sys
  home="${HOME}"
  sys="$(uname -s)"
  case "$sys" in
    Darwin) echo "${home}/Library/Application Support/Cursor/User" ;;
    MINGW*|MSYS*|CYGWIN*)
      local appdata="${APPDATA:-${home}/AppData/Roaming}"
      echo "${appdata}/Cursor/User"
      ;;
    *) echo "${home}/.config/Cursor/User" ;;
  esac
}

projects_root() { echo "${HOME}/.cursor/projects"; }
chats_root() { echo "${HOME}/.cursor/chats"; }

global_state_db() {
  echo "$(cursor_config_root)/globalStorage/state.vscdb"
}

workspace_state_db() {
  local id="$1"
  echo "$(cursor_config_root)/workspaceStorage/${id}/state.vscdb"
}

normalize_theme() {
  local raw="${1:-}"
  raw="$(echo "$raw" | tr '[:upper:]' '[:lower:]' | tr ' _' '-')"
  raw="$(echo "$raw" | sed -E 's/[^a-z0-9-]+//g; s/-+/-/g; s/^-|-$//g')"
  if [[ -z "$raw" ]]; then raw="general-scan"; fi
  echo "$raw"
}

TRUNCATE_MAX="${TRUNCATE_MAX:-20}"
