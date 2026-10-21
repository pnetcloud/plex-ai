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

Profiles configure subagents. Choose the root coordinator's model in your main chat;
the plan shows a recommendation. See [how the main chat and team work](../docs/product.md#the-main-chat-and-the-team).

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

## Option reference

Omitted settings keep their saved values. Interaction is explicitly saved in every applied preset. See [configuration](../docs/configuration.md) for profiles, overrides and file paths.

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
| `--release TAG` | Use a published tag, for example v0.5.3. |
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
