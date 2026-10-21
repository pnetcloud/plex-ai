# Installation

[English](installation.md) · [Русский](translations/ru/installation.md) · [Deutsch](translations/de/installation.md) · [简体中文](translations/zh-CN/installation.md)

## Install

Run from your project directory. Requires Git, curl, your client CLI, and uv or Python 3.11+.

**Standard**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

**Dev mode · Codex**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --dev --client codex
```

Select the client, scope, team and profile, then confirm the plan. **Project** scope is recommended. Open a new client session after installation.

The final **Apply this plan?** prompt defaults to **Yes** for setup and refresh; select **No** to cancel. Archiving other agents and uninstall still require their own confirmation.

Profiles configure subagents. Choose the root coordinator's model in your main chat;
the plan shows a recommendation. See [how the main chat and team work](product.md#the-main-chat-and-the-team).

The installer registers the shared Plex plugin and applies the selected team. A plugin-only installation supplies skills; team setup supplies native roles and the managed instruction block. Dev mode uses local skill links instead.

[Chat examples](../README.md#use-in-chat).

## Short skill names · Codex

Standard setup adds `$plex` and `$plex-setup` through symlinks to the shared Plex checkout; the plugin stays enabled. Project scope uses `.agents/skills/`; user scope uses `$CODEX_HOME/skills/` (default `~/.codex/skills/`). No skill contents are copied. Keep the source checkout available.

Refresh setup once to add the names to an existing installation, then open a new Codex session. Foreign skills are preserved and reported as conflicts. `--roles-only` preserves existing aliases but does not add them to a new installation. Namespaced plugin calls remain available.

## Other Codex agents

Plex-owned assignments use only exact `plex-<role>` names from the checked active team. Other installed or built-in agents are outside that team; workflow-owned leaves follow their workflow contract.

Setup lists other `.toml` agents found in the selected scope and offers **Keep** (default) or **Move to backup**. They remain available to the client and can affect role selection. Only eligible files move to `.plex/backups/<timestamp>/codex/other-agents/`; restore a file manually from that directory if needed. Other scopes, symlinks and files referenced by explicit `config.toml` registrations are preserved. Edited managed roles remain conflicts.

For unattended cleanup, pass `--archive-other-agents --client codex`; `--yes` alone preserves other agents. `--dry-run` never moves files.

## Common commands

If the optional `plex` shortcut is absent (for example after a fresh dev installation), use `~/.local/share/plex-ai/setup.sh` in place of `plex` below.

| Task | Command |
|---|---|
| Configure or refresh this project | `plex` |
| Check configuration | `plex status` |
| Download a new release and open setup | `plex update` |
| Preview setup without writes | `plex --dry-run --client codex --project .` |
| Preview removal | `plex uninstall --dry-run` |
| Remove the project team | `plex uninstall` |
| Read status as JSON | `plex status --json` |
| Read the removal plan as JSON | `plex uninstall --dry-run --json` |

When a team is already installed:

| Option | Purpose |
|---|---|
| **Update only** | Keep saved settings and refresh managed files. |
| **Reconfigure** | Open setup menus with saved values. |

Explicit CLI options still apply. `plex` uses the current checkout; `plex update` downloads a newer published release, including previews.

## Dev mode

- Codex, **project scope only**. Both Plex skill folders link to the source checkout; keep it available.
- The project disables the shared Plex plugin and its managed instruction block selects local Plex skills. Codex must trust the project. Cloud-managed plugins and other same-name skills are not disabled.
- Skill edits follow the links. Role, profile and workflow-catalog changes require setup refresh; reopen the client. Dev mode stays enabled until `--no-dev`.

| Task | Command |
|---|---|
| Link a working checkout | `./setup.sh --dev --client codex --project /path/to/project` |
| Return to the shared plugin | `./setup.sh --no-dev --client codex --project /path/to/project` |

## BMad

Requires Node.js/npm and uv. Select the `bmad` team in setup, or run:

| Task | Command |
|---|---|
| Install selected official skills and initialize the project | `plex --team bmad --client codex --install-bmad` |
| Initialize using already installed BMad skills | `plex --team bmad --client codex --init-bmad` |

Skills are user-wide and selected skill files may be replaced. Runtime belongs to the project. Completed dependency/runtime installation remains after cancellation or a later failure. For unattended runs, add `--project . --yes`; displayed BMad defaults are accepted.

## Uninstall

**Project team** · run in the project directory:

```sh
plex uninstall --dry-run
plex uninstall
```

This removes unchanged managed roles, the owned Plex instruction block and owned skill links and dev overrides. Project instructions outside the block are preserved. Edited managed files stop removal for review.

**User-wide team** · choose the client whose global roles you installed:

```sh
plex uninstall --scope user --client codex
```

**Shared plugin** · remove only when your other projects no longer need it. Run the command for your client:

| Client | Command |
|---|---|
| Codex | `codex plugin remove pnet-plex@pnet-plex` |
| Claude Code | `claude plugin uninstall pnet-plex@pnet-plex --scope user` |
| Antigravity | `agy plugin uninstall pnet-plex` |

Codex can also remove the plugin through its `/plugins` browser. See the [OpenAI plugin guide](https://learn.chatgpt.com/docs/plugins#remove-a-plugin) and [Claude Code command reference](https://code.claude.com/docs/en/plugins/cli-reference#plugin-uninstall).

Team removal retains preferences/backups under `.plex`, BMad dependencies/runtime, the optional launcher and the source checkout. Plugin removal is a separate client operation; it does not remove teams from other projects. Keep the shared checkout while any project or dev link still uses it.

## Option reference

Omitted settings keep their saved values. Interaction is explicitly saved in every applied preset. See [configuration](configuration.md) for profiles, overrides and file paths.

### Clients and scope

| Option | Purpose |
|---|---|
| `--project PATH` | Existing project directory. |
| `--client CLIENT` | codex, claude or antigravity; repeat to select several. |
| `--host CLIENT` | Single-client compatibility alias; allows vendor-specific profiles. |
| `--scope project / user` | Role/instruction scope; default project. Normal plugins are user-wide. |
| `--instructions / --no-instructions` | Manage the Plex instruction block, or skip it. |

### Team and models

| Option | Purpose |
|---|---|
| `--team pnet / bmad` | Role set; default pnet for new installs. |
| `--model-profile PROFILE` | inherit, basic, plus, pro or pro-plus. |
| `--interaction MODE` | interactive, balanced (default) or auto. |
| `--max-agents N` | Positive concurrent-assignment limit. |

### Execution and output

| Option | Purpose |
|---|---|
| `--dev / --no-dev` | Link local Plex skills, or leave dev mode; Codex project only. |
| `--archive-other-agents` | Codex: explicitly back up and remove eligible other agents in the selected scope. |
| `--roles-only` | Skip Plex plugin installation; explicit BMad flags still apply. |
| `--command / --no-command` | Create ~/.local/bin/plex (default), or skip; dev mode skips it. |
| `--install-command` | Install only the shortcut; refuses foreign commands and cannot combine with --dev. |
| `--dry-run` | Preview without writes; incompatible with --install-command. |
| `--yes` | Apply without prompts; requires a client and project path (path optional with --scope user). |
| `--json` | JSON for status or uninstall, including removal previews. |
| `-h / --help` | Show grouped help and examples. |

### BMad

| Option | Purpose |
|---|---|
| `--install-bmad` | Authorize selected user skills and missing project runtime. |
| `--init-bmad` | Initialize missing runtime from installed official setup. |
| `--bmad-skill PATH` | Explicit installed BMad setup skill directory. |

### Source selection — update / GitHub bootstrap

| Option | Purpose |
|---|---|
| `--release TAG` | Use a published tag, for example v0.5.10. |
| `--development` | Use main; does not enable --dev mode. |
| `--checkout PATH` | GitHub bootstrap only; default ~/.local/share/plex-ai. |

The bootstrap stores the shared checkout in `~/.local/share/plex-ai`. Keep it available. Update/bootstrap `--dry-run` previews source selection only; other setup options are forwarded.

## Ownership and troubleshooting

- Removal defaults to project scope. Use `--client codex` to limit it, `--scope user` for user roles, or `--yes` for unattended removal.
- Only unchanged owned roles, instruction blocks and dev links/overrides are removed. Shared plugins, source, preferences and backups remain; edited owned files and unknown formats stop changes.
- Source updates refuse dirty, unrelated or symlinked checkouts. Native plugin changes and completed client installations are separate from role-file rollback.
- `status` checks project configuration first, otherwise user scope. It checks configuration/plugin discovery, not actual model routing.

| If… | Use… |
|---|---|
| plex is not on PATH | ~/.local/bin/plex, or ./setup.sh from the source checkout. |
| The shortcut belongs to another checkout | The printed setup.sh entrypoint; foreign commands are preserved. |
| A skill or managed file conflicts | Review the reported file; setup does not overwrite it. |
| An existing project plugin override blocks --dev | Set its enabled value to false manually; preexisting overrides are preserved on exit. |

## Output

Colors are terminal-only. `NO_COLOR=1` or `TERM=dumb` selects plain output and numbered menus; redirected output is plain. `--json` keeps stdout free of styling and progress messages.
