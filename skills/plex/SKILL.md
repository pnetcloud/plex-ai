---
name: plex
description: Coordinate a team of coding agents when the user explicitly invokes Plex or asks for coordinated multi-agent work. Best suited to complex tasks with useful specialist assignments.
---

# Plex

Activate only when the user invokes this skill or explicitly requests coordinated
multi-agent work. Task size, complexity or the number of files alone does not
activate Plex. Otherwise, handle the task normally without loading a team coordinator.

## Delegation contract

For every Plex-owned assignment, select the checked native `plex-<role>` so its
instructions and model settings apply. On Codex, use that registered name as
`agent_type` when the tool exposes it. A task label does not select a role.
Do not silently substitute a generic agent or infer routing from installed files.
If the current session cannot select the role or honor an explicit user override,
report the mismatch and continue independent authorized work locally; do not
invent a fallback or change setup. Preserve the root's session model.

Where the host supports task names, use `plex_<role>_<short_task>`, with the role
from the checked team and a concise task label. Include role and current task in
every handoff, and ask the executor to use `[plex:<role>:<short_task>]` in its
progress and final return. Use these labels in the coordinator's own updates too.
Runner nicknames are not role identities. When reusing an agent, retain its
thread identity but supply the new current-task label; do not imply its original
name changed or launch another agent solely to rename it. For workflow-owned
children, preserve the workflow's launch recipe and context contract.

On continuation, retain a compact checkpoint: role, current task, explicit user
overrides, verified package paths, write ownership, evidence and next acceptance
gate. Reuse these facts unless inputs change or a concrete gap requires discovery.

## 1. Check the selected team

Before delegating, follow [configuration preflight](references/preflight.md) once.
Use the verified configuration's roles, model settings and concurrency limit.
Missing or conflicting setup requires `plex-setup`; do not install or repair it
without authorization.

## 2. Become the coordinator

Read `teams/<team>/coordinator.md` from this installed package, using the team
identified by preflight. Read [interaction policy](references/interaction.md), select
the effective mode and follow both contracts for assignments, handoffs and verification.
Read each instruction document separately from configuration dumps or other skills.
Truncated output is incomplete: retrieve the missing sections before acting on it.
You remain the current root agent; do not launch a separate coordinator or change
your session model or permissions. Project and host instructions remain applicable.

## 3. Coordinate only useful work

Keep clear, small work local. Delegate bounded assignments with ready inputs and
explicit ownership, integrate the results and verify the outcome. An invoked
coordinator does not require every role or a fixed sequence of agents.
