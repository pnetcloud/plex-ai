# Host plugin packaging

These directories hold Plex's distribution manifests for **Antigravity**, **Claude
Code**, and **Codex**. They configure installation of Plex into those hosts; they
are not plugins used to develop this repository.

The shared source lives in `skills/` and `teams/` at the repository root.
`teams/` contains each team's definition and agents, plus team-specific model profiles.
`setup.py` assembles the selected host's manifests, shared source
and license into a self-contained `.build/plugins/<host>/` package before invoking
the native plugin manager. Only individually approved files from `.gitignore` are
included. Developer configuration, tests, reports and local files are excluded.

Run the checkout's `setup.sh` from your project directory, or pass `--project`.
One full run installs the shared user plugin, configures project or user roles and
creates the `plex` shortcut. There is no separate project initialization step.
`--no-command` skips the shortcut; `--install-command` creates only the shortcut.
The launcher uses uv when available or Python 3.11+ with numbered menus otherwise.
`--dry-run` previews without building or installing; `--roles-only` configures
project roles without building a plugin. The manifest folders here are templates,
not standalone installation targets. Antigravity receives the assembled path.
Codex and Claude register the checkout's small marketplace indexes
(`.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`), which point
to `.build/plugins/<host>/`. These native discovery entry points remain at the root
to preserve existing local marketplace registrations; they contain no plugin code.

`.build/` is generated, ignored and recreated when source changes. Keep the checkout
and built packages in place while registered as a local marketplace, particularly
for Claude Code, which can load local marketplace plugins in place. Package updates
still use each host's native update behavior and versioning.
