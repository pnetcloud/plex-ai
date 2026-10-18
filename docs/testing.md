# Testing and efficiency

[English](testing.md) · [Русский](translations/ru/testing.md) · [Deutsch](translations/de/testing.md) · [简体中文](translations/zh-CN/testing.md)

## Scope and method

Evidence window: October 16–18, 2026. These are development smoke trials on one
Focus Session task: a responsive local HTML/CSS/JS form, validation, duration summary,
keyboard support, reduced motion and no backend or persistence. Independent Chromium
acceptance used 12 checks; wall time covers agent execution, its checks and reviews,
excluding setup and independent acceptance. Times are rounded to the nearest second.

Tables select retained completed runs, not all attempts or an attempt success rate.
Quota-blocked and workflow-stopped attempts are not counted as completed.
Raw sessions and audit evidence remain outside
this documentation; only reviewed aggregate results are included here.

## Latest Codex results

| Configuration | Time | Total tokens (M) | Estimated USD | Checks |
|---|---|---|---|---|
| pnet Basic | 4:20 | 1.751 | $0.0396 | 12/12 |
| pnet Plus | 6:01 | 1.482 | $0.1799 | 12/12 |
| BMad Basic | 4:56 | 2.007 | $0.0404 | 12/12 |
| BMad Plus | 14:32 | 7.165 | $0.2007 | 12/12 |

## Token accounting

| Configuration | Uncached input | Cached input | Output | Reasoning subset |
|---|---|---|---|---|
| pnet Basic | 106,523 | 1,618,560 | 25,550 | 7,770 |
| pnet Plus | 217,927 | 1,233,280 | 30,712 | 13,421 |
| BMad Basic | 106,604 | 1,878,912 | 21,980 | 7,769 |
| BMad Plus | 238,379 | 6,842,752 | 84,355 | 58,210 |

Tokens are cumulative across model responses and the root's descendants, not the
size of one context. Each thread's own usage is counted once; inherited replay is
excluded. Total = uncached input + cached input + output. Reasoning is already in
output. Recent Codex totals were cross-checked against Tokscale.

## Additional completed trials

| Configuration | Date | Time | Tokens (M) | Estimated USD |
|---|---|---|---|---|
| Codex BMad Pro | 2026-10-16 | 12:34 | 5.947 | $0.1876 |
| Codex BMad Pro+ | 2026-10-16 | 5:13 | 1.651 | $0.7396 |
| Antigravity Claude Pro (Sonnet) | 2026-10-17 | 2:35 | 2.175 | $1.4302 |
| Antigravity Claude Plus (Sonnet) | 2026-10-17 | 3:19 | 2.308 | $1.5214 |
| Antigravity Google Basic (Flash) | 2026-10-17 | 10:50 | 4.760 | $0.1878 |

All listed runs passed 12/12. These older configurations differ from the latest
profiles. Claude Pro here actually used Sonnet, so it is not a completed Opus test.
Quota interruptions do not establish current account limits.

## Quality assessment

The project owner's qualitative assessment is that **BMad Basic is comparable to
pnet Plus in perceived result quality**: roughly one profile step from adding the
methodology. Treat this as an expert observation and a hypothesis for broader testing.
The BMad artifacts include a minimal spec and review triage; the same 12/12 acceptance
score does not measure the perceived quality difference or establish its cause.

Assess UX, completeness, maintainability, residual defects and verification quality
separately from speed/cost, preferably blindly across several tasks and repeated trials.

## Limits and practical implications

- These are individual runs with changing prompts, routes, caching and tooling; no statistical profile/vendor ranking follows.
- Estimates use historical API-equivalent rate snapshots, not current prices, subscription quota or provider bills. Rates in USD per million input/cached/output tokens: Luna 0.10/0.01/0.50; Sol 2/0.10/10; Astra 10/1/50; Sonnet 3/0.30/15; Flash 0.15/0.015/0.60.
- Successful rendering does not prove runtime model selection. BMad's workflow-owned reviewer did not automatically use the standalone reviewer profile. Record actual nested models.
- The latest build resolved a globally installed BMad skill; plugin inventory alone did not identify the active workflow. Pure plugin-only behavior remains unverified.
- Codex trials used isolated profiles and a VM-specific full-access sandbox adaptation. Normal sandbox operation and screen-reader delivery were not established.
- pnet Basic was fastest/cheapest among the four recent completed runs. This does not prove general superiority or that higher tiers always improve results.

Use the [experiment plan](templates/experiment-plan.md) and [report template](templates/evaluation-report.md) for new comparisons.
