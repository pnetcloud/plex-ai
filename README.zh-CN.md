# pNet Plex

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [简体中文](README.zh-CN.md)

**组建团队，协调工作。**

Plex 是用于 **多智能体编排与协调的 agent harness**，集成 OpenAI Codex、Anthropic Claude Code
和 Google Antigravity。安装可复用团队，选择模型配置档，再让 Plex 组织实现、审查和验证。

**[v0.3.1 Preview](https://github.com/pnetcloud/plex-ai/releases/tag/v0.3.1)** — 开源，MIT。可试用；接口仍可能变化。

## 快速开始

需要 **Git 和 curl**、所选客户端 CLI，以及 **uv 或 Python 3.11+**。
在自己的项目目录运行，或创建空白测试项目：

```sh
mkdir plex-demo && cd plex-demo
```

用一条命令直接从 GitHub 安装：

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

安装器会打开交互菜单：

1. 用 **空格**选择客户端，按 **Enter** 继续（无 uv 时输入编号）。
2. 本次测试保留 **Project** 范围，并确认项目目录。
3. 选择独立团队 **pnet** 和 **Inherit**，使用会话模型设置。
4. 检查并确认每个客户端的安装计划。

安装内容包括共享插件、原生团队角色和托管指令块。
再次运行同一命令即可下载更新并重新打开配置。

## 尝试第一个任务

在 `plex-demo` 或自己的项目中打开编码客户端的 **新会话**。
如客户端要求，重新加载插件/智能体，然后发送：

```text
使用 Plex 创建一个自适应的专注会话预约页面。
只用 HTML、CSS 和 JavaScript，包含姓名、邮箱及 25/50 分钟时长。
验证输入并显示本地确认，不保存或发送数据。
审查修改，执行可用检查，并说明实际验证了什么。
```

Plex 会选择适用角色、实现页面并协调审查与验证。
预期得到源文件、本地预览命令、检查结果和剩余缺口说明。
安装本身不会启动编排，**请明确要求使用 Plex**。

发现问题？[提交 issue](https://github.com/pnetcloud/plex-ai/issues)，附客户端和版本、团队和配置档、
命令或提示词、预期与实际行为。附加日志前请移除秘密信息。

## 团队与模型

| 团队 | 用途 |
|---|---|
| **pnet** | 通用开发：PM、explorer、researcher、dev、reviewer 和 QA；无需 BMad |
| **bmad** | 已有 BMad 技能和工作流及按角色模型；需另行安装 BMad 和项目运行时 |

配置档包括 **Inherit、Basic、Plus、Pro、Pro+**。同一档位应用于所有所选客户端，可按角色覆盖。
Plex 仅管理带标记的指令块，保留周围项目指令。

更改设置或配置其他项目时，在其目录的 **终端中**运行：

```sh
~/.local/bin/plex
```

该命令打开安装配置；客户端内的 Plex 请求启动协调。
更新、用户范围、选项和覆盖设置见[配置](docs/translations/zh-CN/configuration.md)。

## 检查、更新与卸载

```sh
plex status
plex update
plex uninstall --dry-run
```

运行 `plex uninstall` 确认卸载。PATH 中没有 `plex` 时，请用 `~/.local/bin/plex`。
安装和更新选择已发布版本，包括预览版。

## 更多内容

- [文档](docs/translations/zh-CN/README.md) — 安装与使用详情。
- [关于 Plex](docs/translations/zh-CN/product.md) — 目标和原则。
- [兼容性](docs/translations/zh-CN/host-compatibility.md) — Codex 和部分 Antigravity 配置已有实际测试；原生 Claude Code 任务尚未验证。
- [测试与效率](docs/translations/zh-CN/testing.md) — 方法、token/成本测量和主观质量观察。
- [架构](docs/translations/zh-CN/architecture.md) — 配置与协调如何协作。

## 许可证

[MIT](LICENSE)。智能体指令参考 [Awesome Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents) 适配；
详见[第三方声明](THIRD_PARTY_NOTICES.md)。
