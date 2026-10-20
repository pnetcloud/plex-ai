# 安装与命令行参数

[English](../../installation.md) · [Русский](../ru/installation.md) · [Deutsch](../de/installation.md) · [简体中文](../zh-CN/installation.md)

需要 Git、curl、所选客户端的 CLI，以及 uv 或 Python 3.11+。安装 BMad 依赖还需要 Node.js/npm 和 uv。

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


后续失败不会回滚插件管理器操作或已经完成的客户端安装。

来自其他副本的现有命令、外部文件或失效链接会保留并提示，不会阻止正常安装。
安装器会显示自己的启动路径。显式 `--install-command` 仍拒绝覆盖无关命令。

项目范围的 `bmad` 团队缺少运行时时，安装器提供官方初始化、切换到 `pnet` 或取消。
缺少 BMad setup 技能时，另行提供用户范围的依赖安装。必须明确批准：选中的用户技能
可能被替换，并由其他项目共享。现有插件保持不变。

`--install-bmad` 授权安装和项目初始化；`--init-bmad` 使用已安装技能。
`--yes` 接受显示的模块默认值，`--dry-run` 不写入任何文件。确认计划后运行官方 BMad setup，
只询问未回答的模块问题。后续步骤失败时，已创建运行时和依赖仍会保留。

新安装使用 `skills@1.7.4` 和官方 BMad 修订 `495ef6e0996d07b23359cc4d6c73a1aa2f3ba5ad`，
仅选择团队入口和工作流技能、`bmad` hub 及两个模块记录。包含当前插件 marketplace 尚未提供的 PO。
需要 Node.js/npm 和 `uv`。官方 Skills CLI 支持 Codex、Claude Code 和 Antigravity。

发现时优先使用项目和用户的直接技能目录。也支持已安装且启用的 Codex/Claude Toolbox 插件；
不能仅凭缓存目录认定已安装。可用 `--bmad-skill /path/to/installed/bmad` 明确指定 hub。
用户范围角色仍要求每个工作项目具备运行时。


## 现有安装与兼容性

选择客户端、范围和项目后，安装器通过安装记录识别已有团队，提供
**Update only**（`refresh`，仅更新）或 **Reconfigure**（`configure`，重新配置）。
默认选择更新；显式设置参数会使重新配置成为默认选项。仅更新会跳过团队、模型配置、
交互模式和并发数问题，并分别保留每个客户端的指令区块选择。显式 CLI 覆盖仍生效，
安装计划仍须确认。处理多个客户端时，从发现第一个已有团队起复用所选操作。
仅存在共享插件并不意味着新项目已安装团队。

使用 `--yes` 时，没有显式覆盖的设置保持不变。重新配置使用已保存值作为菜单默认值。
缺少 BMad 依赖时仍可能需要决策；更新模式不会提供切换团队的选项。
刷新使用当前工作副本的定义；先通过 `plex update` 或 GitHub 安装器下载新源码。
开发模式及其本地源保持不变。

兼容处理继续由现有解析器负责：补充缺失默认值、保留覆盖设置、迁移支持的旧标记。
更新时保留已有厂商专用模型配置标识。替换托管文件时沿用备份和所有权检查。
托管文件被修改，或配置及安装记录包含未知字段时会停止；个人指令及外部文件保留。
不强制重置，也不引入通用迁移框架。插件管理器更改与角色文件回滚相互独立。

## 使用 Codex 进行本地开发

在 Plex 工作副本中连接测试项目，无需发布新版本：

```sh
./setup.sh --dev --client codex --project /path/to/test-project
```

自 v0.5.0 起可用；请使用需要测试技能的工作副本。

`--dev` 目前仅支持项目级 Codex。它将完整的 `plex` 和 `plex-setup` 技能目录
链接到项目的 `.agents/skills/`，并在项目的 `.codex/config.toml` 中禁用
`pnet-plex@pnet-plex`。用户配置和其他项目保持不变。Codex 必须信任该项目，
才会读取项目配置。这不会禁用云端管理的插件或其他同名技能。

`AGENTS.md` 或选定指令文件中的托管区块要求仅使用项目中的这两个 Plex 技能。
先解析符号链接：引用文件、检查脚本、`teams/`、协调器和模型配置均来自同一工作副本。
BMad 仍为单独安装的依赖。请保留工作副本。

技能修改会通过链接即时可见；重新打开 Codex 会话以加载修改。
修改角色、模型配置或工作流目录后，需要重新运行安装程序。
`plex status --client codex` 显示配置的开发源并检查链接和本地插件覆盖设置，
但无法证明运行中的模型实际加载了哪些指令。再次安装会保留开发模式，除非指定 `--no-dev`。

```sh
./setup.sh --no-dev --client codex --project /path/to/test-project
```

`--no-dev` 删除 Plex 创建的链接和插件禁用区块，刷新团队并恢复共享插件安装。
`plex uninstall` 也会清理开发状态。外部技能或被修改的链接、覆盖区块会阻止更改。
已有的显式插件覆盖设置会保留：进入开发模式前请手动将 `enabled = true`
改为 `false`；原先已有的 `false` 在退出后仍然保留。个人指令文本不会被删除。
`.plex/dev.json` 记录本地源及覆盖区块的所有权，请勿提交此机器专用状态。
`--dry-run` 仅预览。`--dev` 与选择 `main` 的 `plex update --development` 相互独立。

## 终端输出

安装、状态、源码更新和卸载使用统一的标题、对齐设置、智能体/模型表格和突出显示的命令。
绿色表示成功，黄色表示警告，红色表示错误；路径和说明使用较弱的显示样式。
安装计划显示托管指令文件，不再输出完整模板。窄终端会逐项显示智能体设置，避免挤压表格。

颜色和强调仅用于终端。重定向输出保持纯文本；`NO_COLOR=1` 或 `TERM=dumb`
也会启用纯文本和数字菜单。`--help` 按用途分组参数。状态和卸载支持 `--json`，
包括卸载预览；此时 stdout 只包含 JSON，不含装饰或进度信息。

```sh
plex --help
plex status
plex status --json
plex uninstall --dry-run
plex uninstall --dry-run --json
NO_COLOR=1 plex status
```

## 命令

| 命令 | 行为 |
|---|---|
| `plex setup` | 打开安装程序，也是省略命令时的默认操作。 |
| `plex status` | 只读检查配置及插件或源的发现状态；支持 --json。 |
| `plex update` | 下载所选版本，然后重新打开安装程序。 |
| `plex uninstall` | 删除未修改的托管角色、指令及开发链接和覆盖区块；保留共享依赖、源码和偏好。 |

`status` 和 `uninstall` 支持 `--project`、重复的 `--client`（或 `--host`）及 `--scope`。卸载支持 `--dry-run` 和 `--yes`。`--dev`/`--no-dev` 仅用于安装；状态检查和卸载会自动识别开发模式。

## 所有安装参数

交互安装仅为所有所选客户端询问一次模式，默认选中已保存模式，新安装默认 `balanced`。每次应用配置都会显式保存 `interaction`，包括刷新旧配置时。

| 参数 | 行为 |
|---|---|
| `--project PATH` | 现有项目目录；交互安装会询问未提供的路径。 |
| `--client codex\|claude\|antigravity` | 选择客户端；可重复以选择多个客户端。 |
| `--host CLIENT` | 单个客户端的兼容别名，也支持厂商专用模型配置。 |
| `--scope project\|user` | 项目级（默认）或用户级角色和指令区块；普通插件始终为用户共享。 |
| `--team pnet\|bmad` | 角色集合；保留已有团队，新安装默认 pnet。 |
| `--model-profile PROFILE` | 共享等级：inherit、basic、plus、pro、pro-plus；保留已有配置。厂商专用标识见配置文档。 |
| `--interaction interactive\|balanced\|auto` | 智能体提问策略；保留已有值，默认 balanced。 |
| `--max-agents N` | 并发任务上限，必须为正整数；保留已有值。 |
| `--instructions / --no-instructions` | 管理 Plex 指令区块（默认），或跳过。 |
| `--dev / --no-dev` | 仅限项目级 Codex：链接工作副本技能或退出开发模式。需要托管指令；省略时保留开发模式。 |
| `--install-bmad` | 授权安装选定的官方用户级 BMad 技能并初始化缺失的项目 runtime；可能替换选定技能文件。 |
| `--init-bmad` | 使用已安装的官方 setup 初始化缺失的项目 BMad runtime。 |
| `--bmad-skill PATH` | 显式指定已安装的官方 BMad setup 技能目录。 |
| `--roles-only` | 跳过 Plex 插件安装；显式 BMad 依赖选项仍然有效。 |
| `--command / --no-command` | 创建可选的 ~/.local/bin/plex 命令（默认），或跳过；开发模式不会安装此命令。 |
| `--install-command` | 仅安装指向此工作副本的命令，不覆盖其他命令。不能与 --dev 组合。 |
| `--dry-run` | 仅预览，不写入；不能与 --install-command 组合。 |
| `--yes` | 无提示执行；须指定客户端和项目路径（使用 --scope user 时可省略路径）。BMad 初始化采用显示的默认值。 |
| `--json` | 以机器可读格式输出 status 或 uninstall。 |
| `-h / --help` | 显示可用参数。 |

## 下载与更新参数

指定发布标签：`plex update --release TAG`；使用 `main`：`plex update --development`。GitHub 引导安装程序接受相同的源选项及 `--checkout PATH`（默认 `~/.local/share/plex-ai`）；`--checkout` 不属于 setup 选项。引导安装/update 的 `--dry-run` 仅预览源选择，其余安装参数会传递给 setup。示例：

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --release v0.5.1
```

配置优先级与托管文件见[配置](../../../docs/translations/zh-CN/configuration.md)。
