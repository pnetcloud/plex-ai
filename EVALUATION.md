# Plex evaluation

See [testing and efficiency](docs/testing.md) for the compiled results and measurement limits.

Use the [experiment plan](docs/templates/experiment-plan.md) before a live
comparison and the [evaluation report](docs/templates/evaluation-report.md) after
it. Store completed plans, reports and evidence outside the installed plugin.
The templates define a reporting contract, not an automatic benchmark runner.

## What is verified now

`tests/test_package.py` checks native metadata, presets, host role identities,
model inheritance, a real local Codex plugin installation in a disposable profile,
and `codex doctor --json` validation of rendered `.codex/agents/plex-*.toml` role
definitions. `tests/test_config.py` checks all team/profile pairs (including
`inherit`, `openai-plus`, `openai-pro`, `anthropic-pro`), field precedence, switch
preservation, inactive overrides, legacy configs, invalid inputs, deterministic
role rendering (`render`), read-only status checks (`check`), atomic application
with backups and SHA-256 receipts (`apply`), conflict detection, and independent
dual-host receipts. Neither executes an LLM or proves live orchestration quality.

## Behavior before performance

Run `plex-setup` and `plex` through each actual host in a disposable project. Keep
the starting tree and a full post-run diff. Verify:

| Scenario | Required observation |
| --- | --- |
| Fresh pnet setup | Only selected native roles, project preset and receipt created; unrelated files unchanged |
| Second setup | No change to role contents or preset; `resolve_config.py check` reports `in_sync` |
| Host and role model overrides | Rendered native fields agree; root and global settings unchanged |
| Team/profile resolution | Snapshot matches resolver output and source hash; native roles match final host settings |
| Edited source before refresh | Plex reports stale snapshot before dispatching any role |
| Profile switch with overrides | Team and personal overrides preserved; remaining values follow new profile |
| Team switch with role overrides | Profile preserved; absent-role overrides reported inactive and restored when role returns |
| Reset overrides / inherit profile | Explicit reset clears overrides; obsolete native model/reasoning fields disappear |
| Plugin definition update | Running tasks use applied snapshot; refresh shows definition changes before applying |
| Foreign file or local role edit | Conflict reported; existing contents preserved |
| Symlink destination or concurrent edit | No write through link and no overwrite of newer data |
| BMad unavailable | No BMad role setup and no automatic installation or plain fallback |
| BMad available & dispatch | Subagents follow the installed skills' actual activation and workflow; explicit handoffs avoid redundant menu selection without bypassing gates |
| Selective framing | Clear bounded work skips PM/architect; ambiguous scope or cross-component invariants receive a framing audit before implementation |
| Caught write failure | Previous managed state restored and retry succeeds; concurrent edits are preserved and unresolved recovery paths reported |
| Overlapping applies | Second apply refuses the held lock without changing configuration |
| List presets or check settings | Available presets and desired/applied settings shown; no writes |
| Switch pnet to BMad and back | New preset applied; unchanged owned deselected roles archived outside discovery in `.plex/backups/`; settings backed up |
| Switch with missing prerequisites or a modified old role | Preflight fails; working preset and roles preserved |
| Both hosts in one project | Each host's receipt and native files survive the other's refresh; stale host reported after shared preset changes |
| Workflow human gate | Execution pauses and resumes only after an actual user answer |
| Bounded handoff | Supplied files/diff, exclusions, ownership and acceptance survive delegation; unrelated defects are reported without expanded edits |
| Configuration preflight | One check before first dispatch; repeat only after changed configuration or evidence of drift |
| Already reviewed build | Completed build review evidence does not trigger another full review automatically; extra review names its concrete reason |
| Correction pass | Fixes receive focused verification; unchanged results do not restart full review; repeated unresolved findings are reported |
| Nested workflow routing | Leaf reviewers do not re-enter workflow-owning roles; actual nested models and observable concurrency are recorded, conflicts reported |
| Resumed BMad gate | Exact question and resume context reach the coordinator; actual user answer resumes the same assignment without repeating completed steps |
| BMad review artifacts | Assigned reports may change; application code remains unchanged |
| BMad route applicability | A fully specified small oneshot takes its early exit; no dispatch-only checkpoint or extra review layer is imported |
| Initial artifact authority | Developer can create required workflow spec and authorized check artifacts without negotiating application ownership again |
| Reported workflow blocker | Coordinator checks the cited reached rendered step before relaying a gate; real gates still pause |
| Optional review customization | Installed schema accepts both overrides, rendered full/oneshot layer sets remain intact, zero material findings is allowed; personal policy conflicts are reported |
| Source and product scope | Source is readable and unminified, follows local conventions and contains no unrequested features, fields or branding |
| Reproducible verification | Existing checks are reused or one runnable check is retained; harness errors are distinguished from application defects |

Record failed cases as failed, fix the demonstrated cause and repeat that case.
These are required live scenarios, not assertions that they already passed.

For fresh versus inherited handoffs, run a separate paired experiment. Keep native
role instructions/model routing, task, checks and review policy fixed; pass all
constraints and verified environment facts in the fresh handoff. Record the actual
host context-transfer option and verify that constraints survive before comparing
tokens. A short message with full history inheritance is not a fresh context.
Do not combine a context change and a review-policy change into a savings claim.

## Compare orchestration approaches

Use the same frozen task inputs and clean starting revisions. Compare:
1. Single flagship agent vs Plex `pnet` (with flagship Coordinator vs lightweight
   Luna/Sonnet Coordinator + flagship `pm`/`architect`/`reviewer` Framing Loop).
2. For BMad tasks, compare running the installed BMad workflow directly vs Plex `bmad`
   with `openai-plus` / `openai-pro` / `anthropic-pro`.

Keep provider versions, available skills, permissions, task acceptance checks and
machine conditions fixed. Record both the Coordinator's root model/reasoning and
subagent models as part of each approach.

Start with a small local fix, a change spanning several components, and a BMad
artifact-led change. Write acceptance checks before running either approach and
do not expose the hidden checks as implementation hints. Run at least three fresh
trials per approach/task, alternate execution order and record unsuccessful runs.

For every run record task and starting revision, host/plugin/preset versions,
effective models and reasoning, actual agent handoffs, acceptance pass/fail,
out-of-scope edits, elapsed time, input/output/cached tokens, reported cost,
human interventions and retries. Use unavailable for missing usage or cost data;
do not estimate it from role names or assume nested agents used preset models.

Keep raw evidence and reports outside the plugin installation and exclude secrets.
Compare correctness first, then time and resource use for successful runs; also
report failure rates and the cost of failed attempts. A fast failing run is not
an efficiency gain. Preserve the results that contradict the preferred approach.

## Repeatable experiments for profiles and coordination

Separate three kinds of verification:

1. **Package regression:** run the affected existing automated tests. These check
   configuration and rendering without model execution.
2. **Live behavior:** verify actual role routing, handoff preservation and workflow
   adherence on the affected host. A rendered setting alone does not prove routing.
3. **Comparative evaluation:** measure outcomes against a frozen baseline across
   repeated runs. A smoke pair can reveal a problem; it cannot rank profiles.

Before a run, freeze the task, starting tree, acceptance evaluator, exact prompts,
Plex/host/workflow versions, rendered configuration and effective role settings.
Keep an artifact hash manifest. Without a Git revision, retain a source snapshot
and hashes. Pin the available verification tools and worker-facing check commands
so rediscovering the environment is not an accidental experimental variable.
Keep independent acceptance separate from the checks supplied to the worker.

Declare one primary measure and quality gates in advance. The default cost
measure is total attempt cost divided by independently accepted completions,
including failed attempts; it is undefined when no attempt succeeds. Also report
success fraction, per-run cost and elapsed time, and successful-run medians and
ranges. Report out-of-scope edits and workflow violations separately, even when
application checks pass. Record unavailable measures explicitly.

Alternate A/B and B/A order in fresh projects and sessions, with at least three
trials per variant/task. Three is a screening minimum, not evidence of statistical
significance. Predeclare timeout, retry and intervention policy; retain timeouts,
blocks and failures. A changed task, evaluator, policy or environment starts a new
comparison series. Preserve the previous series and explain the change.

### Diagnose the extra work before upgrading a model

Capture each delegation as an evidence-linked event: parent/child ID, role,
actual model/reasoning, context-transfer mode, triggering question, supplied
evidence, returned result and the downstream decision it informed. Record whether
it produced new information, repeated a known fact, found a defect, or returned
no actionable result; mark uncertain assessments as unknown.

Distinguish requirement ambiguity, missing handoff context, workflow-mandated
work, optional discovery, model/runtime failure, application defect, and verifier
failure. Include the exact handoff and response before assigning a cause.
A higher-cost call is not automatically wasted; an additional call may prevent
a correctness failure. Conversely, configuring a stronger unused role explains
none of a run's observed behavior.

Use a bounded framing request when testing PM/architect coordination:

> Decide whether the supplied implementation contract has a concrete design
> blocker. Read the listed inputs and verified findings first. Return the blocker
> with file evidence and the smallest decision needed, or state that implementation
> can proceed. Identify only relevant invariants and ownership changes. Trace further
> dependencies only when evidence requires it. Do not repeat completed discovery
> without a conflict or changed inputs. Return new findings and remaining uncertainty.

Supply the actual task-specific inputs, ownership, acceptance and known facts with
this request. Preserve installed workflow requirements and real human gates.
This is an experimental handoff example, not a replacement for runtime instructions.

### Isolate the variable

| Question | Change in candidate | Keep fixed |
| --- | --- | --- |
| Does a better handoff reduce repeated discovery? | Handoff context and bounded question | Models, reasoning, role policy, task and evaluator |
| Does PM reasoning improve the implementation contract? | PM reasoning by one supported level | PM model, handoff and all other roles |
| Does architect reasoning improve design decisions? | Architect reasoning by one supported level | Architect model and identical decision inputs |
| Does a stronger model help? | One role's model, with compatible reasoning recorded | Task, handoff, workflow and other role settings |
| Does selective delegation help overall? | Coordinator's delegation policy | Role settings, inputs and acceptance |

Model reasoning levels are host-specific; record the exact accepted value and do
not assume levels are equivalent across models. If changing a model requires a
different reasoning setting, label it a combined treatment.

Start from the current applied baseline. Test handoff quality first when logs show
repeated discovery; test PM and architect reasoning independently afterward.
Use both a clear task and a task with a real design decision. For a role-level
probe, give the role identical frozen inputs and score its decision separately.
For an end-to-end test, keep selective delegation active and record invocation
rates. If the architect never runs, the trial cannot evaluate architect quality.

Promote a candidate only against the predeclared quality gates and resource/time
criteria. Report inconclusive results as inconclusive. Preserve the baseline for
rollback and verify the promoted configuration with affected package and live
routing checks. Do not change default profiles on the strength of one cheap run.
