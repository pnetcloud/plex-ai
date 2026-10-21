# Interaction policy

## Select the mode

- Read `interaction` from the applied snapshot; default: `balanced`.
- An explicit user choice overrides it for the current task only. Do not rewrite configuration.
- Pass the effective mode and rules in every handoff, including nested work.
- This is a coordination policy, not a universal BMad CLI flag.

| Mode | Behavior |
|---|---|
| `interactive` | Involve the user in discovery and meaningful choices. Use the workflow's interactive route; reuse supplied facts. |
| `balanced` | Resolve routine choices from requirements, code and conventions. Record reversible assumptions. Ask only for unresolved consequential user decisions or applicable checkpoints. |
| `auto` | Do not ask or wait. Complete authorized work; return assumptions, open decisions, partial results and blockers. Missing answers block dependent work only. |

## Questions and blockers

1. Subagents return questions to the coordinator with evidence and resume context. No direct user questions or polling.
2. Check requirements, prior user decisions and the reached workflow branch.
3. Answer from existing authority. Never fabricate consent.
4. In `balanced`, group necessary questions into one concise request with a recommendation.
5. Continue independent work while an answer is pending.
6. In `auto`, record unresolved gates as blockers; keep completed artifacts and finish with a clear partial/blocked report.

Incomplete requirements are not approved implementation inputs.

## BMad execution

For bounded artifact work in `balanced` or `auto`:

- Explicitly request native headless execution **only if the installed workflow supports it**.
- Supply intent, inputs, output location, scope and budget.
- Follow its actual headless contract and complete/partial/blocked semantics; record assumptions.

In `interactive`, use the workflow's interactive contract.

If headless execution is unsupported:

- Follow the actual rendered route. Being a subagent does not imply headless support.
- Do not invent flags, force oneshot or skip required reviews/validation.
- Verify early-exit conditions before escalating a checkpoint.
- A genuine checkpoint with no authorized non-interactive path blocks `auto`; `interactive`/`balanced` may relay it to the user.
- Resume the same assignment after an actual answer.

## Authority

All modes preserve host permissions, write ownership, user exclusions and required checks/reviews.

- `auto` grants no publication, destructive-action, scope-expansion or analyst-research authority.
- Existing explicit authorization remains valid; do not request it again.
- Report observed execution and checks; do not promise unattended completion.
