# Coordinator session state

The coordinator owns one small state file per Plex session:
`.plex/work/<session-id>.json`. Use the host's stable session ID when available.
Otherwise choose a unique local ID and carry the file path in continuation context.
Never merge different sessions. This state is private runtime context, not a ticket
store, package asset, global memory or worker inbox. Workers receive only their
assigned goal, inputs and constraints; they do not read the coordinator's queue.

Start from [`assets/coordinator-state.template`](../assets/coordinator-state.template).
The schema is versioned and the arrays name each item's current state:

| Field | Meaning |
|---|---|
| `primary_id` | The one current user outcome. It points to one item in `active`, `queued` or `paused`; use `null` only when no unfinished work remains. |
| `active` | Work currently being executed. Two outcomes total may be active by default, including the primary. |
| `queued` | Unrelated requests recorded for later routing or execution. |
| `paused` | Unfinished work with a concrete resume condition. |
| `recently_completed` | Up to four compact result references, retained only after handoff. |
| `decisions` | Up to eight priority, supersession and authority records. |

Each open outcome keeps its ID, goal, canonical source reference, owner, user
authorization, current priority, next action, blocker and resume condition. The
`owner` names the coordinator or the current executor role/handle. For active or
paused work, `reference` points to the accepted assignment or continuation record
that identifies live executors and file write ownership. Update that record before
preemption or re-entry; do not free a slot until its executor stops or hands off.
primary goal may use up to 1024 Unicode characters; other goals and ordinary
strings use at most 512. IDs and owners use at most 64. Next actions, blockers and
resume conditions use at most 256. A completed item keeps its result reference.
Record a higher or lower active limit as a decision with an integer `active_limit`,
`authority: "user"` and an exact reference. The most recent limit record is the
current override; without one, the limit is two.

## Lifecycle

- A related followup amends its existing outcome and assignment. Do not create a
  duplicate or ask routine scheduling questions.
- Record an unrelated request in `queued` without launching PM intake or workers.
  Before choosing its route or executing it, obtain PM intake; batch queued
  requests when one assessment can cover their order and readiness. Do not repeat
  intake for an accepted assignment or unchanged continuation.
- Follow explicit user priorities and supersession decisions. Otherwise finish the
  primary before opening another direction. If an explicit urgent request
  preempts it, save a concrete resume point and account for its real executors and
  write ownership. Keep work active until its executors stop or hand off; changing
  a label alone does not free a slot. Keep blocked work visible while authorized,
  independent work proceeds.
- Read this file when handling a new request, resuming after compaction or re-entry,
  and before selecting the next bounded step. Compact at substantive transitions
  and before context compaction. Keep the primary goal, user decisions, unfinished
  and paused commitments, next actions, blockers, resume conditions and exact
  retrievable references. Do not copy full conversations or detailed assignments.
- Before removing a completed item, hand off its result reference to the canonical
  task record or final delivery. Keep unresolved and paused work. Delete this
  disposable file when the session's agreed work is finished; do not archive chat
  history.

## Limits and validation

The serialized UTF-8 file, including whitespace, is at most 8192 bytes. The
checker also requires unique IDs, one valid primary reference, bounded arrays,
required open-item fields and a resume condition for every paused item. It rejects
an active count above two unless the state records a sufficient user override.

Before creating the first state file, ensure its path is ignored by Git. Check that
the session path is not already tracked, then run `git check-ignore -q --no-index`
for `.plex/work/<session-id>.json`. If Git does not ignore it, preserve any existing
`.plex/work/.gitignore` contents and add `*` there, then verify the session path is
ignored. Do not change the project's root `.gitignore`. If the session file is
already tracked, report that condition; do not silently untrack it.

Run the read-only state check before opening the file in conversation context; it reads
at most 8193 bytes and reports oversized files without dumping their contents:

```sh
python3 skills/plex/scripts/check_coordinator_state.py .plex/work/<session-id>.json
```

Exit 0 means the structure and limits pass; exit 1 returns a JSON error list. Do not
load an invalid or oversized state file into context. The checker never writes
state. Keep `.plex/work/` out of version control and do not stage session state.

If a byte or item-count limit is reached, first deduplicate, batch requests only
when one PM intake can cover them, and semantically compress using exact retrievable
references. Preserve current user decisions, authorization and unfinished or paused
commitments. Do not overwrite an item or silently drop a request or decision. If a
lossless compact state still cannot fit, keep the last valid state and report the
storage condition while the unrecorded request remains visible for resolution.

When replacing a valid state, write a candidate beside it, run this checker on the
candidate, and replace the saved file with a same-filesystem atomic rename only after
the check passes. If the candidate fails, remove it and leave the last valid file
untouched. Validation checks form and required references, not whether a remote
reference is reachable or whether a summary preserves its meaning; the coordinator
remains responsible for those checks.
