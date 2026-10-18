---
name: plex-setup
description: List, check, configure or refresh Plex teams and model profiles for Codex, Claude Code or Antigravity, at project or user scope.
---

# Plex setup

Configure the team; this does not activate the Plex coordinator.
Read applicable project instructions. Use Python 3.11+ and the resolver below,
from this installed package. Do not merge settings or render native roles by hand.
Do not install packages, initialize Git or change credentials and host permissions.

## 1. Identify the request

Use the current host and working project unless the user specifies another target.
Project scope is recommended and is the default for setup. Use user/global scope
only when explicitly selected; it applies to that host's user profile.

- Listing and status requests are read-only.
- Setup, refresh and switch requests authorize the requested configuration changes.
- Preserve the saved team, profiles, concurrency and model overrides unless asked to change them.
- A project can use several clients with one shared `model_profile`: `inherit`,
  `basic`, `plus`, `pro` or `pro-plus`. Each tier uses the team's corresponding vendor
  settings. The installer supports checkboxes or repeated `--client`. When changing
  a shared profile through the resolver, refresh every configured client's receipt;
  the installer does this automatically. Do not silently migrate vendor-specific IDs.
- For new setup, use `team = "pnet"` and `model_profile = "inherit"` unless specified.
  Offer the team concurrency default during interactive setup; do not choose models for the user.

## 2. Inspect and preview

`<plugin-root>` is two directories above this skill folder. The examples below use
Codex; replace `codex` with `claude` or `antigravity` for the selected host.

```sh
python3 <plugin-root>/skills/plex-setup/scripts/resolve_config.py list
python3 <plugin-root>/skills/plex-setup/scripts/resolve_config.py check <project> --host codex --scope auto
```

For status, `auto` selects project configuration first, otherwise user defaults.
For an explicit setup or refresh, check the selected `project` or `user` scope;
never use a global fallback to bypass stale or conflicting project configuration.

Present common tiers by default; vendor-specific recipes are a compatibility path.
Show the target, scope, team, profile, effective role settings and changes before
applying. The editable source is `<root>/.plex/preset.toml`; inspect the selected
team and its own profiles under `<plugin-root>/teams/<team>/`.
Use `resolve <preset-file>` and `render <preset-file> --host codex` for read-only
candidate previews (`render` also accepts `--scope user`).
For custom overrides, scope paths, legacy presets or recovery, read the relevant
section of [configuration reference](references/configuration.md).

`pnet` needs no BMad installation. For `bmad`, resolve the selected roles' required
skills from the host's active inventory. Project-scoped setup also requires a
working BMad runtime in that project; use its installed configuration resolver to
verify it before applying. User-scoped role registration does not require a runtime
in the user's home; verify each working project before BMad execution.
Report missing or ambiguous prerequisites; do not install BMad or silently change teams.

## 3. Apply and verify

For a new setup, the minimal application is:

```sh
python3 <plugin-root>/skills/plex-setup/scripts/resolve_config.py apply <project> --host codex --scope project --instructions
python3 <plugin-root>/skills/plex-setup/scripts/resolve_config.py check <project> --host codex --scope project
```

Use `--scope user` for explicitly requested global setup. Add `--team`,
`--model-profile` or `--max-agents` only for requested changes. A refresh without
those flags preserves saved settings and uses the current package definitions.
Reset overrides only on explicit request with `--reset-overrides`.

`--instructions` manages only the Plex block inside the native instruction file,
alongside role installation. Preview its target and
[AGENTS.md.template](assets/AGENTS.md.template). Preserve everything outside the
markers. If instruction integration is declined, omit the flag; retain any existing
managed block and report if it needs a refresh.

The resolver handles conflicts, backups, retired roles, receipts and rollback.
Stop on conflicts or unsupported model routing; never force-overwrite manual edits
or substitute another model. Report other hosts needing refresh and inactive overrides.
Require overall and selected-host `in_sync` after applying. Report installed roles,
remaining issues and any required host reload. File checks do not prove live model routing.

BMad's optional [review policy](../../teams/bmad/review-policy.md) is a separate,
explicitly requested change; ordinary setup does not apply it.
