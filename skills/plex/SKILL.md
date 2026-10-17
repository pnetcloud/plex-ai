---
name: plex
description: Coordinate coding subagents for complex tasks using the project's Plex roles and preset, when delegation is useful or explicitly requested.
---

# Plex

Keep small, clear tasks in the current agent unless delegation is requested or
independent verification is useful. Multiple files alone do not require a team.

## 1. Check the applied configuration once

Run the read-only check before the first delegation:

```sh
python3 <plugin-root>/skills/plex-setup/scripts/resolve_config.py check <project> --host <codex|claude|antigravity>
```

Proceed only when the selected host is `in_sync`. Read `.plex/resolved.json` for
active roles, final `hosts.<host>.<role>` settings and `max_agents`; do not reassemble
configuration layers. Missing, stale or conflicting configuration requires
`plex-setup`; it does not authorize installation or writes. Repeat the check only
if configuration changes or there is evidence of drift during this task.

Select the configured native `plex-<role>` so the host applies its instructions,
model and reasoning. Do not hardcode models in handoff prose or silently substitute
the root model. If explicit spawn parameters are required, derive them from the
snapshot and retain the role instructions; report unsupported routing.
The Coordinator keeps its session model and permissions.

For `process = "bmad"`, read [references/bmad.md](references/bmad.md).
Delegate only to active roles; unknown processes are configuration errors.

## 2. Choose only the work that is needed

In `default`, PM combines investigation, requirements and architecture planning;
dev implements and tests; reviewer independently examines the change. Clear work
can go directly to dev. Request PM only for uncertain scope, acceptance criteria,
shared invariants or a design blocker.

In `bmad`, select relevant roles and follow the installed workflow. A workflow
that owns implementation also owns its required checks and reviews. Inspect its
returned evidence before assigning more work: do not append another complete
review or QA stage automatically. Additional review needs an explicit user request,
a concrete uncovered risk, incomplete evidence or a material subsequent change.
For custom teams, select only roles in the snapshot.

## 3. Give a compact handoff contract

Pass paths and a short digest, not full transcripts or copies of available files:

- **Outcome:** The requested result and workflow intent; identify an existing spec
  or story when applicable.
- **Inputs:** Task/spec paths, relevant files or review diff and exclusions. Pass
  verified skill roots, environment facts and existing test commands when known;
  do not make each role rediscover them. State when no spec exists.
- **Authority:** Writable application paths plus required workflow spec and test
  artifact paths, or read-only status; one writer per file. Preserve user exclusions
  and state whether nested delegation is authorized.
- **Checks:** Observable acceptance, relevant invariants and completed checks.
  Require readable, unminified source following project conventions and no
  unrequested features, fields or branding. Reuse existing tests; if none cover the
  task, authorize one small runnable check file in the test/artifact area and
  retain its command/results.
- **Result:** Changed/artifact paths, check results, completed review layers and
  unresolved findings. A blocker cites evidence; a gate cites the reached rendered
  step, exact question and resume context.

Investigate beyond the supplied inputs only to trace a concrete dependency or
suspected defect affecting the outcome. Report unrelated issues separately without
fixing them or turning the assignment into a project-wide audit. If ownership or
scope must expand, return the reason to the Coordinator first.

The Coordinator assigns work and integrates results. Dependencies between artifacts
are not permission for children to spawn other roles. Run independent assignments
in parallel only when inputs are stable and ownership does not overlap. Count known
in-flight Plex assignments, including authorized nested work, against `max_agents`.
If nested counts are unobservable, do not claim a global cap is enforced. If a
workflow requires more simultaneous agents than the available budget, report the
conflict rather than silently exceeding it or rewriting its required sequence.

## 4. Finish without restarting the process

Inspect returned evidence and the integrated diff, including readability and scope.
For a workflow blocker or disputed review stage, check the cited reached step of
the selected rendered route before relaying it. A checkpoint or layer on another
branch is not applicable. Correct a mistaken route claim and resume the same
assignment; relay real gates unchanged. Do not audit the entire workflow again.
Reuse completed checks while
their inputs remain unchanged; rerun affected checks after fixes or when evidence
is insufficient. Finish when acceptance criteria pass and material findings are
resolved or explicitly reported as blocked.

For Plex-owned review, perform one correction pass and focused verification of the
findings. Do not restart full review merely to seek another clean verdict. Further
review needs a material new change, an uncovered risk or an explicit request; if the
same unresolved finding returns without new evidence, report the blocker instead of
looping. Required installed-workflow cycles and human gates retain their own rules.

Retry a recoverable agent failure once with corrected scope or context. Missing
skills, permission limits, conflicting invariants and applicable human gates are blockers,
not retry opportunities. Relay workflow gates to the user through the Coordinator
and resume the same assignment after an actual answer; do not treat a recommendation
as approval or restart the workflow from scratch. Account for failed and unfinished
work. Report only delegation, routing and verification actually observed.
