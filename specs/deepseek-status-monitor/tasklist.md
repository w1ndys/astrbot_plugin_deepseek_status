# 需求实施计划

按带教规则：**一个任务 = 一个函数**。轮到某个函数时先单独谈它的判断规则；标注「判断规则待定」的任务在谈定前不写代码。

- [x] 0. 范围切换后的配置对齐
  - [x] 0.1 `_conf_schema.json`：五个字段，`event_retention_days` 改为 `history_retention_days`
  - [x] 0.2 `metadata.yaml`：`short_desc` / `desc` 改为整体状态监控
  - [x] 0.3 `AGENTS.md`：分层说明去掉组件、feed 与严重度表
  - [x] 0.4 `_conf_schema.json` / `metadata.yaml`：状态历史文案改为变更记录

- [x] 1. 实体层（结构任务）
  - [x] 1.1 `entity/constants.py`：`PLUGIN_NAME`、`STATUS_PAGE_BASE`、`PAGE_ID`、`REQUEST_TIMEOUT_SECONDS`、`CLOSED_EVENT_STATUSES`、`STATUS_NORMAL`、`STATUS_ABNORMAL`、`NOTIFY_ABNORMAL`、`NOTIFY_RECOVERED`、`COMMAND_NAME`、`DEFAULT_TIMEZONE`
  - [x] 1.2 `entity/models.py`：`StatusEvent`、`Snapshot`、`Subscription`、`Notification`
  - [x] 1.3 实体层单测：默认时区可用、常量取值符合设计
  - [x] 1.4 `entity/constants.py`：`STATUS_LABELS`、`EVENT_TYPE_LABELS`、`NOTIFY_CHANGES`；同步 `entity/models.py` 注释

- [x] 2. 数据层
  - [x] 2.1 `data/db.py::connect`
  - [x] 2.2 `data/db.py::init_db`：三张表 `subscriptions` / `status_history` / `push_records`
  - [x] 2.3 `data/db.py::utc_now`
  - [x] 2.4 `data/db.py::get_db_path`：显式传插件名
  - [x] 2.5 `data/subscription_store.py::list_subscriptions`
  - [x] 2.6 `data/subscription_store.py::get_by_session`
  - [x] 2.7 `data/subscription_store.py::get_by_id`
  - [x] 2.8 `data/subscription_store.py::enable_session`：已存在且停用时重新启用、保留备注
  - [x] 2.9 `data/subscription_store.py::disable_session`
  - [x] 2.10 `data/subscription_store.py::create`：重复会话返回失败原因
  - [x] 2.11 `data/subscription_store.py::update`
  - [x] 2.12 `data/subscription_store.py::delete`
  - [x] 2.13 取消：随 `status_history` 删除 `record_transition`
  - [x] 2.14 取消：随 `status_history` 删除 `list_history`
  - [x] 2.15 `data/history_store.py::record_push`：写一条推送结果（成功/失败、原因、原始报错）
  - [x] 2.16 取消：删除 `list_pending_retry`（不重试）
  - [x] 2.17 取消：删除 `mark_retried`（不重试）
  - [x] 2.18 `data/history_store.py::purge_expired`：历史按采集时间、推送按推送完成时间，早于截止点才删
  - [x] 2.19 数据层测试：临时目录 SQLite，不 import `astrbot`
  - [x] 2.20 取消：`record_transition` 过滤已结束事件（随 `status_history` 一起删除）
  - [x] 2.21 `data/db.py`：用 `change_log` 表替换 `status_history`
  - [x] 2.22 `data/history_store.py::record_change`：每条变化一行
  - [x] 2.23 `data/history_store.py::list_changes`：按采集时间倒序分页
  - [x] 2.24 `data/history_store.py::purge_expired`：改删 `change_log` 与推送记录
  - [x] 2.25 数据层测试更新：变更记录写入、分页与清理

- [x] 3. 采集与解析
  - [x] 3.1 `business/collector.py::api_url`
  - [x] 3.2 `business/collector.py::make_timeout`
  - [x] 3.3 `business/collector.py::fetch_summary_active`
  - [x] 3.4 `business/parser_api.py::parse_event`（判断规则：ID 必须是整数，字符串按结构异常）
  - [x] 3.5 `business/parser_api.py::parse_snapshot`（判断规则：保留全部事件，整体状态按过滤 `resolved` / `completed` 后计算）
  - [x] 3.6 `business/parser_api.py::event_link`
  - [x] 3.7 解析测试：真实 `summary_active.json` 正常态；非正常态与已结束事件用构造对象

- [x] 4. 判定与文案
  - [x] 4.1 取消：无 `detect_transition`（整体翻转不再落库）
  - [x] 4.2 `business/detector.py::detect_event_changes`（新出现、状态变化；消失不算）
  - [x] 4.3 `business/detector.py::changes_key`
  - [x] 4.4 `business/text.py::resolve_timezone`
  - [x] 4.5 `business/text.py::to_local`：`YYYY-MM-DD HH:MM:SS`，不带偏移后缀
  - [x] 4.6 `business/text.py::render_changes`：版式 A（每条一行 + 链接缩进），空标题用“未命名事件”
  - [x] 4.7 `business/text.py::render_summary`：正常一句状态，非正常列出未结束事件
  - [x] 4.8 `business/text.py::render_status_reply`：复用摘要，空快照提示刚启动
  - [x] 4.9 `business/text.py::render_help`：使用实际触发的指令名
  - [x] 4.10 文案与判定测试：`tests/test_detector.py`、`tests/test_text.py`

- [x] 5. 轮询编排
  - [x] 5.1 `business/monitor.py::Monitor.__init__`：显式依赖 + `MonitorConfig`
  - [x] 5.2 `business/monitor.py::Monitor.start`：关闭停旧任务；已启动先停再重启
  - [x] 5.3 `business/monitor.py::Monitor.stop`：取消并等待任务退出
  - [x] 5.4 `business/monitor.py::Monitor.run`：立即首轮；按开始时间对齐，超时立刻下一轮；配置每轮重读
  - [x] 5.5 `business/monitor.py::Monitor._tick`：采集 → 差分 → 写变更记录 → 推送 → 清理；采集失败不清理，记录写失败保留已写行
  - [x] 5.6 `business/monitor.py::Monitor._collect`：请求失败与结构异常分别记日志并返回 None
  - [x] 5.7 `business/monitor.py::Monitor._dispatch`：逐个发送，相邻两条间隔 1 秒
  - [x] 5.8 取消：无 `retry_failed`（不重试）
  - [x] 5.9 `business/monitor.py::Monitor.push_summary`：主动查询一次，失败不影响订阅开启，不更新基线
  - [x] 5.10 `business/monitor.py::Monitor.snapshot`：返回最近一次成功快照
  - [x] 5.11 编排测试：假采集函数，覆盖基线、状态变化、同轮汇总、消失不推、变更记录写失败与清理

- [x] 6. 入口层
  - [x] 6.0 `main.py::Plugin._register_routes`：注册 8 条 Web API
  - [x] 6.1 `main.py::Plugin.__init__`：建库、转换配置、创建 Monitor、注册路由
  - [x] 6.2 `main.py::Plugin.initialize`：启动轮询并记一行日志
  - [x] 6.3 `main.py::Plugin.terminate`：先停轮询再关连接
  - [x] 6.4 `main.py::Plugin.dsstatus`：状态 / 开 / 关 / 帮助；全局关时只写订阅不推送
  - [x] 6.5 `main.py::page_get_settings`：返回五个非密钥配置
  - [x] 6.6 `main.py::page_save_settings`：缺字段沿用当前值，非法整单 400，保存后热重启
  - [x] 6.7 `main.py::page_get_status`：关闭时隐藏旧快照
  - [x] 6.8 `main.py::page_list_subscriptions`：返回全部订阅（含停用）
  - [x] 6.9 `main.py::page_create_subscription`：重复会话 400；启用时补推摘要
  - [x] 6.10 `main.py::page_update_subscription`：停用改启用时补推摘要
  - [x] 6.11 `main.py::page_delete_subscription`：不存在返回 404
  - [x] 6.12 `main.py::page_list_changes`：变更记录分页，默认 20、最多 100
  - [x] 6.13 入口层测试：注入 astrbot 替身，覆盖命令分支、配置校验与订阅接口

- [x] 7. 前端（一个视图，三个 Tab）
  - [x] 7.1 `dashboard/` 工程骨架与构建配置：pnpm + React 19 + antd 6 + Vite 8，单份 IIFE 输出到 `views/status/`
  - [x] 7.2 概览与全局配置视图：状态卡 + 五字段表单，打开/刷新/保存后请求
  - [x] 7.3 订阅管理视图：列表、即时开关、新增/编辑/删除
  - [x] 7.4 变更记录视图：服务端分页，打开/刷新请求
  - [x] 7.5 构建产物与页面检查：三个 Tab 预览通过，产物随仓库提交

- [ ] 8. 收尾
  - [ ] 8.1 写 `README.md`（安装、五个配置项、命令、三个 Tab、数据目录）
  - [ ] 8.2 真实网络冒烟（默认 `skip`，`DEEPSEEK_STATUS_LIVE=1` 才跑）
  - [ ] 8.3 在 `w1ndys/dev-memory` 的项目 README 里更新本周期
