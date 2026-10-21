# pNet Plex

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [简体中文](README.zh-CN.md)

**组建团队，协调工作。**

Plex 是用于 **多智能体编排与协调的 agent harness**，集成 OpenAI Codex、Anthropic Claude Code
和 Google Antigravity。安装可复用团队，选择模型配置档，再让 Plex 组织实现、审查和验证。

**[v0.5.6](https://github.com/pnetcloud/plex-ai/releases/tag/v0.5.6)** — 开源，MIT。可试用；接口仍可能变化。

## 安装

在项目目录中运行：

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

**开发模式 · Codex · 项目本地技能**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --dev --client codex
```

选择客户端、范围、团队和模型配置档，然后确认计划。推荐 **Project** 范围。安装后打开新的客户端会话。

常规安装器会完成两部分配置：

- **共享插件** — 为客户端提供可复用的 `plex` 和 `plex-setup` 技能。
- **团队配置** — 在项目或用户范围创建原生智能体角色和托管指令块。

只安装插件并不会配置团队。开发模式在该项目中使用本地技能链接代替共享 Plex 插件。

[环境要求、BMad、开发模式及全部参数](readme/translations/zh-CN/installation.md)。

## 工作方式

当前对话继续担任协调者并保留其模型。它委派有用的任务、整合结果并验证最终成果。简单任务可以在当前对话中完成。

```mermaid
flowchart TD
    A[你的任务] --> B[当前对话负责协调]
    B --> C[选定角色执行有明确边界的任务]
    C --> D[协调者整合并验证]
```

## 对话示例

以下是**对话请求，不是终端命令**。发送前替换尖括号中的占位符。

**协调任务 · Codex 插件**

```text
$pnet-plex:plex 协调<任务>。要求：<需求>。验证<验收标准>。
```

**审查变更**

```text
$pnet-plex:plex 根据<需求>审查<变更>，报告问题和验证缺口。
```

**检查或配置团队**

```text
$pnet-plex:plex-setup 检查当前项目的 Plex 配置。
$pnet-plex:plex-setup 配置当前项目：团队<团队>、模型配置档<配置档>、交互模式<模式>。
```

**协调任务 · Claude Code 插件**

```text
/pnet-plex:plex 协调<任务>。要求：<要求>。验证<验收标准>。
/pnet-plex:plex-setup 检查此项目的 Plex 配置。
```

Codex `--dev` 模式使用本地 `$plex` 和 `$plex-setup` 标签。其他客户端可选择已安装技能，或明确请求：`使用 Plex 协调<任务>。`

安装不会自动启动协调。`plex-setup` 修改配置，`plex` 协调工作。

## 团队与模型

| 团队 | 用途 |
|---|---|
| **pnet** | 通用开发：PM、explorer、researcher、dev、reviewer 和 QA；无需 BMad |
| **bmad** | 已安装的 BMad 角色和工作流；安装器提供所选依赖安装和项目初始化 |

**Inherit、Basic、Plus、Pro、Pro+** 配置子智能体。主对话模型由你选择；安装器显示所选配置档的建议。参见[配置](docs/translations/zh-CN/configuration.md)。

## 终端命令

| 任务 | 命令 |
|---|---|
| 配置或刷新项目 | `plex` |
| 检查安装 | `plex status` |
| 下载更新并打开安装器 | `plex update` |
| 预览团队移除 | `plex uninstall --dry-run` |
| 移除当前项目团队 | `plex uninstall` |

若没有可选的 `plex` 命令，可使用 `~/.local/share/plex-ai/setup.sh`。**Update only** 保留设置；**Reconfigure** 打开配置菜单。

## 卸载

在项目目录运行 `plex uninstall`，移除未被修改的托管角色、Plex 指令块和所属开发链接；保留周围项目指令。偏好设置、备份和共享插件仍保留。

其他项目不再需要共享 **Codex 插件**时，可一并移除：

```sh
codex plugin remove pnet-plex@pnet-plex
```

其他客户端及用户级团队移除方式参见[卸载说明](readme/translations/zh-CN/installation.md#卸载)。

## 更多内容

- [报告问题](https://github.com/pnetcloud/plex-ai/issues).
- [文档](docs/translations/zh-CN/README.md) — 安装与使用详情。
- [关于 Plex](docs/translations/zh-CN/product.md) — 目标和原则。
- [兼容性](docs/translations/zh-CN/host-compatibility.md) — Codex 和部分 Antigravity 配置已有实际测试；原生 Claude Code 任务尚未验证。
- [测试与效率](docs/translations/zh-CN/testing.md) — 方法、token/成本测量和主观质量观察。
- [架构](docs/translations/zh-CN/architecture.md) — 配置与协调如何协作。

## 许可证

[MIT](LICENSE)。智能体指令参考 [Awesome Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents) 适配；
详见[第三方声明](THIRD_PARTY_NOTICES.md)。
