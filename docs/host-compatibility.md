# Host compatibility

[English](host-compatibility.md) · [Русский](translations/ru/host-compatibility.md) · [Deutsch](translations/de/host-compatibility.md) · [简体中文](translations/zh-CN/host-compatibility.md)

Hosts execute agents; model vendors supply models. A vendor profile does not add a host adapter.

| Client | Plex integration | Verification coverage |
|---|---|---|
| OpenAI Codex | Native TOML roles, plugin and scope/instruction support | Isolated installation/configuration and live task trials |
| Anthropic Claude Code | Native Markdown roles and plugin installation path | Native CLI 2.1.306: manifest validation, isolated plugin installation and both-team configuration; live model trials remain unverified |
| Google Antigravity | Native Markdown roles and plugin package | Installation/configuration and selected live model trials |

Coverage is bounded by the tested versions and settings; see [testing](testing.md).
Gemini CLI is a separate, unsupported host. Additional host adapters are outside the current scope.

## Model and permission constraints

Codex renders `model` and `model_reasoning_effort`. Claude Code and Antigravity
render `model` and `effort`; availability depends on the actual host/model.
Antigravity rendering accepts its native `inherit`, `flash_lite`, `flash`, `pro`
tiers. Explicit family IDs in a profile do not prove the native host can execute them;
unsupported routing is reported rather than silently substituted. `inherit` follows
the parent session and cannot independently choose Sonnet versus Opus for each child.

Native permissions and limits remain authoritative. Do not infer tool isolation,
concurrency or model selection solely from role names, profiles or successful rendering.
Plex does not enable another host or relax global permissions to make an adapter work.

## Claude Code dispatch

Plex selects native roles with `Agent.subagent_type`. Task labels go in
`description` and handoff text: passing `name` can launch an Agent Teams teammate.
Roles with `delegation = false` render `disallowedTools: Agent`; BMad roles retain
nested delegation subject to the installed client's depth limit and permissions.
See the [Claude subagent reference](https://code.claude.com/docs/en/sub-agents).

Model and effort support depend on the installed client and model. Session/provider
overrides, including `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` and `CLAUDE_CODE_EFFORT_LEVEL`,
can take precedence over role settings; inspect actual execution before claiming routing.
