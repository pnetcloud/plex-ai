# Changelog

Important changes retained in Plex, grouped by release. The releases below are
previews; interfaces and configuration may change before 1.0.

## [0.5.4] — 2026-10-21

- Put native-role dispatch and Plex/role/task labels at the start of coordination
  instructions; report unavailable routing instead of silently using generic agents.
- Read instruction documents separately and recover truncated sections before
  delegation; move detailed BMad workflow rules into a separately loaded contract.
- Keep current assignment labels visible when reusing agents; task names do not
  replace native role selection or rename host-assigned nicknames.

## [0.5.3] — 2026-10-21

- Separate the main-chat coordinator recommendation from subagent settings in
  setup; read tier-specific recommendations from model profiles, keep the root
  model under the user's control and shorten profile menus.
- Recommend Codex coordinators by profile: Basic Luna/high, Plus Sol/low,
  Pro Sol/medium and Pro+ Sol/high; leave `inherit` to the session choice.
- Fix spacing between CLI labels and values; explain coordinator responsibilities
  and model selection in all four documentation languages.

## [0.5.2] — 2026-10-20

- Simplify Quick start to standard and Codex `--dev` installation commands; remove
  demo-directory scaffolding and move prerequisites to the installation guide.
- Reorganize installation documentation around command scenarios, dev/BMad setup,
  grouped options and troubleshooting; shorten the guide by about half in all four languages.
- Document the source-checkout entrypoint when the optional `plex` shortcut is absent,
  including fresh dev installations. Installer behavior is unchanged.

## [0.5.1] — 2026-10-20

- Restyle CLI setup, status, source updates, removal and help with consistent
  sections, model tables, command highlights and terminal-aware colors. Keep
  redirected/NO_COLOR output plain and JSON responses free of decoration.
- Show compact instruction-file summaries instead of dumping the full template;
  make removal output human-readable by default, with `--json` for automation.

## [0.5.0] — 2026-10-20

- Detect existing team installations and offer update-only or reconfiguration;
  preserve saved settings, legacy profile IDs and per-client instruction choices
  during refresh, using existing compatibility and conflict checks.
- Offer interaction-mode selection in interactive setup and explicitly save it in
  every applied preset, preserving saved modes and upgrading older configurations.
- Use `plex:managed:start/end` instruction markers and migrate unchanged owned
  blocks with legacy markers during refresh.
- Add Codex project `--dev` setup with live links to the working Plex skills,
  a project-only plugin override, explicit local-source instructions, source status
  and owned cleanup through `--no-dev` or uninstall.
- Publish a dedicated installation and CLI reference with English, Russian, German
  and Chinese versions, linked from every root README.

## [0.4.0] — 2026-10-20

- Offer explicit user-wide installation of selected official BMad skills for Codex,
  Claude Code and Antigravity, using a verified revision that includes PO; keep existing
  plugins unchanged and verify all required skills after installation.
- Offer official BMad project initialization when its runtime is missing, with
  module questions, explicit unattended flags and a pnet/cancel alternative.

## [0.3.1] — 2026-10-20

- Continue setup when the optional `plex` command belongs to another checkout or
  is an existing foreign file/link; preserve it instead of blocking project setup.

## [0.3.0] — 2026-10-20

- Add `interactive`, `balanced` (default) and `auto` interaction modes with saved
  configuration and setup flags. Route questions through the coordinator and use
  supported BMad headless contracts without bypassing required checks or authority.
- Add a described, per-role BMad workflow catalog in `team.toml` and resolved
  snapshots, including internal PO operation codes, for explicit coordinator dispatch.
- Keep one Markdown source per agent within each team. Compile native Codex,
  Claude Code and Antigravity roles during setup, preserving instructions, model
  settings and tool permissions without maintaining three copies.

## [0.2.0] — 2026-10-18

- Add a one-command GitHub installer with interactive terminal support and a
  shorter quick start in all four README languages.
- Install and update from published releases, including previews. Support pinned
  releases and explicit development builds; refuse updates to dirty or unrelated
  source checkouts.
- Add `plex status` with human-readable and JSON output for version, scope,
  team/profile, native roles, plugin discovery and configuration conflicts.
- Add scoped `plex uninstall` with receipt checks, backups and rollback on caught
  failures. Preserve edited or foreign files and instruction blocks still used by
  another client. Shared plugins and the source checkout remain installed.
- Publish portable regression tests and gate releases on Linux/macOS CI with
  Python 3.11 and 3.14. Isolate BMad preflight checks from locally installed clients
  and normalize test fixture paths for macOS.

## [0.1.0] — 2026-10-18

First public preview.

- Provide reusable `plex` and `plex-setup` skills for explicitly invoked agent
  coordination and team configuration.
- Support OpenAI Codex, Anthropic Claude Code and Google Antigravity through
  native plugin packages and agent definitions.
- Add one interactive installer with multi-client selection, project or user
  scope, configuration checks and managed instruction blocks that preserve user
  content.
- Include `pnet` and `bmad` teams with coordinator instructions, role contracts
  and team-specific model profiles under `teams/`. Keep roles separate from model
  choices and use shared Basic, Plus, Pro and Pro+ tiers across clients.
- Integrate existing BMad personas and workflows through dedicated roles. BMad
  skills and project runtime must be installed separately.
- Bound delegated work by ownership, scope and acceptance criteria; reuse completed
  checks and relay BMad user decisions with the context needed to resume.
- Publish English documentation with Russian, German and Simplified Chinese
  translations, plus consolidated benchmark methodology, measurements and
  qualitative findings with their limitations.
- Release under the MIT license with third-party attribution notices.

[0.4.0]: https://github.com/pnetcloud/plex-ai/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/pnetcloud/plex-ai/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/pnetcloud/plex-ai/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pnetcloud/plex-ai/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pnetcloud/plex-ai/releases/tag/v0.1.0
