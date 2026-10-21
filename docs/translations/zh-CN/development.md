# 开发

[English](../../development.md) · [Русский](../ru/development.md) · [Deutsch](../de/development.md) · [简体中文](development.md)

## 源码布局

| 路径 | 职责 |
|---|---|
| `install.sh` | 从 GitHub 下载与更新入口 |
| `setup.sh`、`setup.py` | 安装器与可选 `plex` 快捷命令 |
| `skills/plex/` | 显式协调入口与 preflight |
| `skills/plex-setup/` | 配置技能、解析器和指令块模板 |
| `teams/<team>/` | 团队、根契约、角色与配置档 |
| `plugins/<host>/` | 原生清单模板 |
| `.build/plugins/<host>/` | 生成的独立包 |
| `tests/` | 配置、打包与隔离安装检查 |
| `docs/` | 英文源及翻译 |
| `_bmad/custom/` | 仓库开发使用的 BMad 定制 |

修改行为前阅读产品、架构与配置；修改提示词或团队前阅读角色契约。
保留其他人的工作区修改。未被要求时不要提交或发布。

## 检查

可移植测试包含在 `tests/` 中。CI 在 Linux/macOS 上检查 Python 3.11/3.14，
发布需等待这些检查通过。缺少对应 CLI 时跳过原生客户端检查；模型运行和私有基准数据另存。
从仓库根目录运行：

```sh
uv run --with pyyaml --with questionary==2.1.1 python -m unittest discover -s tests -v
```

测试覆盖解析、范围、指令块、覆盖设置、冲突、回滚、渲染、打包，以及 CLI 可用时的临时安装。
这些测试不调用模型。配置检查不能证明实际模型路由、质量、延迟或节省；
这些需要[评估协议](../../../EVALUATION.md)。聚合结果见[测试](testing.md)，原始证据单独保存。

### CI 覆盖范围

| 环境 | 检查 |
|---|---|
| Ubuntu 和 macOS，Python 3.11/3.14 | 完整测试套件、shell 语法、本地 Markdown 链接目标与包约定 |
| Docker，Python 3.11 slim | 三个客户端的项目/用户安装、刷新、配置检查和卸载；保留个人指令及其他代理 |

Docker 检查使用不含 uv、questionary 或客户端 CLI 的纯 Python 环境。
以非特权用户、无网络、只读源码目录运行。检查的是 `--roles-only` 配置，
不包含原生插件或 BMad 安装。这些任务不证明原生 Windows 支持或模型运行行为。

具体 Docker 命令见 [CI 工作流](../../../.github/workflows/ci.yml)。
发布要求该工作流的所有任务成功完成。

## 仓库开发的 BMad 环境

通过客户端管理器安装指定的官方 BMad 技能和插件，然后在仓库中使用已安装 Toolbox 的 `bmad` 配置流程。
它会生成 `_bmad/`；共享定制指向 `docs/` 与 `_bmad-output/`。
不要从 vendor 源码复制运行时，也不要创建第二套初始化机制。

已有运行时时可检查配置：

```sh
uv run _bmad/scripts/resolve_config.py --project-root .
```

全局技能和插件副本并存时，应确认实际激活的技能身份。
项目安装不应顺带删除或更新全局技能。

## 打包与文档

`.gitignore` 中的公开目录和文件类型模式决定导出范围。开发运行时、机器路径、注册表和原始实验不进入客户端包。
管理器安装的是 `.build/plugins/<host>`，不只是清单模板；请保留注册的本地来源。
安装器修改应复用现有解析和应用流程。

英文文档在 `docs/`；`translations/ru`、`translations/de`、`translations/zh-CN`
镜像相同文件名和模板目录。同步更新各语言与导航，保持测量数字一致，明确标注定性评价，
从当前指南中移除过期研究和迁移记录。

根目录 `README.md` 是英文项目概览。翻译位于
`docs/translations/<语言>/README.md`，指南目录为 `index.md`。
安装说明与其他指南统一保存在 `docs/` 中。
