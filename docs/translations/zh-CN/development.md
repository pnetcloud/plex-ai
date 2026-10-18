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
