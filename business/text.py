# 业务层文案：时区解析与后续的通知/命令文本渲染。
# 本文件不访问数据库；AstrBot 的 logger 只在运行时存在，测试环境可缺席。
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..entity.constants import (
    CLOSED_EVENT_STATUSES,
    DEFAULT_TIMEZONE,
    EVENT_TYPE_LABELS,
    STATUS_LABELS,
    SUBCOMMAND_HELP,
    SUBCOMMAND_OFF,
    SUBCOMMAND_ON,
)
from ..entity.models import Snapshot, StatusEvent

try:
    from astrbot.api import logger
except ImportError:
    # 测试环境不装 AstrBot；运行时一定有，缺了只影响非法时区的 warning
    logger = None


def resolve_timezone(raw: str) -> ZoneInfo:
    """把配置里的 IANA 名称解析成时区；空或非法时回退默认并记 warning。"""
    # 空配置直接回退，不必尝试解析
    if not raw:
        return DEFAULT_TIMEZONE
    try:
        return ZoneInfo(raw)
    except (ZoneInfoNotFoundError, ValueError):
        # 运行时非法值回退；页面保存会在入口层直接拒绝，不走到这里
        if logger is not None:
            logger.warning(f"display_timezone 不是合法 IANA 名称：{raw!r}，回退到 Asia/Shanghai")
        return DEFAULT_TIMEZONE


def to_local(fetched_at: str, tz: ZoneInfo) -> str:
    """把 UTC ISO 采集时间按传入时区渲染成 YYYY-MM-DD HH:MM:SS。"""
    # 库里的时间固定是 UTC 带 Z，先按同一格式解析，再换到展示时区
    moment = datetime.strptime(fetched_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return moment.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")


def render_changes(changes: list[StatusEvent], fetched_at: str, tz: ZoneInfo) -> str:
    """把一轮变化汇总成一条消息：每条一行，标题后跟类型与状态，链接缩进一行。"""
    lines = [f"检测到 {len(changes)} 条变化（{to_local(fetched_at, tz)}）"]
    for index, event in enumerate(changes, start=1):
        # 标题正常不会为空；真为空时给个占位，不让消息出现空条目
        title = event.title or "未命名事件"
        change_type = EVENT_TYPE_LABELS.get(event.change_type, event.change_type)
        status = STATUS_LABELS.get(event.status, event.status)
        lines.append(f"{index}. {title}（{change_type} / {status}）")
        lines.append(f"   {event.link}")
    return "\n".join(lines)


def render_summary(snapshot: Snapshot, tz: ZoneInfo) -> str:
    """订阅开启时的当前状态摘要；非正常时列出全部未结束事件。"""
    moment = to_local(snapshot.fetched_at, tz)
    unfinished = [event for event in snapshot.events if event.status not in CLOSED_EVENT_STATUSES]
    # 没有未结束事件就是页面上的“一切运行正常”，只回一句状态
    if not unfinished:
        return f"当前状态：一切运行正常（{moment}）"
    lines = [f"当前状态：有 {len(unfinished)} 条未结束事件（{moment}）"]
    for index, event in enumerate(unfinished, start=1):
        # 与变化汇总同一套占位与映射规则，保持两种消息一致
        title = event.title or "未命名事件"
        change_type = EVENT_TYPE_LABELS.get(event.change_type, event.change_type)
        status = STATUS_LABELS.get(event.status, event.status)
        lines.append(f"{index}. {title}（{change_type} / {status}）")
        lines.append(f"   {event.link}")
    return "\n".join(lines)


def render_status_reply(snapshot: Snapshot | None, tz: ZoneInfo) -> str:
    """dsstatus 查状态：有快照就复用摘要，没有就提示刚启动。"""
    # 首次采集还没成功时没有可展示的状态
    if snapshot is None:
        return "监控刚启动，还没有数据"
    return render_summary(snapshot, tz)


def render_help(command_name: str) -> str:
    """命令用法；指令名与子命令都从常量取，改名后帮助自动跟着变。"""
    return (
        f"{command_name} —— DeepSeek 状态页监控\n"
        f"  {command_name}          查看当前状态\n"
        f"  {command_name} {SUBCOMMAND_ON}       开启本群通知\n"
        f"  {command_name} {SUBCOMMAND_OFF}       关闭本群通知\n"
        f"  {command_name} {SUBCOMMAND_HELP}     显示这条说明"
    )
