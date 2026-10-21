# Configuration preflight

Run only after Plex activation, before first delegation. This check is read-only.

## 1. Locate the package

- Resolve the skill directory's symlinks.
- `<plugin-root>` is two directories above the real skill folder.
- In dev mode, the project skill links into the working checkout.
- Use this package's checker and `teams/` definitions. An incomplete package is a blocker; do not borrow another checkout.

## 2. Check configuration

```sh
python3 <plugin-root>/skills/plex-setup/scripts/resolve_config.py check <project> --host <codex|claude|antigravity> --scope auto
```

Proceed only when the JSON reports both:

- Overall `status = "in_sync"`.
- Selected host `status = "in_sync"`.

Exit code zero or manually compared hashes are insufficient.

- `root` and `scope` identify the applied configuration.
- Project configuration takes precedence; otherwise use user configuration.
- Never bypass stale project state with a global fallback.
- Missing, stale or conflicting setup requires `plex-setup`; the check grants no installation or write authority.
- Repeat only after configuration changes or evidence of drift.

## 3. Read the snapshot

Read `<root>/.plex/resolved.json`; do not reconstruct configuration layers.

| Field | Use |
|---|---|
| `team`, `process` | Selected team |
| `roles` | Active roles |
| `skills`, optional `workflows` | Entry skills and assignment catalog |
| `hosts.<host>.<role>` | Effective model/effort |
| `interaction`, `max_agents` | Interaction mode and assignment limit |

Use `roles` as the allowlist for Plex-owned dispatch, not the host's full agent inventory. Other installed agents and inactive `plex-` roles are outside this team.

The check proves configuration consistency, not live readiness. Inspect the actual
native spawn tool schema before dispatch:

| Observation | Action |
|---|---|
| No native spawn tool | Report unavailable delegation; continue independent authorized work |
| No role selector (Codex `agent_type`) | Report hidden/unsupported role selection, not missing installed agents; inspect effective native configuration through setup |
| Role selector exposed, no role inventory | Request the exact checked role once; lack of a displayed inventory is not proof of absence |
| Host rejects the selected role | Record the rejection and report a role/configuration mismatch; do not substitute a generic child |
| Host accepts the selected role | Record accepted dispatch; verify effective model/effort separately when exposed |

For Codex, use `fork_turns = "none"` when that field is exposed and send a
self-contained handoff, including interaction mode and workspace authorization.
Do not invent unsupported parameters. A full-history fork can inherit the root's
role/model instead of the selected profile. Never change config or the root model
inside preflight. A configuration change requires a fresh client session before
claiming its tools have changed.

## 4. Load the coordinator

- Read `<plugin-root>/teams/<team>/coordinator.md` before planning or delegation.
- Use the same installed package as the skill and checker, not the target project's similarly named files.
- Read the coordinator separately; recover truncated sections.
- Check `team.toml` for process consistency when needed; do not rebuild effective role/model settings.
- Missing coordinator, unknown process or team/process mismatch: stop that route. Do not borrow another team's coordinator.

Legacy snapshots:

| Value | Team |
|---|---|
| `team = null`, `process = "plain"` | `pnet` |
| `team = null`, `process = "bmad"` | `bmad` |
| `team = "default"` | `pnet` |
