# pNet Plex

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [简体中文](README.zh-CN.md)

**Compose your team. Coordinate the work.**

Plex is an **agent harness for multi-agent orchestration and coordination** in
OpenAI Codex, Anthropic Claude Code and Google Antigravity. Install a reusable team,
choose its model profile, and ask Plex to organize implementation, review and verification.

**[v0.5.4 Preview](https://github.com/pnetcloud/plex-ai/releases/tag/v0.5.4)** — open source, MIT. Ready to try; interfaces may change.

## Quick start

Run from your project directory.

**Standard installation**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

**Development mode — Codex, project-local Plex skills**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --dev --client codex
```

Normal installation opens an interactive menu:

1. Select clients with **Space**, then **Enter** (numbered prompts without uv).
2. Choose the installation scope (**Project** is recommended) and confirm the directory.
3. Choose **pnet** for a standalone team and **Inherit** to use session model settings.
4. Choose **Balanced** interaction for routine work, or select **Interactive** / **Auto**.
5. Review and confirm the installation plan for each client.

Normal installation adds the shared plugin, native team roles and a managed instruction block.
Run the same command again to download updates and reopen setup.

[Installation and all parameters](readme/installation.md).

Already installed for this client and scope? Choose **Update only** to keep settings, or **Reconfigure** to reopen the setup menus.

## Try your first task

Open a **new session** of your coding client in your project.
Reload plugins/agents if the client requires it, then send:

```text
Use Plex to build a responsive focus-session booking page.
Use plain HTML, CSS and JavaScript with name, email and 25/50-minute duration.
Validate input and show a local confirmation without saving or sending data.
Review the changes, run available checks, and report what was verified.
```

Plex selects useful roles, implements the page and coordinates review/checks.
Expect source files, a local preview command and a report of checks and remaining gaps.
Installation alone does not start orchestration; **ask for Plex explicitly**.

Found a problem? [Open an issue](https://github.com/pnetcloud/plex-ai/issues) with your
client/version, team/profile, command or prompt, expected behavior and actual result.
Remove secrets from any attached logs.

## Teams and models

| Team | Use it for |
|---|---|
| **pnet** | General development with PM, explorer, researcher, dev, reviewer and QA; no BMad required |
| **bmad** | BMad skills/workflows with role-specific models; setup offers selected skill installation and project initialization |

Choose **Inherit, Basic, Plus, Pro or Pro+**. One tier applies across selected clients;
per-role overrides are available. Plex only manages its marked instruction block,
preserving your surrounding project instructions.

To change settings or configure another project, run this **in the terminal** from that project:

```sh
~/.local/bin/plex
```

This command opens setup; the Plex request inside your client starts coordination.
Team/profile overrides are described in [configuration](docs/configuration.md).

## Check, update or remove

```sh
plex status
plex update
plex uninstall --dry-run
```

Run `plex uninstall` to confirm removal. If `plex` is unavailable, use
`~/.local/share/plex-ai/setup.sh` instead (including fresh dev installations).
Installation and updates select published releases, including previews.

## Develop Plex locally

From the working Plex checkout, connect a Codex test project:

```sh
./setup.sh --dev --client codex --project /path/to/test-project
```

Live skill links use this checkout; the managed instruction block requires the project Plex skills. The shared plugin is disabled only in that project. Rerun with `--no-dev` to return to normal setup. Reopen Codex after changes.

[Installation and all parameters](readme/installation.md).

## Learn more

- [Documentation](docs/README.md) — setup and usage details.
- [About Plex](docs/product.md) — purpose and working principles.
- [Compatibility](docs/host-compatibility.md) — Codex and selected Antigravity live trials; native Claude Code live execution remains unverified.
- [Testing and efficiency](docs/testing.md) — methodology, measured token/cost results and subjective quality observations.
- [Architecture](docs/architecture.md) — how configuration and coordination fit together.

## License

[MIT](LICENSE). Agent instructions adapt [Awesome Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents);
see [third-party notices](THIRD_PARTY_NOTICES.md).
