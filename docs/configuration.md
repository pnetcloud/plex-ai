# Configuration

[English](configuration.md) · [Русский](translations/ru/configuration.md) · [Deutsch](translations/de/configuration.md) · [简体中文](translations/zh-CN/configuration.md)

[Installation, dev mode and all CLI options](installation.md).

## Generated state files

Plex stores `applied.toml`, `resolved.toml` and `skill-aliases.toml` alongside
`preset.toml` in `.plex/`. Setup automatically migrates their legacy JSON files
when configuration is applied, using verified backups and rollback. Read-only
status/preview supports old installations without modifying them. Conflicting
JSON/TOML copies are preserved and reported; matching copies are consolidated.
`plex status` shows the observed config format. CLI `--json` output remains JSON.
Edit durable settings in `preset.toml`; the other files are generated.

## Teams and profiles

| Team | Roles | Workflow |
|---|---|---|
| `pnet` | pm, explorer, researcher, dev, reviewer, qa, devops | Standalone coordination |
| `bmad` | analyst, pm, po, ux, architect, dev, reviewer, devops | Existing BMad skills |

Choose `inherit`, `basic`, `plus`, `pro`, `pro-plus`, `ultra` or `ultra-plus`. Shared tiers combine the
selected team's OpenAI settings for Codex, Anthropic settings for Claude Code and
Google settings for Antigravity. `inherit` leaves model/effort to host defaults.
Profiles describe settings, not measured quality levels.

Both teams provide six named tiers plus `inherit`. Coordinator recommendations appear first within each tier in the provider files. Anthropic uses Haiku/Sonnet/Opus as approximate Luna/Sol/Astra counterparts; these are not measured equivalents. Google native profiles use Flash or inherit the main-chat model, with higher requested effort for Ultra tiers. Claude on Antigravity substitutes Sonnet for unavailable Haiku; exact model IDs require host support.

Role recipes are explicit per team and provider; the profile table in the README describes `pnet`
only. For example, BMad's Codex main-chat recommendation is Luna/xhigh on Pro+ and Sol/medium
on Ultra, while `pnet` uses Luna/max and Sol/low. BMad OpenAI Ultra+ UX remains Astra/medium.
DevOps has its own entry in each team/provider profile; it does not inherit another role's
settings. See the [pnet](../teams/pnet/profiles/) and [BMad](../teams/bmad/profiles/) profile
files for exact recipes; setup shows effective settings after overrides.

Interactive **Reconfigure** shows edited receipt-owned role paths, backs up their previewed content and regenerates them from the selected profile and preset overrides. **Update only** still stops on manual edits. Missing or unmanaged files, symlinks, edited instruction blocks, client configuration conflicts and changes after preview remain protected. Put durable model choices in `.plex/preset.toml`.

Edit `.plex/preset.toml` in the selected installation root:

```toml
team = "pnet"
model_profile = "plus"
max_agents = 3

[codex.dev]
reasoning = "max"
```

Plex does not configure token budgets. Refresh removes retired budget settings from older presets. Work follows acceptance criteria and actual host constraints.

Optional `[coordinator.<tier>]` tables in vendor profile files hold main-chat
recommendations (`model`, `reasoning`). They are separate from role settings and
appear as `coordinator` in the resolved snapshot. Setup displays the selected
profile's recommendation; it never applies it to the client or installs a coordinator
role. A missing recommendation, including `inherit`, leaves the choice to the user.

Per field: **profile default → profile role → host override → role override**.
Host tables are `[codex]`, `[claude]`, `[antigravity]`; role tables add the role name.
Both accept `model` and `reasoning`. For Codex inheritance, omit `model`.
Team switches preserve inactive overrides for roles absent from the selected team.

Definitions live in `teams/<team>/team.toml`, `agents/*.md` and `profiles/*.toml`.
Vendor files declare one host and independent tier blocks; profiles have no include chain.
Exact model IDs and effort settings belong there, not in duplicated documentation tables.

`[skills]` binds each role to its persona entry skill. Optional `[[workflows.<role>]]`
entries list supported assignments: required `skill` and `description`, plus an
optional `operation` menu code for dispatch inside that persona. Its absence only
indicates that no persona-local menu code is specified; it does not select direct
versus persona/menu mode or prove standalone eligibility. Existing outcome/input
selects entry mode, and the selected installed skill's actual contract governs. The
role key identifies the eligible executor. For example:

```toml
[[workflows.analyst]]
skill = "bmad-deep-recon"
description = "Research a topic or compare options using cited evidence."

[[workflows.po]]
skill = "bmad-agent-po"
operation = "SPEC"
description = "Write requirements and a specification from the supplied inputs."
```

The resolver validates this catalog and includes it in `.plex/resolved.toml`.
PM selects the minimal sufficient route from the full map in the exact snapshot;
the root dispatches it with explicit intent and parameters. The subagent checks
installed dispatch and loads only the selected workflow.
Catalog entries do not eagerly activate skills, install BMad or grant approval.
Workflow procedures remain in installed BMad. Edit the team catalog and refresh
setup after changes; existing snapshots do not update automatically.

Before installing official BMad user skills, setup checks the pinned source catalog
and stops before writing if a requested skill is unavailable. It installs only
missing skills, keeps valid existing files, and can be retried after a partial
installation without reinstalling skills that already succeeded.

Vendor-specific IDs such as `openai-plus` or `google-anthropic-plus` are available
through single-client `--host` setup and the resolver. Multi-client `--client` setup
uses shared tiers. The single-client custom menu edits per-role overrides on a named
profile; `custom` itself is not a saved profile. Model availability remains host/provider-dependent.

## Interaction

Interactive setup asks for the mode once for all selected clients, with the saved mode selected (or `balanced` for a new installation). Every applied preset explicitly records `interaction`, including refreshed older presets.

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

Route choice follows the effective mode: in `interactive`, PM may present materially
different task-appropriate routes with a recommendation for the root to ask the user;
in `auto`, PM chooses independently without optional route questions. `balanced`
keeps its existing rule above. Reuse a settled route without asking again. Route
selection does not approve a workflow plan or replace its genuine checkpoints; in
`auto`, a checkpoint without an authorized headless path remains a blocker.

For bounded artifact work, balanced/auto request native BMad headless execution
where supported, using the installed workflow's contract. Unsupported routes keep
their real checkpoints; auto returns a blocker when no authorized path can proceed.
Modes do not skip reviews/tests or grant extra permissions, publication authority
or analyst approval. Partial artifacts with unresolved requirements are not approved
inputs for dependent implementation. This is an instruction policy, not a guarantee
of unattended completion for every BMad workflow.

## Workspace and native delegation

Existing uncommitted changes alone do not require confirmation. Plex records the initial state, assigns task-owned files and preserves pre-existing changes, including unrelated hunks inside an assigned file. That authorization is passed to workflows; a dirty-tree-only confirmation is already answered. Conflicting edits block affected work only. Plex does not create worktrees, switch branches, stash, reset, clean or commit to make the tree clean.

For Codex, setup manages missing `hide_spawn_agent_metadata = false` and `tool_namespace = "agents"` settings under `[features.multi_agent_v2]`. When no explicit native capacity applies, it also manages `agents.max_concurrent_threads_per_session = max_agents` in the same config transaction. The `[agents]` header stays outside the removable capacity block so later personal keys keep their table scope.

Existing canonical `agents.max_concurrent_threads_per_session` and legacy
`agents.max_threads` limits remain user-owned, including equal aliases. Different
aliases and boolean, non-integer or non-positive values conflict before writes.
Values above the signed 64-bit integer range also conflict before writes; this
is a config representation boundary, not a concurrency recommendation.
An equal local legacy alias added beside a Plex-owned canonical key makes Plex
relinquish only its owned key and receipt; the user alias remains. Explicit user
global limits remain in place, even when lower than `max_agents`. An ancestor
`.codex/config.toml` candidate without proof that its layer applies, or a profile
that may supply capacity, makes applicability unknown and suppresses automatic
capacity mutations. Under that uncertainty, an existing unchanged Plex-owned
block and receipt stay unchanged even when `max_agents` changes. Unchanged
Plex-owned capacity follows a refreshed `max_agents` when applicability is
known; Plex relinquishes it for a known applicable inherited limit or an equal
local legacy alias. Edited, missing or unmanaged markers are conflicts. Receipts
keep existing routing ownership compatible and uninstall removes only unchanged
Plex-owned blocks.

`max_agents` counts unfinished Plex assignments. The native setting limits
concurrently open child-agent threads, including nested and idle child handles;
the primary thread is excluded. Setup and status show the origin, value and any
mismatch separately, and mark session activation as unknown. A file check proves
saved configuration only; active profiles, CLI overrides and session recognition
can affect runtime. The installer never restarts Codex. Open a fresh session after
applying settings and verify the active spawn schema and accepted role separately.

Project configuration must be trusted by Codex. Open a new client session after setup. Preflight distinguishes a missing spawn tool, a hidden role selector, a rejected role and accepted dispatch. When the selector is available, request the checked role even if no inventory is displayed; use a fresh context and a self-contained handoff when supported. File/configuration checks do not prove that an existing session loaded its roles or that the child used the requested model.

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

Unchanged receipt-owned blocks using the old `plex:start` / `plex:end` markers are migrated automatically on refresh. Mixed marker formats or edited blocks stop the update.

Only the `<!-- plex:managed:start -->` … `<!-- plex:managed:end -->` block is owned by Plex.
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
| `.plex/resolved.toml` | Generated effective snapshot |
| `.plex/applied.toml` | Per-client receipt and managed hashes |
| `.plex/skill-aliases.toml` | Codex short-name links; generated ownership receipt |
| `.plex/dev.json` | Codex dev links and project plugin override; generated ownership receipt |
| `.plex/backups/` | Replaced files and retired roles |

Do not hand-edit generated roles or receipts. Foreign files, changed managed files,
symlinks and concurrent applies block unsafe updates. Resolve the reported conflict
before refreshing; retain backups. Interactive Reconfigure can replace receipt-owned role edits as described above.

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

## Other Codex agents

Plex-owned assignments use only exact `plex-<role>` names from the checked active team. Other installed or built-in agents are outside that team; workflow-owned leaves follow their workflow contract.

Setup lists other `.toml` agents found in the selected scope and offers **Keep** (default) or **Move to backup**. They remain available to the client and can affect role selection. Only eligible files move to `.plex/backups/<timestamp>/codex/other-agents/`; restore a file manually from that directory if needed. Other scopes, symlinks and files referenced by explicit `config.toml` registrations are preserved. Edited managed roles remain conflicts outside interactive Reconfigure.
