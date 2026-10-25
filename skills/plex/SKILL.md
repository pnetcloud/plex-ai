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

- Root coordinates through active-team subagents: request collection, routing, handoffs, integration and final checks.
- Use native subagent calls for substantive task work. A missing or rejected required role blocks its assignment; root must not take over its planning or implementation.
- Keep deferred requests in the coordinator's [session state](references/coordinator-state.md). Related followups amend existing work; obtain `plex-pm` intake before routing or executing unrelated work. Root does not judge complexity or implementation readiness.
- Keep request collection, integration, final checks and small mechanical actions local.
- Keep the root's session model and permissions; do not spawn another coordinator.
- Follow project instructions and host permissions.

Select the checked native `plex-<role>` for each Plex-owned assignment:

| Client | Role selection |
|---|---|
| Codex | `agent_type = "plex-<role>"` when exposed |
| Claude Code | Agent tool: `subagent_type = "plex-<role>"` |
| Other hosts | Use the exposed native role selector |

- Preserve configured model/effort unless the user overrides them.
- Route assigned CI, release and deployment work through the checked `plex-devops` after PM intake; use the operational route in `references/task-flows.md`. Release authority does not imply deployment authority.
- For Plex-owned assignments, allow only exact `plex-<role>` identities listed in the checked `.plex/resolved.json` `roles`. Ignore all other installed, built-in or stale agents, even if their names or descriptions fit. A `plex-` prefix alone is insufficient. This applies to delegated Plex-owned assignments too; workflow-owned leaves keep their explicit workflow contract.
- Inspect the actual native role selector as described in preflight. A hidden selector is not a missing role; a missing displayed inventory is not proof of absence. Installed files do not prove routing.
- Missing role or unsupported user override: report the mismatch and block dependent work. Local continuation is limited to intake context, status, integration, final checks and already authorized mechanical actions; do not implement or make the missing specialist's decisions.
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

1. **Check setup.** Follow [preflight](references/preflight.md) before first delegation. Use the checked roles, model settings, concurrency limit. Setup changes require authorization.
2. **Load the coordinator.** Read `teams/<team>/coordinator.md` from the verified package. Read [interaction policy](references/interaction.md); apply its effective mode.
3. **Intake before routing.** Read [task flows](references/task-flows.md) and update the session state. Record unrelated requests without dispatch; for work selected for routing or execution, call `plex-pm` with its constraints and existing task references. Obtain the task contract, required specialists and readiness decision; do not substitute root analysis.
4. **Follow the assessed route.** State roles, order and completion checks from the assessment. Collect required specialist outputs before dev. Do not launch every role by default.
5. **Check assignments.** Follow [assignment contracts](references/assignments.md). PM/PO selects normal, plan or goal execution and 1–5 observable criteria. Validate each executable Plex-owned subagent contract before dispatch; initial intake and workflow-owned leaves are exempt.
6. **Execute and integrate.** Delegate ready assignments with explicit ownership. Native Plan/Goal is optional; keep the assessed approach with available tools when unsupported. Validate Plex-owned responses against the current assignment/revision; route help to the decision owner and verify evidence before acceptance.

Read each instruction document separately from other skills and configuration dumps.
Recover truncated sections before acting on them.

## Continuation

- Keep the [session state](references/coordinator-state.md) current at new requests, substantive transitions, compaction and re-entry: role, outcome, user overrides, write ownership, evidence and next action. Pass workers only their scoped assignment, never a queue-reading duty.
- Reuse verified facts and the selected flow.
- Reuse role handles; pass new decisions, changed evidence and remaining questions rather than full transcripts. Keep conflicting specialist conclusions visible to their decision owner.
- After a follow-up or context compaction, resume as coordinator and delegate remaining substantive assignments.
- Reconsider routing when scope, evidence or technical assumptions change.
- Flow selection adds no user approval gate.
