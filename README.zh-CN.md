# pNet Plex

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [简体中文](README.zh-CN.md)

[文档](docs/translations/zh-CN/README.md) · [测试与效率](docs/translations/zh-CN/testing.md)

**组建你的团队，协调每一步工作。**

pNet Plex 是面向软件开发的 **Agent Harness，用于多智能体编排与协调
（multi-agent orchestration and coordination）**。你可以定义专业角色、选择模型，
并在已有的智能体编程工具中，将规划、实现和审查串联起来。

一个能力出色的智能体可以独立完成很多工作。团队协作则带来了新的问题：
每项任务由谁负责，需要哪些上下文，使用什么模型，以及如何验证结果。
Plex 通过项目级团队配置和协调技能（skills），让这些决策清晰可见。

团队定义和原生代理位于 `teams/<team>/`，各团队的模型配置位于 `teams/<team>/profiles/`。`plex-setup` 技能从软件包根目录读取此目录。

根协调器的指令位于 `teams/<team>/coordinator.md`；`plex` 验证已应用的配置后加载所选团队的指令。

## 为什么叫 Plex？

这个名字源于 *multiplex*：通过一个共享系统汇聚多个信息流。
在 Plex 中，这些信息流就是各个专业智能体为共同目标做出的贡献。
每个角色都有明确的职责，协调者负责整合各方的工作。

## 智能体编排、协调与 Agent Harness

- **编排（Orchestration）**组织工作流程：选择合适的角色，委派范围明确的任务，
  遵循依赖关系，并收集结果以进行整合。
- **协调（Coordination）**让团队保持一致：共享相关上下文，明确文件修改职责，
  暴露阻塞问题，并安排独立审查。
- **Agent Harness** 提供可复用的支撑机制：项目配置、可复用技能、模型配置方案，
  以及针对各智能体运行环境的原生角色定义。

当前运行的智能体担任协调者。Plex 遵循所在运行环境的执行机制和权限规则，
无需独立的后台服务或界面。如果输入条件和文件职责划分允许，独立任务可以并行执行。
小任务可以使用小团队；委派工作应当有实际价值。

## 重点平台

Plex 专注于三个智能体生态：

| 平台 | Plex 集成状态 |
| --- | --- |
| **OpenAI Codex** | 已实现；已有隔离环境下的安装与配置检查 |
| **Anthropic Claude Code** | 已实现原生角色生成；实际执行仍需验证 |
| **Google Antigravity** 与 **Gemini 模型** | 已验证原生集成与部分实际任务测试；受客户端及模型限制 |

以上是产品当前的重点。其他运行环境暂未列入路线图。
运行环境与模型是两个独立的选择：提供某个模型的配置，并不意味着支持另一个运行环境。
Gemini CLI 是独立的运行环境，目前不在集成范围内。

## 你的团队，你的模型

可以先使用 **pnet**：PM 明确任务，explorer 探索项目，researcher 核实外部资料，
dev 实现修改，reviewer 审查变更，QA 验证实际行为。协调器按需选择角色，默认最多并行三项任务。
选择 **BMad** 可使用已安装的 BMad 技能和工作流；pnet 无需依赖 BMad。

团队组成与模型选择相互独立。选择模型配置方案，调整各角色的设置，
并将这些选择保存在项目中。Plex 创建项目原生角色，帮助协调者将它们用于当前任务。

质量、速度和成本的改善需要通过测量来确认；增加智能体数量本身并不代表结果会更好。

## 工作方式

```mermaid
flowchart TD
    Root["协调者：分配任务并整合结果"]
    Recon["按需开展探索与调研"]
    Frame["按需由 PM 或架构师检查任务定义"]
    Work["在文件职责明确的前提下实现"]
    Verify["独立验证与审查"]
    Root -->|分配任务| Recon
    Recon -->|调研结果| Root
    Root -->|需要验证假设时| Frame
    Frame -->|约束与任务约定| Root
    Root -->|分配任务| Work
    Work -->|变更与检查结果| Root
    Root -->|实现稳定后| Verify
    Verify -->|证据与发现| Root
```

协调者只从已配置的团队中选择当前需要的角色。清晰且范围明确的任务可以直接进入实现。
当任务范围、验收标准或技术不变量需要确认时，再引入 PM 或架构师。
如果输入条件和文件职责划分允许，调研与审查可以并行进行。

在 BMad 模式下，包装层会激活实际安装的技能，并遵循该版本的工作流与自定义配置。
它不会将菜单命令或步骤顺序写死，也会保留需要人工决策的环节。
图中的箭头表示任务分配和结果返回；只有运行环境与任务交接约定明确授权时，
子智能体才可以继续委派任务。

## 安装范围与托管指令

运行 `./setup.sh`，先选择一个或多个客户端（空格键勾选，Enter 继续），再选择团队安装范围。**项目级**是推荐的默认选项；
**用户级（全局）**让该用户的各个项目都可使用同一团队。
Codex 使用 `CODEX_HOME`，Claude 使用 `CLAUDE_CONFIG_DIR`。
无人值守安装可使用 `--scope project --project <路径>` 或 `--scope user`，
并指定 `--host <平台> --yes`。

配置与安装记录保存在所选项目或平台用户目录下的 `.plex/` 中。
Plex 优先检查项目配置，遇到损坏的项目配置会报告错误；全局安装不会删除
项目智能体。共享插件在所有受支持的运行环境中都安装到用户级；所选范围决定团队文件的位置。
所有客户端共用一个配置档位：Inherit、Basic、Plus、Pro 或 Pro+，Plex 自动使用对应的 OpenAI、Anthropic 和 Google 设置。无交互安装可重复使用 `--client` 参数。
完整安装还会创建 `~/.local/bin/plex`；使用 `--no-command` 可跳过快捷命令。
请从目标项目目录启动安装程序，或传入 `--project`。一次运行会安装插件并配置团队，无需另行运行 `plex-setup`。
启动器优先使用 `uv`；否则可用 Python 3.11+ 运行编号菜单。

安装程序默认在原生指令文件中添加由 `<!-- plex:start -->` 和
`<!-- plex:end -->` 标记的区块：Codex 使用 `AGENTS.md`，Claude 使用
`CLAUDE.md`，Antigravity 使用 `GEMINI.md`/`AGENTS.md`。
安装程序会遵循 Codex 已有的 override 文件与配置的 fallback 文件。
**Plex 只管理自己的区块，保留区块外的全部文本。** 请把个人规则放在区块外。
更新前会备份文件；区块内的手动修改或错误标记会作为冲突报告。
重复安装不会重复添加区块。使用 `--no-instructions` 可保持指令文件不变，
`--dry-run` 只预览而不写入。应用后请重新加载智能体环境。

## 发布状态

这个早期开发预览版包含 `plex` 和 `plex-setup` 技能、基于本地仓库副本的安装程序
（`setup.py` / `setup.sh`）、团队预设、模型配置方案、原生插件清单、文档及汇总测试结果。
自动化测试和原始实验资料在公开仓库之外维护。实际委派与模型路由仍需针对客户端验证；
这是早期预览版。

各平台的分发清单位于 [`plugins/`](plugins/README.md)。安装程序会先为所选平台组装完整的插件包，再进行安装。


角色指令明确区分工作步骤、重点、质量检查和返回结果，并参考 [Awesome Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents) 进行适配；详见[第三方声明](THIRD_PARTY_NOTICES.md)。

## 许可证

pNet Plex 采用 [MIT 许可证](LICENSE)。
