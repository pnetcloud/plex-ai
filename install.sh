#!/usr/bin/env bash
set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
    echo "Plex requires Git. Install Git, then rerun this command." >&2
    exit 127
fi
bootstrap_dir=$(mktemp -d "${TMPDIR:-/tmp}/plex-install.XXXXXX")
trap 'rm -rf "$bootstrap_dir"' EXIT
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/skills/plex-setup/scripts/releases.py \
    -o "$bootstrap_dir/releases.py"

if command -v uv >/dev/null 2>&1; then
    runner=(uv run --script "$bootstrap_dir/releases.py")
elif command -v python3 >/dev/null 2>&1; then
    runner=(python3 "$bootstrap_dir/releases.py")
else
    echo "Plex requires uv or Python 3.11+." >&2
    exit 127
fi
# Restore terminal input after curl | bash so the existing setup menus remain interactive.
if [[ ! -t 0 ]] && { : </dev/tty; } 2>/dev/null; then
    "${runner[@]}" "$@" </dev/tty
else
    "${runner[@]}" "$@"
fi
