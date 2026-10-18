#!/bin/sh
set -eu
script_path=$0
while [ -L "$script_path" ]; do
    script_dir=$(CDPATH= cd -- "$(dirname -- "$script_path")" && pwd)
    link_target=$(readlink "$script_path")
    case "$link_target" in
        /*) script_path=$link_target ;;
        *) script_path=$script_dir/$link_target ;;
    esac
done
script_dir=$(CDPATH= cd -- "$(dirname -- "$script_path")" && pwd)
if command -v uv >/dev/null 2>&1; then
    exec uv run --script "$script_dir/setup.py" "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 "$script_dir/setup.py" "$@"
else
    echo "Plex requires uv or Python 3.11+. Install either, then rerun this command." >&2
    exit 127
fi
