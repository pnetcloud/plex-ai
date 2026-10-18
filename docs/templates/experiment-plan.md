# Experiment plan: <question>

[English](experiment-plan.md) · [Русский](../translations/ru/templates/experiment-plan.md) · [Deutsch](../translations/de/templates/experiment-plan.md) · [简体中文](../translations/zh-CN/templates/experiment-plan.md)

Owner: <name>. Date/timezone: <value>. Evidence: <directory outside installation>.

## Decision

- Hypothesis and baseline: <one testable question>.
- Candidate: <single change, or disclose combined changes>.
- Acceptance and quality criteria: <independent checks and scoring rubric>.
- Promotion and stop criteria: <choose before running>.

## Frozen inputs

Record task/evaluator hashes, starting tree, exact prompts, Plex/host/skill sources,
profiles and overrides, root/child models and reasoning, context transfer, permissions,
concurrency, tools, usage collector and cost-rate snapshot.

## Procedure

Specify fresh/reset state, trial count/order, timeout, retry and intervention policy.
For comparative claims, use at least three trials per variant/task and alternate order.
Keep failed attempts and deviations; a material change starts a new series.
Record real gates and actual answers rather than inventing approvals.

Keep secrets and private environment details out of reusable summaries.
See [testing](../testing.md) for metric definitions.
