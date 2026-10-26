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
booleans; read-only roles cannot enable delegation. Codex roles inherit sandbox,
approval settings and MCP servers from the parent session; generated TOML omits
`sandbox_mode` and `approval_policy`. Read-only boundaries remain behavioral
instructions, not a separate Codex sandbox. Claude read-only roles use tool
allowlists; Antigravity uses explicit tool lists. Host permissions and handoff
authority still apply. Edit the team source, then refresh installation; do not
edit generated roles.

Claude roles with `delegation = false` also deny the native `Agent` tool through `disallowedTools`, including roles with write access.

## Authoring format

The same blocks apply to root coordinators and subagents. Start with a short purpose and selection criteria. Then use:

| Section | Required content |
|---|---|
| Skill activation, when needed | Prerequisites, instructions to load and startup evidence |
| Working mode | Ordered actions, inputs and missing-input handling |
| Focus on | Concerns specific to this assignment |
| Quality checks | Evidence needed before claiming completion |
| Return | Paths, results, unresolved findings and decisions |
| Boundaries | Write scope, delegation authority and stop conditions |

Use actionable steps, concise rules and the same semantics across all three hosts.
Avoid generic second coordinators, arbitrary finding quotas and mandatory stages
for optional roles. Each role has one source in its own team; client renderers produce the native formats.

Coordinators use Markdown headings; their purpose and blocks match the role sources. Keep root-only routing and integration responsibilities explicit. A coordinator is loaded by the Plex skill, not registered as an additional native subagent.

## Mandatory intake

The checkpoint assists continuation; use the full available session context and
accepted requirements. Missing checkpoint details remain applicable until superseded.

New coordinator checkpoints use Markdown; existing JSON remains readable. The
read-only checker can render either format with `--markdown`. Setup automatically
migrates valid canonical JSON checkpoints in the selected root, backs up originals
and removes old files after verification. Conflicts remain intact and are reported;
`plex status` shows the observed memory format. Old-path checks return the migrated
`canonical_path` for the same session. Memory allows
32 KiB of UTF-8 and 16 current decisions; preserve exact references and owner
handles. This storage guard is not a model context or execution budget.

After intake, Dev/DevOps owns routine technical steps within the accepted
assignment. Apply the shared [execution-ownership rule](../skills/plex/references/assignments.md#execution-ownership)
for escalation, alternative tooling and independent work while acceptance waits.

After Plex activation, the coordinator keeps compact [per-session state](../skills/plex/references/coordinator-state.md). Related followups amend their existing outcome; unrelated requests may be recorded as deferred without dispatch. Before routing or executing a new or queued request, the native `plex-pm` role provides a short assessment. Root does not classify complexity or implementation readiness itself. PM returns task class, outcome/non-goals, missing decisions, needed roles/order, the project's task format and reference, a dev contract with checks, and readiness (`ready`, `needs-specialist`, `blocked`).

In the BMad team, this role-local intake does not activate a persona, menu, PRD or Build. Actual BMad assignments still follow their entry contracts. Task/spec authoring uses the project's existing tracker, issue, spec or story conventions; use a supported PO operation or cataloged standalone spec workflow where available. A direct workflow uses its own entry contract without an unrelated persona prerequisite. Do not require `bmad-spec` across all BMad versions or create a parallel task store.

Required technical decisions go to architect in BMad or PM in pnet before dev. A detailed request or small diff does not prove design readiness. Reuse an assessment for covered workflow steps and unchanged continuation; material decisions outside it return to PM. Missing/rejected required roles block their assignments: root may report status and gather bounded context but cannot take over their design or implementation. This adds a specialist-result prerequisite, not another user approval prompt.


## Task intake and routing

Every Plex task selected for routing starts with a short route: outcome, needed roles, execution
order and completion check. The root coordinates; it delegates substantial
planning and implementation to the owning roles. The skill's
[task flows](../skills/plex/references/task-flows.md) define these routes:

| Task | Route |
|---|---|
| Bounded change with clear goal and acceptance | PM intake → dev → required verification → coordinator |
| Substantial new work with missing decisions | PM intake → needed PM/PO/UX/architect assignments → dev → verification → coordinator |
| Unexplained failure | PM intake → bounded investigation → fix → verification → coordinator |
| Review request | PM intake → reviewer → coordinator |
| CI/CD, release or assigned deployment | PM intake → devops → required checks/review → coordinator |

Use the shared [task-routing rules](../skills/plex/references/task-flows.md) to decide when Architect or UX is needed; they are conditional specialists, not default stages.

For an unexplained failure, stop diagnosis once the failing path and cause support
a safe repair. Unknown production identity/effects gate ACK, replay or mutation,
not an isolated fix that fails closed.

Only the selected team's roles apply: pnet PM also owns technical planning;
BMad separates PM, PO, UX and architect. Reuse accepted plans, skip resolved
questions and consult the relevant specialist again when scope or assumptions
change. Flow selection adds no user approval gate; installed workflow checks
and analyst authorization still apply. A small mechanical task can stay local.

For BMad selection, PM reads the full `workflows` map once from the exact snapshot
passed by root and returns the minimal sufficient route, its purpose, eligible role,
entry, sequence and expected canonical output/input. When interactive options are
presented, root dispatches the user's settled choice; otherwise it dispatches PM's
settled route. Root integrates the result and does not substitute its own route.

## Responsibilities

| Role | Outcome |
|---|---|
| pm | First intake, route selection and acceptance; BMad PM owns product requirements, PRDs and assigned standalone spec work |
| explorer | Read-only map of relevant project code and checks |
| researcher | External primary-source evidence and uncertainty |
| analyst | Bounded domain research; BMad use requires direct request or approval |
| po | BMad specification/task workflows, ticket breakdown, tracking and replanning |
| ux | Implementable user flows, states and design constraints |
| architect | Technical boundaries, invariants and decisions |
| dev | Implementation and relevant checks; selected BMad execution workflow |
| reviewer | Independent findings with location, trigger, impact and evidence |
| qa | Independent behavior verification and tests within assigned scope |
| devops | CI/CD, release publication and explicitly assigned deployment/recovery with revision-specific evidence |

DevOps is a native Plex specialist in both teams and uses project release/deployment procedures, without a mandatory BMad persona. PM intake still applies. Release authorization does not imply deployment authorization; preparation, publication, installation and runtime health require separate evidence. Independent review remains with reviewer.

Only the selected team's roles are available. One writer owns each changed file.
Returns distinguish completed checks, assumptions, harness failures and remaining gaps.
Reuse valid evidence; rerun affected checks after changes. Additional full review needs
new risk, a material change or an explicit request.

## BMad startup

- Persona/menu assignments: activate the declared entry persona, then dispatch the selected operation.
- Direct standalone assignments: use the selected workflow's own activation and return contract; do not activate an unrelated persona or menu first.
- Reviewer: activate the review workflow directly. Workflow leaves follow the supplied recipe without restarting the parent.
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

Reuse concrete accepted requirements for implementation. If they are missing, the
selected spec or Build route produces concrete requirements before code; do not
create a PRD, epic, story or duplicate specification by default. In `interactive`,
PM sends materially different route options and a recommendation through root to
the user; `auto` selects without optional route questions. `balanced` keeps its
existing policy. Reuse a settled route and keep workflow gates intact.

Nested delegation requires authority and available capacity. Preserve leaf prompts
and context contracts; do not dispatch a leaf review to a wrapper that starts
another complete workflow. Report actual nested routing and unavailable capabilities.

## Assignments, planning and goals

PM owns framing, technical planning and execution choice in pnet. BMad PM owns intake,
PO refines specifications/tasks, and architect resolves technical decisions. Root
schedules their route and integrates evidence; no extra manager role is installed.

Executable assignments use the [compact contract](../skills/plex/references/assignments.md)
and its read-only validator. Include inputs, ownership/exclusions, accepted dependencies,
readiness and normally three observable criteria (one to five), each with a check.
Reuse the existing issue/spec/story; initial PM intake and workflow-owned leaves are exempt.
Structural validation is not semantic acceptance, sandbox enforcement or dispatch evidence.
The criterion cap applies to the handoff summary; retain all canonical spec/workflow checks.

PM/PO selects `normal`, `plan` or `goal` with a reason. In `auto`, select without another
mode question. Plan resolves decisions before application edits; goal iterates toward
verified criteria within the accepted scope. Native client modes are optional: otherwise
use ordinary planning or bounded criteria-driven work, reporting the actual approach.
Do not switch the user's chat mode, replace an existing goal or promise continuation
that the host cannot provide. Host authority and explicit user choices still apply.

For suitable unattended BMad implementation in `auto`, select installed `bmad-build-auto`:
one rendered workflow iteration with its actual mandatory subagents and terminal status.
Otherwise use an authorized supported Build route. Preserve specification, renderer,
checks and genuine gates; do not append another full planning/review cycle.

Reuse role handles. Send changed evidence, new decisions and the remaining question
instead of the whole transcript. Parallelize independent assessments; wait for accepted
inputs before dependent work. Return conflicting conclusions to their owner without
inventing consensus. Final returns connect each criterion to observed evidence and gaps.

`max_agents` counts concurrently unfinished Plex assignments, not cumulative launches.
Returned/idle work stops consuming that cap; native thread slots may still include idle
handles and must be checked separately before claiming a capacity blocker.

## Validated responses and help

New Plex-owned assignments carry a task label and positive `revision`. The shared
[response contract](../skills/plex/references/assignments.md#response-contract)
checks role, assignment identity, status and criterion evidence before acceptance.
The existing input-check CLI remains compatible; response checking uses
`check_assignment.py --resolved <snapshot> --assignment <current-assignment.json>`
with a response JSON object on stdin. Both checks are read-only.

- `progress`: a new observation/result and next step; no acknowledgement required.
- `needs-decision`: a concrete question, checks already made and recommendation;
  coordinator routes it to PM/PO, architect or the input/permission owner.
- `blocked`: the actual constraint, evidence and condition for resuming dependent work.
- `completed`: every assignment criterion has passed with evidence; the receiving
  role still verifies acceptance. Reviewers may complete by delivering findings.

`completed` closes only that assignment. PM/PO frames the user's parent outcome and
retains its terminal owner and outcome-specific check in the existing handoff; the
coordinator closes the parent only after integrated evidence proves that check. A
completed prerequisite is not parent delivery: a passing build can satisfy a
prerequisite, while a requested running deployment still requires checking its named
target. For multi-step work, record each handed-off result in the
[coordinator state](../skills/plex/references/coordinator-state.md) and advance the
parent's `next_action`; a blocked successor does not reopen a delivered step.

If an evidence method is unavailable or fails for a method-specific reason, use a
supported alternative within the same authorized action and scope; do not request
permission solely to change methods, while preserving acceptance and required checks.
A host denial, changed action/scope/effects, boundary crossing or unclear authority
goes to the actual permission owner.

Continue with the same executor and changed evidence/input or an explicit decision.
Do not reopen an unchanged problem under a new label or restart the entire workflow.
Return one response-envelope correction to its author with the exact diagnostic.
Preserve previously verified evidence with its original artifact, revision and
provenance; rerun work or checks only if that evidence changed or became invalid.
Do not add evidence on the author's behalf. If the correction is still invalid,
retain partial evidence and report the failure. Progress is event-driven, with no
timer, new token cap or automatic model escalation.

Initial PM intake and workflow-owned leaves retain their formats. BMad activation
and workflow evidence remain required in the enclosing return. Existing contracts
without identity remain readable; attach identity for new response checks without
restarting active work. Refresh Plex and start a new client session to load the new
instructions. Structural validity does not prove evidence quality, prevent every
loop, or enforce native dispatch; live behavior must be evaluated separately.
