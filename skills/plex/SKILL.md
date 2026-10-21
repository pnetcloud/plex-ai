---
name: plex
description: Coordinate coding agents when the user invokes Plex or explicitly requests coordinated multi-agent work. Select roles, delegate bounded tasks and verify results.
---

# Plex

## Activation

- Start only on explicit Plex invocation or a request for coordinated multi-agent work.
- Task size, complexity and file count do not activate Plex.
- Otherwise work normally; do not load the coordinator.

## Roles and delegation

- Root coordinates through active-team subagents: intake, routing, handoffs, integration and final checks.
- Use native subagent calls for substantive task work; do not execute those assignments in root when a matching subagent is available.
- Keep brief intake, integration, final checks and small mechanical actions local.
- Keep the root's session model and permissions; do not spawn another coordinator.
- Follow project instructions and host permissions.

Select the checked native `plex-<role>` for each Plex-owned assignment:

| Client | Role selection |
|---|---|
| Codex | `agent_type = "plex-<role>"` when exposed |
| Claude Code | Agent tool: `subagent_type = "plex-<role>"` |
| Other hosts | Use the exposed native role selector |

- Preserve configured model/effort unless the user overrides them.
- For Plex-owned assignments, allow only exact `plex-<role>` identities listed in the checked `.plex/resolved.json` `roles`. Ignore all other installed, built-in or stale agents, even if their names or descriptions fit. A `plex-` prefix alone is insufficient. This applies to delegated Plex-owned assignments too; workflow-owned leaves keep their explicit workflow contract.
- Verify the role is available in this session. Installed files do not prove routing.
- Missing role or unsupported user override: report the mismatch; continue independent authorized work locally.
- Do not substitute a generic agent, invent a fallback or change setup.

## Assignment labels

| Where | Format |
|---|---|
| Task name, where supported | `plex_<role>_<short_task>` |
| Handoff, progress and final return | `[plex:<role>:<short_task>]` |

- Use a role from the checked team and a concise task label.
- Include role and current task in every handoff. Require executor labels in progress/final returns; label coordinator updates too.
- A task label or runner nickname does not select or identify a native role.
- Reuse an agent's identity with a new current-task label. Do not spawn another just to rename it.
- Claude: put the task label in `description` and the handoff; omit `name`. With Agent Teams enabled, `name` can launch a teammate instead of a subagent.
- Workflow-owned children retain the workflow's launch recipe and context contract.

## Execution

1. **Check setup.** Follow [preflight](references/preflight.md) before first delegation. Use the checked roles, model settings and concurrency limit. Setup changes require authorization.
2. **Load the coordinator.** Read `teams/<team>/coordinator.md` from the verified package. Read [interaction policy](references/interaction.md); apply its effective mode.
3. **Select a flow.** Read [task flows](references/task-flows.md). State the outcome, roles, order and completion check. Follow that route; do not run every role by default.
4. **Execute and integrate.** Delegate ready assignments with explicit ownership. Collect results and verify the outcome.

Read each instruction document separately from other skills and configuration dumps.
Recover truncated sections before acting on them.

## Continuation

- Keep a compact checkpoint: role, current task, user overrides, verified package paths, write ownership, evidence and next acceptance gate.
- Reuse verified facts and the selected flow.
- After a follow-up or context compaction, resume as coordinator and delegate remaining substantive assignments.
- Reconsider routing when scope, evidence or technical assumptions change.
- Flow selection adds no user approval gate.
