# astrbot_plugin_deepseek_status

AstrBot 插件，监控 DeepSeek 官方状态页。用中文交流。

## 编码契约

本仓库开发默认启用以下两套**全局安装**的 skill（`~/.agents/skills/`），不需要每次再喊触发词：

- `human-coding-contract`：人话编码契约，管朴素语法、分层、注释与质量门禁。
- `mentored-development`：带教式开发，动手写函数体前先和用户把函数、签名、调用顺序与分支条件谈定；每次停下讲清这次改动在业务路径上的位置，并附一行架构地图更新。

skill 只走全局安装，**不要**往仓库里拷 `.agents/`、`.ohmyagent/` 或其它副本。

硬规则：

- 缺背景就停，问用户；不要猜接口字段、页面结构或业务规则。
- 设计顺序：实体 → 数据 → 业务 → 入口。入口层不直接执行 SQL。
- 函数（不含空行和注释）≤ 50 行；普通语法，不引入 DI、反射、元类、嵌套推导或类型体操。
- 每个文件、函数、`if` 都要有短中文注释；条件注释写业务目的与后果。
- 写完一轮、跑检查、**不要提交**；同一条消息给出审阅路径、本次完成、检查与进度，用户回「继续」或「1」才提交。
- 等审时不做下一片工作。

## 分层

| 层 | 目录 | 职责 |
|---|---|---|
| 实体 | `entity/` | 固定值（接口地址、状态取值、时区）与 dataclass 数据形状；不依赖 AstrBot，不访问数据库 |
| 数据 | `data/` | SQLite 连接、建表与两个 store（订阅、历史）；只被业务层调用 |
| 业务 | `business/` | 采集、解析、整体状态翻转判定、文案与轮询编排 |
| 入口 | `main.py`、`views/status/` | 插件类、Web API、`dsstatus` 命令；只做参数校验与转发 |

## 外部数据源

- 只读 DeepSeek 状态页的 `summary/active`；不读 `change/list`、`change/info`、`summary/structure`，也不读 Atom/RSS。
- 整体状态只看 `active_changes` 过滤 `resolved` / `completed` 后是否为空。
- 不调用状态页的邮箱订阅接口，不向 DeepSeek 提交任何数据。
- 接口没有正式承诺：结构不符保留上一份快照并记「接口结构异常」，请求失败记「请求失败」，两者都不生成通知。

## 存储与配置

- 业务库在 `data/plugin_data/astrbot_plugin_deepseek_status/deepseek_status.db`，用 `StarTools.get_data_dir(PLUGIN_NAME)` **显式传插件名**；从子模块调用不传名会抛 `RuntimeError`。
- 非密钥配置放 `_conf_schema.json`；本插件没有密钥字段。
- 时间列存 UTC ISO8601 带 `Z`；展示层用配置的时区（`display_timezone`，默认 `Asia/Shanghai`），非法值回退默认并记 warning。

## 检查

```bash
python3 -m unittest discover -s tests -t .
ruff check .
pyrefly check
```

AstrBot 要求 Python ≥ 3.12，本机 `python3` 已是 3.12.14（`~/.local/bin` 优先），统一用 `python3`。ruff 规则在 `pyproject.toml`：行宽 100、规则集与 `astrbot_plugin_w1ndys_rules` 一致；lint 报错当 bug 处理，不要绕过。

pyrefly 规则也在 `pyproject.toml`：`preset = "default"`，当前只查 `entity/`、`data/`、`tests/`（AstrBot 依赖层补 `typings/astrbot/` 后再纳入）。类型报错同样当 bug 处理；第一次拉包用 `uvx pyrefly check`。

## 本机环境

2026-10-17 整理。本机 Python 已统一到 uv 管理的 3.12.14：

| 命令 | 指向 | 版本 |
|---|---|---|
| `python` / `python3` / `python3.12` | `~/.local/bin`（uv） | 3.12.14 |
| `pip` / `pip3` | 同上 | 26.2.1（python 3.12） |
| `/usr/bin/python3` | macOS 自带 | 3.9.6（SIP 保护，不要用） |

- PATH 顺序由 `~/.zprofile` 与 `~/.zshenv` 保证：`~/.local/bin` 排在 Homebrew 与 `/usr/bin` 之前。
- Homebrew 已无任何 Python（原 `python@3.14`、`python@3.15` 已卸载）；不要依赖 `python3.14`、`python3.15`。
- 本机 ollama、mlx 及 25 GB 模型已于同日移除；与本插件无关，不要假设可用。
- 只有绕过 shell 的 GUI 进程会拿到 `/usr/bin/python3`（3.9.6）；脚本里遇到这种情况显式写 `~/.local/bin/python3`。

## 提交

- 提交信息格式 `类型(内容): 中文描述`，不加 emoji。
- 未经用户明确允许不要 push；合并走 PR。
- 密钥、Token、Cookie 不进入代码、注释、日志、diff 和提交信息。
