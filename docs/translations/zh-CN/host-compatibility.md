# 客户端兼容性

[English](../../host-compatibility.md) · [Русский](../ru/host-compatibility.md) · [Deutsch](../de/host-compatibility.md) · [简体中文](host-compatibility.md)

客户端执行智能体，模型供应商提供模型。增加供应商配置档不会增加客户端适配器。

| 客户端 | Plex 集成 | 验证范围 |
|---|---|---|
| OpenAI Codex | 原生 TOML 角色、插件、范围与指令支持 | 隔离环境安装配置和实际任务测试 |
| Anthropic Claude Code | 原生 Markdown 角色和插件安装路径 | 渲染及配置检查；尚未验证原生客户端实际任务 |
| Google Antigravity | 原生 Markdown 角色和插件包 | 安装配置及部分模型的实际任务测试 |

覆盖范围限于测试过的版本和设置，参见[测试](testing.md)。
Gemini CLI 是另一个客户端，目前不支持；其他适配器不在当前范围内。

## 模型与权限限制

Codex 渲染 `model` 和 `model_reasoning_effort`；Claude Code 与 Antigravity 渲染 `model` 和 `effort`。
实际可用性取决于客户端与模型。Antigravity 渲染接受原生的 `inherit`、`flash_lite`、`flash`、`pro` 档位。
配置档中显式填写模型系列 ID 不代表原生客户端能够执行；不支持的路由会报错，不会静默替换。
`inherit` 跟随父会话，不能为每个子智能体独立选择 Sonnet 或 Opus。

原生权限和限制始终有效。角色名、配置档和成功渲染不能证明工具隔离、并发行为或模型选择。
Plex 不会为使适配器工作而启用其他客户端或放宽全局权限。
