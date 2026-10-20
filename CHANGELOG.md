# Changelog

Important changes retained in Plex, grouped by release. Both releases below are
previews; interfaces and configuration may change before 1.0.

## Unreleased

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

[0.2.0]: https://github.com/pnetcloud/plex-ai/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pnetcloud/plex-ai/releases/tag/v0.1.0
