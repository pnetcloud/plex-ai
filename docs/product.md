# About Plex

[English](product.md) · [Русский](translations/ru/product.md) · [Deutsch](translations/de/product.md) · [简体中文](translations/zh-CN/product.md)

**Compose your team. Coordinate the work.**

Plex is an agent harness for software development with OpenAI Codex, Anthropic
Claude Code and Google Antigravity. It combines reusable skills, native agent
roles, team configuration and model profiles inside the host you already use.
The name comes from *multiplex*: several contributions sharing one coordinated process.

## Purpose

A team needs clear assignments, relevant context, exclusive write ownership and
checks that establish whether the result works. Plex makes those responsibilities
inspectable and repeatable across projects.

Orchestration selects roles and orders dependent work. Coordination keeps those
roles aligned and integrates their results. The harness supplies their reusable configuration.

## Working principles

- Delegate useful work with a bounded outcome and explicit ownership.
- Keep roles separate from model choices; retain the root's session settings.
- Use only the capabilities the task needs. A team is not a mandatory sequence.
- Preserve project instructions, host permissions and genuine user decisions.
- Verify behavior and actual routing before claiming quality, speed or savings.

## Two operations

1. **Configure:** use the checkout installer or `plex-setup` to install shared
   skills and apply a team/profile at project or user scope.
2. **Coordinate:** explicitly invoke `plex` for work that benefits from a team.
   Installation and task complexity alone do not activate coordination.

`pnet` works independently. `bmad` activates existing BMad personas and workflows;
BMad owns their planning, implementation, review and applicable checkpoints.

## The main chat and the team

The **root coordinator is your current chat**. Invoke `plex` there with the task,
constraints and expected result. PM first assesses the task and selects the
approach and required roles. The root
supplies context, orders dependencies and integrates verified results. PM/PO owns
framing and acceptance; subagents do bounded work. Other roles follow the assessment,
rather than a fixed checklist. Native Plan/Goal modes are optional execution aids.

Choose the main chat's model in your client. Setup shows the selected profile's recommendation
for coordination; it does not set or switch that model. Recommendations can differ
in both model and reasoning between tiers. `inherit` keeps the session choice
without a specific recommendation. Lightweight execution models
can still do the implementation while the root handles coordination.

The selected profile configures **subagents only**. The installation plan separates
the main-chat recommendation from their effective model settings, including local
overrides. A role set to `inherit` follows client/session defaults, so the main-chat
choice can also affect those children. Recommendations describe a starting setup,
not a measured optimum for quality or cost.

See [role responsibilities](role-contracts.md#responsibilities) and
[installation](installation.md).

## Scope

Plex has no separate daemon or UI. It installs selected BMad skill dependencies only with explicit authorization. It does not replace BMad workflows,
deploy applications or guarantee model routing for workflow-owned children.
Gemini models through Antigravity do not imply Gemini CLI support.

See [configuration](configuration.md), [compatibility](host-compatibility.md) and
[measured results](testing.md).
