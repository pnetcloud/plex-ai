# Developing pNet Plex

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow.

Read `docs/product.md` and `docs/development.md` before substantive work. For
configuration changes also read `docs/configuration.md` and `docs/architecture.md`.
These documents describe the project; keep implementation claims backed by files.
For role prompts, catalogs or preset changes, also read `docs/role-contracts.md`.

- `skills/plex/` owns coordination entry and preflight; `teams/<team>/coordinator.md`
  owns the root's team-specific contract. `skills/plex-setup/` owns project setup.
- Teams in `teams/<team>/team.toml` contain no model choices. Model profiles live in
  `teams/<team>/profiles/`. Change resolution in the existing Python resolver, not in
  duplicated instructions or a second configuration engine.
- Preserve native Codex/Claude packaging and standalone operation. BMad integration
  uses installed skills and their actual runtime; do not copy their personas.
- Do not put machine paths, a project registry or vendor research history in the
  reusable package. Do not change global agent configuration during project setup.
- Keep manual files and unrelated work intact. No commit or publishing unless asked.
- Run the checks in `docs/development.md` for affected behavior. Package checks do
  not verify live model routing, setup execution or comparative efficiency.

When using BMad here, this directory is the project root. Project knowledge is
`docs/`; planning and implementation artifacts go under `_bmad-output/` as configured
in `_bmad/custom/config.toml`. Read the docs above before a BMad assignment; do not
infer project context from an empty artifact folder. Runtime bootstrap instructions
are in `docs/development.md`. Do not invoke a BMad workflow merely to edit these docs.

## Instruction style

- Write concise, explicit, structured instructions. No filler or repeated rules.
- Use the agent role format: purpose, working mode, focus, checks, return, boundaries.
- Use numbered steps for order, bullets for rules and tables for choices.
- State triggers, owner, inputs, action, completion evidence and blockers.
- Keep necessary explanations in plain language; remove vague advice and decorative prose.
- Preserve behavior when shortening. Distinguish configured, requested and observed execution.
