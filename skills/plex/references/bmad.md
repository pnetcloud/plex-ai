# BMad coordination

Plex coordinates bounded assignments using actual installed BMad skills. Resolve
skills through the host's active inventory; missing or tied copies are blockers.

| Role | Required installed skill(s) | Assignment |
| --- | --- | --- |
| analyst | bmad-agent-analyst | Research and briefs |
| pm | bmad-agent-pm | Requirements and requested framing audits |
| ux | bmad-agent-ux-designer | UX and interaction design |
| architect | bmad-agent-architect | Architecture and requested framing audits |
| dev | bmad-agent-dev, bmad-build | Implementation and its required verification |
| reviewer | bmad-code-review | Independent review of an explicit target |
| qa | bmad-qa-generate-e2e-tests | Explicit API/E2E test generation |

Read and follow the installed skill's activation, customization, runtime and workflow
instructions. Resolve actual menu entries, rendering commands, review stages and
references there; do not duplicate version-specific details in this plugin. Supply
an explicit intent, input paths, scope, ownership and acceptance criteria. Dispatch
directly when the installed skill permits; do not ask for a menu choice already
supplied. Return ambiguous assignments to the coordinator.

Use PM or architect when scope or technical assumptions need verification, rather
than before every implementation. If a BMad workflow owns the work, respect its
planning, review and human gates; do not create a competing team or skip its stages.
QA is a test-generation assignment, not a mandatory stage for routine checks.

Only the coordinator assigns work and integrates results. Dependencies between
artifacts do not authorize children to spawn other roles. Nested delegation requires
explicit host and handoff authority. Use a sequential fallback only when the installed
workflow documents one; otherwise report the blocker. Record actual model routing
instead of assuming nested agents follow Plex settings.

Assign one writer per file or artifact. Reviewers may write assigned review artifacts
but must preserve application code. Relay user-owned decisions and unresolved gates
to the coordinator; a recommendation or elapsed time is not approval.

## Workflow ownership and bounded returns

A `dev` assignment can own the entire installed build workflow, including nested
implementation and review. Do not follow it with a second full `reviewer` workflow
unless requested or justified by a concrete verification gap. Return completed
checks/layers and their evidence so the coordinator can make that decision.
Nested reviewer models follow the installed workflow's requirements, not an assumed
mapping to `plex-reviewer`. Do not assign workflow-owning wrappers as leaf reviewers
when that would recursively start the workflow. Report model or concurrency conflicts.

A review handoff identifies the exact diff source, optional spec path, or explicit
no-spec intent. A missing spec argument does not mean permission to choose no-spec.
Keep the user's target; do not scan unrelated stories to find another assignment.
Read additional context only for concrete dependencies or suspected defects.

Use only stages on the selected rendered route. Follow early exits before later
checkpoints; do not import full-route review layers into a shorter route. For a
blocker or gate, cite the reached rendered step and its condition, exact question,
artifact paths and resume context. The coordinator checks that specific evidence,
then relays real questions and actual answers to the same assignment. Missing
resume context is a blocker, not permission to skip a gate. Preserve required cycles.

For evidence-based build reviews without a minimum finding count, use the explicit
project customization described in [BMad review setup](../../plex-setup/references/bmad-review.md).
Until applied and verified in the rendered workflow, installed review prompts remain
authoritative; handoff prose alone does not change them.
