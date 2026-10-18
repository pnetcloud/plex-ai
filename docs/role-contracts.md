# Agent role contracts

[English](role-contracts.md) · [Русский](translations/ru/role-contracts.md) · [Deutsch](translations/de/role-contracts.md) · [简体中文](translations/zh-CN/role-contracts.md)

Teams define membership and skill bindings; profiles select models; native templates
supply bounded execution instructions. Keep these responsibilities separate.
The root contract is `teams/<team>/coordinator.md`, not another subagent role.

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
for optional roles. Every configured role needs a template for each supported client.

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

## BMad contracts

Activate existing skills instead of copying personas or assuming a version's menus.
Preserve the selected rendered route, required review cycles and genuine user gates.
An applicable early exit skips later checkpoints in that step; verify its condition
and target before escalating. Correct a false gate in the same assignment without
inventing approval. A completed spec alone is not a reason to stop for permission.

Nested delegation requires authority and available capacity. Preserve leaf prompts
and context contracts; do not dispatch a leaf review to a wrapper that starts
another complete workflow. Report actual nested routing and unavailable capabilities.
