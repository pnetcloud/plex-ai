# Changelog

Important changes retained in Plex, grouped by release. Interfaces and configuration
may change before 1.0. Releases through v0.5.4 were previews; v0.5.5 and later are
regular releases.

## [0.18.1] — 2026-10-26

- Use GPT-6.1 Terra for the Codex Pro developer, preserving max reasoning; recommend Terra/medium for Pro coordination and Terra/high for Pro+ in both teams. Other roles and providers retain their settings.

## [0.18.0] — 2026-10-26

- Manage narrow Claude permissions for the installed Plex cache and read-only checkers, preserving personal settings and using existing backups/rollback; uninstall removes only owned rules.
- Refresh existing Claude plugin caches explicitly during setup and use the native installed path instead of the build export. Install Claude BMad skills with `--copy` to preserve the shared Codex copies.
- Pass the verified package path inside Markdown assignment Inputs and resolve role references against it; preserve existing Markdown/JSON compatibility and workflow-owned formats.

## [0.17.1] — 2026-10-26

- Show the current source version and selected target before Plex update downloads or preview; label first installs and unknown current versions explicitly.

## [0.17.0] — 2026-10-26

- Use readable Markdown assignment and response templates with structural validation across both teams. Keep legacy JSON contracts readable, preserve identity/status/evidence checks and client-owned workflow formats.

## [0.16.2] — 2026-10-26

- Correct the concurrent-write migration test for macOS temporary-directory aliases. v0.16.1 was tagged but not published because this test failed in CI.

- Store applied configuration, resolved snapshots and skill-alias receipts in TOML alongside the preset. Automatically migrate legacy JSON with checked backups, rollback, conflict detection and preserved settings; retain read-only legacy support and JSON CLI output.
- Treat coordinator memory as a continuation aid: retain full available session context, accepted requirements and user corrections; checkpoint omissions do not cancel them.

## [0.16.0] — 2026-10-26

- Keep routine execution with Dev/DevOps inside accepted assignments; escalate material changes and continue independent work while acceptance waits. Carry relevant instruction updates to reused agents.
- Use validated Markdown coordinator memory with automatic migration during setup, existing backups/rollback, legacy-path reading and observed format in status. Raise capacity to 32 KiB and 16 decisions, retaining exact owner handles and references.

## [0.15.0] — 2026-10-26

- Record handed-off steps and resume multi-step work from its next action; do not reopen completed work when a later step is blocked.
- Classify by scope and unresolved decision, not labels such as bug or feature: send ready contained work to Dev, product/UX questions to PM/PO and UX as needed, cross-boundary architecture decisions to BMad Architect (pnet PM owns technical planning), and unknown causes to diagnosis.
- End diagnosis when evidence supports a safe repair; avoid repeated pre-test gates and keep production identity/effect checks on actions that can change production state.
- Validate the pinned BMad skill catalog before installation, install only missing skills and preserve valid existing files. Align BMad workflow entries with skills actually present in the pinned source.

## [0.14.0] — 2026-10-25

- Let PM select the minimal suitable BMad route from the complete role-keyed workflow map, with direct entries for PM specifications, PO planning workflows and Dev walkthroughs while retaining existing PO operations.
- Distinguish direct workflow entry from persona/menu dispatch; use accepted requirements, avoid duplicate planning artifacts and preserve the selected workflow's real checks and gates.
- Clarify route choice by interaction mode: interactive choices go through the root coordinator, auto selects independently and balanced behavior stays unchanged.
- Align coordinator, PM, workflow and four-language guide contracts without changing pnet behavior, assignment schemas, profiles, models or session-state format.

## [0.13.1] — 2026-10-25

- Keep bounded assignments linked to the parent outcome, its terminal owner and delivery check; use representative real inputs when needed.
- Distinguish completed prerequisites from verified delivery in both coordinators.
- Permit supported evidence-method alternatives within the same authority and scope while retaining acceptance, required checks and real permission boundaries.
- Preserve valid evidence and provenance when the same author corrects a malformed response; avoid repeating unchanged work.
- Clarify existing guidance in English, Russian, German and Simplified Chinese without changing assignment fields, session state, roles, models or BMad workflows.

## [0.13.0] — 2026-10-25

- Add bounded coordinator session state with a shared template, an 8192-byte UTF-8 ceiling, field/count limits and a read-only validator.
- Keep the current goal and user decisions visible, queue unrelated requests, and require PM intake before routing or execution; default to at most two active independent outcomes.
- Compact state through retrievable references without silently dropping unfinished work; workers receive scoped assignments rather than the global queue.
- Add a native DevOps specialist to both teams for assigned CI/CD, releases and deployment work, preserving separate publication/deployment authority.
- Apply the revised BMad OpenAI specialist reasoning and Pro+/Ultra coordinator recommendations; document provider-specific profile policies.
- Keep checkpoint data local and preserve it across configuration maintenance. Structural checks do not prove live efficiency or semantic preservation.

## [0.12.3] — 2026-10-24

- Align coordinator recommendations across both teams and all four provider recipes: lightweight models through Pro+, then Sol/Sonnet or the inherited Google model for Ultra tiers.
- Set Plus to high, Pro to xhigh, Pro+ to max and Ultra to low reasoning; Basic and Ultra+ recommendations remain unchanged.
- Keep subagent models, reasoning, profile IDs and the running main-chat model unchanged.

## [0.12.2] — 2026-10-24

- Include the Reconfigure role-replacement fix prepared for v0.12.1, whose publication was blocked by CI.
- Isolate the new Reconfigure test from local BMad runtime availability so it exercises the same behavior on clean runners.

## [0.12.1] — 2026-10-24

- Let interactive Reconfigure regenerate edited receipt-owned roles from the selected profile and preset overrides, instead of stopping before the installation plan.
- Show affected paths, verify backups of previewed content and reject edits after preview. Update only, unmanaged files, symlinks, instruction blocks and client configuration retain their conflict protection.
- Cover Pro to Pro+ switching with edited Dev/Reviewer/UX roles, preview/cancellation, ownership, concurrency and team-switch archives.

## [0.12.0] — 2026-10-24

- Add Ultra and Ultra+ to both pnet and BMad across all four provider recipes and shared client setup.
- Rebalance Plus/Pro for lightweight execution, use Sol/Sonnet development and review in Pro+, and move Astra/Opus specialists to Ultra; Ultra+ increases reasoning effort.
- Put main-chat coordinator recommendations first within each tier and keep PM/PO settings independent; explorer and QA retain role-specific settings in pnet.
- Derive setup guidance from the selected team's catalog; update profile menus, four-language documentation and regression checks.
- Existing profile IDs remain valid, but their model settings can change on refresh. Preview effective settings and preserve project overrides; main-chat models are never switched automatically.

## [0.11.1] — 2026-10-23

- Include the native Codex capacity management prepared for v0.11.0, whose release publication was blocked by CI.
- Correct dev-mode lifecycle test expectations for managed capacity and retained table headers, and isolate configuration inputs from the operator environment.

## [0.11.0] — 2026-10-23

- Configure native Codex child-thread capacity from Plex `max_agents` when no explicit limit applies.
- Preserve explicit canonical, legacy and observed inherited limits; reject invalid or conflicting values and avoid automatic writes when profile or inherited-layer applicability is uncertain.
- Reuse managed configuration transactions, backups, refresh and uninstall, preserving manual edits and existing routing receipts.
- Clarify the separate Plex assignment and native thread limits, saved settings and unknown session activation in setup, status and skills.

## [0.10.1] — 2026-10-22

- Clarify the existing blocker check: verify its source and applicability before
  escalation. Optional agent-selected methods do not become prerequisites.
- Keep alternative methods with the owning specialist and preserve acceptance,
  permissions and required checks. No configuration or response-schema changes.

## [0.10.0] — 2026-10-22

- Add validated subagent responses tied to assignment identity and revision, with evidence for every completion criterion.
- Distinguish progress, decision requests, blockers and completion; route help to the decision owner and resume the same executor with changed inputs or evidence.
- Preserve legacy assignment validation and BMad-owned leaf formats; add event-driven progress without timers or automatic model changes.
- Update both teams, managed instructions and role-contract documentation in four languages. Refresh and open a new client session to load the new contracts.

## [0.9.1] — 2026-10-22

- Clarify agent orchestration, coordinator responsibilities and Interactive/Balanced/Auto modes in all four READMEs.
- Show Basic/Plus/Pro/Pro+ development and review models by client, including BMad differences and model identifiers.
- Document the maintainer release-skill requirement; runtime behavior and project configuration are unchanged.

## [0.9.0] — 2026-10-22

- Remove Plex token-budget settings and assignment checks. Existing presets remain
  readable; refresh removes retired fields while preserving team settings and overrides.
- Remove budget instructions from managers and workers; keep acceptance criteria,
  actual host restrictions and the concurrent-assignment limit.

## [0.8.1] — 2026-10-22

- Omit `sandbox_mode` from generated Codex roles; keep `approval_policy` unset.
  Subagents inherit permissions and MCP servers from the parent session.
- Clarify that read-only Codex roles express behavioral boundaries, not a separate
  sandbox. Preserve Claude Code and Antigravity tool restrictions.
- Verify refresh of older receipt-owned roles removes the sandbox field, preserves
  parent permissions and remains idempotent; retain conflict checks for local edits.

## [0.8.0] — 2026-10-22

- Remove Plex's default 50,000-token Goal budget. Coordinator and subagent budgets
  default to `0` (or may be omitted), so Plex does not set a native token cap.
- Add `coordinator_token_budget` and `subagent_token_budget` to `.plex/preset.toml`;
  positive values request a cap for that role, while `0` keeps it unset.
- Accept Goal assignments without a budget when the project setting is unset or `0`;
  preserve validation and explicit positive budgets.
- Update all native plugin manifests to v0.8.0.

## [0.7.2] — 2026-10-22

- Replace the small README image with a larger dark-mineral banner using the
  approved Triad mark; keep the original reference asset unchanged.
- Synchronize the English, Russian, German and Chinese README artwork and release
  navigation.
- Update all native plugin manifests to v0.7.2.

## [0.7.1] — 2026-10-22

- State the active-development and evaluation status, client verification limits
  and installation prerequisites on all four project READMEs.

## [0.7.0] — 2026-10-21

- Let PM/PO select normal execution, planning first or bounded work toward a goal,
  with one to five observable acceptance criteria. Native Plan/Goal modes are optional;
  unsupported modes retain ordinary planning or criteria-driven execution.
- Add a compact assignment template and read-only JSON validator against the checked
  team's role snapshot. Preserve existing task stores and workflow-owned leaf recipes.
- Support installed `bmad-build-auto` for one unattended iteration, preserving its
  renderer, required subagents and terminal protocol without a repeating outer loop.
- Reuse role context and pass changed evidence and decisions between dependent
  assignments. Native Goal requests default to 50,000 tokens without automatic renewal;
  report when the host cannot enforce that budget.
- Separate unfinished-assignment limits from native thread slots. Preserve exact
  artifact paths/revisions and correct missing inputs before accepting verification.

## [0.6.1] — 2026-10-21

- Require a real `plex-pm` intake assessment for every new Plex task and unplanned
  subtask. Root collects inputs and schedules the assessed route; it does not judge
  complexity or implementation readiness, or replace missing specialists locally.
- Keep intake short and role-local in both teams. It does not activate BMad, a
  persona menu or a PRD; assigned BMad domain work retains its activation contract.
- Use the project's existing task/spec/issue format. Collect required specialist
  decisions before dev; reuse assessments for covered steps and unchanged continuation.
- Update coordinator handoffs, PM role sources, managed instructions and four-language
  documentation to make the planning result a prerequisite, not a user approval gate.

## [0.6.0] — 2026-10-21

- Continue authorized work in dirty trees while preserving pre-existing changes,
  including unrelated hunks in assigned files. Pass this authorization to BMad;
  retain real scope, production and review restrictions without automatic worktrees,
  stash, cleanup or commits.
- Expose native Codex role selection through receipt-owned configuration, with
  backups, conflict detection, rollback and uninstall. Preserve personal settings.
- Distinguish hidden role selection from missing roles; request exact native roles
  with fresh bounded context and verify accepted dispatch separately from models.
- Structure managed instructions into concise blocks; refresh existing installations
  and open a new session to load the updated instructions and role controls.
- Present Plex AI by pNet with the approved Triad reference, live release/CI/license
  badges, a compact workflow diagram and clearer documentation navigation.

## [0.5.11] — 2026-10-21

- Pin macOS CI to macos-15-intel after ARM hosted-runner allocation failed before
  tests started; retain both Python versions, Linux, Docker and all release gates.

- Default the final setup/refresh confirmation to Yes; retain explicit cancellation
  and separate opt-in for uninstall or archiving other agents.
- Gate CI and releases on local documentation links and a clean Docker installation
  lifecycle for all clients/scopes, without uv, client CLIs or model calls.
- Make native subagent delegation explicit in the coordinator role and managed
  instructions; retain local coordination and small mechanical actions, and resume
  that division of work after follow-ups or context compaction.

## [0.5.9] — 2026-10-21

- Restrict Plex-owned dispatch to exact native roles in the checked active team;
  exclude unrelated, built-in and stale roles while preserving workflow-owned leaves.
- Detect other Codex agents during setup; keep them by default and offer explicit
  backup/removal in the selected scope, with rollback and preview hash checks.
- Preserve symlinks, explicit config.toml registrations, managed roles and other scopes.

## [0.5.8] — 2026-10-21

- Consolidate installation guides and translated project READMEs under docs; keep
  one root README with language links and update documentation navigation.
- Add short Codex skill names `$plex` and `$plex-setup` in project and user scope
  through managed links to the shared checkout, without copying skill contents.
- Check link ownership during refresh, status and uninstall; preserve foreign skills
  and roll back owned links when role setup fails. Keep dev mode and roles-only setup.

## [0.5.7] — 2026-10-21

- Align coordinator instructions with the subagent blocks; preserve routing,
  activation evidence, gates, ownership and recovery rules in concise sections.
- Add CONTRIBUTING.md as the entrypoint to existing authoring and verification
  guidance; use one documented format for coordinators and subagents.

## [0.5.6] — 2026-10-21

- Require BMad entry activation and workflow-entry evidence in role startup and
  final returns. Distinguish persona owners, direct review and workflow-owned leaves.
- Keep Build's investigation, planning and review inside Build; consult planning
  specialists for unresolved upstream decisions instead of duplicating its pipeline.
- Record concise, explicit instruction-authoring rules in the tracked AGENTS.md.
- Rewrite Plex skill guidance as short rules, steps and tables; preserve activation,
  native-role routing, task flows, interaction modes and configuration safeguards.
- Require a visible task-flow selection at Plex intake; provide routes for bounded
  changes, substantial new work, diagnosis and standalone review. Delegate missing
  requirements, specifications and architecture to their owning roles before dev,
  while reusing accepted decisions and preserving workflow-owned verification.

## [0.5.5] — 2026-10-21

- Publish regular GitHub releases without the prerelease flag or Preview title.
- Select Claude Code native roles through `subagent_type`; label tasks through
  `description` and handoffs without using `name`, which can launch an Agent Teams teammate.
- Render `disallowedTools: Agent` for Claude roles with delegation disabled;
  preserve BMad roles' conditional nested delegation.
- Add isolated native Claude package validation, plugin installation and both-team
  apply/check coverage without model calls. Document Claude chat syntax in all four languages.
- Restructure READMEs around installation, a short coordination diagram, abstract
  chat requests, team settings and maintenance; explain shared plugins versus team setup.
- Document project/user team removal separately from shared plugin removal for all
  three clients, including retained settings and backups. Update all four languages.

## [0.5.4] — 2026-10-21

- Put native-role dispatch and Plex/role/task labels at the start of coordination
  instructions; report unavailable routing instead of silently using generic agents.
- Read instruction documents separately and recover truncated sections before
  delegation; move detailed BMad workflow rules into a separately loaded contract.
- Keep current assignment labels visible when reusing agents; task names do not
  replace native role selection or rename host-assigned nicknames.

## [0.5.3] — 2026-10-21

- Separate the main-chat coordinator recommendation from subagent settings in
  setup; read tier-specific recommendations from model profiles, keep the root
  model under the user's control and shorten profile menus.
- Recommend Codex coordinators by profile: Basic Luna/high, Plus Sol/low,
  Pro Sol/medium and Pro+ Sol/high; leave `inherit` to the session choice.
- Fix spacing between CLI labels and values; explain coordinator responsibilities
  and model selection in all four documentation languages.

## [0.5.2] — 2026-10-20

- Simplify Quick start to standard and Codex `--dev` installation commands; remove
  demo-directory scaffolding and move prerequisites to the installation guide.
- Reorganize installation documentation around command scenarios, dev/BMad setup,
  grouped options and troubleshooting; shorten the guide by about half in all four languages.
- Document the source-checkout entrypoint when the optional `plex` shortcut is absent,
  including fresh dev installations. Installer behavior is unchanged.

## [0.5.1] — 2026-10-20

- Restyle CLI setup, status, source updates, removal and help with consistent
  sections, model tables, command highlights and terminal-aware colors. Keep
  redirected/NO_COLOR output plain and JSON responses free of decoration.
- Show compact instruction-file summaries instead of dumping the full template;
  make removal output human-readable by default, with `--json` for automation.

## [0.5.0] — 2026-10-20

- Detect existing team installations and offer update-only or reconfiguration;
  preserve saved settings, legacy profile IDs and per-client instruction choices
  during refresh, using existing compatibility and conflict checks.
- Offer interaction-mode selection in interactive setup and explicitly save it in
  every applied preset, preserving saved modes and upgrading older configurations.
- Use `plex:managed:start/end` instruction markers and migrate unchanged owned
  blocks with legacy markers during refresh.
- Add Codex project `--dev` setup with live links to the working Plex skills,
  a project-only plugin override, explicit local-source instructions, source status
  and owned cleanup through `--no-dev` or uninstall.
- Publish a dedicated installation and CLI reference with English, Russian, German
  and Chinese versions, linked from every root README.

## [0.4.0] — 2026-10-20

- Offer explicit user-wide installation of selected official BMad skills for Codex,
  Claude Code and Antigravity, using a verified revision that includes PO; keep existing
  plugins unchanged and verify all required skills after installation.
- Offer official BMad project initialization when its runtime is missing, with
  module questions, explicit unattended flags and a pnet/cancel alternative.

## [0.3.1] — 2026-10-20

- Continue setup when the optional `plex` command belongs to another checkout or
  is an existing foreign file/link; preserve it instead of blocking project setup.

## [0.3.0] — 2026-10-20

- Add `interactive`, `balanced` (default) and `auto` interaction modes with saved
  configuration and setup flags. Route questions through the coordinator and use
  supported BMad headless contracts without bypassing required checks or authority.
- Add a described, per-role BMad workflow catalog in `team.toml` and resolved
  snapshots, including internal PO operation codes, for explicit coordinator dispatch.
- Keep one Markdown source per agent within each team. Compile native Codex,
  Claude Code and Antigravity roles during setup, preserving instructions, model
  settings and tool permissions without maintaining three copies.

## [0.2.0] — 2026-10-18

- Add a one-command GitHub installer with interactive terminal support and a
  shorter quick start in all four README languages.
- Install and update from published releases, including previews. Support pinned
  releases and explicit development builds; refuse updates to dirty or unrelated
  source checkouts.
- Add `plex status` with human-readable and JSON output for version, scope,
  team/profile, native roles, plugin discovery and configuration conflicts.
- Add scoped `plex uninstall` with receipt checks, backups and rollback on caught
  failures. Preserve edited or foreign files and instruction blocks still used by
  another client. Shared plugins and the source checkout remain installed.
- Publish portable regression tests and gate releases on Linux/macOS CI with
  Python 3.11 and 3.14. Isolate BMad preflight checks from locally installed clients
  and normalize test fixture paths for macOS.

## [0.1.0] — 2026-10-18

First public preview.

- Provide reusable `plex` and `plex-setup` skills for explicitly invoked agent
  coordination and team configuration.
- Support OpenAI Codex, Anthropic Claude Code and Google Antigravity through
  native plugin packages and agent definitions.
- Add one interactive installer with multi-client selection, project or user
  scope, configuration checks and managed instruction blocks that preserve user
  content.
- Include `pnet` and `bmad` teams with coordinator instructions, role contracts
  and team-specific model profiles under `teams/`. Keep roles separate from model
  choices and use shared Basic, Plus, Pro and Pro+ tiers across clients.
- Integrate existing BMad personas and workflows through dedicated roles. BMad
  skills and project runtime must be installed separately.
- Bound delegated work by ownership, scope and acceptance criteria; reuse completed
  checks and relay BMad user decisions with the context needed to resume.
- Publish English documentation with Russian, German and Simplified Chinese
  translations, plus consolidated benchmark methodology, measurements and
  qualitative findings with their limitations.
- Release under the MIT license with third-party attribution notices.

[0.4.0]: https://github.com/pnetcloud/plex-ai/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/pnetcloud/plex-ai/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/pnetcloud/plex-ai/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pnetcloud/plex-ai/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pnetcloud/plex-ai/releases/tag/v0.1.0
