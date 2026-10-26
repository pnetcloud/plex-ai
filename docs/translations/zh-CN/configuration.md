# 配置

[English](../../configuration.md) · [Русский](../ru/configuration.md) · [Deutsch](../de/configuration.md) · [简体中文](configuration.md)

[安装、开发模式与所有 CLI 参数](installation.md).

## 团队与配置档

| 团队 | 角色 | 工作方式 |
|---|---|---|
| `pnet` | pm, explorer, researcher, dev, reviewer, qa, devops | 独立协调 |
| `bmad` | analyst, pm, po, ux, architect, dev, reviewer, devops | 使用已有 BMad 技能 |

配置档包括 `inherit`、`basic`、`plus`、`pro`、`pro-plus`、`ultra`、`ultra-plus`。共享档位使用所选团队中适用于
Codex 的 OpenAI、Claude Code 的 Anthropic、Antigravity 的 Google 设置。
`inherit` 将模型和推理强度交由客户端决定。配置档描述设置，不是实测质量等级。

两个团队均提供六个命名档位及 `inherit`。提供商文件在每个档位中先列出协调器建议。Haiku/Sonnet/Opus 大致对应 Luna/Sol/Astra，但并未验证质量等价。Google 原生配置使用 Flash 或继承主会话模型，Ultra 档位提高请求的推理强度。Antigravity 中的 Claude 使用 Sonnet 替代不可用的 Haiku；具体模型 ID 需要客户端支持。

各角色配方按团队和提供商分别明确配置；README 的配置表仅描述 `pnet`。例如，BMad Codex
的主对话建议在 Pro+ 使用 Luna/xhigh、在 Ultra 使用 Sol/medium；`pnet` 对应为 Luna/max
和 Sol/low。BMad OpenAI Ultra+ 的 UX 仍为 Astra/medium。每个团队和提供商都单独配置
DevOps，不继承其他角色的设置。精确配方见 [pnet](../../../teams/pnet/profiles/) 和
[BMad](../../../teams/bmad/profiles/) TOML profile；setup 会显示应用覆盖项后的有效设置。

交互式 **Reconfigure** 显示被修改的受管角色路径，备份预览时核验的内容，并依据所选配置档及 preset 覆盖设置重新生成角色。**Update only** 仍会在发现手动修改时停止。缺失或非受管文件、符号链接、修改后的指令块、客户端配置冲突及预览后的变化仍受到保护。持久模型设置应写入 `.plex/preset.toml`。

可编辑文件位于所选安装根目录的 `.plex/preset.toml`：

```toml
team = "pnet"
model_profile = "plus"
max_agents = 3

[codex.dev]
reasoning = "max"
```

Plex 不配置 token 预算。刷新时会移除旧 preset 中已停用的预算字段。执行依据验收标准和客户端的实际约束。

厂商配置文件中可选的 `[coordinator.<tier>]` 表用于主对话建议（`model`、`reasoning`）。
它与角色设置分开，并作为 `coordinator` 写入解析快照。安装器显示所选配置档的建议，
但不会应用到客户端，也不会安装协调者角色。没有建议时（包括 `inherit`），由用户选择模型。

各字段优先级：**配置档默认值 → 配置档角色值 → 客户端覆盖 → 角色覆盖**。
客户端表为 `[codex]`、`[claude]`、`[antigravity]`；角色表追加角色名。
两类覆盖均接受 `model` 和 `reasoning`。Codex 如需继承模型，省略 `model`。
切换团队时会保留暂未包含角色的非活动覆盖设置。

定义位于 `teams/<team>/team.toml`、`agents/*.md` 和 `profiles/*.toml`。
供应商文件声明客户端和独立档位，不使用 include 链。精确模型 ID 和推理强度以源文件为准，避免在文档中重复维护。

`[skills]` 将角色绑定到 persona 入口技能。可选的 `[[workflows.<role>]]` 条目包含必填的
`skill` 和简短的 `description`，以及可选的 persona 内部菜单代码 `operation`。
缺少 `operation` 仅表示未指定 persona 内菜单代码；它既不决定直接 workflow 模式还是
persona/菜单模式，也不证明该技能可独立调用。现有 outcome/input 决定入口模式；
以所选已安装技能的实际契约为准。角色键表示符合条件的执行者。
例如 analyst 使用 `skill = "bmad-deep-recon"`；PO 使用 `skill = "bmad-agent-po"`
和 `operation = "SPEC"`。每个条目都需要结果说明。

解析器验证目录并将其保存到 `.plex/resolved.json`。PM 从准确快照中的完整映射
选择最小充分路线；Root 按该选择传递明确意图和参数。子智能体验证已安装版本的分派规则，
仅加载选定工作流。目录不会提前激活所有技能、安装 BMad 或代替批准。
具体流程仍由已安装的 BMad 提供。修改团队目录后请刷新安装；现有快照不会自动更新。

安装官方 BMad 用户技能前，Setup 会先核对固定版本的技能目录；若请求的技能不存在，
会在写入前停止。它只安装缺失的技能并保留已有的有效文件。部分安装失败后可以重试，
已成功安装的技能不会再次安装。

`openai-plus`、`google-anthropic-plus` 等供应商配置 ID 可通过单客户端 `--host` 模式或解析器使用。
多客户端 `--client` 模式使用共享档位。单客户端的 custom 菜单编辑已有命名配置档的角色覆盖；
`custom` 不是保存的配置档。模型可用性取决于客户端和供应商。

## 交互模式

交互安装仅为所有所选客户端询问一次模式，默认选中已保存模式，新安装默认 `balanced`。每次应用配置都会显式保存 `interaction`，包括刷新旧配置时。

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

路线选择遵循当前有效模式：在 `interactive` 下，PM 可以提出差异明显的任务路线并给出建议，
由 Root 向用户提问；在 `auto` 下，PM 自行选择，不提出可选的路线问题。`balanced` 保持上述规则。
已确定的路线不再重复询问。路线选择不等于批准 workflow 计划，也不会绕过真实检查点；
在 `auto` 下，没有获授权的 headless 路径仍须报告为阻塞。

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

刷新时，仍与安装记录匹配的旧 `plex:start` / `plex:end` 区块会自动迁移。混用标记格式或修改托管区块会阻止更新。

Plex 只管理 `<!-- plex:managed:start -->` … `<!-- plex:managed:end -->` 之间的内容。个人指令应放在块外。
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
| `.plex/skill-aliases.json` | Codex 短名称链接；自动生成的所有权记录 |
| `.plex/dev.json` | Codex 开发链接与项目插件覆盖；所有权记录 |
| `.plex/backups/` | 被替换的文件和移除的角色备份 |

不要手动编辑生成的角色或 receipt。无归属文件、被修改的托管文件、符号链接和并行应用操作
会阻止不安全更新。刷新前解决报告的冲突，并保留备份。交互式 Reconfigure 可按上述方式替换受管角色修改。

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

## 其他 Codex 代理

Plex 自有任务只使用已检查的活动团队中准确的 `plex-<role>` 名称。其他已安装或内置代理不属于该团队；工作流内部执行者遵循该工作流的约定。

安装器列出所选范围内的其他 `.toml` 代理，提供**保留**（默认）或**移至备份**。这些代理对客户端仍可用，可能影响角色选择。可处理的文件移至 `.plex/backups/<timestamp>/codex/other-agents/`，需要时可从中手动恢复。其他范围、符号链接及在 `config.toml` 中显式注册的文件会被保留。在交互式 Reconfigure 之外，被修改的托管角色仍会报告冲突。

## 工作区与原生代理委派

存在未提交的修改本身不需要再次确认。Plex 记录初始状态、分配任务文件，并保留已有修改，包括任务文件中他人的修改片段。此授权会传递给工作流；仅针对工作区不干净的确认已得到回答。冲突只阻塞受影响的工作。Plex 不会为了获得干净的工作区而创建 worktree、切换分支、stash、reset、clean 或 commit。

对于 Codex，安装程序会在 `[features.multi_agent_v2]` 下补充缺失的 `hide_spawn_agent_metadata = false` 和 `tool_namespace = "agents"`。如果目标配置和已检查的继承配置都没有显式容量设置，还会在同一事务中写入 `agents.max_concurrent_threads_per_session = max_agents`。`[agents]` 表头位于可移除的容量块之外，确保个人键保留正确的作用域。

已有的规范键 `agents.max_concurrent_threads_per_session` 和旧别名
`agents.max_threads` 仍归用户所有；两个键相等时也会原样保留。如果用户在
Plex 托管的规范键旁添加相同的本地旧别名，Plex 只移除自己的键和回执，
保留用户别名。显式的用户全局限制会保留，即使低于 `max_agents`。对于无法
证明适用的祖先 `.codex/config.toml` 候选，或可能设置容量的配置档，安装程序
会报告适用性未知并停止自动修改容量。在此不确定情况下，即使 `max_agents`
变化，现有未修改的 Plex 托管块及其回执也保持原样。确定适用性后，未修改的
Plex 托管块会随 `max_agents` 刷新；只有确认存在适用的显式继承限制或相同的
本地旧别名时，Plex 才会移除自己的键。不同别名，或布尔、非整数、非正数值，
会在写入前报告冲突。超出有符号 64 位正整数范围的值也会在写入前产生冲突；
这是配置表示范围，不是线程数量建议。被修改、缺失或未经管理的标记都会产生冲突。

`max_agents` 统计未完成的 Plex 任务。原生限制统计同时保持打开的子代理线程，
包括嵌套和空闲线程；不包括主线程。预览、应用和状态会分别显示来源、值和
可能的差异，并将会话激活状态标记为未知。配置检查只能证明文件中已保存的值；
安装程序不会重启 Codex。应用设置后打开新会话，并单独验证实际激活情况。

Codex 必须信任项目配置；安装后请打开新会话。预检会区分缺少启动工具、隐藏角色选择、角色被拒绝和调用被接受。若角色选择可用，即使未展示角色列表，也应请求团队中准确的角色；在支持的情况下使用新上下文和完整交接信息。配置文件检查无法证明当前会话已加载角色，或子代理实际使用了指定模型。
