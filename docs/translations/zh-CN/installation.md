# 安装

[English](../../installation.md) · [Русский](../ru/installation.md) · [Deutsch](../de/installation.md) · [简体中文](installation.md)

## 安装

在项目目录运行。需要 Git、curl、客户端 CLI，以及 uv 或 Python 3.11+。

**普通安装**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

**开发模式 · Codex**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --dev --client codex
```

选择客户端、范围、团队和模型配置，确认计划。推荐 **Project** 范围。安装后打开新的客户端会话。

安装和刷新时，最后的 **Apply this plan?** 默认选择 **Yes**。选择 **No** 可取消。归档其他代理及卸载仍需要单独确认。

模型配置档用于子智能体。请在主对话中选择根协调者的模型；安装计划会显示建议。
参见[主对话与团队](product.md#主对话与团队)。

安装器注册共享 Plex 插件并应用所选团队。插件提供技能；团队配置提供原生角色和托管指令块。开发模式使用本地技能链接。

[对话请求示例](README.md#对话示例)。

## 技能短名称 · Codex

标准安装通过符号链接提供 `$plex` 和 `$plex-setup`，指向共享 Plex 工作副本；插件保持启用。项目范围使用 `.agents/skills/`，用户范围使用 `$CODEX_HOME/skills/`（默认 `~/.codex/skills/`）。不复制技能内容，请保留源工作副本。

现有安装刷新一次配置后，打开新的 Codex 会话即可使用。其他技能会被保留并报告冲突。`--roles-only` 保留已有链接，但不会为新安装添加链接。带插件前缀的调用仍可使用。

## 其他 Codex 代理

Plex 自有任务只使用已检查的活动团队中准确的 `plex-<role>` 名称。其他已安装或内置代理不属于该团队；工作流内部执行者遵循该工作流的约定。

安装器列出所选范围内的其他 `.toml` 代理，提供**保留**（默认）或**移至备份**。这些代理对客户端仍可用，可能影响角色选择。可处理的文件移至 `.plex/backups/<timestamp>/codex/other-agents/`，需要时可从中手动恢复。其他范围、符号链接及在 `config.toml` 中显式注册的文件会被保留。被修改的托管角色仍会报告冲突。

Codex 原生角色选择还需要受信任的项目配置和新会话。安装器通过备份及归属检查管理所需的角色选择参数，并保留冲突的个人值。参见[配置](configuration.md)。

如果没有显式的原生容量限制，安装器会根据 `max_agents` 保存 Codex 子线程限制。预览、应用和状态会分别显示未完成的 Plex 任务与最多可打开的子代理线程数；主线程不计入。会话激活状态在 Codex 中得到验证前始终未知。安装器不会重启 Codex。

如果无法确定配置档或祖先配置层是否适用，即使 `max_agents` 变化，现有未修改
的 Plex 托管容量块及其回执也保持原样。只有确认显式继承限制适用，或存在相同
的本地旧别名时，Plex 才会移除自己的键。

无人值守清理需明确使用 `--archive-other-agents --client codex`；仅使用 `--yes` 会保留其他代理。`--dry-run` 不移动文件。

## 常用命令

若没有可选的 `plex` 命令（例如首次开发模式安装后），下文用 `~/.local/share/plex-ai/setup.sh` 代替 `plex`。

| 任务 | 命令 |
|---|---|
| 配置或刷新项目 | `plex` |
| 检查配置 | `plex status` |
| 下载新版本并打开安装器 | `plex update` |
| 预览安装，不写入 | `plex --dry-run --client codex --project .` |
| 预览卸载 | `plex uninstall --dry-run` |
| 卸载项目团队 | `plex uninstall` |
| JSON 状态 | `plex status --json` |
| JSON 卸载计划 | `plex uninstall --dry-run --json` |

已有团队时：

| 参数 | 用途 |
|---|---|
| **Update only** | 保留设置并刷新托管文件。 |
| **Reconfigure** | 使用已保存值重新打开菜单。 |

显式 CLI 选项仍生效。`plex` 使用当前工作副本；`plex update` 下载更新的已发布版本，包括预览版。

## 开发模式

- 仅支持 Codex 和 **project** 范围。两个 Plex 技能目录链接到源码副本，请保留该副本。
- 项目禁用共享插件，托管指令区块选择本地 Plex 技能。Codex 必须信任项目。云端插件及其他同名技能不受影响。
- 技能修改通过链接可见。角色、模型配置和工作流目录修改需要刷新安装并新建会话。开发模式保留至指定 `--no-dev`。

| 任务 | 命令 |
|---|---|
| 链接工作副本 | `./setup.sh --dev --client codex --project /path/to/project` |
| 恢复共享插件 | `./setup.sh --no-dev --client codex --project /path/to/project` |

## BMad

需要 Node.js/npm 和 uv。在菜单选择 `bmad` 团队，或运行：

| 任务 | 命令 |
|---|---|
| 安装选定官方技能并初始化项目 runtime | `plex --team bmad --client codex --install-bmad` |
| 使用已安装技能初始化 | `plex --team bmad --client codex --init-bmad` |

技能为用户共享。Setup 会先核对固定版本的来源，只安装缺失的所选技能并保留已有的有效文件。遇到不完整的技能目录时会保持原样并停止，等待检查。Runtime 属于项目。取消或后续失败时，已安装依赖/runtime 会保留。无人值守运行可添加 `--project . --yes`，接受显示的 BMad 默认值。

## 卸载

**项目团队** · 在项目目录运行：

```sh
plex uninstall --dry-run
plex uninstall
```

移除未修改的托管角色、Plex 指令块和所属技能链接及开发模式覆盖配置。块外的项目指令保留。托管文件被修改时会停止移除，等待检查。

**用户级团队** · 选择安装全局角色的客户端：

```sh
plex uninstall --scope user --client codex
```

**共享插件** · 仅在其他项目不再需要时移除。运行对应客户端的命令：

| 客户端 | 命令 |
|---|---|
| Codex | `codex plugin remove pnet-plex@pnet-plex` |
| Claude Code | `claude plugin uninstall pnet-plex@pnet-plex --scope user` |
| Antigravity | `agy plugin uninstall pnet-plex` |

Codex 也可通过 `/plugins` 浏览器卸载插件。参见 [OpenAI 插件指南](https://learn.chatgpt.com/docs/plugins#remove-a-plugin)和 [Claude Code 命令参考](https://code.claude.com/docs/en/plugins/cli-reference#plugin-uninstall)。

移除团队会保留 `.plex` 中的偏好设置和备份、BMad 依赖/运行时、可选启动命令和源码副本。移除插件是独立的客户端操作，不会移除其他项目的团队。只要仍有项目或开发链接使用共享源码目录，就应保留它。

## 参数参考

省略的设置保留已有值。每个应用的 preset 均保存 `interaction`。模型配置、覆盖及路径见[配置](configuration.md)。

### 客户端与范围

| 参数 | 用途 |
|---|---|
| `--project PATH` | 现有项目目录。 |
| `--client CLIENT` | codex、claude 或 antigravity；可重复选择多个客户端。 |
| `--host CLIENT` | 单客户端兼容别名，允许厂商专用模型配置。 |
| `--scope project / user` | 角色/指令范围，默认 project；普通插件为用户共享。 |
| `--instructions / --no-instructions` | 管理 Plex 指令区块，或跳过。 |

### 团队与模型

| 参数 | 用途 |
|---|---|
| `--team pnet / bmad` | 角色集合，新安装默认 pnet。 |
| `--model-profile PROFILE` | inherit、basic、plus、pro、pro-plus、ultra 或 ultra-plus。 |
| `--interaction MODE` | interactive、balanced（默认）或 auto。 |
| `--max-agents N` | 未完成 Plex 任务的正整数上限；Codex 原生线程容量会单独显示。 |

### 执行与输出

| 参数 | 用途 |
|---|---|
| `--dev / --no-dev` | 链接本地技能或退出开发模式，仅限 Codex/project。 |
| `--archive-other-agents` | Codex：明确授权将所选范围内其他可处理代理移至备份。 |
| `--roles-only` | 跳过 Plex 插件安装；显式 BMad 选项仍有效。 |
| `--command / --no-command` | 创建 ~/.local/bin/plex（默认）或跳过；开发模式不创建命令。 |
| `--install-command` | 仅安装命令，不替换其他命令，不能与 --dev 组合。 |
| `--dry-run` | 仅预览，不能与 --install-command 组合。 |
| `--yes` | 无提示执行；须指定客户端和项目路径（--scope user 可省略路径）。 |
| `--json` | status 或 uninstall 的 JSON 输出，包括卸载预览。 |
| `-h / --help` | 显示分组帮助和示例。 |

### BMad

| 参数 | 用途 |
|---|---|
| `--install-bmad` | 授权安装选定用户级技能及缺失 runtime。 |
| `--init-bmad` | 使用已安装的官方 setup 初始化 runtime。 |
| `--bmad-skill PATH` | 显式指定已安装的 BMad setup 技能目录。 |

### 源码选择 — update / GitHub 引导安装

| 参数 | 用途 |
|---|---|
| `--release TAG` | 使用发布标签，例如 v0.5.11。 |
| `--development` | 使用 main，不启用 --dev。 |
| `--checkout PATH` | 仅用于 GitHub 引导安装，默认 ~/.local/share/plex-ai。 |

引导安装在 `~/.local/share/plex-ai` 保存共享副本，请保留。引导安装/update 的 `--dry-run` 仅预览源码选择，其余安装选项转发给 setup。

## 文件保护与故障排查

- 卸载也会删除收据确认归 Plex 管理且未被修改的 Codex 路由设置；安装前已有的相同设置仍归用户所有。
- 卸载默认作用于项目。`--client codex` 限定客户端，`--scope user` 选择用户级角色，`--yes` 无提示确认卸载。
- 仅删除未修改的托管角色、指令区块和技能链接及开发模式覆盖配置。共享插件、源码、偏好及备份保留；托管文件被修改或格式未知时停止。
- 源码更新拒绝修改有本地更改、来源不同或使用符号链接的副本。插件管理器更改及已完成的客户端安装与角色回滚分离。
- `status` 优先检查项目，否则检查用户范围。它检查配置和插件发现，不证明实际模型路由。

| 如果… | 使用方式 |
|---|---|
| PATH 中没有 plex | 使用 ~/.local/bin/plex，或在源码目录运行 ./setup.sh。 |
| 命令属于另一个副本 | 使用显示的 setup.sh 路径，已有命令会保留。 |
| 技能或托管文件冲突 | 检查报告的文件，安装器不会覆盖。 |
| 现有插件覆盖阻止 --dev | 手动设置 enabled = false；退出时保留已有覆盖。 |

## 输出

颜色仅用于终端。`NO_COLOR=1` 或 `TERM=dumb` 选择纯文本和数字菜单；重定向输出为纯文本。使用 `--json` 时，stdout 不含样式或进度消息。
