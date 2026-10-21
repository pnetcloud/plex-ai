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

The check proves configuration consistency. Before dispatch, separately verify
that the session exposes the selected native role. On mismatch, follow the
skill's delegation rules; do not claim actual routing from installed files.

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
