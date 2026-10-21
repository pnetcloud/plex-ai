# Development

[English](development.md) · [Русский](translations/ru/development.md) · [Deutsch](translations/de/development.md) · [简体中文](translations/zh-CN/development.md)

## Source map

| Path | Responsibility |
|---|---|
| `install.sh` | GitHub download/update entrypoint |
| `setup.sh`, `setup.py` | Checkout installer and optional `plex` shortcut |
| `skills/plex/` | Explicit coordination entry and configuration preflight |
| `skills/plex-setup/` | Setup skill, resolver and managed instruction template |
| `teams/<team>/` | Team definition, root contract, native roles and profiles |
| `plugins/<host>/` | Native distribution manifest templates |
| `.build/plugins/<host>/` | Generated, self-contained client packages |
| `tests/` | Configuration, packaging and isolated installation checks |
| `docs/` | Maintained English documentation and translations |
| `_bmad/custom/` | Development-only BMad customization |

Read product, architecture and configuration documentation before behavioral changes;
read role contracts before editing prompts or team membership. Preserve unrelated
working-tree changes. Do not commit or publish without a request.

## Verification

Portable tests are included in `tests/`. CI runs Python 3.11/3.14 on Linux/macOS,
and release publication requires those jobs to pass. Native-client checks skip when
the corresponding CLI is unavailable; model runs and private benchmark data stay separate.
Run from the repository root:

```sh
uv run --with pyyaml --with questionary==2.1.1 python -m unittest discover -s tests -v
```

Tests cover resolution, scopes, managed blocks, overrides, conflict detection,
rollback, native rendering, packaging and disposable installation where the host
CLI is available. They make no model calls. Configuration checks do not establish
live routing, quality, latency or savings; use the [evaluation protocol](../EVALUATION.md).
Measured summaries belong in [testing](testing.md), with raw evidence kept separately.

### CI coverage

| Environment | Checks |
|---|---|
| Ubuntu and macOS, Python 3.11/3.14 | Full test suite, shell syntax, local Markdown link targets and package contracts |
| Docker, Python 3.11 slim | Project/user install, refresh, configuration check and uninstall for all three clients; preserve personal instructions and unrelated agents |

The Docker check uses bare Python without uv, questionary or client CLIs. It runs
without network access as an unprivileged user, with a read-only checkout. It
checks `--roles-only` configuration, not native plugin installation or BMad setup.
These jobs do not establish native Windows support or live model behavior.

The exact Docker command is in the [CI workflow](../.github/workflows/ci.yml).
Release publication requires every job in that workflow to pass.

## BMad for repository development

Install the intended official BMad skills/plugins using the host manager, then use
the installed Toolbox `bmad` setup flow from this repository. It generates `_bmad/`;
shared customization points to `docs/` and local `_bmad-output/` folders. Do not copy
runtime from vendor checkouts or invent a second bootstrap procedure.

When that runtime is present, verify its configuration with:

```sh
uv run _bmad/scripts/resolve_config.py --project-root .
```

Resolve the actual active skill identity when global and plugin copies coexist.
Do not remove or update global skills as a side effect of project setup.

## Packaging and documentation

Public directories and file-type masks in `.gitignore` define the export; development runtime, machine paths,
registries and raw experiments do not belong in client packages. Native managers
install `.build/plugins/<host>`, not the manifest template alone. Keep registered
local sources available. Installer changes reuse the existing resolver/application path.

English pages live at `docs/`; `translations/ru`, `translations/de` and
`translations/zh-CN` mirror their names and template subdirectory. Update all versions
and navigation together. Keep benchmark numbers identical across languages, label
qualitative assessments, and remove obsolete research/migration notes from current guides.

The root `README.md` is the English project overview. Translated overviews live
in `docs/translations/<language>/README.md`; their guide indexes are `index.md`.
Installation instructions live alongside the other guides in `docs/`.
