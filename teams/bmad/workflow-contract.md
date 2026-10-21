# BMad workflow execution contract

Plex coordinates bounded assignments using actual installed BMad skills. Resolve
skills through the host's active inventory; missing or tied copies are blockers.

Use the checked team's workflow catalog to select the persona and requested workflow. A persona
adds professional judgment and dispatch; the workflow owns its procedure. Direct
workflow invocation is valid when supported by the assignment and installed skill.
Do not copy personas, menus or version-specific workflow steps into handoffs.

Read and follow the installed skill's activation, customization, runtime and workflow
instructions. Resolve actual menu entries, rendering commands, review stages and
references there; do not duplicate version-specific details in this plugin. Supply
an explicit intent, input paths, scope, ownership and acceptance criteria. Dispatch
directly when the installed skill permits; do not ask for a menu choice already
supplied. Return ambiguous assignments to the coordinator.

Use PM for product requirements, PO for specifications/tickets/replanning, and
architect for technical decisions when needed, rather than before every implementation. If a BMad workflow owns the work, respect its
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

## Activation and entry evidence

| Executor | Required startup |
|---|---|
| analyst, pm, po, ux, architect, dev | Activate entry persona, then dispatch the assigned operation |
| reviewer | Activate the assigned review workflow directly |
| Workflow-owned leaf | Execute the supplied technical recipe; do not restart a persona or parent workflow |

- Resolve the actual installed skill and project customization.
- Execute its activation steps and required resolver/renderer commands. Use a fallback only when that skill documents it.
- Report persona activation after its activation steps complete; report workflow entry after reaching its first applicable step.
- Cite the resolved skill path, workflow/operation, reached step and command/result references. A label or greeting is insufficient.
- Send evidence once available; include it in the final return. Do not wait for acknowledgement.
- Missing/ambiguous skills, renderer failure or `HALT` block that route. Do not run raw workflow templates or install substitutes.
- Build owns its applicable investigation, plan generation, implementation, review and fixes. Upstream planning is input, not permission to skip Build steps.

## Models and nested workers

The root keeps its session model and permissions. Persona executor models and
reasoning come from the checked native configuration. Launch standalone code review
with the dedicated reviewer's configured model, not the cheaper dev model. An
explicit inherit profile keeps host/session defaults; do not silently override it.
If the chosen profile does not provide the requested review capability, report the
mismatch before launching instead of claiming a stronger review model was used. Selecting a persona model
does not establish the model of workers launched inside its workflow.

Where a supported, applied workflow adapter configures nested launch points, use
its resolved model/effort for that stage and preserve the BMad task and context.
Do not invent stage settings absent from the applied configuration, hardcode model
names from an example, or silently substitute another model. Report requested
routing that the host or adapter cannot apply; report inherited execution as inherited.
Implementation handoffs and review-lens recipes are customization points, not proof
that automatic nested routing is already installed.

In build `full`, a separate implementation worker can use a separate model/context;
in `oneshot`, implementation remains in the workflow owner's session. Model selection
occurs at agent launch, not as an assumed switch within an existing session.

Nested implementation and review workers are technical executors, not persona
sessions. Never dispatch implementation to a wrapper that restarts `bmad-build`,
or a review lens to a wrapper that restarts `bmad-code-review`. Keep the workflow's
leaf prompt, permissions and model requirements. When it requests a fix from the
same implementation worker, resume that worker rather than launching a new workflow.

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

Use only stages on the selected rendered route; do not import full-route review
layers into a shorter route. Apply the question/early-exit check in the coordinator's Quality checks
before relaying a gate. Returns cite the reached step and condition, exact question,
artifact paths and resume context. Preserve required cycles and real human gates;
missing resume context is a blocker, not permission to skip one.

For evidence-based build reviews without a minimum finding count, use `plex-setup`
and its `references/bmad-review.md` for the explicit project customization.
Until applied and verified in the rendered workflow, installed review prompts remain
authoritative; handoff prose alone does not change them.
