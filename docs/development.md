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

The test suite is maintained in the development checkout and is not included in
the public preview. When `tests/` is available, run from the repository root:

```sh
uv run --with pyyaml --with questionary==2.1.1 python -m unittest discover -s tests -v
```

Tests cover resolution, scopes, managed blocks, overrides, conflict detection,
rollback, native rendering, packaging and disposable installation where the host
CLI is available. They make no model calls. Configuration checks do not establish
live routing, quality, latency or savings; use the [evaluation protocol](../EVALUATION.md).
Measured summaries belong in [testing](testing.md), with raw evidence kept separately.

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
