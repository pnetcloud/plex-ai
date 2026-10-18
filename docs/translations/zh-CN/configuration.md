# 配置

[English](../../configuration.md) · [Русский](../ru/configuration.md) · [Deutsch](../de/configuration.md) · [简体中文](configuration.md)

## 安装与更新

首次安装请使用[快速开始](../../../README.zh-CN.md#快速开始)。
其中的 GitHub 命令将 `main` 分支下载到 `~/.local/share/plex-ai` 并启动配置，
不会改变当前目标项目目录。

在目标项目中更新该副本：

```sh
git -C "$HOME/.local/share/plex-ai" pull --ff-only && \
  "$HOME/.local/share/plex-ai/setup.sh"
```

不要向已有副本重复执行 `git clone`。如果选择了其他位置，请使用实际路径。
检查安装计划以应用新角色/配置档，然后重新加载客户端。
终端命令 `~/.local/bin/plex` 打开配置；客户端内的 Plex 请求启动协调。

在源码目录运行 `./setup.sh`。用空格选择客户端，按 Enter 继续。
选择团队、安装范围和共享配置档，并检查各安装计划；默认选择项目范围。需要相应客户端 CLI。

```sh
./setup.sh --project /path/to/project --client codex --client antigravity --team pnet --model-profile plus --yes
```

完整安装会安装共享 Plex 插件，并配置原生角色与指令，不会把技能复制进各项目。
本地 marketplace 仍引用源码或导出目录时，请保留这些目录。BMad 需要已安装的匹配技能和项目运行时。

再次运行安装器可更新定义或切换团队、配置档；覆盖设置会保留。更新定义后需刷新才能更新原生角色；
新技能或角色应在新客户端会话中使用。共享项目配置档会更新已配置的客户端，不会隐式安装没有 receipt 的客户端。

| 选项 | 作用 |
|---|---|
| `--dry-run` | 只预览，不写入 |
| `--roles-only` | 仅配置角色和状态，跳过插件安装 |
| `--no-instructions` | 跳过托管指令块 |
| `--no-command` | 跳过 `~/.local/bin/plex` 快捷命令 |
| `--install-command` | 仅安装指向源码的快捷命令 |
| `--max-agents N` | 设置共享任务并发上限 |

后续失败不会回滚插件管理器操作或已经完成的客户端安装。

## 团队与配置档

| 团队 | 角色 | 工作方式 |
|---|---|---|
| `pnet` | pm, explorer, researcher, dev, reviewer, qa | 独立协调 |
| `bmad` | analyst, pm, po, ux, architect, dev, reviewer | 使用已有 BMad 技能 |

配置档包括 `inherit`、`basic`、`plus`、`pro`、`pro-plus`。共享档位使用所选团队中适用于
Codex 的 OpenAI、Claude Code 的 Anthropic、Antigravity 的 Google 设置。
`inherit` 将模型和推理强度交由客户端决定。配置档描述设置，不是实测质量等级。

可编辑文件位于所选安装根目录的 `.plex/preset.toml`：

```toml
team = "pnet"
model_profile = "plus"
max_agents = 3

[codex.dev]
reasoning = "max"
```

各字段优先级：**配置档默认值 → 配置档角色值 → 客户端覆盖 → 角色覆盖**。
客户端表为 `[codex]`、`[claude]`、`[antigravity]`；角色表追加角色名。
两类覆盖均接受 `model` 和 `reasoning`。Codex 如需继承模型，省略 `model`。
切换团队时会保留暂未包含角色的非活动覆盖设置。

定义位于 `teams/<team>/team.toml`、`agents/<host>/` 和 `profiles/*.toml`。
供应商文件声明客户端和独立档位，不使用 include 链。精确模型 ID 和推理强度以源文件为准，避免在文档中重复维护。

`openai-plus`、`google-anthropic-plus` 等供应商配置 ID 可通过单客户端 `--host` 模式或解析器使用。
多客户端 `--client` 模式使用共享档位。单客户端的 custom 菜单编辑已有命名配置档的角色覆盖；
`custom` 不是保存的配置档。模型可用性取决于客户端和供应商。

## 项目与用户范围

| 客户端 | 项目角色目录 | 用户根目录 / 角色目录 |
|---|---|---|
| Codex | `.codex/agents/` | `$CODEX_HOME` 或 `~/.codex` / `agents/` |
| Claude Code | `.claude/agents/` | `$CLAUDE_CONFIG_DIR` 或 `~/.claude` / `agents/` |
| Antigravity | `.agents/agents/` | `~/.gemini` / `config/agents/` |

各根目录分别保存 `.plex` 状态。`check --host <host> --scope auto` 优先选择项目，否则选择用户范围。
项目状态过期或冲突时不会静默回退。切换范围不会删除或迁移另一范围。
即使 BMad 角色安装在用户范围，各工作项目仍需满足其运行前提。

## 托管指令与状态

Plex 只管理 `<!-- plex:start -->` … `<!-- plex:end -->` 之间的内容。个人指令应放在块外。
被修改、缺失、重复或无效的标记会产生冲突，不会被强制覆盖。

安装器优先选择已有非空文件，否则创建默认文件：Codex 按 `AGENTS.override.md`、`AGENTS.md`、
项目 fallback 的顺序；Claude 按 `CLAUDE.md`、项目 `.claude/CLAUDE.md` 的顺序；
Antigravity 按 `GEMINI.md`、项目 `AGENTS.md` 的顺序。用户范围的 Codex 不使用 fallback。
文件选择不会更改客户端 fallback 配置，也不会强制额外读取另一份指令文件。

| 文件 | 用途 |
|---|---|
| `.plex/preset.toml` | 可编辑团队、配置档和覆盖设置 |
| `.plex/resolved.json` | 自动生成的有效配置快照 |
| `.plex/applied.json` | 客户端 receipt 与托管文件哈希 |
| `.plex/backups/` | 被替换的文件和移除的角色备份 |

不要手动编辑生成的角色或 receipt。无归属文件、被修改的托管文件、符号链接和并行应用操作
会阻止不安全更新。刷新前解决报告的冲突，并保留备份。

## 只读检查

在 Plex 源码目录运行，需要 Python 3.11+：

```sh
python3 skills/plex-setup/scripts/resolve_config.py list
python3 skills/plex-setup/scripts/resolve_config.py resolve /path/to/project/.plex/preset.toml
python3 skills/plex-setup/scripts/resolve_config.py render /path/to/project/.plex/preset.toml --host codex
python3 skills/plex-setup/scripts/resolve_config.py check /path/to/project --host codex --scope auto
```

`apply` 会写入原生配置。直接使用解析器时，需显式添加 `--instructions` 才会集成指令。
安装器统一提供预览、插件安装和指令集成。

可选 BMad 审查定制参见[审查策略](../../../teams/bmad/review-policy.md)，普通安装不会启用它。
