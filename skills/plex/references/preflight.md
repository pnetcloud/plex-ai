# Plex configuration preflight

Read this only after the user invokes Plex coordination.

Resolve this skill directory's symlinks before deriving `<plugin-root>` (two
directories above the real skill folder). In development mode the project skill
links point into the working checkout; its `teams/` and `skills/` form one package.

## Check the applied configuration once

Run the read-only check before the first delegation:

```sh
python3 <plugin-root>/skills/plex-setup/scripts/resolve_config.py check <project> --host <codex|claude|antigravity> --scope auto
```

Read the JSON result; proceed only when its overall status and the selected host
are `in_sync`. A zero process exit or matching hand-checked hashes is not a substitute.
Use the installed package's checker, with team definitions and model profiles under its package root's `teams/`;
an incomplete copy is a blocker, not permission to search another checkout.
The result's `root` and `scope` identify the configuration: project state takes
precedence; otherwise use user state. Never bypass stale project configuration by
falling back to a global team. Read `<root>/.plex/resolved.json` for
active roles, entry `skills`, optional `workflows` catalog, final
`hosts.<host>.<role>` settings, `interaction` and `max_agents`; do not reassemble
configuration layers. Missing, stale or conflicting configuration requires
`plex-setup`; it does not authorize installation or writes. Repeat the check only
if configuration changes or there is evidence of drift during this task.

## Load the selected team's root coordinator

From the verified snapshot, use its `team` to read
`<plugin-root>/teams/<team>/coordinator.md` before planning or launching delegated work.
Read it from the same installed package as this skill and its checker. Never load
instructions from the target project's similarly named directory or another checkout.
For legacy snapshots with `team = null`, use `pnet` for `process = "plain"` and
`bmad` for `process = "bmad"`. The former team ID `default` means `pnet`.
A missing coordinator document, unknown process or team/process mismatch is a blocker;
do not borrow another team's coordinator. Use the selected package's `team.toml`
to check the process when needed; do not reconstruct effective role/model settings.
