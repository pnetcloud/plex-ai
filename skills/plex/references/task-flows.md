# Task flows

Use after explicit Plex activation and successful preflight.
Follow the selected team's coordinator, installed workflows and project adapters.
These routes assign work; BMad retains its procedures and checkpoints.

## Intake before routing

1. Root locates the request, project instructions, existing task references and authority. Do not classify complexity, design the solution or declare the task ready.
2. Keep one coordinator-owned [session state](coordinator-state.md). Related followups amend their current outcome; record unrelated requests there without dispatch or intake.
3. Before routing or executing a new unrelated request, queued item or material decision outside an accepted plan, call the checked `plex-pm` for a short intake assessment. Batch related queued requests when one assessment covers them; reuse its identity with a new task label.
4. Supply intent, constraints, existing artifacts, interaction mode and write authority. Do not activate a PRD or planning workflow by default.
5. PM returns: task class; outcome/non-goals; accepted inputs and missing decisions; required roles/order; task format and canonical reference; dev contract and observable checks; `ready`, `needs-specialist` or `blocked` with evidence. PM/PO selects the execution approach through [assignment contracts](assignments.md); root does not choose it from apparent task size.
6. Follow PM's route and collect required outputs before implementation. Give each worker only its assigned goal, inputs and constraints; workers do not read the global queue. Root checks team/permission consistency and schedules work; it does not replace specialist judgment.

### Readiness and task format

- PM owns intake in both teams. In BMad this short role-local assessment does not activate PRD, PO or Build automatically. Domain work uses the installed BMad skill when actually assigned.
- Use the project's existing task format and store: issue/tracker, local spec, story or an explicit short handoff. Reference and refine existing records; do not introduce a parallel tracker or force a new document for a small task.
- If BMad owns the spec/ticket format, dispatch the installed PO operation or spec skill supported by that version. `bmad-spec` is an option when installed, not a universal prerequisite. External record mutation still needs the project's authority.
- In BMad, PM reads the full `workflows` map once from the exact snapshot passed by root and selects the minimal sufficient route. Return each step's purpose, eligible role, exact entry, sequence and expected canonical output/input; root alone dispatches and integrates.
- Reuse concrete accepted requirements for a ready bug or executable contract and send it to Dev Build. For a small new capability, use an assigned standalone spec workflow or Build's supported minimal-spec route before code. For larger unresolved requirements, select only the workflows needed to settle them; do not require a PRD, epic or story by default.
- Before implementing code against newly authored or materially revised BMad executable requirements, require semantic validation through the installed generation's supported operation and project adapter (PO `VALIDATE` when supported). Build may investigate, diagnose, plan and draft its implementation spec before this gate; validation is required at the code boundary. Evidence names the installed generation, actual operation and adapter used, plus the canonical requirements revision and identities/revisions of checked source requirements, load-bearing companions and current human decisions (or a canonical revision that binds them), relevant scenarios/dependencies and terminal acceptance, findings and disposition. Reuse evidence only while this complete input bundle is unchanged. If Build drafts new executable requirements, the coordinator pauses only code implementation, routes that exact spec through PO `VALIDATE` or the installed equivalent without another PM intake, then resumes the same Dev at a safe boundary after material gaps are resolved. A missing required capability blocks only implementation against those requirements. Structural assignment checks and persona activation are not semantic validation. Continue already accepted work with its current owner and apply new deltas at a safe boundary; do not restart it retroactively.
- Classify by the planned change and unresolved decision, not labels like bug or feature:

  | Class | Route |
  |---|---|
  | `execution-ready` — change stays within a known component/boundary; outcome, acceptance and implementation path are clear | Dev Build; no extra specialist |
  | `product-ux` — product scope, acceptance or user experience is unresolved | PM/PO; UX only for user journeys, interaction states or design decisions |
  | `architecture` — a new/changed capability spans subsystem/service/data-store boundaries, changes a shared interface, data owner or invariant, or affected architecture is missing/contradictory | Architect before dev in BMad; PM owns the technical plan in pnet |
  | `diagnosis` — failure cause is unknown | Dev investigates; pnet explorer maps unfamiliar code. Route a design decision only if diagnosis shows one is needed |

- PM includes the class and required role order in the intake. Reuse accepted decisions and the selected team's installed workflow catalog.
- Only a specialist-produced or explicitly user-approved decision covering the current scope can satisfy a missing planning result. Root's previous analysis, a small diff or the label "bugfix" cannot.
- Routine steps already covered by the assessment, workflow-owned leaves, status questions and unchanged continuation reuse that assessment. Intake itself does not recursively require another intake.
- Missing/rejected required roles block their assignments. Root may gather bounded context and report status, but must not do the blocked planning/design/implementation locally or substitute generic agents.
- This is a specialist-result prerequisite, not another user approval prompt. Apply `auto` and preserve actual project/workflow gates.

## 1. Bounded change

**Use:** PM intake returned ready, or the assigned specialists supplied its missing decisions; scope and acceptance are explicit.

`coordinator → PM intake → dev → required checks/review → coordinator`

- Give dev accepted inputs, write ownership and checks. Build may create the implementation plan.
- Reuse the intake assessment and accepted specialist outputs; do not repeat planning for covered steps.
- Before code, reuse concrete accepted requirements or have the selected spec/Build route produce them. Do not create a PRD, epic, story or duplicate specification automatically.
- BMad: use the applicable project build route. Its owner handles investigation, planning, implementation, review and fixes. Do not skip its steps or add a duplicate planning/review pipeline.
- In `auto`, PM/PO selects installed `bmad-build-auto` for suitable unattended implementation: one workflow iteration, not an endless loop. Verify its actual dispatch, mandatory subagents and capacity. If unavailable, use `bmad-build` only through an authorized supported route; never skip its checkpoints. Native Goal availability does not decide workflow readiness.
- Before implementation acceptance, require independent code review of the exact candidate and requirements unless the human explicitly overrides. A completed applicable Build-internal independent review counts once; absent or unproven review routes the exact candidate and requirements to the standalone `reviewer`. Record exact requirement/candidate revisions, reviewer independence, findings and disposition; reuse evidence only while both candidate and requirements are unchanged, and review material changes. A later explicit human override remains authoritative. Do not add a second full review after a completed applicable internal review.
- QA remains a separate behavior check; use only roles in the selected team.
- Root may perform a mechanical step only when the PM assessment explicitly assigns it; this never bypasses intake.
- Apply [execution ownership](assignments.md#execution-ownership): the assigned
  executor handles routine technical steps without another PM round. Freeze only
  the inputs under comparison; continue independent authorized implementation
  while measurement or acceptance is pending.

## 2. Resolve a product, UX or architecture decision

**Use:** PM classified an unresolved product, UX or architectural decision that needs its owner before implementation.

`coordinator → PM intake → required specialists → dev → required checks/review → coordinator`

| Missing decision | BMad | pnet |
|---|---|---|
| Product outcome, scope, priorities, acceptance | `pm` | `pm` |
| Specification, task breakdown, replanning | `po` | `pm` |
| User journeys, interaction states, design | `ux` | `pm` plan; no separate UX role |
| Component boundaries, interfaces, data ownership, architectural tradeoffs | `architect` | `pm` technical plan; no separate architect role |

- PM selects unresolved rows; required specialists return their decisions before flow 1 can start.
- PM owns product requirements; PO turns agreed requirements into executable specifications/tasks.
- Resolve architectural questions with architect before dev; do not leave them to a cheaper implementation worker.
- Pass outputs by reference. Start dev when scope, acceptance and necessary technical decisions are ready.
- Select workflows from the checked catalog; preserve project adapters.
- Missing required role/skill: report a blocker. No silent persona substitution.

## 3. Diagnose and fix

**Use:** failure, code path or cause is unknown.

`coordinator → PM intake → assigned investigation/design → dev fix → required verification → coordinator`

- pnet: `explorer` maps unfamiliar code; `dev` owns reproduction and technical diagnosis.
- BMad: Dev Build owns code-path investigation. Return only a product or architectural decision found during diagnosis to PM/PO/Architect; do not invent an explorer role.
- Establish evidence and a failing check before selecting the fix.
- End diagnosis when the failing path and cause support a safe repair. Record
  unresolved facts as fail-closed behavior or acceptance checks; investigate further
  only when a specific answer could change the fix, scope or safety.
- Separate code repair from recovery of the held production item. Unknown identity
  or possible prior effects block ACK, replay or mutation, but do not block an
  isolated fix that safely holds unknown cases.
- Use the repository's established test route. If a runner stops before tests,
  correct the evidenced environment failure within the assignment and applicable
  retry rules, or mark that check blocked; do not create repeated pre-test gates.
- New scope or architectural decision → flow 2 for that question.
- Resume the implementation owner with the diagnosis. Verify the original failure and affected behavior.
- Use reviewer/QA when independent proof is required and the role exists in the selected team.
- External knowledge gap: pnet may use `researcher` for bounded work.
- BMad analyst/research work requires explicit user authorization; uncertainty is insufficient.

## 4. Review a change

**Use:** independent assessment of an exact change is requested.

`coordinator → PM intake → reviewer → coordinator`

- Supply exact diff/revision, requirements and review scope.
- BMad: use the applicable project review workflow and retain its required stages.
- Return actionable findings and verification gaps.
- Review alone authorizes neither fixes nor unrelated audits.
- If fixes are authorized: assign dev, then verify affected findings.
- Repeat full review only for a material new change or uncovered risk.

## 5. CI, release or deployment

**Use:** CI/CD changes, release preparation/publication, or explicitly assigned deployment/recovery.

`coordinator → PM intake → required decisions → devops → required checks/review → coordinator`

- DevOps owns the assigned pipeline/release/deployment paths; application fixes remain with dev. Use reviewer for required independent review.
- Pass the exact source SHA/artifact, target, project procedure, checks and existing authorization. Publication and deployment are separate operations.
- Check required-role availability before accepting the operational route. A
  missing role blocks its assignment, not the whole team; do not hide that blocker
  behind repeated measurements or substitute another role without authority.
- DevOps is a native Plex specialist in both teams; do not require a BMad persona or invent a workflow binding for it.
- Reuse valid checks for the same revision. Verify publication, installation and runtime state separately; inspect state after interrupted operations before retrying.

## Revisit the route

| Change | Consult |
|---|---|
| Scope or acceptance | PM / PO, as supported by the team |
| Material technical assumptions outside the accepted assignment | Architect where available; pnet PM for technical planning |

- Ask a bounded question; reuse accepted work.
- Do not restart all stages for each message or routine implementation detail.
- Report missing capabilities and unresolved gates; continue independent assignments through ready roles. Root remains within coordination and explicitly assigned mechanical steps.
- Preserve the installed workflow's actual checkpoints.
