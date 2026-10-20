# Installation and CLI reference

[English](installation.md) · [Русский](translations/ru/installation.md) · [Deutsch](translations/de/installation.md) · [简体中文](translations/zh-CN/installation.md)

Requirements: Git, curl, the selected client CLI, and uv or Python 3.11+. BMad dependency installation also needs Node.js/npm and uv.

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



Plugin-manager changes and completed client installations are not rolled back if a later client fails.

An existing command from another checkout, a foreign file or a broken link is
kept with a notice; it does not block normal setup. The installer prints its own
entrypoint when the existing command is retained. Explicit `--install-command`
still refuses to overwrite an unrelated command.


## Existing installations and compatibility

After selecting the client, scope and project, setup detects an existing team
from its installation receipt and offers **Update only** (`refresh`) or
**Reconfigure** (`configure`). Update is selected by default; explicit settings
flags make reconfiguration the default. Selecting update skips the team, profile,
interaction and concurrency questions and retains each client's instruction-block
choice. Explicit CLI overrides still apply; the plan always requires confirmation.
For several clients, the selected action is reused after the first existing team
is found. A shared plugin alone does not count as a team installed in a new project.

Without prompts (`--yes`), existing settings are kept unless overridden explicitly.
Reconfiguration opens the normal menus with saved values. Missing BMad prerequisites
may still need a decision; update mode does not offer switching to another team.
Refresh uses this checkout's definitions; use `plex update` or the GitHub installer
to download a newer source first. Dev mode remains local and is preserved.

Compatibility stays in the existing resolver: add missing defaults, keep overrides,
and migrate supported old managed markers. Existing vendor-specific profile IDs
are kept during refresh. Replaced managed files use the existing backups and
ownership checks. Edited managed files, unknown configuration or receipt fields
stop the operation; personal text and foreign files are preserved. There is no
forced reset or general migration framework. Plugin-manager changes remain separate
from role-file rollback.

## Local development with Codex

From the working Plex checkout, connect a test project without a release:

```sh
./setup.sh --dev --client codex --project /path/to/test-project
```

Available since v0.5.0; use the checkout whose skills you want to test.

`--dev` supports Codex at project scope. It links the complete `plex` and
`plex-setup` skill folders into `.agents/skills/` and disables
`pnet-plex@pnet-plex` in that project's `.codex/config.toml`. User configuration and
other projects stay unchanged. Codex must trust the project to load its config.
This does not disable cloud-managed plugins or unrelated same-name skills.

The managed `AGENTS.md` block (or the selected native instruction file) requires
using only these two project Plex skills. Resolve their symlinks first: references,
checker, `teams/`, coordinator and profiles come from the same working checkout.
BMad remains a separately installed dependency. Keep the checkout available.

Skill edits are visible through the links; reopen Codex to load them. Changes to
roles, profiles or the workflow catalog require rerunning setup.
`plex status --client codex` reports the configured development source and checks
its links and local plugin override; it does not prove what a running model has loaded.
Rerunning setup preserves dev mode unless `--no-dev` is supplied.

```sh
./setup.sh --no-dev --client codex --project /path/to/test-project
```

`--no-dev` removes owned links and the owned plugin override, refreshes the team
and resumes shared plugin installation. `plex uninstall` also cleans up dev state.
Foreign skills and modified links/overrides stop changes. An existing explicit
plugin override is preserved: if enabled, set it to `false` before entering dev
mode; a preexisting `false` stays disabled when leaving. Personal instruction text
is preserved. `.plex/dev.json` records the local source and override ownership;
do not commit that machine-specific state. `--dry-run` previews without writes.
`--dev` is independent of `plex update --development`, which selects `main`.

## Terminal output

Setup, status, source updates and removal use consistent headings, aligned settings,
agent/model tables and highlighted shell commands. Green marks success, yellow marks
warnings, red marks errors, and muted text separates paths and explanatory details.
The installation plan shows the managed instruction file without printing its full template.
Narrow terminals stack agent settings instead of squeezing a table.

Colors and emphasis are enabled only for a terminal. Redirected output stays plain;
`NO_COLOR=1` or `TERM=dumb` also selects plain output and numbered menu prompts.
`--help` groups options by purpose. Machine-readable status and removal use `--json`,
including removal previews; JSON stdout contains no decoration or progress messages.

```sh
plex --help
plex status
plex status --json
plex uninstall --dry-run
plex uninstall --dry-run --json
NO_COLOR=1 plex status
```

## Commands

| Command | Behavior |
|---|---|
| `plex setup` | Open setup; also the default when no command is supplied. |
| `plex status` | Read-only check of configuration and plugin/source discovery; --json is available. |
| `plex update` | Download a selected version, then reopen setup. |
| `plex uninstall` | Remove unchanged owned roles/instructions and dev links/override; retain shared dependencies, checkout and preferences. |

`status` and `uninstall` accept `--project`, repeated `--client` (or `--host`) and `--scope`. Removal accepts `--dry-run` and `--yes`. `--dev`/`--no-dev` apply to setup only; status and removal detect dev state automatically.

## All setup options

Interactive setup asks for the mode once for all selected clients, with the saved mode selected (or `balanced` for a new installation). Every applied preset explicitly records `interaction`, including refreshed older presets.

| Option | Behavior |
|---|---|
| `--project PATH` | Existing target project; interactive setup asks if omitted. |
| `--client codex\|claude\|antigravity` | Select a client; repeat for several clients. |
| `--host CLIENT` | Compatibility alias for one client; also supports vendor-specific profiles. |
| `--scope project\|user` | Project (default) or user-wide roles and managed instructions; the normal plugin is user-wide in both cases. |
| `--team pnet\|bmad` | Role set; preserve the saved team if omitted, otherwise use pnet. |
| `--model-profile PROFILE` | Shared tier: inherit, basic, plus, pro, pro-plus; preserve the saved profile. See configuration for vendor-specific IDs. |
| `--interaction interactive\|balanced\|auto` | Question policy for agent work; preserve the saved value, default balanced. |
| `--max-agents N` | Positive concurrent-assignment limit; preserve the saved limit. |
| `--instructions / --no-instructions` | Manage only the Plex instruction block (default enabled), or skip it. |
| `--dev / --no-dev` | Codex project only: connect this checkout with live skill links, or leave dev mode. Requires managed instructions; preserves dev mode when omitted. |
| `--install-bmad` | Authorize selected official user-wide BMad skills and missing project runtime initialization; selected skill files may be replaced. |
| `--init-bmad` | Initialize missing project BMad runtime using installed official setup. |
| `--bmad-skill PATH` | Explicit installed official BMad setup skill directory. |
| `--roles-only` | Skip Plex plugin installation; explicit BMad dependency flags still apply. |
| `--command / --no-command` | Create the optional ~/.local/bin/plex shortcut (default), or skip it; dev mode skips shortcut installation. |
| `--install-command` | Install only the shortcut to this checkout; refuses foreign commands. Cannot combine with --dev. |
| `--dry-run` | Preview without writes; incompatible with --install-command. |
| `--yes` | Apply without prompts; specify a client and a project path (the path may be omitted with --scope user). BMad initialization uses displayed defaults. |
| `--json` | Machine-readable status or uninstall output. |
| `-h / --help` | Show available arguments. |

## Download and update options

Use `plex update --release TAG` for a published tag, or `plex update --development` for `main`. The GitHub bootstrap accepts the same source options and `--checkout PATH` (default `~/.local/share/plex-ai`); `--checkout` is a bootstrap option, not a setup option. Bootstrap/update `--dry-run` previews source selection only. Other setup flags are forwarded. Example:

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --release v0.5.1
```

See [configuration](../docs/configuration.md) for team/profile precedence and managed files.
