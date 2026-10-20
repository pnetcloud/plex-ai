# Configuration

[English](configuration.md) · [Русский](translations/ru/configuration.md) · [Deutsch](translations/de/configuration.md) · [简体中文](translations/zh-CN/configuration.md)

## Install and refresh

For first installation, follow the [quick start](../README.md#quick-start).
The bootstrap keeps a shared checkout in `~/.local/share/plex-ai` and installs the
newest **published release, including previews**. Keep that checkout: installed plugins refer to it.
The entrypoint comes from `main`; application files are checked out at the selected release tag.

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

### Status, update and removal

```sh
plex status
plex status --json
plex update
plex update --release v0.2.0
plex update --development
plex uninstall --dry-run
plex uninstall
```

`status` checks project configuration first, otherwise the selected client's user
installation. It reports the source version, team/profile, native roles, conflicts
and plugin discovery. It changes no Plex configuration. `--json` gives structured
output; configured clients with conflicts, stale state or an unavailable plugin
return a nonzero status. This does not prove runtime model routing.

`update` selects the newest published release and reopens setup to refresh the chosen
clients. `--release` pins a published tag; `--development` explicitly selects `main`.
Source checkouts with local changes, symlinks or another origin are refused. Updates
use detached release checkouts, not a moving branch. `update --dry-run` previews
source selection without writing a checkout or applying configuration.

`uninstall` defaults to project scope and all recorded clients. Preview with
`--dry-run`; interactive removal asks for confirmation, unattended removal needs
`--yes`. Filter with `--client codex`, or explicitly select `--scope user`.
Only unchanged receipt-owned roles and the matching managed instruction block are
removed. Modified/missing owned files or malformed markers stop the operation;
foreign files and surrounding instructions remain untouched. A block shared with
another client stays until that client is removed. Each client's removal has its
own lock, transaction and backups; multi-client removal is not one global transaction.

Shared plugins, the source checkout, CLI shortcut, editable preset and backups remain
for other projects or reinstall. Native instruction files remain after block removal.
Retained project preferences continue to take precedence over global defaults; the
command does not automatically switch your scope. Reopen a client session after changes.
Use `~/.local/bin/plex` if the shortcut is not on your PATH. Plain `plex` opens setup.

From a checkout, run `./setup.sh`. Select clients with Space, then press Enter.
Choose a team, scope and shared profile; inspect each installation plan before applying.
Project scope is the default. The host CLI must be available.

```sh
./setup.sh --project /path/to/project --client codex --client antigravity --team pnet --model-profile plus --yes
```

Full setup installs the shared Plex plugin and configures native roles/instructions.
The plugin remains shared; project skills are not duplicated. Keep its source/export
available while a local marketplace refers to it. BMad project setup requires the appropriate installed skills and project runtime;
the installer can initialize missing runtime through installed official BMad setup.

Rerun setup to refresh or switch team/profile. Existing overrides are preserved;
new definitions reach installed roles only after refresh. Start a fresh host session
to load changed skills/roles. A shared project-profile change refreshes already
configured clients; a client without a receipt is not installed implicitly.

For a project-scoped `bmad` team without runtime, setup offers official
initialization, switching to `pnet`, or cancellation. If the BMad setup skill is
missing, it offers a separate user-wide dependency installation. Explicit approval
is required: selected user skill files may be replaced and other projects share
them. Existing plugins are left unchanged.

`--install-bmad` authorizes that installation and project initialization;
`--init-bmad` initializes from already installed skills. With `--yes`, displayed
module defaults are accepted. `--dry-run` writes nothing. Setup invokes BMad's
official script after plan confirmation, asking only unanswered module questions.
Runtime and installed dependencies remain if a later step fails.

Fresh installations use `skills@1.7.4` and the official BMad revision
`495ef6e0996d07b23359cc4d6c73a1aa2f3ba5ad`, selecting only the team's entry/workflow
skills, the `bmad` hub and two module records. This includes PO, which the current
plugin marketplace lacks. Node.js/npm and `uv` are required. Codex, Claude Code and
Antigravity are supported by the official Skills CLI.

Direct project/user skills are preferred during discovery. Enabled installed
Codex/Claude Toolbox plugins are also supported; arbitrary cache folders are not
installation evidence. Use `--bmad-skill /path/to/installed/bmad` for an explicit
hub. User-scoped roles still require runtime in every working project.


| Option | Behavior |
|---|---|
| `--dry-run` | Preview without writes |
| `--roles-only` | Skip Plex plugin installation; explicit BMad dependency flags still apply |
| `--no-instructions` | Skip managed instruction integration |
| `--no-command` | Skip the `~/.local/bin/plex` shortcut |
| `--install-command` | Install only that checkout shortcut |
| `--max-agents N` | Set the shared assignment limit |

Plugin-manager changes and completed client installations are not rolled back if a later client fails.

An existing command from another checkout, a foreign file or a broken link is
kept with a notice; it does not block normal setup. The installer prints its own
entrypoint when the existing command is retained. Explicit `--install-command`
still refuses to overwrite an unrelated command.


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

Definitions live in `teams/<team>/team.toml`, `agents/*.md` and `profiles/*.toml`.
Vendor files declare one host and independent tier blocks; profiles have no include chain.
Exact model IDs and effort settings belong there, not in duplicated documentation tables.

`[skills]` binds each role to its entry skill. Optional `[[workflows.<role>]]`
entries list the team's supported assignments: required `skill` and `description`,
plus an optional `operation` menu code for dispatch inside a persona. For example:

```toml
[[workflows.analyst]]
skill = "bmad-deep-recon"
description = "Research a topic or compare options using cited evidence."

[[workflows.po]]
skill = "bmad-agent-po"
operation = "SPEC"
description = "Write requirements and a specification from the supplied inputs."
```

The resolver validates this catalog and includes it in `.plex/resolved.json`.
The coordinator selects by description and passes explicit intent and parameters;
the subagent checks installed dispatch and loads only the selected workflow.
Catalog entries do not eagerly activate skills, install BMad or grant approval.
Workflow procedures remain in installed BMad. Edit the team catalog and refresh
setup after changes; existing snapshots do not update automatically.

Vendor-specific IDs such as `openai-plus` or `google-anthropic-plus` are available
through single-client `--host` setup and the resolver. Multi-client `--client` setup
uses shared tiers. The single-client custom menu edits per-role overrides on a named
profile; `custom` itself is not a saved profile. Model availability remains host/provider-dependent.

## Interaction

Set `interaction = "balanced"` at the root of `.plex/preset.toml`, or pass
`--interaction interactive|balanced|auto` to setup or resolver `apply`.
Omitting it preserves the saved value; new configurations default to `balanced`.
The plan shows the effective mode. It is shared across clients and survives team
and profile changes. Refresh setup after editing the preset.

| Mode | Behavior |
|---|---|
| `interactive` | Collaborative discovery and meaningful user choices |
| `balanced` | Resolve routine choices; ask only for consequential unresolved decisions or applicable checkpoints |
| `auto` | No questions or waiting; complete authorized work and return partial results or blockers |

An explicit user mode for one task overrides the saved mode without changing
configuration. The coordinator passes it to all assignments. Subagents return
questions to the coordinator; it reuses existing answers, groups necessary questions
in balanced mode and continues independent work. In auto, unresolved gates block
dependent work and are reported instead of waiting indefinitely.

For bounded artifact work, balanced/auto request native BMad headless execution
where supported, using the installed workflow's contract. Unsupported routes keep
their real checkpoints; auto returns a blocker when no authorized path can proceed.
Modes do not skip reviews/tests or grant extra permissions, publication authority
or analyst approval. Partial artifacts with unresolved requirements are not approved
inputs for dependent implementation. This is an instruction policy, not a guarantee
of unattended completion for every BMad workflow.

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
