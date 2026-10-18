# Configuration

[English](configuration.md) · [Русский](translations/ru/configuration.md) · [Deutsch](translations/de/configuration.md) · [简体中文](translations/zh-CN/configuration.md)

## Install and refresh

For the first installation, follow the [quick start](../README.md#quick-start).
The bootstrap keeps a shared checkout in `~/.local/share/plex-ai` and starts setup
from your current project directory. Keep that checkout: installed plugins refer to it.
Rerun the same command to update it and reopen setup:

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

Updates use a fast-forward Git pull; conflicting local changes stop the update.
Review the setup plan to apply changed roles/profiles, then reload the client.
`~/.local/bin/plex` reopens setup without downloading updates; asking for Plex
inside the client starts coordination.

From a checkout, run `./setup.sh`. Select clients with Space, then press Enter.
Choose a team, scope and shared profile; inspect each installation plan before applying.
Project scope is the default. The host CLI must be available.

```sh
./setup.sh --project /path/to/project --client codex --client antigravity --team pnet --model-profile plus --yes
```

Full setup installs the shared Plex plugin and configures native roles/instructions.
The plugin remains shared; project skills are not duplicated. Keep its source/export
available while a local marketplace refers to it. BMad project setup requires an
existing BMad runtime and the appropriate installed skills.

Rerun setup to refresh or switch team/profile. Existing overrides are preserved;
new definitions reach installed roles only after refresh. Start a fresh host session
to load changed skills/roles. A shared project-profile change refreshes already
configured clients; a client without a receipt is not installed implicitly.

| Option | Behavior |
|---|---|
| `--dry-run` | Preview without writes |
| `--roles-only` | Apply roles/state without native plugin installation |
| `--no-instructions` | Skip managed instruction integration |
| `--no-command` | Skip the `~/.local/bin/plex` shortcut |
| `--install-command` | Install only that checkout shortcut |
| `--max-agents N` | Set the shared assignment limit |

Plugin-manager changes and completed client installations are not rolled back if a later client fails.

## Teams and profiles

| Team | Roles | Workflow |
|---|---|---|
| `pnet` | pm, explorer, researcher, dev, reviewer, qa | Standalone coordination |
| `bmad` | analyst, pm, po, ux, architect, dev, reviewer | Existing BMad skills |

Choose `inherit`, `basic`, `plus`, `pro` or `pro-plus`. Shared tiers combine the
selected team's OpenAI settings for Codex, Anthropic settings for Claude Code and
Google settings for Antigravity. `inherit` leaves model/effort to host defaults.
Profiles describe settings, not measured quality levels.

Edit `.plex/preset.toml` in the selected installation root:

```toml
team = "pnet"
model_profile = "plus"
max_agents = 3

[codex.dev]
reasoning = "max"
```

Per field: **profile default → profile role → host override → role override**.
Host tables are `[codex]`, `[claude]`, `[antigravity]`; role tables add the role name.
Both accept `model` and `reasoning`. For Codex inheritance, omit `model`.
Team switches preserve inactive overrides for roles absent from the selected team.

Definitions live in `teams/<team>/team.toml`, `agents/<host>/` and `profiles/*.toml`.
Vendor files declare one host and independent tier blocks; profiles have no include chain.
Exact model IDs and effort settings belong there, not in duplicated documentation tables.

Vendor-specific IDs such as `openai-plus` or `google-anthropic-plus` are available
through single-client `--host` setup and the resolver. Multi-client `--client` setup
uses shared tiers. The single-client custom menu edits per-role overrides on a named
profile; `custom` itself is not a saved profile. Model availability remains host/provider-dependent.

## Project and user scope

| Client | Project roles | User root / role directory |
|---|---|---|
| Codex | `.codex/agents/` | `$CODEX_HOME` or `~/.codex` / `agents/` |
| Claude Code | `.claude/agents/` | `$CLAUDE_CONFIG_DIR` or `~/.claude` / `agents/` |
| Antigravity | `.agents/agents/` | `~/.gemini` / `config/agents/` |

Each root keeps its own `.plex` state. `check --host <host> --scope auto` chooses
project state first, otherwise user state. Stale or conflicting project state does
not fall back silently. Changing scope does not delete or migrate another scope.
User-scoped BMad roles still require BMad prerequisites in each working project.

## Managed instructions and state

Only the `<!-- plex:start -->` … `<!-- plex:end -->` block is owned by Plex.
Keep personal instructions outside it. Edited, missing, duplicate or malformed
managed markers cause a conflict instead of overwriting user changes.

The installer selects an existing nonempty native instruction file, or creates the
standard file: Codex `AGENTS.override.md`, then `AGENTS.md`, then configured project
fallbacks; Claude `CLAUDE.md`, then project `.claude/CLAUDE.md`; Antigravity `GEMINI.md`,
then project `AGENTS.md`. User-scope Codex fallbacks are not used. Selection does not
change the host's fallback configuration or make it read an additional instruction file.

| File | Ownership |
|---|---|
| `.plex/preset.toml` | Editable team/profile/overrides |
| `.plex/resolved.json` | Generated effective snapshot |
| `.plex/applied.json` | Per-client receipt and managed hashes |
| `.plex/backups/` | Replaced files and retired roles |

Do not hand-edit generated roles or receipts. Foreign files, changed managed files,
symlinks and concurrent applies block unsafe updates. Resolve the reported conflict
before refreshing; retain backups.

## Inspect without applying

From the Plex checkout, with Python 3.11+:

```sh
python3 skills/plex-setup/scripts/resolve_config.py list
python3 skills/plex-setup/scripts/resolve_config.py resolve /path/to/project/.plex/preset.toml
python3 skills/plex-setup/scripts/resolve_config.py render /path/to/project/.plex/preset.toml --host codex
python3 skills/plex-setup/scripts/resolve_config.py check /path/to/project --host codex --scope auto
```

`apply` writes native configuration; instruction integration requires its explicit
`--instructions` flag when using the resolver directly. The checkout installer
handles the preview, plugin installation and instruction integration together.

For optional BMad review customization, follow the team's
[review policy](../teams/bmad/review-policy.md). Ordinary setup does not enable it.
