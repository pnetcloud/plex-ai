# Assignment contract

PM owns framing and execution choice in pnet. In BMad, PM owns intake and route
selection and may execute an explicitly assigned bounded product/spec workflow.
PO owns specification/task refinement and executable assignment work when selected;
architect owns technical decisions. Root dispatches the selected route and integrates
results.

## Prepare and check

1. PM/PO supplies the compact [JSON contract](../assets/assignment.json.template)
   for each executable Plex-owned native subagent assignment. Initial PM intake is exempt.
2. Use the existing issue/spec/story reference, or the current request for a task
   without one. No new tracker or mandatory assignment file. Pass JSON directly;
   store it only in an already authorized artifact area when useful for continuation.
3. Include the assigned bounded result, its relation to the parent outcome, inputs,
   write/exclusion paths, accepted dependencies and acceptance. When a user's outcome
   spans steps, preserve its terminal owner/check in the existing outcome/acceptance;
   include a representative real input when needed to make that check concrete.
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
Use the existing outcome/input to identify a direct workflow or persona/menu entry;
do not add an assignment field for route selection.
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
- Probe actual tool availability and permission for the owning session. Use
  native Plan/Goal only when supported and authorized. Do not switch the user's
  chat mode, replace an active goal, or infer Goal authority from a task label.
  When available, create Goal in the assigned executor's thread with its outcome,
  criteria and boundaries. Do not turn it into a project-wide goal.
- Without native support or authorization, keep the same assignment: return a
  normal plan or iterate toward its criteria using available tools. Report the
  actual approach. Do not claim native mode or automatic continuation after the
  host ends the turn. Client/provider restrictions and tool availability still apply. No custom runner/daemon.
- During goal work, compare each iteration to the criteria and retain evidence.
  Follow the coordinator's existing retry/no-progress limits. Missing authority,
  an unavailable required specialist or a real workflow gate blocks dependent work.
- Scope/acceptance changes return to PM/PO; technical conflicts go to architect
  in BMad or PM in pnet. Root does not decide them; dev does not expand the goal.

## Context and return

- The coordinator owns its session state and passes each worker only the current assigned goal, inputs and boundaries; workers do not read or update the global queue.
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

## Response contract

For new Plex-owned assignments, root attaches `assignment` (the current task label)
and a positive integer `revision`, starting at 1. Preserve them on continuation.
PM/PO changes the revision when outcome, scope or acceptance changes; ordinary
progress does not. Keep the current contract in the conversation or an authorized
artifact area, not a new tracker. Reusing a handle does not reuse a previous task's
identity. Legacy input contracts remain readable; attach identity before using the
response check. Do not restart running work merely to add identity.

Return a JSON object using the [response template](../assets/response.json.template).
All responses require `assignment`, `revision`, exact native `role`, `status` and
`summary`. Preserve role-specific findings and BMad activation/step evidence as
additional fields or referenced artifacts. Intake and workflow-owned leaves retain
their existing return formats; validate the enclosing Plex-owned assignment only.

| Status | Required fields | Meaning |
|---|---|---|
| `progress` | Non-empty `evidence` list and `next` | New result or observation; continue without acknowledgement |
| `needs-decision` | `request` with `kind`, `question`, non-empty `attempted`, `recommendation`; `next` | A specific decision is needed; continue independent authorized work |
| `blocked` | `blocker` with `constraint`, non-empty `evidence`, `resume` | Dependent work cannot proceed; name what would unblock it |
| `completed` | `criteria` covering every acceptance item as `passed` with evidence; `artifacts` list | Ready for acceptance, not automatically accepted |

`criteria` entries use a unique 1-based `index`, `state` (`passed`, `failed`,
`pending`) and `evidence` list. Passed/failed require evidence; pending may use an
empty list. Intermediate responses may omit criteria or report a subset. Artifacts
may be empty for consultations. A reviewer can complete an assignment that finds
bugs: its criteria require findings, not a positive verdict on the implementation.
`request` is allowed only for `needs-decision`; `blocker` only for `blocked`.
`completed` cannot contain an unresolved request or blocker.

### Parent outcome and terminal delivery

`completed` closes only the assigned work. PM/PO frames the user's parent outcome
and retains its terminal owner and outcome-specific check in the existing handoff;
the coordinator owns integration and closes that outcome only after the check has
evidence. A completed prerequisite remains complete but does not prove parent
delivery. For example, a passing build can complete a prerequisite; when the parent
outcome is a running deployment, confirm the requested release is running on the
named target before reporting delivery.

Root checks a returned object before accepting it or using it as a dependent input:

```sh
python3 <plugin-root>/skills/plex/scripts/check_assignment.py --resolved <root>/.plex/resolved.json --assignment <current-assignment.json>
```

Pass the response on stdin; supply the current accepted contract via an authorized
temporary file when it exists only in conversation. The checker is read-only.
A valid structure does not prove evidence, scope containment, progress, delivery or
acceptance. It does not intercept native dispatch. Inspect actual evidence and the
host completion event before closing work; a progress message is never completion.

## Help and continuation

- Ask for help on a demonstrated uncertainty before expanding scope or repeatedly
  guessing. `attempted` records relevant observations/checks, not a required number
  of failed experiments. A confirmed contradiction can be escalated immediately.
- Route `request.kind`: `context` to the input owner; `scope` to PM/PO; `technical`
  to BMad architect or pnet PM; `permission` to its actual authority owner. Root
  routes decisions, not substitutes for the required specialist. A recommendation
  is not authorization; `auto` preserves real gates.
- Return the decision, changed input/evidence and next check to the same executor.
  Preserve its write ownership. Do not spawn another dev or change models merely
  because it requested help.
- Resume a repeated problem only with a concrete change in evidence, input or
  decision. Reuse an already supplied answer instead of opening another routing
  cycle. Compare canonical reference, affected criterion and cause across task
  labels; renaming/revising a task does not reset the problem's history.
- Keep existing retry and installed workflow rules. If the same problem remains
  without new evidence, preserve partial results and report the actual constraint;
  do not repeat the whole workflow or create a manager consultation loop.
- Return response-format errors once to the same author with exact diagnostics.
  The author may correct the envelope while retaining previously verified evidence
  and its original source, revision and provenance. Do not rerun unchanged work or
  checks, or invent evidence on the author's behalf; repeat them only when the
  evidence changed or became invalid. If the correction is still invalid, retain
  partial evidence and report the validation failure.
- Send concise event-driven progress for a completed check/criterion, new risk or
  needed decision. Include what changed, evidence and next step. Do not repeat an
  unchanged update, wait for an ACK, or start a periodic manager review. No timer,
  execution timeout or model budget is introduced. Silence during a blocking tool
  call alone does not establish drift. Report unavailable live messaging honestly.
