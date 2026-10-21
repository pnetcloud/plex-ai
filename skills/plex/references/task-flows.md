# Task flows

Use after explicit Plex activation and successful preflight.
Follow the selected team's coordinator, installed workflows and project adapters.
These routes assign work; BMad retains its procedures and checkpoints.

## Intake

1. Identify outcome, acceptance checks and existing plans, specifications, decisions and evidence.
2. Choose a flow. Select only checked team roles with a concrete unresolved question or deliverable.
3. State the route: outcome → roles and order → completion check. Cite existing decisions for skipped planning; explain a local mechanical-task shortcut briefly.
4. Assign the first ready step. Collect its result before dependent work; parallelize only independent ready assignments within limits.

Root owns routing, handoffs, dependencies, integration and final checks.

- Delegate missing specialist decisions to their owner; leave routine Build planning inside Build.
- Do not silently replace PM, PO, architect or dev with root.
- Root must not invent missing specialist decisions to classify substantial work as ready.
- Reuse completed work. Role availability alone does not require a call.
- Routing adds no approval gate; user authorization and interaction policy still apply.

## 1. Bounded change

**Use:** goal and acceptance are clear; no unresolved product or architectural decision blocks implementation.

`coordinator → dev → required checks/review → coordinator`

- Give dev accepted inputs, write ownership and checks. Build may create the implementation plan.
- Reuse planning; no repeat PM/architect approval.
- BMad: use the applicable project build route. Its owner handles investigation, planning, implementation, review and fixes. Do not skip its steps or add a duplicate planning/review pipeline.
- Separate reviewer/QA: only for required independent proof, explicit review or a concrete evidence gap. Use only roles in the selected team.
- Small mechanical work with clear checks may stay local.

## 2. Substantial new task

**Use:** substantial work needs product requirements, specification/task breakdown, UX or architectural decisions before implementation.

`coordinator → needed planning roles → dev → required checks/review → coordinator`

| Missing decision | BMad | pnet |
|---|---|---|
| Product outcome, scope, priorities, acceptance | `pm` | `pm` |
| Specification, task breakdown, replanning | `po` | `pm` |
| User journeys, interaction states, design | `ux` | `pm` plan; no separate UX role |
| Component boundaries, interfaces, data ownership, architectural tradeoffs | `architect` | `pm` technical plan; no separate architect role |

- Select unresolved rows only. All resolved → flow 1.
- PM owns product requirements; PO turns agreed requirements into executable specifications/tasks.
- Resolve architectural questions with architect before dev; do not leave them to a cheaper implementation worker.
- Pass outputs by reference. Start dev when scope, acceptance and necessary technical decisions are ready.
- Select workflows from the checked catalog; preserve project adapters.
- Missing required role/skill: report a blocker. No silent persona substitution.

## 3. Diagnose and fix

**Use:** failure, code path or cause is unknown.

`coordinator → bounded investigation → dev fix → required verification → coordinator`

- pnet: `explorer` maps unfamiliar code; `dev` owns reproduction and technical diagnosis.
- BMad: use dev's applicable installed workflow; do not invent an explorer role.
- Establish evidence and a failing check before selecting the fix.
- New scope or architectural decision → flow 2 for that question.
- Resume the implementation owner with the diagnosis. Verify the original failure and affected behavior.
- Use reviewer/QA when independent proof is required and the role exists in the selected team.
- External knowledge gap: pnet may use `researcher` for bounded work.
- BMad analyst/research work requires explicit user authorization; uncertainty is insufficient.

## 4. Review a change

**Use:** independent assessment of an exact change is requested.

`coordinator → reviewer → coordinator`

- Supply exact diff/revision, requirements and review scope.
- BMad: use the applicable project review workflow and retain its required stages.
- Return actionable findings and verification gaps.
- Review alone authorizes neither fixes nor unrelated audits.
- If fixes are authorized: assign dev, then verify affected findings.
- Repeat full review only for a material new change or uncovered risk.

## Revisit the route

| Change | Consult |
|---|---|
| Scope or acceptance | PM / PO, as supported by the team |
| Technical assumptions | Architect where available; pnet PM for technical planning |

- Ask a bounded question; reuse accepted work.
- Do not restart all stages for each message or routine implementation detail.
- Report missing capabilities and unresolved gates; continue independent authorized work.
- Preserve the installed workflow's actual checkpoints.
