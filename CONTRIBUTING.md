# Contributing to Plex

## Before changing files

1. Read [AGENTS.md](AGENTS.md) and the documentation it selects for your change.
2. Keep the change bounded; preserve unrelated work and manual configuration.
3. Use the existing resolver and native renderers. Keep models in profiles and workflows in the team catalog.

## Write role instructions

Use the same structure for coordinators and subagents:

- Short purpose and selection criteria.
- **Skill activation**, when needed: prerequisites and instructions to load.
- **Working mode:** ordered actions and handoffs.
- **Focus on:** role-specific concerns.
- **Quality checks:** completion evidence and failure handling.
- **Return:** outputs, results and unresolved issues.
- **Boundaries:** authority, exclusions and stop conditions.

Write direct rules, numbered steps and concise tables. Avoid filler, repeated rules,
unsupported tools and implicit permissions. Preserve behavior when shortening.

The authoritative format and source layout are in [role contracts](docs/role-contracts.md).
Coordinators remain Markdown instructions loaded by Plex; they are not additional native subagents.

## Verify and submit

- Run the relevant checks from [development](docs/development.md#verification).
- Check links, native rendering and package exports affected by the change.
- Update English documentation and matching translations when behavior changes.
- Describe the problem, resulting behavior, verification and remaining limits in the PR.
- Do not claim live model routing or quality from configuration/package tests.
- Exclude secrets, machine configuration, private registries and raw session evidence.

Contributions use the repository's [MIT license](LICENSE).
