---
name: plex-setup
description: List teams and model profiles, check settings, set up, refresh or switch Plex project subagents in Codex, Claude Code or Antigravity.
---

# Plex Setup

Configure the user's explicit project and host; do not install packages, initialize
Git, modify credentials or change global agent configuration. Read applicable project
instructions first. Use the plugin root two directories above this skill folder.

## One project configuration

Teams are `presets/*.toml` (roles, process, skill bindings, default concurrency).
Basic / Plus / Pro / Pro+ IDs are `<vendor>-<tier>` (for example `openai-plus`).
Only current vendor/tier IDs are supported; model-named aliases were removed.
Model profiles are `[profiles.<tier>]` blocks in `model-profiles/<vendor>.toml`,
with one file-level `host` (model/reasoning defaults and role
exceptions). Neither can include another file. List both collections for “show
presets”, with their actual settings and host support; listing is read-only:

```sh
python3 <skill-directory>/scripts/resolve_config.py list
```

The only editable project source is `.plex/preset.toml`. New setup starts with:

```toml
team = "default"
model_profile = "inherit"
```

Use the user's requested team/profile instead when specified. Optional project
`max_agents`, `[codex]`, `[codex.<role>]`, `[claude]`, `[claude.<role>]`,
`[antigravity]`, and `[antigravity.<role>]` are personal
overrides. During interactive setup ask once for the shared positive-integer
concurrency limit, suggesting the saved value or team default. Save it as root
`max_agents`; do not add per-role or per-model-profile concurrency settings. This
limits Plex assignments, subject to native host limits.
Do not choose models for the user. A team switch changes only `team`;
a profile switch changes only `model_profile`. Preserve overrides and the other
selection. Known role overrides outside the current team remain stored but inactive;
show them explicitly. Unknown roles are errors. Reset overrides only on request.
An ordinary refresh preserves the source but resolves the currently installed team
and profile definitions again, showing any changes before applying them.

Legacy full presets with `process`, `roles`, `[skills]` and host overrides still
work without `team`. Do not silently migrate them. On an explicit switch to a named
team, show replacement of those three team fields by `team`; preserve concurrency
and model overrides. A custom TOML file must follow one of these same formats.

## Resolve, check and apply deterministically

Use Python 3.11+ and this skill's `scripts/resolve_config.py` rather than merging
settings, rendering files or computing SHA-256 receipts by hand:

```sh
# Read-only resolution of a preset.toml (legacy positional or explicit subcommand)
python3 <skill-directory>/scripts/resolve_config.py <project>/.plex/preset.toml

# Read-only status check of .plex/preset.toml, .plex/resolved.json, .plex/applied.json and native role files
python3 <skill-directory>/scripts/resolve_config.py check <project> [--host codex|claude|antigravity]

# Preview rendered native role files in memory without writing
python3 <skill-directory>/scripts/resolve_config.py render <project>/.plex/preset.toml --host codex|claude|antigravity

# Apply setup, refresh or switch for a specific host with preflight, backups and receipt verification
python3 <skill-directory>/scripts/resolve_config.py apply <project> --host codex|claude|antigravity [--team <name>] [--model-profile <name>] [--max-agents <n>] [--reset-overrides]
```

Do not merge settings by hand or install dependencies if Python is unavailable.
The resolver rejects invalid fields, names, roles, bindings and reasoning values.
Precedence per field: profile defaults → profile role → project host → project role.
Its `hosts.<host>.<role>` entries are final values; omitted Codex fields inherit.
Claude profiles explicitly use Claude models; Google profiles explicitly use
Antigravity model tiers (`inherit`, `flash_lite`, `flash`, `pro`). Project `reasoning`
maps to native Claude and Antigravity `effort`; validate it against the host's
supported levels and actual model.

Show the exact target, selections, effective per-role model/reasoning and changes.
A setup/refresh/switch request authorizes bounded writes without a second
confirmation; status requests authorize none (`check` and `resolve` are strictly
read-only). For status, compare freshly resolved desired settings with the saved
snapshot, host receipts and actual native files.

In BMad mode (`team = "bmad"` or `process = "bmad"`), resolve every selected role's
`skills` entries from the host's active inventory and verify its project runtime
(for example, `uv run _bmad/scripts/resolve_config.py --project-root <project>`)
before running `apply`. Report missing or ambiguous skills and runtime prerequisites;
do not install BMad or fall back to plain automatically. Required bindings come from
the packaged BMad preset and cannot be silently removed by a custom preset. Consult
each installed skill's actual prerequisites rather than treating `_bmad` directory
presence as readiness.

An explicit request for build review without a finding quota uses the optional
[BMad review customization](references/bmad-review.md). This is a separate project
policy change, not part of ordinary setup/refresh; verify the installed schema,
preserve existing overrides and inspect the rendered result.

## Native roles & receipt lifecycle

For Codex use `assets/codex/*.toml`; for Claude Code use `assets/claude/*.md`;
for Antigravity use `assets/antigravity/*.md`.
Install only selected roles, named `plex-<role>`, into the explicit project's
`.codex/agents/`, `.claude/agents/`, or `.agents/agents/`. Do not copy skills or
overwrite `AGENTS.md`, `CLAUDE.md`, sandbox settings or the complete Codex config.
Verify native role support in the installed host version; unsupported discovery must
be reported.
For BMad, `resolve_config.py` selects `assets/bmad/<host>/<role>` first, falling back
to the ordinary host assets only where no BMad override exists. These wrappers load
installed BMad skills; do not copy persona text or replace BMad's workflows. Each
wrapper retains the mandatory binding for that role when model overrides and any
extra legacy `skills` bindings are rendered.

`resolve_config.py` renders only final settings:
- In Codex it maps `model` to `model` and `reasoning` to `model_reasoning_effort` in
  role TOML. Omitted fields remain absent, including when clearing a previous override.
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
