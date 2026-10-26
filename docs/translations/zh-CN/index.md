<p align="center">
  <img src="../../assets/readme/hero-banner.png" width="800" alt="Plex AI by pNet，搭配深色矿物质感背景上的 Triad 标志">
</p>

# Plex 文档

[English](../../README.md) · [Русский](../ru/index.md) · [Deutsch](../de/index.md) · [简体中文](index.md)

Plex 在 Codex、Claude Code 和 Antigravity 中配置并协调智能体团队。

## 从这里开始

1. [安装 Plex](installation.md) — 环境要求、标准模式和开发模式。
2. [选择团队和配置档](configuration.md) — 模型、交互和并发。
3. [在聊天中调用 Plex](README.md) — 协调工作并验证结果。

| 指南 | 内容 |
|---|---|
| [关于 Plex](product.md) | 目标、原则和范围 |
| [安装与所有参数](installation.md) | 安装、开发模式与所有 CLI 参数 |
| [配置](configuration.md) | 团队、模型配置与覆盖设置 |
| [兼容性](host-compatibility.md) | 原生集成、模型限制和验证范围 |
| [架构](architecture.md) | 配置、安装与协调 |
| [角色契约](role-contracts.md) | 职责和执行指令 |
| [开发](development.md) | 源码布局与检查 |
| [测试与效率](testing.md) | 实测结果、token、成本和质量观察 |

实验请使用[评估协议](../../../EVALUATION.md)、[实验计划](templates/experiment-plan.md)
和[报告模板](templates/evaluation-report.md)。英文是维护源；各语言版本使用相同文件名。

<details>
<summary>版本归档</summary>

| 版本 | 变更 |
|---|---|
| [v0.18.0](releases/v0.18.0.md) | Claude 缓存更新、托管包访问与兼容的 Markdown 交接。 |
| [v0.17.1](releases/v0.17.1.md) | 更新与预览前显示当前版本和目标版本。 |
| [v0.17.0](releases/v0.17.0.md) | 易读的 Markdown 智能体契约、结构校验及旧 JSON 兼容。 |
| [v0.16.2](releases/v0.16.2.md) | 易读 TOML、自动迁移及完整上下文提醒。 |
| [v0.16.0](releases/v0.16.0.md) | 执行者自主工作与自动迁移的 Markdown 状态。 |
| [v0.15.0](releases/v0.15.0.md) | 从已交付步骤继续、分类任务路由并安全安装 BMad 技能。 |
| [v0.14.0](releases/v0.14.0.md) | PM 优先选择 BMad 工作流并支持直接入口。 |
| [v0.13.1](releases/v0.13.1.md) | 有界任务、最终交付与证据保留。 |
| [v0.13.0](releases/v0.13.0.md) | 有界协调器状态、目标队列与 DevOps 专家。 |
| [v0.12.3](releases/v0.12.3.md) | 统一团队及提供商的协调器建议。 |
| [v0.12.2](releases/v0.12.2.md) | 重新配置受管角色并验证备份。 |
| [v0.12.1](releases/v0.12.1.md) | 重新配置受管角色并验证备份。 |
| [v0.12.0](releases/v0.12.0.md) | 两个团队均提供六个均衡模型档位。 |
| [发布说明](releases/v0.11.1.md) | v0.11.1: 管理 Codex 原生子线程容量。 |
| [发布说明](releases/v0.11.0.md) | v0.11.0: 管理 Codex 原生子线程容量。 |
| [发布说明](releases/v0.10.1.md) | v0.10.1: 核实阻碍的来源及适用性。 |
| [发布说明](releases/v0.10.0.md) | v0.10.0: 可验证的子智能体响应与清晰的求助请求。 |
| [发布说明](releases/v0.9.1.md) | v0.9.1: 文档热修复：更清晰地说明模型配置档和智能体编排。 |
| [发布说明](releases/v0.9.0.md) | v0.9.0: Plex 不再管理 token 预算。 |
| [发布说明](releases/v0.8.1.md) | v0.8.1：Codex 角色从主聊天继承权限。 |
| [发布说明](releases/v0.8.0.md) | v0.8.0：Goal token 预算为可选项，默认不设置上限。 |
| [发布说明](releases/v0.7.2.md) | v0.7.2：更大的深色 README 横幅，并同步展示素材。 |
| [发布说明](releases/v0.7.1.md) | v0.7.1：README 中明确项目状态和安装要求。 |
| [发布说明](releases/v0.7.0.md) | v0.7.0: PM/PO 契约、可选 Plan/Goal 与 BMad Build Auto。 |
| [发布说明](releases/v0.6.1.md) | v0.6.1: 路由和实现前必须先由专家评估。 |
| [发布说明](releases/v0.6.0.md) | v0.6.0: Auto、Codex 原生角色与 Plex AI 展示。 |
| [发布说明](releases/v0.5.11.md) | v0.5.11: 稳定 macOS CI、协调者委派及安装默认值。 |
| [发布说明](releases/v0.5.9.md) | v0.5.9: 仅使用活动团队角色，并可选择清理旧代理。 |
| [发布说明](releases/v0.5.8.md) | v0.5.8: 文档整理与 Codex 技能短名称 |
| [发布说明](releases/v0.5.7.md) | v0.5.7: 统一协调者结构与贡献指南 |
| [发布说明](releases/v0.5.6.md) | v0.5.6：任务路线与 BMad 激活证据 |
| [发布说明](releases/v0.5.5.md) | v0.5.5：Claude 委派修复与正式发布 |
| [发布说明](releases/v0.5.4.md) | v0.5.4 预览版：内容、安装和限制 |
| [发布说明](releases/v0.5.3.md) | v0.5.3 预览版：内容、安装和限制 |
| [发布说明](releases/v0.5.2.md) | v0.5.2 预览版：内容、安装和限制 |
| [发布说明](releases/v0.5.1.md) | v0.5.1 预览版：内容、安装和限制 |
| [发布说明](releases/v0.5.0.md) | v0.5.0 预览版：内容、安装和限制 |
| [发布说明](releases/v0.4.0.md) | v0.4.0 预览版：内容、安装和限制 |
| [发布说明](releases/v0.3.1.md) | v0.3.1 预览版：内容、安装和限制 |
| [发布说明](releases/v0.3.0.md) | v0.3.0 预览版：内容、安装和限制 |
| [发布说明](releases/v0.2.0.md) | v0.2.0 预览版：内容、安装和限制 |
| [发布说明](releases/v0.1.0.md) | v0.1.0 预览版：内容、安装和限制 |

</details>
