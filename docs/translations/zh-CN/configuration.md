# 配置

[English](../../configuration.md) · [Русский](../ru/configuration.md) · [Deutsch](../de/configuration.md) · [简体中文](configuration.md)

## 安装与更新

首次安装请使用[快速开始](../../../README.zh-CN.md#快速开始)。
引导脚本在 `~/.local/share/plex-ai` 保留共享副本，默认安装**最新已发布版本，包括预览版**。
请保留该目录，插件仍引用它。入口脚本来自 `main`，应用文件检出所选发布标签。

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

### 状态、更新与卸载

```sh
plex status
plex status --json
plex update
plex update --release v0.2.0
plex update --development
plex uninstall --dry-run
plex uninstall
```

`status` 优先检查项目配置，否则检查相应客户端的用户安装。显示源码版本、团队/配置档、
原生角色、冲突和插件发现结果，不更改 Plex 配置。`--json` 提供结构化输出。
已配置客户端如有冲突、状态过期或插件不可用，会返回非零状态。这不能证明实际模型路由。

`update` 选择最新已发布版本并打开配置以刷新所选客户端。`--release` 固定已发布标签，
`--development` 明确选择 `main`。本地修改、符号链接和其他 origin 会阻止更新。
源码检出具体标签而非浮动分支。`update --dry-run` 只显示版本选择，不写入源码或配置。

`uninstall` 默认作用于项目和 receipt 中所有客户端。`--dry-run` 预览；交互卸载要求确认，
无人值守执行需 `--yes`。可用 `--client codex` 筛选，或用 `--scope user` 明确选择用户范围。
仅移除哈希未变的 receipt 所属角色和匹配指令块。修改/缺失文件或错误标记会中止操作，
其他文件及周围指令保持不变。其他客户端仍使用的共享块将保留。
每个客户端单独使用锁、事务和备份，多客户端卸载不是一个整体事务。

共享插件、源码、CLI 快捷命令、可编辑 preset 和备份会保留，供其他项目或重装使用。
删除块后原生指令文件仍保留。保留的项目偏好仍优先于全局默认值，不会自动切换范围。
修改后打开新的客户端会话。如果 PATH 中没有 `plex`，请使用 `~/.local/bin/plex`。
不带子命令的 `plex` 打开配置。

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

来自其他副本的现有命令、外部文件或失效链接会保留并提示，不会阻止正常安装。
安装器会显示自己的启动路径。显式 `--install-command` 仍拒绝覆盖无关命令。

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

定义位于 `teams/<team>/team.toml`、`agents/*.md` 和 `profiles/*.toml`。
供应商文件声明客户端和独立档位，不使用 include 链。精确模型 ID 和推理强度以源文件为准，避免在文档中重复维护。

`[skills]` 将角色绑定到入口技能。可选的 `[[workflows.<role>]]` 条目包含必填的
`skill` 和简短的 `description`，以及可选的角色内部菜单代码 `operation`。
例如 analyst 使用 `skill = "bmad-deep-recon"`；PO 使用 `skill = "bmad-agent-po"`
和 `operation = "SPEC"`。每个条目都需要结果说明。

解析器验证目录并将其保存到 `.plex/resolved.json`。协调者根据描述选择操作并传递明确意图和参数；
子智能体验证已安装版本的分派规则，仅加载选定工作流。目录不会提前激活所有技能、安装 BMad 或代替批准。
具体流程仍由已安装的 BMad 提供。修改团队目录后请刷新安装；现有快照不会自动更新。

`openai-plus`、`google-anthropic-plus` 等供应商配置 ID 可通过单客户端 `--host` 模式或解析器使用。
多客户端 `--client` 模式使用共享档位。单客户端的 custom 菜单编辑已有命名配置档的角色覆盖；
`custom` 不是保存的配置档。模型可用性取决于客户端和供应商。

## 交互模式

在 `.plex/preset.toml` 顶层设置 `interaction = "balanced"`，或向安装器及解析器
`apply` 传递 `--interaction interactive|balanced|auto`。省略参数会保留已保存值；
默认是 `balanced`。安装计划显示有效模式。模式由客户端共享，切换团队或配置档时保留。
手动修改后请刷新安装。

- `interactive`：共同探索，并就重要选择与用户讨论。
- `balanced`：自行解决常规问题，仅询问重要未决事项或适用检查点。
- `auto`：不提问或等待；完成已授权工作，返回部分结果及阻塞原因。

用户明确指定的单次任务模式覆盖保存值，但不改写配置。协调者将模式传递给所有执行者。
子智能体向协调者返回问题；协调者复用已知答案，在 balanced 中合并必要问题，并继续独立工作。
auto 中未决事项只阻塞依赖它的工作。

对于范围明确的产物任务，balanced/auto 在支持时使用 BMad 原生 headless 合约；
不支持时仍遵守实际检查点。auto 无法在授权范围内继续时返回阻塞状态。
这些模式不跳过测试或审查，不扩大权限，也不授予发布或分析师研究许可。
带有未决需求的部分产物不能作为已批准的后续实现输入。这不是所有工作流均可无人值守完成的保证。

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
