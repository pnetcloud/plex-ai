# Host compatibility

[English](host-compatibility.md) · [Русский](translations/ru/host-compatibility.md) · [Deutsch](translations/de/host-compatibility.md) · [简体中文](translations/zh-CN/host-compatibility.md)

Hosts execute agents; model vendors supply models. A vendor profile does not add a host adapter.

| Client | Plex integration | Verification coverage |
|---|---|---|
| OpenAI Codex | Native TOML roles, plugin and scope/instruction support | Isolated installation/configuration and live task trials |
| Anthropic Claude Code | Native Markdown roles and plugin installation path | Rendering/configuration checks; native live trials remain unverified |
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
