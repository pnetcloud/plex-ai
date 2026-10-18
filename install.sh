#!/usr/bin/env bash
set -euo pipefail

source_dir="$HOME/.local/share/plex-ai"
repository="https://github.com/pnetcloud/plex-ai.git"

if ! command -v git >/dev/null 2>&1; then
    echo "Plex requires Git. Install Git, then rerun this command." >&2
    exit 127
fi

if [[ -e "$source_dir" || -L "$source_dir" ]]; then
    if [[ -L "$source_dir" || ! -d "$source_dir/.git" ]] ||
       [[ "$(git -C "$source_dir" remote get-url origin)" != "$repository" ]]; then
        echo "Plex cannot update this directory; existing files left unchanged: $source_dir" >&2
        exit 1
    fi
    git -C "$source_dir" pull --ff-only
else
    git clone "$repository" "$source_dir"
fi

# A piped bootstrap must return stdin to the terminal for interactive menus.
if [[ ! -t 0 ]] && { : </dev/tty; } 2>/dev/null; then
    exec "$source_dir/setup.sh" "$@" </dev/tty
fi
exec "$source_dir/setup.sh" "$@"
