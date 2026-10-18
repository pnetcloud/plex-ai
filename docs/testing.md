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

## Test procedure

1. Copy the frozen Focus Session task into a fresh disposable project. Apply the chosen team/profile and preserve source/configuration snapshots. No previous application is reused.
2. Start the native client with a recorded root assignment and a 900-second run limit. Let implementation, required review and corrections finish without injecting the acceptance script.
3. Audit actual child models, context transfer, workflow branches and completion. A CLI exit code of zero is insufficient.
4. Run independent browser acceptance on a local loopback server, inspect desktop and 360px mobile screenshots, and retain commands/results.
5. Collect own-thread usage, historical cost estimates, activity and source hashes. Separate implementation defects, coordination failures and harness repairs.

The latest Codex trials used Codex CLI 0.163.0, Python 3.14.3 and headed cached Chromium under Xvfb. BMad plugin inventory reported 6.13.0-next; the latest active build came from a global skill without an exact version manifest. It was verified by source hashes. Profile names are labels of frozen settings, not guarantees about the present catalog.

The task required plain HTML/CSS/JavaScript; Name (trimmed, at least two characters), valid Email, and 25/50-minute Duration; field errors; a local confirmation retaining form values; no backend, storage, dependencies or external requests. All completed runs used the same twelve acceptance categories:

| # | Independent acceptance |
|---|---|
| 1 | Structure and accessible labels |
| 2 | Blank-form validation |
| 3 | Field errors associated with inputs |
| 4 | Invalid name and email |
| 5 | Trimmed-name validation |
| 6 | Valid confirmation, retained values and no persistence |
| 7 | Live duration summary |
| 8 | Actual keyboard submission and focus |
| 9 | Layout at 360px without horizontal overflow |
| 10 | Reduced-motion preference |
| 11 | No JavaScript errors |
| 12 | No external requests |

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

Estimated USD is summed per actual model as `(uncached input × input rate + cached input × cache rate + output × output rate) / 1,000,000`. Historical rates appear below; reasoning output is not billed a second time in this calculation.

## Descriptive statistics

Each latest configuration has **n = 1 completed run**. The following changes compare those individual observations; the denominator is the configuration after `/`. A negative number means less time, lower cost or fewer tokens. These are not estimated average treatment effects.

| Comparison | Time change | Cost change | Token change |
|---|---|---|---|
| BMad Basic / pnet Basic | +13.8% | +2.1% | +14.7% |
| BMad Plus / pnet Plus | +141.5% | +11.6% | +383.5% |
| BMad Basic / pnet Plus | -18.0% | -77.5% | +35.5% |

| Configuration | Cached share of input | Threads incl. root |
|---|---|---|
| pnet Basic | 93.8% | 4 |
| pnet Plus | 85.0% | 4 |
| BMad Basic | 94.6% | 3 |
| BMad Plus | 96.6% | 4 |

BMad Basic used **77.5% less estimated cost** and **18.0% less time** than pnet Plus in this pair, while producing a result the owner judged comparable. It nevertheless used 35.5% more total tokens. Different model rates and cache reuse explain why raw tokens cannot substitute for cost.

BMad Plus took 2.41× the pnet Plus time for 1.12× the estimated cost. This alone does not identify the cause: reasoning, investigation, reviews, context and cached reuse differed. Cache percentages are cached input / all input; thread counts include the root, not the concurrency peak.

No within-configuration variance, confidence intervals, significance test or general success probability can be estimated from these one-off configurations. Pooling revisions would mix different treatments. The twelve checks are assertions on one task, not twelve independent task trials.

## Historical completed trials

| Configuration | Date | Time | Tokens (M) | Estimated USD |
|---|---|---|---|---|
| Codex BMad Basic | 2026-10-16 | 6:26 | 2.882 | $0.0669 |
| Codex BMad Plus | 2026-10-16 | 12:40 | 3.945 | $0.1508 |
| Codex BMad Pro+ | 2026-10-16 | 5:13 | 1.651 | $0.7396 |
| Codex BMad Pro (rev. 1) | 2026-10-16 | 7:58 | 2.865 | $0.1338 |
| Codex BMad Plus (rev. 2) | 2026-10-16 | 9:52 | 3.587 | $0.2232 |
| Codex BMad Pro (rev. 2) | 2026-10-16 | 7:47 | 3.526 | $0.1438 |
| Codex BMad Plus (rev. 3) | 2026-10-16 | 8:45 | 4.448 | $0.1525 |
| Codex BMad Pro (rev. 3) | 2026-10-16 | 12:34 | 5.947 | $0.1876 |
| Antigravity Claude Plus (Sonnet) | 2026-10-17 | 3:19 | 2.308 | $1.5214 |
| Antigravity Claude Pro (Sonnet) | 2026-10-17 | 2:35 | 2.175 | $1.4302 |
| Antigravity Google Basic (Flash) | 2026-10-17 | 10:50 | 4.760 | $0.1878 |

These eleven historical rows plus the four latest rows describe **15 distinct completed runs**, each passing 12/12. Revisions intentionally retain separate labels: their prompts, profiles and workflow sources changed. They are not repeated measurements of one frozen configuration. Claude Pro actually used Sonnet; no successful Opus trial is established.

## Archive coverage and stopped attempts

| Retained record category | Distinct records |
|---|---|
| Completed and independently accepted | 15 |
| Stopped at an inapplicable workflow checkpoint | 2 |
| Quota interruption / timeout | 1 |
| Sandbox blocked | 1 |
| Launcher failed before sending the prompt | 1 |

The inventory contains 21 `run.json` files representing 20 distinct recorded attempts. One Sonnet run is stored twice with identical run/usage hashes and is counted once. The Opus timeout directory contains stale Sonnet acceptance/cost artifacts, so those files do not establish a completed Opus run or its cost. Google quota notes without a distinct recorded run are outside this count.

This is an archive inventory, not an exhaustive attempt log or a homogeneous reliability sample. The main tables select completed tasks; missing/stopped attempts are not zero-cost successes. The two workflow stops produced no application. Deleted, superseded material is not reconstructed or counted.

## Quality assessment

The project owner's qualitative assessment is that **BMad Basic is comparable to
pnet Plus in perceived result quality**: roughly one profile step from adding the
methodology. Treat this as an expert observation and a hypothesis for broader testing.
The BMad artifacts include a minimal spec and review triage; the same 12/12 acceptance
score does not measure the perceived quality difference or establish its cause.

Assess UX, completeness, maintainability, residual defects and verification quality
separately from speed/cost, preferably blindly across several tasks and repeated trials.

No blinded panel, scoring rubric applied after the runs, or numeric subjective ratings were recorded. No 1–10 scores or quality percentages are inferred retrospectively.

| Quality dimension | What the evidence supports |
|---|---|
| Required behavior | 12/12 in every completed run; the acceptance suite does not rank those results |
| Perceived overall quality | Owner assessment: BMad Basic is comparable to pnet Plus; other profiles/clients have no established subjective ranking |
| Process completeness | BMad retained a minimal spec, route and review triage; pnet completed PM → dev → reviewer → corrections |
| Review value | pnet review exposed input edge cases and mobile clipping; BMad review recorded input, confirmation-copy and live-region findings before corrections |
| Maintainability and remaining defects | No blinded comparative score or exhaustive defect search; screen-reader delivery was not tested |

Review findings are intermediate observations, not final acceptance failures. Their number is not a quality score; the BMad review recipe itself imposed a finding floor.

## Coordination observations

- Both latest pnet roots spawned PM, dev and reviewer, then reused the developer for one correction. All children inherited the full conversation. No lost assignment or user blocker was observed in these two runs.
- Basic repeated configuration/browser discovery; Plus retained a reusable check and exact invocation. Environment retries and repeated verification consumed work without demonstrating an application defect.
- BMad Basic used root → dev → workflow reviewer. Latest BMad Plus added a bounded architect scan and completed one applicable Blind Hunter review without the false approval stop.
- Actual models: pnet Basic used Luna/high throughout; pnet Plus used Luna/high root, Sol/low PM, Luna/max dev and Sol/medium reviewer. BMad Basic used Luna/high throughout; BMad Plus used Luna/high root, Luna/max dev/reviewer and Sol/medium architect. Sol denotes `gpt-6.1-sol`; Luna denotes `gpt-6-luna`.
- The workflow-owned BMad reviewer did not use the standalone reviewer profile automatically. Exact direct handoff bodies were encrypted in native logs; readable replies, targets, metadata and behavior establish the observed sequence.

Useful optimization candidates are compact task context, reuse of working verification commands, route-aware checkpoint checks and explicit model mapping for workflow-owned children. These are proposals supported by observed friction, not measured savings from implemented changes.

## Limits and practical implications

- These are individual runs with changing prompts, routes, caching and tooling; no statistical profile/vendor ranking follows.
- Estimates use historical API-equivalent rate snapshots, not current prices, subscription quota or provider bills. Rates in USD per million input/cached/output tokens: Luna 0.10/0.01/0.50; Sol 2/0.10/10; Astra 10/1/50; Sonnet 3/0.30/15; Flash 0.15/0.015/0.60.
- Successful rendering does not prove runtime model selection. BMad's workflow-owned reviewer did not automatically use the standalone reviewer profile. Record actual nested models.
- The latest build resolved a globally installed BMad skill; plugin inventory alone did not identify the active workflow. Pure plugin-only behavior remains unverified.
- Codex trials used isolated profiles and a VM-specific full-access sandbox adaptation. Normal sandbox operation and screen-reader delivery were not established.
- pnet Basic was fastest/cheapest among the four recent completed runs. This does not prove general superiority or that higher tiers always improve results.

Use the [experiment plan](templates/experiment-plan.md) and [report template](templates/evaluation-report.md) for new comparisons.

## Next controlled comparison

Compare Basic + BMad against Plus + pnet on several tasks, with at least three fresh runs per frozen configuration/task and alternating execution order. Record blind scores for requirements, UX, maintainability, remaining defects and verification separately; freeze task/acceptance/skill/profile hashes, context policy and rate snapshot.

Retain every attempt and intervention. Report completion rate, median/range for successful time and cost, and all-attempt cost per completed task. A larger repeat count may be necessary for a specific effect size; three is a starting protocol, not a statistical power guarantee. Until then, the observed “one profile step” remains a useful testable hypothesis.
