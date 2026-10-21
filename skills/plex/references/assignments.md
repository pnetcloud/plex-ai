# Assignment contract

PM owns framing and execution choice in pnet. BMad PM owns intake; PO refines
specifications and executable assignments, and architect owns technical decisions.
Root schedules their decisions; it does not become another manager.

## Prepare and check

1. PM/PO supplies the compact [JSON contract](../assets/assignment.json.template)
   for each executable Plex-owned native subagent assignment. Initial PM intake is exempt.
2. Use the existing issue/spec/story reference, or the current request for a task
   without one. No new tracker or mandatory assignment file. Pass JSON directly;
   store it only in an already authorized artifact area when useful for continuation.
3. Include inputs, write/exclusion paths, accepted dependencies and acceptance.
   Dependencies list accepted decisions, not work still pending. Preserve the
   baseline and unrelated hunks from the coordinator's workspace handoff.
4. Normally use three criteria, at most five; one is enough for a simple task.
   Each criterion needs an observable result and a concrete verification method.
   This caps the handoff summary, not upstream requirements: reference the
   canonical spec's detailed criteria and retain every required workflow check.
5. Root checks the contract before native dispatch, using this package's script
   and the snapshot already verified by preflight:

   ```sh
   python3 <plugin-root>/skills/plex/scripts/check_assignment.py --resolved <root>/.plex/resolved.json
   ```

   Supply the contract as JSON on stdin. Exit 0 and `status: valid` mean the
   structure passed; exit 1 reports errors. Return substantive corrections to
   PM/PO. This check grants no authority, checks no filesystem containment and
   does not prove semantic readiness or native role availability.

Preserve the coordinator's interaction, authority, workspace and workflow handoff.
The JSON is its compact task core, not a replacement for those boundaries.
Workflow-owned leaves keep their installed recipe, not an extra Plex JSON gate.
Root's integration, final checks and PM-assigned mechanical actions retain their
existing scope; do not invent a root subagent contract or bypass PM intake.

Pass capacity with nested work: `max_agents` caps concurrently unfinished Plex
assignments, not cumulative launches. Returned/idle assignments no longer count
as in flight. Native live-thread slots may still include idle handles; check
those limits separately. Report current active work and the planned batch before
claiming a capacity blocker. Reuse handles without reserving a Plex assignment slot
forever, and preserve implementation handles required for workflow fix resumption.

## Choose execution

| `execution.mode` | Manager's intent | Completion |
|---|---|---|
| `normal` | Implement a ready, bounded assignment | Criteria verified |
| `plan` | Resolve missing decisions before implementation | Accepted decisions and an actionable plan; no application edits |
| `goal` | Iterate implementation, checks and corrections toward a measurable result | Criteria verified or an evidenced stopping condition |

- PM/PO includes `execution.reason`; in interaction `auto`, select without asking
  another mode question. User choices and host authority still take precedence.
- `normal` and `goal` require `readiness: ready`. `plan` may resolve
  `needs-specialist`; `blocked` assignments cannot launch. A plan assignment must
  have its own usable inputs even if the overall task awaits its result.
- Planning may precede a goal assignment. Reuse accepted decisions; do not add
  another planning cycle merely because the execution approach changes.
- For `goal`, include `execution.token_budget: 50000` unless the user explicitly
  supplies another positive budget. It is a requested native budget, not a
  promise of shared accounting across nested agents. Never renew, increase or
  replace an exhausted goal automatically. Exhaustion stops that assignment;
  do not switch to ordinary execution to bypass the limit. Report progress and gaps.
- Probe actual tool availability and permission for the owning session. Use
  native Plan/Goal only when supported and authorized. Do not switch the user's
  chat mode, replace an active goal, or infer Goal authority from a task label.
  When available, create Goal in the assigned executor's thread with its outcome,
  criteria, boundaries and requested token budget; do not turn it into a project-wide goal.
- Without native support or authorization, keep the same assignment: return a
  normal plan or iterate toward its criteria using available tools. Report the
  actual approach. Do not claim native mode, enforced token accounting or
  automatic continuation after the host ends the turn. No custom runner/daemon.
- During goal work, compare each iteration to the criteria and retain evidence.
  Follow the coordinator's existing retry/no-progress limits. Missing authority,
  an unavailable required specialist or a real workflow gate blocks dependent work.
- Scope/acceptance changes return to PM/PO; technical conflicts go to architect
  in BMad or PM in pnet. Root does not decide them; dev does not expand the goal.

## Context and return

- Reuse the same role's live handle for continuation. Send new decisions, changed
  evidence and the remaining question, not the full transcript again.
- Pass exact artifact paths/revisions from tool output. A missing input returns
  to its owner; a similar filename is not identity evidence. Correct the reference
  and resume the same assignment before accepting a check on a different input.
- Run independent assessments in parallel; pass accepted results before dependent
  implementation. Relay relevant conflicting conclusions to their decision owner;
  do not invent consensus or broadcast all history to every role.
- Return each criterion with evidence, changed paths and unresolved gaps. A native
  goal completes only after its own criteria pass; required independent acceptance
  still belongs to the owning review/QA or manager assignment.
