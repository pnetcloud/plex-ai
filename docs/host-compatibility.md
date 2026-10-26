# Host compatibility

[English](host-compatibility.md) · [Русский](translations/ru/host-compatibility.md) · [Deutsch](translations/de/host-compatibility.md) · [简体中文](translations/zh-CN/host-compatibility.md)

Hosts execute agents; model vendors supply models. A vendor profile does not add a host adapter.

| Client | Plex integration | Verification coverage |
|---|---|---|
| OpenAI Codex | Native TOML roles, plugin and scope/instruction support | Isolated installation/configuration and live task trials |
| Anthropic Claude Code | Native Markdown roles and plugin installation path | Native CLI 2.1.310: manifest validation, isolated plugin installation and both-team configuration; live model trials remain unverified |
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

Codex subagents inherit sandbox, approval settings and MCP servers from the main
chat. Plex omits `sandbox_mode` and `approval_policy` from generated role TOML.
Set permissions in the parent session. Read-only role instructions do not provide
a separate sandbox. See the [Codex subagent reference](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Claude Code dispatch

Plex selects native roles with `Agent.subagent_type`. Task labels go in
`description` and handoff text: passing `name` can launch an Agent Teams teammate.
Roles with `delegation = false` render `disallowedTools: Agent`; BMad roles retain
nested delegation subject to the installed client's depth limit and permissions.
See the [Claude subagent reference](https://code.claude.com/docs/en/sub-agents).

Model and effort support depend on the installed client and model. Session/provider
overrides, including `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` and `CLAUDE_CODE_EFFORT_LEVEL`,
can take precedence over role settings; inspect actual execution before claiming routing.

Claude setup manages narrow allow rules in `.claude/settings.local.json` (user scope: `settings.json` in the Claude config root). Full setup gets the actual plugin cache path from the native inventory and explicitly updates an existing plugin cache. Roles-only refresh keeps the saved package path; a standalone resolver uses its own package/source root. Existing personal rules are preserved. Changed owned rules are conflicts; uninstall removes only Plex-owned rules, with backups and rollback. BMad adds read access to installed skill roots, not blanket runtime execution. Claude BMad installation uses `--copy`, keeping shared Codex skill copies separate.

Assignments carry the verified absolute plugin path in Markdown Inputs. Display/configuration checks do not prove active-session permissions or model routing; restart Claude after updating its plugin. Tests cover native CLI 2.1.310 installation, cache upgrades and configuration, not every model/profile combination.
