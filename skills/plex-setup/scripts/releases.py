# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Select a published Plex release and update a dedicated source checkout."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "https://github.com/pnetcloud/plex-ai.git"
API = "https://api.github.com/repos/pnetcloud/plex-ai/releases"


def message(text, *, error=False):
    stream = sys.stderr if error else sys.stdout
    label = "ERROR" if error else "SOURCE"
    if stream.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb":
        label = f"\033[{'1;31' if error else '1;36'}m{label}\033[0m"
    print(f"\n  [{label}] {text}", file=stream, flush=True)


def published_release(version=None):
    suffix = "/tags/" + urllib.parse.quote(version, safe="") if version else "?per_page=100"
    request = urllib.request.Request(API + suffix, headers={"User-Agent": "Plex Installer"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot look up published Plex releases: {error}") from error
    releases = [data] if version else data
    if not isinstance(releases, list):
        raise ValueError("Invalid GitHub release response")
    candidates = [r for r in releases if isinstance(r, dict) and not r.get("draft") and r.get("published_at")
                  and re.fullmatch(r"v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", r.get("tag_name", ""))]
    if version:
        candidates = [r for r in candidates if r["tag_name"] == version]
    if not candidates:
        raise ValueError("No published Plex release found; use --development only to explicitly select main")
    return max(candidates, key=lambda r: r["published_at"])["tag_name"]


def git(checkout, *args):
    result = subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "Git command failed")
    return result.stdout.strip()


def update_checkout(checkout, version=None, development=False, dry_run=False):
    if development and version:
        raise ValueError("Choose --release or --development, not both")
    checkout = Path(checkout).expanduser().absolute()
    target = "main" if development else published_release(version)
    if checkout.exists() or checkout.is_symlink():
        if checkout.is_symlink() or not (checkout / ".git").exists():
            raise ValueError(f"Existing directory left unchanged: {checkout}")
        if git(checkout, "remote", "get-url", "origin") not in (REPOSITORY, "git@github.com:pnetcloud/plex-ai.git"):
            raise ValueError(f"Unrelated checkout left unchanged: {checkout}")
        if git(checkout, "status", "--porcelain"):
            raise ValueError("Checkout has local changes; commit or move them before updating")
        if dry_run:
            message(f"Would update {checkout} to {target}")
            return target
        message(f"Fetching {target} → {checkout}")
        git(checkout, "fetch", "origin", *(["main"] if development else ["tag", target]))
        git(checkout, "checkout", "--detach", "FETCH_HEAD" if development else target)
    else:
        if dry_run:
            message(f"Would install {target} in {checkout}")
            return target
        checkout.parent.mkdir(parents=True, exist_ok=True)
        message(f"Downloading {target} → {checkout}")
        result = subprocess.run(["git", "clone", "--branch", target, REPOSITORY, str(checkout)],
                                capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise ValueError("Could not download Plex: " + (result.stderr.strip() or result.stdout.strip()))
        if development:
            git(checkout, "checkout", "--detach", "HEAD")
    message(f"Plex source: {target} ({git(checkout, 'rev-parse', '--short', 'HEAD')})")
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--checkout", type=Path, default=Path.home() / ".local/share/plex-ai")
    parser.add_argument("--release", help="Published tag, for example v0.2.0; default: newest published release, including previews")
    parser.add_argument("--development", action="store_true", help="Explicitly use main instead of a release")
    parser.add_argument("--dry-run", action="store_true", help="Preview source selection without checkout or setup writes")
    args, setup_args = parser.parse_known_args(argv)
    try:
        update_checkout(args.checkout, args.release, args.development, args.dry_run)
        if args.dry_run:
            return 0
        return subprocess.call([str(args.checkout / "setup.sh"), *setup_args])
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        message(f"Plex update stopped: {error}", error=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
