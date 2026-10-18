# Evaluation report: <question>

[English](evaluation-report.md) · [Русский](../translations/ru/templates/evaluation-report.md) · [Deutsch](../translations/de/templates/evaluation-report.md) · [简体中文](../translations/zh-CN/templates/evaluation-report.md)

State: <partial/completed/stopped>. Owner/date: <value>. Plan/evidence: <references>.

## Result

Separate measured outcomes, expert assessment and proposed explanations.

| Attempt | Completion | Acceptance | Seconds | Uncached / cached / output tokens | Cost and basis | Evidence |
|---|---|---|---:|---|---|---|
| <ID> | <result> | <passed/total or not run> | <value> | <values or unavailable> | <estimate/bill/unavailable> | <reference> |

Include failed attempts and interventions. A zero exit code does not prove completion.
Keep setup and independent acceptance timing separate from execution time.

## Routing and interpretation

Record actual root/child models, reasoning, context transfer, required review layers,
checks and unresolved findings. Distinguish application defects, harness corrections,
workflow failures and duplicated work. List configured-but-unused roles.

For repeated comparisons, report acceptance rate, successful-run time/cost median
and range, and total attempt cost per accepted completion. Explain cache/environment
confounders and missing usage; do not infer causal savings from one pair.
Use the [testing definitions](../testing.md) and [evaluation protocol](../../EVALUATION.md).
