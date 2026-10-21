# Agent role contracts

[English](role-contracts.md) · [Русский](translations/ru/role-contracts.md) · [Deutsch](translations/de/role-contracts.md) · [简体中文](translations/zh-CN/role-contracts.md)

Teams define membership and skill bindings; profiles select models; team-owned Markdown sources
supply bounded execution instructions. Keep these responsibilities separate.
The root contract is `teams/<team>/coordinator.md`, not another subagent role.


Each source is `teams/<team>/agents/<role>.md`: TOML metadata between `+++`
delimiters followed by the Markdown instructions. Teams remain independent, even
for roles with the same name. Models stay in profiles; skill bindings stay in
`team.toml`.

```markdown
+++
name = "plex-dev"
description = "Implement the assigned change."
access = "workspace-write"
web = true
delegation = false
+++

Own the assigned implementation.
```

`access` is `read-only` or `workspace-write`; `web` and `delegation` are explicit
booleans. The resolver maps these to existing native sandbox/tool settings;
read-only roles cannot enable delegation. Client capabilities still differ:
Codex uses its sandbox setting, Claude read-only roles use tool allowlists, and
Antigravity uses explicit tool lists. Host permissions and handoff authority still
apply. Edit the team source, then refresh installation; do not edit generated roles.

Claude roles with `delegation = false` also deny the native `Agent` tool through `disallowedTools`, including roles with write access.

## Authoring format

Start with a short purpose and a description of when to select the role. Then use:

| Section | Required content |
|---|---|
| Working mode | Ordered actions, inputs and missing-input handling |
| Focus on | Concerns specific to this assignment |
| Quality checks | Evidence needed before claiming completion |
| Return | Paths, results, unresolved findings and decisions |
| Boundaries | Write scope, delegation authority and stop conditions |

Use actionable steps, concise rules and the same semantics across all three hosts.
Avoid generic second coordinators, arbitrary finding quotas and mandatory stages
for optional roles. Each role has one source in its own team; client renderers produce the native formats.

## Task intake and routing

Every new Plex task starts with a short route: outcome, needed roles, execution
order and completion check. The root coordinates; it delegates substantial
planning and implementation to the owning roles. The skill's
[task flows](../skills/plex/references/task-flows.md) define four routes:

| Task | Route |
|---|---|
| Bounded change with clear goal and acceptance | dev → required verification → coordinator |
| Substantial new work with missing decisions | needed PM/PO/UX/architect assignments → dev → verification → coordinator |
| Unexplained failure | bounded investigation → fix → verification → coordinator |
| Review request | reviewer → coordinator |

Only the selected team's roles apply: pnet PM also owns technical planning;
BMad separates PM, PO, UX and architect. Reuse accepted plans, skip resolved
questions and consult the relevant specialist again when scope or assumptions
change. Flow selection adds no user approval gate; installed workflow checks
and analyst authorization still apply. A small mechanical task can stay local.

## Responsibilities

| Role | Outcome |
|---|---|
| pm | Scope, acceptance and a bounded implementation contract; BMad PM owns PRD work |
| explorer | Read-only map of relevant project code and checks |
| researcher | External primary-source evidence and uncertainty |
| analyst | Bounded domain research; BMad use requires direct request or approval |
| po | BMad specifications, tickets, tracking and change planning |
| ux | Implementable user flows, states and design constraints |
| architect | Technical boundaries, invariants and decisions |
| dev | Implementation and relevant checks; selected BMad execution workflow |
| reviewer | Independent findings with location, trigger, impact and evidence |
| qa | Independent behavior verification and tests within assigned scope |

Only the selected team's roles are available. One writer owns each changed file.
Returns distinguish completed checks, assumptions, harness failures and remaining gaps.
Reuse valid evidence; rerun affected checks after changes. Additional full review needs
new risk, a material change or an explicit request.

## BMad startup

- Persona roles: execute entry activation, then dispatch the selected operation.
- Reviewer: activate the review workflow directly.
- Workflow leaves: follow the supplied recipe; do not restart the parent workflow.
- Startup and final return cite the resolved skill path, activation evidence,
  selected workflow/operation and reached step. A greeting or role name is insufficient.
- The coordinator reports requested activation as pending until evidence is available.
- Bounded changes go to Build without a mandatory external planning chain. Build
  retains its own investigation, implementation plan, review and fixes.

## BMad contracts

Activate existing skills instead of copying personas or assuming a version's menus.
Preserve the selected rendered route, required review cycles and genuine user gates.
An applicable early exit skips later checkpoints in that step; verify its condition
and target before escalating. Correct a false gate in the same assignment without
inventing approval. A completed spec alone is not a reason to stop for permission.

Nested delegation requires authority and available capacity. Preserve leaf prompts
and context contracts; do not dispatch a leaf review to a wrapper that starts
another complete workflow. Report actual nested routing and unavailable capabilities.
