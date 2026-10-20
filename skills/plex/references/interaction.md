# Interaction policy

Read the applied snapshot's `interaction` setting: `interactive`, `balanced`
(default), or `auto`. An explicit user choice for the current task overrides the
saved setting for that task only; do not rewrite configuration to record it.
Pass the effective mode and these rules in each handoff, including nested work.
This policy governs coordination; it is not a universal BMad CLI flag.

## Modes

- **interactive:** Involve the user in discovery and meaningful choices. Use the
  selected workflow's interactive route; do not ask for facts already supplied.
- **balanced:** Resolve routine implementation choices from requirements, code
  and established conventions. Record reversible assumptions. Ask only when a
  consequential user-owned decision or an applicable checkpoint remains unresolved.
- **auto:** Do not ask questions or wait for user input. Complete authorized work,
  record assumptions and return open decisions, partial results and blockers.
  A required answer that is unavailable blocks dependent work, not unrelated work.

## Questions and blockers

Subagents return questions to the coordinator with relevant evidence and resume
context; they do not ask the user directly or poll for answers. The coordinator
first checks existing requirements, prior user decisions and the reached workflow
branch. Answer from existing authority, never fabricate consent.

In balanced mode, combine necessary questions into one concise request with a
recommendation. Continue independent work while an answer is pending. In auto,
record an unresolved gate as blocked, keep completed artifacts, continue independent
work and finish with a clear partial/blocked report instead of waiting indefinitely.
Do not treat incomplete requirements as approved downstream implementation inputs.

## BMad execution

For bounded artifact assignments in balanced or auto, explicitly request native
headless execution when the selected installed workflow supports it. Supply the
intent, inputs, output location, scope and budget; use its actual headless contract.
Honor the workflow's complete/partial/blocked semantics and record assumptions.
Interactive mode uses the interactive contract. Do not infer headless support from
the fact that an agent is a subagent.

Where headless is unsupported, follow the actual rendered route. Do not set invented
flags, force oneshot, or skip required review/validation to avoid a question.
Verify early-exit conditions before escalating a checkpoint. A genuine checkpoint
without an authorized non-interactive path returns a blocker in auto; balanced or
interactive may relay it to the user. Resume the same assignment after a real answer.

All modes retain host permissions, write ownership, user exclusions and required
checks/reviews. Auto does not authorize publication, destructive actions, expanded
scope or analyst research. Existing explicit authorization remains valid; do not
ask for it again. Report only observed execution and checks, not promised autonomy.
