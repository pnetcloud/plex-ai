# Plex configuration reference

Read the relevant section for custom settings, legacy formats or recovery.

## Configuration scope

Project state lives in `<project>/.plex/`. User state lives in the host's own home:
`$CODEX_HOME/.plex/` (default `~/.codex`), `~/.claude/.plex/` (respecting
`CLAUDE_CONFIG_DIR`), or `~/.gemini/.plex/`. Each host's user state is independent.
`check --host <host> --scope auto` returns the effective `root` and `scope`.
Existing project state takes precedence, including stale/conflicting state; do not
silently bypass it. A global setup never removes project overrides. Scope switches
are not migrations or uninstall requests. Detailed role instructions stay in team templates.

The editable block template is `../assets/AGENTS.md.template`; keep both markers
and all template content inside them.

Ordinary setup may add/update a short `<!-- plex:managed:start -->` / `<!-- plex:managed:end -->`
block in the selected native instruction file using `apply --instructions`. Preview
the target and block. Preserve all bytes outside it; malformed or manually changed
managed blocks require resolution. Existing Codex overrides/fallbacks are respected;
do not create an override to mask user instructions or change fallback configuration.

Teams are `<plugin-root>/teams/<team>/team.toml` (roles, process, skill bindings, default concurrency).
The ordinary profile IDs are `inherit`, `basic`, `plus`, `pro` and `pro-plus`.
Vendor-prefixed IDs such as `openai-plus` remain available for compatibility.
The default standalone team is `pnet`; old `default` selections migrate on refresh.
Model-named aliases were removed; use a shared tier for multi-client setup.
Model profiles are `[profiles.<tier>]` blocks in `<plugin-root>/teams/<team>/profiles/<vendor>.toml`,
with one file-level `host` (model/reasoning defaults and role
exceptions). Profile IDs are local to the selected team; the catalog groups them
by team. Never borrow a profile from another team. If the preserved profile is
missing after a team switch, ask for a supported selection; unattended setup must
specify it explicitly. Team and profile files cannot include other files. List both collections for “show
presets”, with their actual settings and host support; listing is read-only:

```sh
python3 <skill-directory>/scripts/resolve_config.py list
```

Shared tiers (`basic`, `plus`, `pro`, `pro-plus`) combine the selected team's
OpenAI, Anthropic and Google definitions for all clients under one `model_profile`.
Vendor-specific IDs remain compatible with earlier configuration.

The editable source is `<root>/.plex/preset.toml` for the selected scope. New setup starts with:

```toml
team = "pnet"
model_profile = "inherit"
```

Refresh removes retired token-budget fields from older presets.

Use the user's requested team/profile instead when specified. Optional project
`interaction` (`interactive`, `balanced`, `auto`; default `balanced`),
`max_agents`, `[codex]`, `[codex.<role>]`, `[claude]`, `[claude.<role>]`,
`[antigravity]`, and `[antigravity.<role>]` are personal
overrides. During interactive setup ask once for the shared positive-integer
concurrency limit, suggesting the saved value or team default. Save it as root
`max_agents`; do not add per-role or per-model-profile concurrency settings. This
limits Plex assignments, subject to native host limits.
Do not choose models for the user. A team switch changes only `team`;
a profile switch changes the shared `model_profile`. Refresh all configured clients
after a shared-profile switch; their role/model settings stay derived from the same tier. Preserve overrides and the other
selection. Known role overrides outside the current team remain stored but inactive;
show them explicitly. Unknown roles are errors. Reset overrides only on request.
An ordinary refresh preserves the source but resolves the currently installed team
and profile definitions again, showing any changes before applying them.

Legacy full presets with `process`, `roles`, `[skills]` and host overrides still
work without `team`. Do not silently migrate them. On an explicit switch to a named
team, show replacement of those three team fields by `team`; preserve concurrency
and model overrides. A custom TOML file must follow one of these same formats.

## Resolution and model support

Precedence per field is profile defaults → profile role → scope host overrides →
scope role overrides. The resolved `hosts.<host>.<role>` entries are final values.
Omitted Codex fields inherit; Claude and Antigravity use native `model: inherit`.
Profiles belong to their team; a missing profile requires an explicit replacement.

The resolver validates settings and native output, not provider availability.
Antigravity rendering accepts only its supported tier aliases; catalogued exact
model IDs without native routing support fail rather than silently substituting.
Report unsupported configuration without claiming live model execution was verified.

Team files may define `[[workflows.<role>]]` entries with `skill`, `description`
and an optional persona-internal `operation` menu code. The resolver validates
and copies this assignment catalog to the resolved snapshot; it is not another
entry-skill binding. Do not load all catalog skills or install them during setup.
Workflow instructions and availability belong to the installed BMad version.

The checkout installer initializes missing BMad runtime after an explicit menu choice
or `--init-bmad`, delegating to the official installed setup. When the hub is absent,
it offers user-wide installation of the team's selected official skills from a pinned
revision through Skills CLI (`--install-bmad` authorizes this unattended). Selected
user skill files may be replaced; existing plugins are not changed. Do not copy skills
into the project or emulate BMad materialization. `--bmad-skill PATH` selects an
installed hub; `--yes` accepts displayed module defaults.

## Native roles & receipt lifecycle

Read role sources from `<plugin-root>/teams/<team>/agents/<role>.md`: Markdown
with TOML metadata between `+++` delimiters. The resolver compiles Codex TOML or
Claude Code/Antigravity Markdown, mapping access and tool capabilities explicitly.
Each team owns its instructions; no cross-team fallback or shared persona is used.
Team data lives outside this
skill, alongside the plugin's `skills/` directory, including in installed packages.
User-scoped BMad registration does not assume a runtime in the user's home;
verify prerequisites in the actual working project before starting its workflow.
User roles go under `$CODEX_HOME/agents/`, `~/.claude/agents/` (or `CLAUDE_CONFIG_DIR`),
or `~/.gemini/config/agents/`. Project roles go into the explicit project's
`.codex/agents/`, `.claude/agents/`, or `.agents/agents/`. Do not copy skills, replace complete instruction files or change sandbox settings
or the complete Codex config. Instruction integration owns only the marked Plex block.
Verify native role support in the installed host version; unsupported discovery must
be reported.
The resolver uses only the selected team's templates; missing files are errors,
with no fallback to another team. Legacy `plain` settings use the six `pnet`
roles; legacy `bmad` settings use the BMad team. BMad wrappers load
installed BMad skills; do not copy persona text or replace BMad's workflows. Each
wrapper retains the mandatory binding for that role when model overrides and any
extra legacy `skills` bindings are rendered.

`resolve_config.py` renders only final settings:
- In Codex it maps `model` to `model` and `reasoning` to `model_reasoning_effort` in
  role TOML. Omitted fields remain absent, including when clearing a previous override.
  Sandbox, approval settings and MCP servers inherit from the parent session;
  role TOML omits `sandbox_mode` and `approval_policy`. Read-only instructions are
  behavioral boundaries, not a separate Codex sandbox.
- In Claude Code and Antigravity it renders `model` and optional `effort` in YAML
  frontmatter. Project `reasoning` supports `low`, `medium`, `high`, `xhigh`, `max`;
  Antigravity `model` supports `inherit`, `flash_lite`, `flash`, `pro`; actual model
  and host version support must be checked separately.
- The resolver validates syntax, not provider model availability or model-specific
  effort support; verify those through the host before writes.

When `resolve_config.py apply` runs, it enforces the full lifecycle automatically:
1. **Preflight checks:** Validates all destinations, rejects symlinked parent paths or
   files, checks `.plex/applied.json`, detects unmanaged file collisions (`plex-<role>`
   files not in the receipt) and modified or missing previously managed files. Any
   preflight conflict aborts without changing the working configuration.
2. **Backups & role archiving:** Moves deselected roles owned by the selected host's
   receipt and copies replaced `.plex/preset.toml`, `.plex/resolved.json` and role
   files into `.plex/backups/<unique-run>/<host>/`, outside native discovery.
3. **Atomic writes & read-back hashes:** Writes `.codex/agents/plex-<role>.toml`,
   `.claude/agents/plex-<role>.md`, or `.agents/agents/plex-<role>.md`,
   `.plex/preset.toml` and `.plex/resolved.json` (with matching `source_sha256`),
   verifying SHA-256 digests on read-back.
4. **Independent host receipts:** Updates `hosts.<host>` in `.plex/applied.json` while
   preserving other hosts' records and reporting in `other_host` / `other_hosts`
   whether other configured hosts differ from the new desired settings. Never claim
   multiple hosts switched from one host's run.

The installer holds `.plex/.apply.lock`, rechecks managed contents before mutations,
and rolls back its changes on caught write errors. It preserves concurrent edits
instead of overwriting them during rollback and reports remaining recovery paths.
If the process was killed, inspect the lock PID, actual files, receipt and backups
before recovering; never remove a lock held by a live apply. Power loss, process kill
and permanent disk failure are not covered by an all-files atomicity guarantee.

Finish with installed roles, effective model overrides, remaining conflicts and any
required host reload and inactive overrides. A subsequent `resolve_config.py check`
must report `in_sync` with no pending changes. Installing configuration does not
prove that live subagent execution or model routing works.

## Codex role selection

Role application exposes native role metadata through a receipt-owned block in the selected scope's `config.toml`: missing `features.multi_agent_v2.hide_spawn_agent_metadata = false` and `tool_namespace = "agents"`. It preserves personal settings, rejects conflicting values and uses the existing apply/check/backup/rollback/uninstall lifecycle. It does not change models, permissions, concurrency, the selected backend or project trust. Existing matching fields remain user-owned. Use a supported native client, trust the project through Codex, and open a new session. Verify the active spawn schema and actual accepted role separately; setup makes no model calls.
